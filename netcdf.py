
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
				args = [self._raw.variables[dimensionName][:],
							self._raw.variables[dimensionName].units]
				if aa.Axes.aliases[dimensionName] == 'time' :
					self.axes[dimensionName] = aa.TimeAxis(*args)
				elif aa.Axes.aliases[dimensionName] == 'latitude' :
					self.axes[dimensionName] = aa.Meridian(*args)
				elif aa.Axes.aliases[dimensionName] == 'longitude' :
					self.axes[dimensionName] = aa.Parallel(*args)
				else :
					self.axes[aa.Axes.aliases[dimensionName]] = aa.Axis(*args)
		# give longitude the appropriate latitude weights
		if 'longitude' in self._raw.dimensions and \
				'latitude' in self._raw.dimensions :
			self.longitude.latitudes = self.lats
		#############
		# VARIABLES #
		#############
		for variableName in set(self._raw.variables.keys()) \
				- set(self._raw.dimensions.keys()) :
			variableAxes = aa.Axes()
			for axisName in self._raw.variables[variableName].dimensions :
				axisName = aa.Axes.aliases[axisName]
				if axisName in self.axes :
					variableAxes[axisName] = self.axes[axisName]
			self.variables[variableName] = \
					Variable(
						self._raw.variables[variableName][:], {},
						variableAxes)


class Variable(aa.Variable) :
	pass

