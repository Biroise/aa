
import aa
import numpy as np
import netCDF4 as nc
import operator as op
from collections import OrderedDict
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
			variableAxes = OrderedDict()
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
		self.data = data
		self.metadata = metadata
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
					# if the user does not provide the type of boundaries
					if len(kwargs[axisName]) == 2 :
						# default boundaries are "closed-closed" unlike numpy
						kwargs[axisName] = kwargs[axisName] + ('cc')
					# if the lower boundary is closed...
					if kwargs[axisName][2][0] == 'c' :
						lowerCondition = op.ge
					else :
						lowerCondition = op.gt
					# if the upper boundary is closed...
					if kwargs[axisName][2][1] == 'c' :
						upperCondition = op.le
					else :
						upperCondition = op.lt
					# now extract the sub-axis corresponding to the conditions
					mask = np.logical_and(
							lowerCondition(
								self.axes[axisName][:],
								kwargs[axisName][0]),
							upperCondition(
								self.axes[axisName][:],
								kwargs[axisName][1]))
					outputAxes[axisName] = aa.Axis(
							self.axes[axisName][:][mask],
							self.axes[axisName].units)
				# extract a single index only
				else :
					mask = np.argmax(
						self.axes[axisName][:] == kwargs[axisName])
					if mask == 0 and \
							self.axes[axisName][0] != kwargs[axisName] :
						print "No match in " + axisName
						return None
					# don't add this axis to outputAxes
			# leave the axis untouched
			else :
				mask = slice(None)
				outputAxes[axisName] = self.axes[axisName]
			multipleSlice.append(mask)
		return Variable(self[:][multipleSlice], self.metadata, outputAxes)

	

