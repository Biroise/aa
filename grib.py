
import pygrib
from datetime import datetime
from datetime import timedelta

import aa

class File(aa.File) :
	def __init__(self, filePath) :
		self.fileFormat = 'grib'
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
		# sometimes 2D data is followed by 3D data
		self.variableLevels = {}
		verticalExtensions = {}
		gribLine = self._raw.readline()
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			if gribLine.typeOfLevel not in verticalExtensions.keys() :
				verticalExtensions[gribLine.typeOfLevel] = [gribLine.level]
			else :
				verticalExtensions[gribLine.typeOfLevel].append(gribLine.level)
			if gribLine.shortName not in self.variableLevels.keys() :
				self.variableLevels[gribLine.shortName] = gribLine.typeOfLevel
			gribLine = self._raw.readline()
		self.variableNames = self.variableLevels.keys()
		# create a vertical axis if number of levels is credible
		for levelType, levels in verticalExtensions.iteritems() :
			if len(levels) > 1 :
				self.level = aa.Axis(levels, levelType)
			else :
				verticalExtensions[levelType] = None
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

	def __getattr__(self, attributeName) :
		"Load variables on demand"
		if attributeName in self.variableNames :
			if self.variableLevels[attributeName] == None :
				data = np.empty(
						(len(self.time),
						len(self.latitude), len(self.longitude)),
						dtype=float)
				source = f._raw.select(shortName=attributeName)
				for timeIndex in range(len(self.time)) :
					data[timeIndex] = source[timeIndex].values
				return aa.Variable(data, source[0].units,
						(self.time, self.latitude, self.longitude))
			else :
				data = np.empty(
						(len(self.time), len(self.level),
						len(self.latitude), len(self.longitude)),
						dtype=float)
				source = f._raw.select(shortName=attributeName)
				for timeIndex in range(len(self.time)) :
					for levelIndex in range(len(self.level)) :
						data[timeIndex, levelIndex] = source[timeIndex].values
				return aa.Variable(data, source[0].units,
						(self.time, self.level, self.latitude, self.longitude))
		else :
			raise AttributeError
	

if __name__ == "__main__" :
	f = aa.open('/home/ambroise/atelier/anniversaire/tmp.grib')

