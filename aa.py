
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

#import numpy as np
import pygrib
import matplotlib.pyplot as plt
from scipy.io.netcdf import netcdf_file
from datetime import datetime
from datetime import timedelta


class DataFile(object) :
	def close(self) :
		self.raw.close()
		del self

class NetcdfFile(DataFile) :
	def __init__(self, filePath) :
		self.fileFormat = 'nc'
		self.raw = netcdf_file(filePath, mode)
		self.dimensionNames = set(self.raw.dimensions.keys())
		self.variableNames = set(self.raw.variables.keys()) \
				- self.dimensionNames
		########
		# AXES #
		########
		for dimensionName in self.dimensionNames :
			if dimensionName == 'time' :
				setattr(self, dimensionName, TimeAxis(
					self.raw.variables[dimensionName].data,
					self.raw.variables[dimensionName].units
					))
			else :
				setattr(self, dimensionName, Axis(
					self.raw.variables[dimensionName].data,
					self.raw.variables[dimensionName].units
					))

	def __getattr__(self, attributeName) :
		"Load variables on demand"
		if attributeName in self.variableNames :
			return Variable(
				self.raw.variables[attributeName].data,
				self.raw.variables[attributeName].units,
				[getattr(self, dimensionName) for dimensionName in
					self.raw.variables[attributeName].dimensions]
				)
		else :
			raise AttributeError
	

class GribFile(DataFile) :
	def __init__(self, filePath) :
		self.fileFormat = 'grib'
		self.raw = pygrib.open(filePath)
		gribLine = self.raw.readline()
		firstInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		###################
		# HORIZONTAL AXES #
		###################
		lats, lons = gribLine.latlons()
		if lats[0, 0] == lats[0, 1] :
			self.latitude = Axis(lats[:, 0], 'degrees')
			self.longitude = Axis(lons[0, :], 'degrees')
		else :
			self.latitude = Axis(lats[0, :], 'degrees')
			self.longitude = Axis(lons[:, 0], 'degrees')
		self.raw.rewind()
		#################
		# VERTICAL AXIS #
		#################
		# sometimes 2D data is followed by 3D data
		self.variableLevels = {}
		verticalExtensions = {}
		while datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)\
					== firstInstant :
			gribLine = self.raw.readline()
			if gribLine.typeOfLevel not in verticalExtensions.keys() :
				verticalExtensions[gribLine.typeOfLevel] = [gribLine.level]
			if gribLine.shortName not in self.variableLevels.keys() :
				self.variableLevels[gribLine.shortName] = gribLine.typeOfLevel
		self.variableNames = self.variableLevels.keys()
		# create a vertical axis if number of levels is credible
		for levelType, levels in verticalExtensions.iteritems() :
			if len(levels) != 1 :
				self.level = Axis(levels, levelType)
		#############
		# TIME AXIS #
		#############
		# "seek/tell" index starts with 0 : -1
		linesPerInstant = self.raw.tell() - 1
		# determine the interval between two samples
		gribLine = self.raw.readline()
		secondInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		timeStep = secondInstant - firstInstant
		# go to the end
		self.raw.seek(0, 2)
		lastIndex = self.raw.tell()
		self.time = TimeAxis(
				[firstInstant + timeIndex*timeStep
					for timeIndex in range(lastIndex/linesPerInstant)],
				None)
		# check consistency
		gribLine = self.raw.message(lastIndex)
		lastInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
					gribLine.hour, gribLine.minute, gribLine.second)
		if lastInstant != self.time[-1] or \
				lastIndex % linesPerInstant != 0 :
			print "Error in time axis"
		self.raw.rewind()

	def __getattr__(self, attributeName) :
		"Load variables on demand"
		if attributeName in self.variableNames :
			pass
		else :
			raise AttributeError
	
def open(filePath) :
	"Picks the appropriate DataFile subclass to model a gridded data file"
	if filePath.endswith('nc') :
		return NetcdfFile(filePath)
	if filePath.endswith('grib') :
		return GribFile(filePath)


class Variable(object) :
	def __init__(self, data, units, axes) :
		self.data = data
		self.units = units
		self.axes = axes
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)

	#def mean
	#def getitem
	#def slices puissantes
	#def interpolation
	#def map


class Axis(object) :
	def __init__(self, data, units) :
		self.data = data
		self.units = units
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


class TimeAxis(Axis) :
	def __init__(self, data, unitDefinition=None) :
		super(TimeAxis, self).__init__(data, unitDefinition)
		if unitDefinition != None :
			# unit definition is conventionally :
			# seconds/hours/days since YYYY-MM-DD HH
			words = unitDefinition.split()
			if words[1] != 'since' :
				print "Unconventional definition of time units"
			units = words[0]
			date = [int(bits) for bits in words[2].split('-')]
			epoch = datetime(date[0], date[1], date[2])
			self.data = [epoch + timedelta(**{units: offset}) for offset in self.data]


#f = DataFile('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
f = open('/home/ambroise/atelier/anniversaire/tmp.grib')

