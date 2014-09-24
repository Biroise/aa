
"""
An interface between scipy, netCDF4, pygrib and matplotlib's basemap
"""

from axis import *
from variable import Variable

import numpy as np


class File(object) :
	def __init__(self) :
		self.axes = Axes()
		self.variables = {}

	def __getattr__(self, attributeName) :
		if 'variables' in self.__dict__ :
			if attributeName in self.variables :
				return self.variables[attributeName]
		if 'axes' in self.__dict__ :
			return self.axes[attributeName]
		raise AttributeError
	
	def __getitem__(self, item) :
		return getattr(self, item)
	
	def close(self) :
		pass
	
	def write(self, fileName) :
		import netCDF4	
		pass

def averager(data, axisIndices) :
	# still axes needing averaging
	if len(axisIndices) > 0 :
		# extract the first/next axisIndex
		nextIndex = axisIndices.pop(0)
		# reduce the other axisIndices by one to account for the loss
		# in dimension due to the averaging
		axisIndices = [axisIndex - 1 for axisIndex in axisIndices]
		return averager(data.mean(axis=nextIndex), axisIndices)
	else :
		return data
	
# allow operation on variables e.g. add, substract, etc.
def wrap_operator(operatorName) :
	# a function factory
	def operator(self, operand) :
		# the operator expects a Variable or a numpy-compatible input
		if isinstance(operand, Variable) :
			operand = operand.data
		# use the numpy operator on the Variable's data
		# and return as a new varaible
		return Variable(
					getattr(self.data, operatorName)(operand),
					self.metadata.copy(), self.axes.copy())
	return operator
for operatorName in ['__add__', '__sub__', '__div__', '__mul__'] :
	setattr(Variable, operatorName, wrap_operator(operatorName))

def open(filePath, mode='r') :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aatk import netcdf
		return netcdf.File(filePath, mode)
	if filePath.endswith('grib') or filePath.endswith('grb') \
			or filePath.endswith('grb2') :
		import os
		fileName = os.path.splitext(filePath)[0]
		picklePath = fileName + '.p'
		indexPath = fileName + '.idx'
		if os.path.isfile(picklePath) and os.path.isfile(indexPath) :
			import __builtin__
			import cPickle as pickle
			malossol = __builtin__.open(picklePath)
			return pickle.load(malossol)
		else :
			from aatk import grib
			return grib.File(filePath)


