
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

from variable import Variable
from variable import glazier
from axis import Axis
from axis import TimeAxis
from axis import month


class File(object) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		elif attributeName in self.variables.keys() :
			return self.variables[attributeName]
		else :
			raise AttributeError
	
	def __getitem__(self, argument) :
		if argument in self.axes.keys() :
			return self.axes[argument]
		if argument in self.variables.keys() :
			return self.variables[argument]

	def close(self) :
		self._raw.close()
		del self


def open(filePath) :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		import netcdf
		return netcdf.File(filePath)
	if filePath.endswith('grib') :
		import grib
		return grib.File(filePath)


