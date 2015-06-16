
import pygrib
import numpy as np
import cPickle as pickle
from operator import itemgetter
from os.path import splitext
from datetime import datetime
from datetime import timedelta

import aa


class File(aa.File) :
	def __init__(self, filePath) :
		super(File, self).__init__()
		fileName = splitext(filePath)[0]
		rawFile = pygrib.open(filePath)
		# read the first line of the file
		gribLine = rawFile.readline()
		firstInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		###################
		# HORIZONTAL AXES #
		###################
		lats, lons = gribLine.latlons()
		if lats[0, 0] == lats[0, 1] :
			self.axes['latitude'] = aa.Meridian(lats[:, 0], 'degrees')
			self.axes['longitude'] = aa.Parallel(lons[0, :], 'degrees')
		else :
			self.axes['latitude'] = aa.Meridian(lats[0, :], 'degrees')
			self.axes['longitude'] = aa.Parallel(lons[:, 0], 'degrees')
		#################
		# VERTICAL AXIS #
		#################
		# sometimes there are several types of level
		# 2D data is followed by 3D data e.g. jra25
		variablesLevels = {}					# variable - level type - level
		variablesMetaData = {}
		# loop through the variables and levels of the first time step
		# default : grib has a time axis
		timeDimension = True
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			# is it the first time this variable is met ?
			if gribLine.shortName not in variablesLevels :
				# create a dictionary for that variable
				# that will contain different level types
				variablesLevels[gribLine.shortName] = {}
				variablesMetaData[gribLine.shortName] = {}
				variablesMetaData[gribLine.shortName]['shortName'] = gribLine.shortName
				variablesMetaData[gribLine.shortName]['units'] = gribLine.units
				variablesMetaData[gribLine.shortName]['name'] = gribLine.name
			# is this the first time this type of level is met ?
			if gribLine.typeOfLevel not in \
					variablesLevels[gribLine.shortName] :
					# create a list that will contain the level labels
				variablesLevels[gribLine.shortName][gribLine.typeOfLevel] = []
			# append the level label to the variable / level type
			variablesLevels[gribLine.shortName][gribLine.typeOfLevel]\
					.append(gribLine.level)
			# move to the next line
			gribLine = rawFile.readline()
			if gribLine == None :
				timeDimension = False
				break
		# find the longest vertical axis
		maxLevelNumber = 0
		for variableName, levelKinds in variablesLevels.iteritems() :
			for levelType, levels in levelKinds.iteritems() :
				# does levels look like a proper axis ?
				if len(levels) > 1 :
					variablesLevels[variableName][levelType] \
							= aa.Vertical(np.array(levels), levelType)
				# is levels longer than the previous longest axis ?
				if len(levels) > maxLevelNumber :
					maxLevelNumber = len(levels)
					mainLevels = aa.Vertical(np.array(levels), levelType)
		# the longest vertical axis gets to be the file's vertical axis
		self.axes['level'] = mainLevels
		if timeDimension :
			#############
			# TIME AXIS #
			#############
			# "seek/tell" index starts with 1
			# but we've moved on the next instant at the end of the while loop
			# hence the minus one
			linesPerInstant = rawFile.tell() - 1
			# determine the interval between two samples
			secondInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
						gribLine.hour, gribLine.minute, gribLine.second)
			timeStep = secondInstant - firstInstant
			# go to the end of the file
			rawFile.seek(0, 2)
			lastIndex = rawFile.tell()
			# this index points at the last message
			# e.g. f.message(lastIndex) returns the last message
			# indices start at 1 meaning that lastIndex is also the
			# number of messages in the file
			self.axes['time'] = aa.TimeAxis(
					np.array([firstInstant + timeIndex*timeStep
						for timeIndex in range(lastIndex/linesPerInstant)]), None)
			# check consistency
			gribLine = rawFile.message(lastIndex)
			lastInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
						gribLine.hour, gribLine.minute, gribLine.second)
			if lastInstant != self.dts[-1] or \
					lastIndex % linesPerInstant != 0 :
				raise Exception, "Error in time axis"
		rawFile.rewind()
		#############
		# VARIABLES #
		#############
		for variableName, levelKinds in variablesLevels.iteritems() :
			for levelType, verticalAxis in levelKinds.iteritems() :
				conditions = {'shortName' : variableName.encode('ascii'),
						'typeOfLevel' : levelType.encode('ascii')}
				axes = aa.Axes()
				if timeDimension :
					axes['time'] = self.axes['time']
				else :
					conditions['time'] = firstInstant
				variableLabel = variableName + '_' + levelType
				# does this variable have a vertical extension ?
				# it may not be the file's vertical axis
				if len(verticalAxis) > 1 :
					axes['level'] = verticalAxis
					# in case of homonyms, only the variable with the main 
					# vertical axis gets to keep the original shortname
					if verticalAxis.units == mainLevels.units :
						variableLabel = variableName
				else :
					# flat level i.e. 2D data
					# the condition is a list to be iterable
					conditions['level'] = verticalAxis
				# no ambiguity
				if len(levelKinds) == 1 :
					variableLabel = variableName
				axes['latitude'] = self.axes['latitude']
				axes['longitude'] = self.axes['longitude']
				self.variables[variableLabel] = \
						Variable(axes, variablesMetaData[variableName],
								conditions, fileName)

		##################
		# PICKLE & INDEX #
		##################
		rawFile.close()
		pickleFile = open(fileName+'.p', 'w')
		#import pdb ; pdb.set_trace()
		pickle.dump(self, pickleFile)
		pickleFile.close()
		gribIndex = pygrib.index(filePath,
						'shortName', 'level', 'typeOfLevel',
						'year', 'month', 'day', 'hour')
		gribIndex.write(fileName+'.idx')
		gribIndex.close()	


