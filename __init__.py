
"""
An interface between scipy, netCDF4, pygrib and matplotlib's basemap
"""

from axis import *
from file import File
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


def open(filePath, mode='r') :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aa import netcdf
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
			from aa import grib
			return grib.File(filePath)


