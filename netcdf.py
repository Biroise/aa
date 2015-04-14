
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
				if aa.Axes.standardize(dimensionName) == 'time' :
					self.axes['time'] = aa.TimeAxis(*args)
				elif aa.Axes.standardize(dimensionName) == 'longitude' :
					self.axes['longitude'] = aa.Parallel(*args)
				elif aa.Axes.standardize(dimensionName) == 'latitude' :
					self.axes['latitude'] = aa.Meridian(*args)
				elif aa.Axes.standardize(dimensionName) == 'level' :
					# convert pascals to hectopascals
					if (args[0] > 10000).any() :
						args[0] /= 100
					self.axes['level'] = aa.Vertical(*args)
				else :
					self.axes[aa.Axes.standardize(dimensionName)] = aa.Axis(*args)
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
			variableMetaData = {'shortName':variableName}
			if 'units' in self._raw.variables[variableName].__dict__ :
				variableMetaData['units'] = \
						self._raw.variables[variableName].units
			self.variables[variableName] = \
					Variable(
						data=self._raw.variables[variableName][:],
						axes=variableAxes,
						metadata=variableMetaData, 
						rawFile=self._raw)
	
	def close(self) :
		self._raw.close()


class Variable(aa.Variable) :
	def __init__(self, data, axes, metadata, rawFile)	:
		super(Variable, self).__init__(data, axes, metadata)
		self._raw = rawFile
	
	def close(self) :
		self._raw.close()

		

