
import numpy as np
from axis import Axes

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
		# loop through axes in their correct order
		# and match axis with a sub-item
		for axisIndex, axisName in enumerate(self.axes) :
			# there mey be more axes than sub-items
			# do not overshoot
			if axisIndex < len(item) :
				# if it's a single index slice
				if not isinstance(item[axisIndex], slice) :
					conditions[axisName] = \
						self.axes[axisName][item[axisIndex]]
				else :
					# it's a slice
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
		import matplotlib.pyplot as plt
		from mpl_toolkits.basemap import Basemap
		if len(self.axes) == 1 :
			if self.axes.keys()[0] == 'level' :
				# make sure pressures decrease with height
				if not plt.gca().yaxis_inverted() :
					plt.gca().invert_yaxis()
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

	def mean(self, axisNames) :
		# still basic, no weights
		# input can either either be like "zy" or like ['lev', 'lat']
		print "/!\\ Careful : no weights, \n\
				not even to integrate along \n\
				a vertical or a meridian"
		axisIndices = []
		newAxes = self.axes.copy()
		for i in range(len(axisNames)) :
			axisIndices.append(
				self.axes.keys().index(
					Axes.aliases[axisNames[i]]))
			# remove the axis along which the averaging is to be done
			del newAxes[Axes.aliases[axisNames[i]]]
		return Variable(
					averager(self.data, sorted(axisIndices)),
					self.metadata.copy(), newAxes)
	
