
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

from axis import Axis
from axis import TimeAxis
from axis import month
from axis import Parallel

import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
from mpl_toolkits.basemap import Basemap


class DataMedium(object) :
	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		# dealing with the most common aliases
		latitudeNames = ['latitude', 'latitudes', 'lat']
		longitudeNames = ['longitude', 'longitudes', 'lon']
		levelNames = ['level', 'levels', 'lev']
		axesNames = [latitudeNames, longitudeNames, levelNames]
		for axisNames in axesNames :
			if attributeName in axisNames :
				for axisName in axisNames :
					if axisName in self.axes.keys() :
						return self.axes[axisName]
		# returns the array of coordinates instead of the axis object
		if attributeName in ['lats', 'lons', 'levs'] :
			return getattr(self, attributeName[:-1])[:]
		if attributeName == 'dts' :
			return getattr(self, 'time')[:]
		# if no cases fit
		raise AttributeError


class File(DataMedium) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.variables.keys() :
			return self.variables[attributeName]
		return super(File, self).__getattr__(attributeName)
	
	def __getitem__(self, item) :
		return getattr(self, item)

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

	def __getitem__(self, item) :
		if isinstance(self.data, np.ndarray) :
			return self.data[item]
		# in case of scalar variables
		else :
			return self.data
		
	def __call__(self, **kwargs) :
		slices = {axisName:slice(None) for axisName in self.axes.keys()}
		newAxes = self.axes.copy()
		for axisName, condition in kwargs.iteritems() :
			item, newAxis = self.axes[axisName](condition)
			slices[axisName] = item
			if newAxis == None :
				del newAxes[axisName]
			else :
				newAxes[axisName] = newAxis
		# twisted longitudes...
		if 'longitude' in kwargs.keys() :
			if type(slices['longitude']) == tuple :
				secondSlices = slices.copy()
				secondSlices['longitude'] = slices['longitude'][1]
				slices['longitude'] = slices['longitude'][0]
			# longitude is assumed to be the last axis
			return Variable(
					np.hstack((
						self.data[slices.values()],
						self.data[secondSlices.values()])),
					self.metadata, newAxes)
		return Variable(self.data[slices.values()], self.metadata, newAxes)
	
	def mean(self, axes) :
		return NotImplementedError

	def _get_basemap(self) :
		# assign to self a standard basemap
		self._basemap = Basemap(
				projection = 'cyl',
				llcrnrlon = self.longitude.data.min(),
				llcrnrlat = self.latitude.data.min(),
				urcrnrlon = self.longitude.data.max(),
				urcrnrlat = self.latitude.data.max())
		return self._basemap
	def _set_basemap(self, someMap) :
		# user may set basemap himself
		self._basemap = someMap
	basemap = property(_get_basemap, _set_basemap)

	@property
	def plot(self) :
		if len(self.axes) == 1 :
			if self.axes.keys()[0] == 'levels' :
				return plt.plot(self.data, self.axes['levels'])
			else :
				return plt.plot(self.axes.values()[0], self.data)
		elif len(self.axes) == 2 :
			if 'latitude' in self.axes.keys() and \
					'longitude' in self.axes.keys() :
				self.basemap.drawcoastlines()
				x, y = self.basemap(
					*np.meshgrid(self.longitude.data, self.latitude.data))
				return self.basemap.pcolormesh(x, y, self.data)
		else :
			print "Variable has too many axes or none"


def open(filePath) :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aatk import netcdf
		return netcdf.File(filePath)
	if filePath.endswith('grib') :
		from aatk import grib
		return grib.File(filePath)


