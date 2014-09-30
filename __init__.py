
"""
An interface between scipy, netCDF4, pygrib and matplotlib's basemap
"""

from axis import *
from file import File
from variable import Variable

import numpy as np


def open(filePath, mode='r') :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aa import netcdf
		File = netcdf.File(filePath, mode)
	elif filePath.endswith('grib') or filePath.endswith('grb') \
			or filePath.endswith('grb2') :
		import os
		fileName = os.path.splitext(filePath)[0]
		picklePath = fileName + '.p'
		indexPath = fileName + '.idx'
		if os.path.isfile(picklePath) and os.path.isfile(indexPath) :
			import __builtin__
			import cPickle as pickle
			malossol = __builtin__.open(picklePath)
			File = pickle.load(malossol)
		else :
			from aa import grib
			File = grib.File(filePath)
	return File
	"""
	if len(File.variables) == 1 :
		return File.variables.values()[0]
	else :
		return File
	"""


