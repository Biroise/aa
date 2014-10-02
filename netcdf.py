
import aa
import numpy as np
import netCDF4 as nc
import operator as op
#from scipy.io.netcdf import netcdf_file



class File(aa.File) :
	def __init__(self, filePath, mode) :
		super(File, self).__init__()
		#self._raw = netcdf_file(filePath)
		self._raw = nc.Dataset(filePath, mode)
		########
		# AXES #
		########
		for dimensionName in self._raw.dimensions :
			if dimensionName in self._raw.variables :
				if hasattr(self._raw.variables[dimensionName], 'units') :
					units = self._raw.variables[dimensionName].units
				else :
					units = None
				args = [self._raw.variables[dimensionName][:], units]
				if aa.Axes.aliases[dimensionName] == 'time' :
					self.axes[dimensionName] = aa.TimeAxis(*args)
				elif aa.Axes.aliases[dimensionName] == 'longitude' :
					self.axes[dimensionName] = aa.Parallel(*args)
				else :
					self.axes[aa.Axes.aliases[dimensionName]] = aa.Axis(*args)
		#############
		# VARIABLES #
		#############
		for variableName in set(self._raw.variables.keys()) \
				- set(self._raw.dimensions.keys()) :
			variableAxes = aa.Axes()
			for axisName in self._raw.variables[variableName].dimensions :
				if axisName in aa.Axes.aliases :
					axisName = aa.Axes.aliases[axisName]
					if axisName in self.axes :
						variableAxes[axisName] = self.axes[axisName]
			self.variables[variableName] = \
					Variable(
						self._raw.variables[variableName][:], {},
						variableAxes, self._raw)
	
	def close(self) :
		self._raw.close()


class Variable(aa.Variable) :
	def __init__(self, data, metadata, axes, rawFile)	:
		super(Variable, self).__init__(data, metadata, axes)
		self._raw = rawFile
	
	def close(self) :
		self._raw.close()

		

