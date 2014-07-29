
import aa
import numpy as np
import operator as op
from collections import OrderedDict
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt


class Variable(aa.DataMedium) :
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
					outputAxes[axisName] = aa.Axis(
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


def glazier(conditions) :
	"The glazier makes windows : functions that test if conditions are met"
	# if the user does not provide the type of boundaries
	if len(conditions) == 2 :
		# default boundaries are "closed-closed" unlike numpy
		conditions = conditions + ('cc',)
	# if the lower boundary is closed...
	if conditions[2][0] == 'c' :
		lowerCondition = op.ge
	else :
		lowerCondition = op.gt
	# if the upper boundary is closed...
	if conditions[2][1] == 'c' :
		upperCondition = op.le
	else :
		upperCondition = op.lt
	# extract the sub-axis related to the newConditions
	def window(x) :
		return lowerCondition(
				x, conditions[0]) and \
			upperCondition(
				x, conditions[1])
	return window


levelNames = ['level', 'levels', 'lev']
latitudeNames = ['latitude', 'latitudes', 'lat']
longitudeNames = ['longitude', 'longitudes', 'lon']
