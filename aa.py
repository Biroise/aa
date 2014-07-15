
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

import numpy as np
from datetime import datetime
from datetime import timedelta


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

	def close(self) :
		self._raw.close()
		del self
	"""
	@property
	def variables() :
		raise NotImplementedError
	@property
	def axes() :
		raise NotImplementedError
	"""


class Variable(object) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.variables.keys() :
			return self.variables[attributeName]
		elif attributeName in self.axes.keys() :
			return self.axes[attributeName]
		else :
			raise AttributeError

	def __getitem__() :
		raise NotImplementedError
	def __call__() :
		raise NotImplementedError
	"""
	@property
	def variables() :
		raise NotImplementedError
	@property
	def axes() :
		raise NotImplementedError
	"""


class Axis(object) :
	def __init__(self, data, units) :
		self.data = data
		self.units = units
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)

	def __len__(self) :
		return len(self.data)
	

class TimeAxis(Axis) :
	def __init__(self, data, unitDefinition=None) :
		super(TimeAxis, self).__init__(data, unitDefinition)
		if unitDefinition != None :
			# unit definition is conventionally :
			# seconds/hours/days since YYYY-MM-DD HH
			words = unitDefinition.split()
			if words[1] != 'since' :
				print "Unconventional definition of time units"
			units = words[0]
			date = [int(bits) for bits in words[2].split('-')]
			epoch = datetime(date[0], date[1], date[2])
			self.data = [epoch + timedelta(**{units: offset}) for offset in self.data]


def open(filePath) :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		import netcdf
		return netcdf.File(filePath)
	if filePath.endswith('grib') :
		import grib
		return grib.File(filePath)


if __name__ == "__main__" :
	f = open('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
	#f = open('/home/ambroise/atelier/anniversaire/tmp.grib')