class Variable(aa.Variable) :
	def __init__(self, axes, metadata, conditions,
			fileName, full_axes = None) :
		super(Variable, self).__init__()
		self.axes = axes
		if full_axes == None :
			self.full_axes = axes.copy()
		else :
			self.full_axes = full_axes
		self.metadata = metadata
		self.conditions = conditions
		self.fileName = fileName
	
	@property
	def shape(self) :
		if "_data" not in self.__dict__ :
			dimensions = []
			for axis in self.axes.values() :
				dimensions.append(len(axis))
			return tuple(dimensions)	
		else :
			return super(Variable, self).shape
	
	def __getitem__(self, item) :
		# if the variable is still in pure grib mode
		if "_data" not in self.__dict__ :
			conditions = {}
			# make item iterable, even when it's a singleton
			if not isinstance(item, tuple) :
				if not isinstance(item, list) :
					item = (item,)
			# loop through axes in their correct order
			# and match axis with a sub-item
			for axisIndex, axisName in enumerate(self.axes) :
				# there may be more axes than sub-items
				# do not overshoot
				if axisIndex < len(item) :
					# if it's a single index slice
					if not isinstance(item[axisIndex], slice) :
						conditions[axisName] = \
							self.axes[axisName].data[item[axisIndex]]
					else :
						# it's a slice
						# if it's a ':' slice, do nothing
						if item[axisIndex] != slice(None) :
							conditions[axisName] = \
									(self.axes[axisName][item[axisIndex]].min(),
									self.axes[axisName][item[axisIndex]].max())
			return self(**conditions)
		# if _data already exists (as a numpy array), follow standard protocol
		else :
			return super(Variable, self).__getitem__(item)

	def extract_data(self, **kwargs) :
		"Extract a subset via its axes"
		# if the variable is still in pure grib mode
		if "_data" not in self.__dict__ :
			# conditions and axes of the output variable
			newConditions = self.conditions.copy()
			newAxes = self.axes.copy()
			for axisName, condition in kwargs.iteritems() :
				# lat/lon get a special treatment within grib messages (array)
				if axisName in ['latitude', 'longitude'] :
					# there may already be restrictions on lat/lon from former calls
					# refer to the complete axes to define the new slice
					item, newAxis = self.full_axes[axisName](condition)
					newConditions[axisName] = item
				# time and level slices need to be made explicit
				else :
					# given the condition, call axis for a new version
					item, newAxis = self.axes[axisName](condition)
					# to what datetimes and pressures
					# do the conditions correspond ? slice former axis
					newConditions[axisName] = \
						self.axes[axisName][item]
					# make sure newConditions is still iterable though
					if not isinstance(newConditions[axisName], list) :
						if not isinstance(newConditions[axisName], np.ndarray) :
							newConditions[axisName] = \
								[newConditions[axisName]]
				# if item is scalar, there will be no need for an axis
				if newAxis == None :
					del newAxes[axisName]
					self.metadata[axisName] = condition
				# otherwise, load newAxis in the new variable's axes
				else :
					newAxes[axisName] = newAxis
			return Variable(newAxes, self.metadata.copy(),
						newConditions, self.fileName, self.full_axes.copy())
		# if _data already exists (as a numpy array), follow standard protocol
		else :
			return super(Variable, self).extract_data(**kwargs)
	
	def _get_data(self) :
		if '_data' not in self.__dict__ :
			# dummy conditions to play with
			newConditions = self.conditions.copy()
			# scalar conditions only (input for the gribIndex)
			subConditions = self.conditions.copy()
			################
			# TIME & LEVEL #
			################
			if 'time' not in self.conditions :
				newConditions['time'] = self.axes['time'].data
			else :
				# gribIndex won't want lists of datetimes
				# but rather individual year/month/day/hour
				del subConditions['time']
				# make sure time condition is iterable
				if not isinstance(newConditions['time'], list) :
					if not isinstance(newConditions['time'], np.ndarray) :
						newConditions['time'] = [newConditions['time']]
			# if data is 2D, it will have already have a level condition
			# idem if it's 3D and has already been sliced
			# if not, that means the user wants all available levels
			if 'level' not in self.conditions :
				newConditions['level'] = self.axes['level'].data
			########################
			# LATITUDE & LONGITUDE #
			########################
			### MASK ###
			# mask is used to slice the netcdf array contained in gribMessages
			mask = []
			if 'latitude' in self.conditions :
				del subConditions['latitude']
				mask.append(self.conditions['latitude'])
			else :
				mask.append(slice(None))
			twistedLongitudes = False
			if 'longitude' in self.conditions :
				del subConditions['longitude']
				# twisted longitudes...
				if type(self.conditions['longitude']) == tuple :
					twistedLongitudes = True
					secondMask = mask[:]
					mask.append(self.conditions['longitude'][0])
					slice1 = slice(0, -mask[-1].start)
					secondMask.append(self.conditions['longitude'][1])
					slice2 = slice(-secondMask[-1].stop, None)
				else :
					mask.append(self.conditions['longitude'])
			else :
				mask.append(slice(None))
			mask = tuple(mask)
			### HORIZONTAL SHAPE ###
			# shape of the output array : (time, level, horizontalShape)
			horizontalShape = []
			if hasattr(self, 'lats') :
				horizontalShape.append(len(self.lats))
			if hasattr(self, 'lons') :
				horizontalShape.append(len(self.lons))
			horizontalShape = tuple(horizontalShape)
			#####################
			# GET GRIB MESSAGES #
			#####################
			shape = ()
			for axisName, axis in self.axes.iteritems() :
				shape = shape + (len(axis),)
			# build the output numpy array
			self._data = np.empty(shape, dtype=float)
			# flatten time and level dimensions
			# that's in case there's neither time nor level dimension
			self._data.shape = (-1,) + horizontalShape
			# load the grib index
			gribIndex = pygrib.index(self.fileName+'.idx')
			lineIndex = 0
			for instant in newConditions['time'] :
				subConditions['year'] = instant.year
				subConditions['month'] = instant.month
				subConditions['day'] = instant.day
				subConditions['hour'] = instant.hour
				for level in newConditions['level'] :
					subConditions['level'] = \
						np.asscalar(np.array(level))
						# converts numpy types to standard types
						# standard types are converted to numpy
					# normally, there should be only one line
					# that answers our query
					gribLine = gribIndex(**subConditions)[0]
					if twistedLongitudes :
						self._data[lineIndex, ..., slice1] = \
							gribLine.values[mask]
						self._data[lineIndex, ..., slice2] = \
							gribLine.values[secondMask]
					else :
						self._data[lineIndex] = gribLine.values[mask]
					lineIndex += 1
			gribIndex.close()
			self._data.shape = shape
		return self._data
	def _set_data(self, newValue) :
		self._data = newValue
	data = property(_get_data, _set_data)

