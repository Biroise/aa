
import pygrib
import numpy as np
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
		gribLine = rawFile.readline()
		firstInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		###################
		# HORIZONTAL AXES #
		###################
		lats, lons = gribLine.latlons()
		if lats[0, 0] == lats[0, 1] :
			self.axes['latitude'] = aa.Axis(lats[:, 0], 'degrees')
			self.axes['longitude'] = aa.Parallel(lons[0, :], 'degrees')
		else :
			self.axes['latitude'] = aa.Axis(lats[0, :], 'degrees')
			self.axes['longitude'] = aa.Parallel(lons[:, 0], 'degrees')
		# give the lats to lon to get the proper weights
		self.axes['longitude'].latitudes = self.axes['latitude'].data
		rawFile.rewind()
		#################
		# VERTICAL AXIS #
		#################
		# sometimes there are several types of level
		# 2D data is followed by 3D data e.g. jra25
		variablesLevels = {}					# variable - level type - level
		gribLine = rawFile.readline()
		# loop through the variables and levels of the first time step
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			# is it the first time this variable is met ?
			if gribLine.shortName not in variablesLevels :
				variablesLevels[gribLine.shortName] = {}
			if gribLine.typeOfLevel not in \
					variablesLevels[gribLine.shortName] :
				variablesLevels[gribLine.shortName][gribLine.typeOfLevel] = []
			variablesLevels[gribLine.shortName][gribLine.typeOfLevel]\
					.append(gribLine.level)
			# move to the next line
			gribLine = rawFile.readline()
		# find the longest vertical axis
		maxLevelNumber = 0
		for variableName, levelKinds in variablesLevels.iteritems() :
			for levelType, levels in levelKinds.iteritems() :
				if len(levels) > 1 :
					variablesLevels[variableName][levelType] \
							= aa.Axis(np.array(levels), levelType)
				else :
					variablesLevels[variableName][levelType] = False
				if len(levels) > maxLevelNumber :
					maxLevelNumber = len(levels)
					mainLevels = aa.Axis(np.array(levels), levelType)
		self.axes['level'] = mainLevels
		#############
		# TIME AXIS #
		#############
		# "seek/tell" index starts with 0 : -1
		linesPerInstant = rawFile.tell() - 1
		# determine the interval between two samples
		gribLine = rawFile.readline()
		secondInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		timeStep = secondInstant - firstInstant
		# go to the end
		rawFile.seek(0, 2)
		lastIndex = rawFile.tell()
		self.axes['time'] = aa.TimeAxis(
				np.array([firstInstant + timeIndex*timeStep
					for timeIndex in range(lastIndex/linesPerInstant)]),
				None)
		# check consistency
		gribLine = rawFile.message(lastIndex)
		lastInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		if lastInstant != self.axes['time'][-1] or \
				lastIndex % linesPerInstant != 0 :
			print "Error in time axis"
		rawFile.rewind()
		#############
		# VARIABLES #
		#############
		for variableName, levelKinds in variablesLevels.iteritems() :
			for levelType, verticalAxis in levelKinds.iteritems() :
				location = {'shortName' : variableName.encode('ascii'),
						'typeOfLevel' : levelType.encode('ascii')}
				axes = aa.Axes()
				axes['time'] = self.axes['time']
				variableLabel = variableName + '_' + levelType
				# does this variable have a vertical extension ?
				# it may not be the file's vertical axis
				if verticalAxis :
					axes['level'] = verticalAxis
					# in case of homonyms, only the variable with the main 
					# vertical axis gets to keep the original shortname
					if verticalAxis.units == mainLevels.units :
						variableLabel = variableName
				else :
					# flat level i.e. 2D data
					location['level'] = levelType
				# no ambiguity
				if len(levelKinds) == 1 :
					variableLabel = variableName
				axes['latitude'] = self.axes['latitude']
				axes['longitude'] = self.axes['longitude']
				self.variables[variableLabel] = \
						Variable(axes, {}, location, fileName)
		##################
		# PICKLE & INDEX #
		##################
		rawFile.close()
		pickleFile = open(fileName+'.p', 'w')
		aa.pickle.dump(self, pickleFile)
		pickleFile.close()
		gribIndex = pygrib.index(filePath,
						'shortName', 'level', 'typeOfLevel',
						'year', 'month', 'day', 'hour')
		gribIndex.write(fileName+'.idx')
		gribIndex.close()
	
	def __getattr__(self, attributeName) :
		if hasattr(self, 'variables') and hasattr(self, 'axes') :
			return super(File, self).__getattr__(attributeName)
		raise AttributeError
	

