
import pygrib
import numpy as np
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
		rawFile.rewind()
		#################
		# VERTICAL AXIS #
		#################
		# sometimes there are several types of level
		# 2D data is followed by 3D data e.g. jra25
		variableLevels = {}					# variable and level type
		verticalExtensions = {} 			# level type and list of levels
		gribLine = rawFile.readline()
		# loop through the variables and levels of the first time step
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			# is it the first time this type of level is met ?
			if gribLine.typeOfLevel not in verticalExtensions :
				verticalExtensions[gribLine.typeOfLevel] = [gribLine.level]
			# the level type already exists : does this particular level too ?
			elif gribLine.level not in \
					verticalExtensions[gribLine.typeOfLevel] :
				verticalExtensions[gribLine.typeOfLevel].append(gribLine.level)
			# is it the first time this variable is met ?
			if gribLine.shortName not in variableLevels :
				variableLevels[gribLine.shortName] = gribLine.typeOfLevel
			# move to the next line
			gribLine = rawFile.readline()
		# create a vertical axis if the number of levels is credible
		for levelType, levels in verticalExtensions.iteritems() :
			if len(levels) > 1 :
				self.axes['level'] = aa.Axis(np.array(levels), levelType)
				verticalExtensions[levelType] = True
			else :
				verticalExtensions[levelType] = False
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
		for variableName, levelType in variableLevels.iteritems() :
			axes = aa.Axes()
			axes['time'] = self.axes['time']
			# does this variable have a vertical extension ?
			if verticalExtensions[levelType] :
				axes['level'] = self.axes['level']
			axes['latitude'] = self.axes['latitude']
			axes['longitude'] = self.axes['longitude']
			location = {'shortName' : variableName,
					'typeOfLevel' : self.axes['level'].units}
			self.variables[variableName] = \
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
				# already restrictions on lat/lon in the former conditions ?
				if axisName in ['latitude', 'longitude'] :
					if axisName in self.conditions :
						# slices of slices not handled
						raise NotImplementedError
					else :
						newConditions[axisName] = item
				# time and level slices need to be made explicit
				else :
					# to what datetimes and pressures
					# do the conditions correspond ? slice former axis
					newConditions[axisName] = self.axes[axisName][item]
				# if item is scalar, there will be no need for length 1 axis
				if newAxis == None :
					del newAxes[axisName]
				# otherwise, load newAxis in the new variable's axes
				else :
					newAxes[axisName] = newAxis
			return Variable(newAxes, self.metadata, newConditions, self.fileName)
		# if _data already exists (as a numpy array), follow standard protocol
		else :
			return super(Variable, self).__call__(**kwargs)
	
	def _get_data(self) :
		"Loads variable.data ; leave it to the last minute"
		if '_data' not in self.__dict__ :
			newConditions = self.conditions.copy()
			if 'time' in self.conditions :
				newConditions['year'] = newConditions['time'].year
				newConditions['month'] = newConditions['time'].month
				newConditions['day'] = newConditions['time'].day
				newConditions['hour'] = newConditions['time'].hour
				del newConditions['time']
			mask = []
			if 'latitude' in self.conditions :
				del newConditions['latitude']
				mask.append(self.conditions['latitude'])
			else :
				mask.append(slice(None))
			twistedLongitudes = False
			if 'longitude' in self.conditions :
				del newConditions['longitude']
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
			gribIndex = pygrib.index(self.fileName+'.idx')
			print newConditions
			gribLines = gribIndex(**newConditions)
			#gribLines = gribIndex(hour=12, day=1, year=1979, month=1, shortName='q',
				#typeOfLevel='isobaricInhPa', level=1000)
			print gribLines
			gribIndex.close()
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

