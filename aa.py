
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

from axis import Axis
from axis import TimeAxis
from axis import month

import numpy as np
import operator as op
import matplotlib.pyplot as plt
from collections import OrderedDict
from mpl_toolkits.basemap import Basemap


class DataMedium(object) :
	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		if attributeName == 't' :
			return self.time
		if attributeName == 'lat' :
			return self.latitude
		if attributeName == 'lon' :
			return self.longitude
		if attributeName == 'lev' :
			return self.level
		if attributeName == 'levels' :
			return self.level
		if attributeName == 'level' :
			return self.levels
		if attributeName == 'lats' :
			return self.latitude[:]
		if attributeName == 'lons' :
			return self.longitude[:]
		if attributeName == 'levs' :
			return self.level[:]
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


class Variable(DataMedium) :
	def __init__(self, data=None, metadata={}, axes=OrderedDict()) :
		self.axes = axes
		self.metadata = metadata
		if data != None :
			self._data = data

	def _get_data(self) :
		return self._data
	def _set_data(self, newValue) :
		self._data = newValue
	data = property(_get_data, _set_data)
		
	def __call__(self, **kwargs) :
		multipleSlice = []
		outputAxes = OrderedDict()
		for axisName, axis in self.axes.iteritems() :
			# must this axis be sliced ?
			if axisName in kwargs.keys() :
				# should a range of indices be extracted ?
				if type(kwargs[axisName]) == tuple :
					window = np.vectorize(glazier(kwargs[axisName]))	
					# now extract the sub-axis corresponding to the conditions
					mask = window(self.axes[axisName][:])
					item = slice(
							np.argmax(mask),
							len(mask) - np.argmax(mask[::-1]))
					outputAxes[axisName] = Axis(
							self.axes[axisName][mask],
							self.axes[axisName].units)
				# extract a single index only
				else :
					item = np.argmax(
						self.axes[axisName][:] == kwargs[axisName])
					if item == 0 and \
							self.axes[axisName][0] != kwargs[axisName] :
						print "No match in " + axisName
						return None
					# don't add this axis to outputAxes
			# leave the axis untouched
			else :
				item = slice(None)
				outputAxes[axisName] = self.axes[axisName]
			multipleSlice.append(item)
		return Variable(self.data[multipleSlice], self.metadata, outputAxes)
	

def open(filePath) :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		import netcdf
		return netcdf.File(filePath)
	if filePath.endswith('grib') :
		import grib
		return grib.File(filePath)


