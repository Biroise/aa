
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
		conditions = {}
		# make item iterable, even when it's a singleton
		if not isinstance(item, tuple) :
			item = (item,)
		for axisIndex, axisName in enumerate(self.axes) :
			if axisIndex < len(item) :
				if not isinstance(item[axisIndex], slice) :
					conditions[axisName] = \
						self.axes[axisName][item[axisIndex]]
				else :
					# if it's a ':' slice, do nothing
					if item[axisIndex] != slice(None) :
						conditions[axisName] = \
							(self.axes[axisName][item[axisIndex]].min(),
							self.axes[axisName][item[axisIndex]].max())
		return self(**conditions)

	@property
	def shape(self) :
		return self.data.shape

	def __call__(self, **kwargs) :
		# standardize the axisNames
		for axisName, condition in kwargs.iteritems() :
			if Axes.aliases[axisName] != axisName :
				kwargs[Axes.aliases[axisName]] = condition
				del kwargs[axisName]
		# prepare to slice the data array
		slices = Axes()
		for axisName in self.axes :
			# default behaviour : leave this dimension intact
			slices[axisName] = slice(None)
		# the new variable's axes
		newAxes = self.axes.copy()
		for axisName, condition in kwargs.iteritems() :
			item, newAxis = self.axes[axisName](condition)
			slices[axisName] = item
			if newAxis == None :
				del newAxes[axisName]
			else :
				newAxes[axisName] = newAxis
		# update longitude weights
		if 'latitude' in kwargs and 'longitude' in newAxes :
			newAxes['longitude'].latitudes = \
					self.axes['latitude'][slices['latitude']].reshape((-1,))
		# twisted longitudes...
		if 'longitude' in kwargs :
			if type(slices['longitude']) == tuple :
				secondSlices = slices.copy()
				secondSlices['longitude'] = slices['longitude'][1]
				slices['longitude'] = slices['longitude'][0]
				# longitude is assumed to be the last axis
				return Variable(
						np.concatenate((
							self.data[slices.values()],
							self.data[secondSlices.values()])),
						self.metadata, newAxes)
		return Variable(self.data[slices.values()], self.metadata, newAxes)
	
	def close(self) :
		pass

	def _get_basemap(self) :
		# assign to self a standard basemap
		self._basemap = Basemap(
				projection = 'cyl',
				llcrnrlon = self.lons.min(),
				llcrnrlat = self.lats.min(),
				urcrnrlon = self.lons.max(),
				urcrnrlat = self.lats.max())
		return self._basemap
	def _set_basemap(self, someMap) :
		# user may set basemap himself
		self._basemap = someMap
	basemap = property(_get_basemap, _set_basemap)

	@property
	def plot(self) :
		if len(self.axes) == 1 :
			if self.axes.keys()[0] == 'level' :
				return plt.plot(self.data, self.axes['level'])
			else :
				return plt.plot(self.axes.values()[0], self.data)
		elif len(self.axes) == 2 :
			if 'latitude' in self.axes and \
					'longitude' in self.axes :
				self.basemap.drawcoastlines()
				x, y = self.basemap(
					*np.meshgrid(np.array(self.lons), self.lats))
				return self.basemap.pcolormesh(x, y, self.data)
		else :
			print "Variable has too many axes or none"
	
	def __getattr__(self, attributeName) :
		if 'axes' in self.__dict__ :
			return self.axes[attributeName]
		raise AttributeError

	"""
	def integrate(self, axisNames) :
		# input can either be "zy" or ['lev', 'lat']
		axisIndices = []
		for i in range(len(axisNames)) :
			axisNames[i] = aa.Axes.aliases[axisNames[i]]
			axisIndices.append(self.axes.keys().index(axisNames[i]))
		# if 'longitude' in axisNames
		"""
			

def wrap_operator(operatorName) :
	def operator(self, operand) :
		if isinstance(operand, Variable) :
			operand = operand.data
		return Variable(
					getattr(self.data, operatorName)(operand),
					self.metadata.copy(), self.axes.copy())
	return operator
for operatorName in ['__add__', '__sub__'] :
	setattr(Variable, operatorName, wrap_operator(operatorName))

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


