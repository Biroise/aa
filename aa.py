
"""
An interface between scipy, pygrib and matplotlib's basemap
"""
from axis import *

import os
import __builtin__
import numpy as np
import cPickle as pickle
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


class File(object) :
	def __init__(self) :
		self.axes = Axes()
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.variables :
			return self.variables[attributeName]
		return self.axes[attributeName]
	
	def __getitem__(self, item) :
		return getattr(self, item)


class Variable(object) :
	def __init__(self, data=None, metadata={}, axes=Axes()) :
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
		# standard case : slicing an array
		if isinstance(self.data, np.ndarray) :
			return self.data[item]
		# in case of scalar variables sliced with ":"
		else :
			return self.data
	def __setitem__(self, item, value) :		
		if isinstance(self.data, np.ndarray) :
			self.data[item] = value
		else :
			self.data = value
	
	def __call__(self, **kwargs) :
		slices = {axisName:slice(None) for axisName in self.axes.keys()}
		newAxes = self.axes.copy()
		for axisName, condition in kwargs.iteritems() :
			axisName = Axes.aliases[axisName]
			item, newAxis = self.axes[axisName](condition)
			slices[axisName] = item
			if newAxis == None :
				del newAxes[axisName]
			else :
				newAxes[axisName] = newAxis
		# twisted longitudes...
		if 'longitude' in kwargs :
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
			if 'latitude' in self.axes and \
					'longitude' in self.axes :
				self.basemap.drawcoastlines()
				x, y = self.basemap(
					*np.meshgrid(self.longitude.data, self.latitude.data))
				return self.basemap.pcolormesh(x, y, self.data)
		else :
			print "Variable has too many axes or none"


def open(filePath, mode='r') :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aatk import netcdf
		return netcdf.File(filePath, mode)
	if filePath.endswith('grib') :
		fileName = os.path.splitext(filePath)[0]
		picklePath = fileName + '.p'
		indexPath = fileName + '.idx'
		if os.path.isfile(picklePath) and os.path.isfile(indexPath) :
			malossol = __builtin__.open(picklePath)
			return pickle.load(malossol)
		else :
			from aatk import grib
			return grib.File(filePath)


