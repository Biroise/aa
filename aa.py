
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

from variable import Variable
from variable import glazier
from axis import Axis
from axis import TimeAxis
from axis import month

class DataMedium(object) :
	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		if attributeName == 't' :
			return self.time
		if attributeName == 'lat' :
			return self.latitude :
		if attributeName == 'lon' :
			return self.longitude
		if attributeName == 'lev' :
			return self.level
		if attributeName == 'levels' :
			return self.level
		if attributeName == 'level' :
			return self.levels
		else :
			raise AttributeError



class File(DataMedium) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		if attributeName in self.variables.keys() :
			return self.variables[attributeName]
		return super(File, self).__getattr__(self, attributeName)

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


