
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

#import numpy as np
import matplotlib.pyplot as plt
from scipy.io.netcdf import netcdf_file
from datetime import datetime
from datetime import timedelta


class DataFile(object) :
	def __init__(self, filePath, mode = 'r') :
		if filePath.endswith('nc') :
			self.fileFormat = 'nc'
			self.raw = netcdf_file(filePath, mode)
			self.dimensionNames = set(self.raw.dimensions.keys())
			self.variableNames = set(self.raw.variables.keys()) \
					- self.dimensionNames
			# create axes
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
		else :
			print "Format not supported"

	# load variables on demand
	def __getattr__(self, attributeName) :
		if attributeName in self.variableNames :
			return Variable(
				self.raw.variables[attributeName].data)
		else :
			raise AttributeError


class Variable(object) :
	def __init__(self, data) :
		self.data = data
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


class Axis(object) :
	def __init__(self, data, units) :
		self.data = data
		self.units = units
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


class TimeAxis(Axis) :
	def __init__(self, data, unitDefinition) :
		super(TimeAxis, self).__init__(data, unitDefinition)
		# unit definition is conventionally :
		# seconds/hours/days since YYYY-MM-DD HH
		words = unitDefinition.split()
		if words[1] != 'since' :
			print "Unconventional definition of time units"
		units = words[0]
		date = [int(bits) for bits in words[2].split('-')]
		epoch = datetime(date[0], date[1], date[2])
		self.data = [epoch + timedelta(**{units: offset}) for offset in self.data]

		


f = DataFile('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')