class Variable(aa.Variable) :
	def __init__(self, axes, metadata, conditions, fileName) :
		super(Variable, self).__init__()
		self.axes = axes
		self.metadata = metadata
		self.conditions = conditions
		self.fileName = fileName
	
	def __getattr__(self, attributeName) :
		if hasattr(self, 'axes') :
			return self.axes[attributeName]
		raise AttributeError

	def __call__(self, **kwargs) :
		"Extract a subset via its axes"
		# if the variable is still in pure grib mode
		if "_data" not in self.__dict__ :
			# conditions and axes of the output variable
			newConditions = self.conditions.copy()
			newAxes = self.axes.copy()
			for axisName, condition in kwargs.iteritems() :
				# standardize the axis name
				axisName = aa.Axes.aliases[axisName]
				# given the condition, call axis for a new version
				item, newAxis = self.axes[axisName](condition)
				# lat/lon get a special treatment within grib messages (array)
				if axisName in ['latitude', 'longitude'] :
					# already restrictions on lat/lon in the former conditions ?
					if axisName in self.conditions :
						# slices of slices not handled
						raise NotImplementedError
					else :
						newConditions[axisName] = item
				# time and level slices need to be made explicit
				else :
					# to what datetimes and pressures
					# do the conditions correspond ? slice former axis
					newConditions[axisName] = \
						self.axes[axisName][item]
				# if item is scalar, there will be no need for length 1 axis
				if newAxis == None :
					del newAxes[axisName]
					# make sure newConditions is still iterable though
					newConditions[axisName] = \
						[newConditions[axisName]]
				# otherwise, load newAxis in the new variable's axes
				else :
					newAxes[axisName] = newAxis
				if axisName == 'latitude' and 'longitude' in newAxes :
					newAxes['longitude'].latitudes = \
							self.axes['latitude'][newConditions['latitude']]\
							.reshape((-1,))
			return Variable(newAxes, self.metadata.copy(),
						newConditions, self.fileName)
		# if _data already exists (as a numpy array), follow standard protocol
		else :
			return super(Variable, self).__call__(**kwargs)
	
	def _get_data(self) :
		"Loads variable.data ; leave it to the last minute"
		if not hasattr(self, '_data') :
			# dummy conditions to play with (possibly superfluous)
			newConditions = self.conditions.copy()
			# scalar conditions only
			subConditions = self.conditions.copy()
			################
			# TIME & LEVEL #
			################
			# scalar conditions only
			subConditions = self.conditions.copy()
			################
			# TIME & LEVEL #
			################
			# assumes grib files always have a time dimension
			if 'time' not in self.conditions :
				newConditions['time'] = self.axes['time'].data
			else :
				# won't be needing it : year/month/day/hour instead
				del subConditions['time']
			# if data is 2D, it will have level in self.conditions
			# idem if it's 3D and has already been sliced
			if 'level' not in self.conditions :
				newConditions['level'] = self.axes['level'].data
			########################
			# LATITUDE & LONGITUDE #
			########################
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
			#####################
			# GET GRIB MESSAGES #
			#####################
			# gribLines will store all the results of our select queries
			gribLines = []
			gribIndex = pygrib.index(self.fileName+'.idx')
			for instant in newConditions['time'] :
				subConditions['year'] = instant.year
				subConditions['month'] = instant.month
				subConditions['day'] = instant.day
				subConditions['hour'] = instant.hour
				for level in newConditions['level'] :
					subConditions['level'] = np.asscalar(level)
					gribLines.extend(gribIndex(**subConditions))
			gribIndex.close()
			##############
			# FILL ARRAY #
			##############
			shape = ()
			for axisName, axis in self.axes.iteritems() :
				shape = shape + (len(axis),)
			self._data = np.empty(shape, dtype=float)
			# flatten time and levels
			self._data.shape = (-1,) + self._data.shape[-2:]
			if twistedLongitudes :
				for lineIndex, gribLine in enumerate(gribLines) :	
					self._data[lineIndex, ..., slice1] = \
						gribLine.values[mask]
					self._data[lineIndex, ..., slice2] = \
						gribLine.values[secondMask]
			else :
				for lineIndex, gribLine in enumerate(gribLines) :	
					self._data[lineIndex] = gribLine.values[mask]
			self._data.shape = shape
		return self._data
	def _set_data(self, newValue) :
		self._data = newValue
	data = property(_get_data, _set_data)
