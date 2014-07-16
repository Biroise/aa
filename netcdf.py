
import aa
import numpy as np
from collections import OrderedDict
from scipy.io.netcdf import netcdf_file


class File(aa.File) :
	def __init__(self, filePath) :
		super(File, self).__init__()
		self._raw = netcdf_file(filePath, 'r')
		########
		# AXES #
		########
		for dimensionName in self._raw.dimensions.keys() :
			if dimensionName == 'time' :
				self.axes[dimensionName] = \
					aa.TimeAxis(
						self._raw.variables[dimensionName].data,
						self._raw.variables[dimensionName].units)
			else :
				self.axes[dimensionName] = \
					aa.Axis(
						self._raw.variables[dimensionName].data,
						self._raw.variables[dimensionName].units)
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
						self._raw.variables[variableName].data,
						self._raw.variables[variableName].units,
						variableAxes)


class Variable(aa.Variable) :
	def __init__(self, data, units, axes) :
		super(Variable, self).__init__()
		self.data = data
		self.units = units
		self.axes = axes
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)

	def __call__(self, **kwargs) :
		multipleSlice = []
		outputAxes = OrderedDict()
		for axisName, axis in self.axes.iteritems() :
			# must this axis be sliced ?
			if axisName in kwargs.keys() :
				# should a range of indices be extracted ?
				if type(kwargs[axisName]) == tuple :
					mask = np.logical_and(
							# CAUTION : default slicing different from numpy
							self.axes[axisName].data >= kwargs[axisName][0],
							self.axes[axisName].data <= kwargs[axisName][1])
					outputAxes[axisName] = aa.Axis(
							self.axes[axisName].data[mask],
							self.axes[axisName].units)
				# extract a single index only
				else :
					mask = np.argmax(
						self.axes[axisName].data == kwargs[axisName])
					# don't add this axis to outputAxes
			# leave the axis untouched
			else :
				mask = slice(None)
				outputAxes[axisName] = self.axes[axisName]
			multipleSlice.append(mask)
		return Variable(self[mask], self.units, outputAxes)


if __name__ == "__main__" :
	f = aa.open('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
	first = f.time[0]
	a = f.h(time=first, levels=1000)
	

