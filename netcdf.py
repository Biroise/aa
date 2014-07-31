
import aa
import numpy as np
import netCDF4 as nc
import operator as op
from collections import OrderedDict
#from scipy.io.netcdf import netcdf_file



class File(aa.File) :
	def __init__(self, filePath, mode) :
		super(File, self).__init__()
		#self._raw = netcdf_file(filePath)
		self._raw = nc.Dataset(filePath, mode)
		########
		# AXES #
		########
		for dimensionName in self._raw.dimensions.keys() :
			if dimensionName in self._raw.variables.keys() :
				args = [self._raw.variables[dimensionName][:],
							self._raw.variables[dimensionName].units]
				if dimensionName == 'time' :
					self.axes[dimensionName] = aa.TimeAxis(*args)
				elif dimensionName in ['longitude', 'longitudes', 'lon'] :	
					self.axes[dimensionName] = aa.Parallel(*args)
				else :
					self.axes[dimensionName] = aa.Axis(*args)
		#############
		# VARIABLES #
		#############
		for variableName in set(self._raw.variables.keys()) \
				- set(self._raw.dimensions.keys()) :
			variableAxes = OrderedDict()
			for axisName in self._raw.variables[variableName].dimensions :
				if axisName in self.axes.keys() :
					variableAxes[axisName] = self.axes[axisName]
			self.variables[variableName] = \
					Variable(
						self._raw.variables[variableName][:], {},
						variableAxes)


class Variable(aa.Variable) :
	pass

