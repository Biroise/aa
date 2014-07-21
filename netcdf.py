
import aa
import numpy as np
import netCDF4 as nc
import operator as op
#from scipy.io.netcdf import netcdf_file



class File(aa.File) :
	def __init__(self, filePath) :
		super(File, self).__init__()
		#self._raw = netcdf_file(filePath)
		self._raw = nc.Dataset(filePath)
		########
		# AXES #
		########
		for dimensionName in self._raw.dimensions.keys() :
			if dimensionName == 'time' :
				self.axes[dimensionName] = \
					aa.TimeAxis(
						self._raw.variables[dimensionName][:],
						self._raw.variables[dimensionName].units)
			elif dimensionName in self._raw.variables.keys() :
				self.axes[dimensionName] = \
					aa.Axis(
						self._raw.variables[dimensionName][:],
						self._raw.variables[dimensionName].units)
		#############
		# VARIABLES #
		#############
		for variableName in set(self._raw.variables.keys()) \
				- set(self._raw.dimensions.keys()) :
			variableAxes = aa.OrderedDict()
			for axisName in self._raw.variables[variableName].dimensions :
				if axisName in self.axes.keys() :
					variableAxes[axisName] = self.axes[axisName]
			self.variables[variableName] = \
					Variable(
						self._raw.variables[variableName][:], {},
						variableAxes)


class Variable(aa.Variable) :
	def __init__(self, data, metadata, axes) :
		super(Variable, self).__init__()
		self._data = data
		self.metadata = metadata
		self.axes = axes
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)

