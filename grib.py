
import pygrib
from datetime import datetime
from datetime import timedelta

import aa

class File(aa.File) :
	def __init__(self, filePath) :
		super(File, self).__init__()
		self._raw = pygrib.open(filePath)
		gribLine = self._raw.readline()
		firstInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		###################
		# HORIZONTAL AXES #
		###################
		lats, lons = gribLine.latlons()
		if lats[0, 0] == lats[0, 1] :
			self.latitude = aa.Axis(lats[:, 0], 'degrees')
			self.longitude = aa.Axis(lons[0, :], 'degrees')
		else :
			self.latitude = aa.Axis(lats[0, :], 'degrees')
			self.longitude = aa.Axis(lons[:, 0], 'degrees')
		self._raw.rewind()
		#################
		# VERTICAL AXIS #
		#################
		# sometimes 2D data is followed by 3D data e.g. jra25
		variableLevels = {}	# variable and level type
		verticalExtensions = {} 	# level type and list of levels
		gribLine = self._raw.readline()
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			if gribLine.typeOfLevel not in verticalExtensions.keys() :
				verticalExtensions[gribLine.typeOfLevel] = [gribLine.level]
			else :
				verticalExtensions[gribLine.typeOfLevel].append(gribLine.level)
			if gribLine.shortName not in variableLevels.keys() :
				variableLevels[gribLine.shortName] = gribLine.typeOfLevel
			gribLine = self._raw.readline()
		# create a vertical axis if number of levels is credible
		for levelType, levels in verticalExtensions.iteritems() :
			if len(levels) > 1 :
				self.level = aa.Axis(levels, levelType)
				verticalExtensions[levelType] = True
			else :
				verticalExtensions[levelType] = False
		#############
		# TIME AXIS #
		#############
		# "seek/tell" index starts with 0 : -1
		linesPerInstant = self._raw.tell() - 1
		# determine the interval between two samples
		gribLine = self._raw.readline()
		secondInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		timeStep = secondInstant - firstInstant
		# go to the end
		self._raw.seek(0, 2)
		lastIndex = self._raw.tell()
		self.time = aa.TimeAxis(
				[firstInstant + timeIndex*timeStep
					for timeIndex in range(lastIndex/linesPerInstant)],
				None)
		# check consistency
		gribLine = self._raw.message(lastIndex)
		lastInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		if lastInstant != self.time[-1] or \
				lastIndex % linesPerInstant != 0 :
			print "Error in time axis"
		self._raw.rewind()
		########
		# AXES #
		########
		self.axes['time'] = self.time
		self.axes['level'] = self.level
		self.axes['latitude'] = self.latitude
		self.axes['longitude'] = self.longitude
		#############
		# VARIABLES #
		#############
		for variableName, levelType in variableLevels.iteritems() :
			axes = aa.OrderedDict()
			axes['time'] = self.time
			# does this variable have a vertical extension ?
			if verticalExtensions[levelType] :
				axes['level'] = self.level
			axes['latitude'] = self.latitude
			axes['longitude'] = self.longitude
			self.variables[variableName] = Variable(axes, self._raw)

	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		elif attributeName in self.variables.keys() :
			return self.variables[attributeName]
		else :
			raise AttributeError
	

class Variable(aa.Variable) :
	def __init__(self, axes, rawFile) :
		super(Variable, self).__init__()
		self._raw = rawFile
		self.axes = axes
	
	def __call__(self, **kwargs) :
		# the standard way to extract a subset
		raise NotImplemented
	
	def get_data(self) :
		"Loads variable.data ; a waste of time for most uses"
		self._data = np.empty(
				(len(self.time), len(self.level),
				len(self.latitude), len(self.longitude)),
				dtype=float)
		source = f._raw.select(shortName=attributeName)
		for timeIndex in range(len(self.time)) :
			for levelIndex in range(len(self.level)) :
				self._data[timeIndex, levelIndex] = source[timeIndex].values
		return self._data
	def set_data(self, newValue) :
		self._data = newValue
	data = property(get_data, set_data)
		
	def __getitem__(self, *args, **kwargs) :
		# only if indices are used specifically must the whole data be loaded
		return self.data.__getitem__(*args, **kwargs)

