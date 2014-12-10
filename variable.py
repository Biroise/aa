
import numpy as np
from axis import Axes
from collections import OrderedDict
from matplotlib.colors import Normalize


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
			if not isinstance(item, list) :
				item = (item,)
		# loop through axes in their correct order
		# and match axis with a sub-item
		for axisIndex, axisName in enumerate(self.axes) :
			# there may be more axes than sub-items
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
		# input : {axisName: condition, ...}
		# standardize the axisNames
		for axisName, condition in kwargs.iteritems() :
			del kwargs[axisName]
			if type(condition) == tuple :
				condition = tuple(sorted(condition[:2]))+condition[2:]
			kwargs[Axes.standardize(axisName)] = condition
		output = self.extract_data(**kwargs)
		# do we need to interpolate along an axis ?
		for axisName, condition in kwargs.iteritems() :
			# did we ask for a single value for an axis
			# yet still have this axis in the output variable ?
			# this means extract_data returned the neighbouring points
			# because this single value is not on the grid
			if type(condition) != tuple and axisName in output.axes :
				firstSlice = [slice(None)]*len(output.shape)
				secondSlice = [slice(None)]*len(output.shape)
				firstSlice[output.axes.index(axisName)] = 0
				secondSlice[output.axes.index(axisName)] = 1
				# linear interpolation !
				output = \
					(output[secondSlice]-output[firstSlice])/\
							(output.axes[axisName][1] - output.axes[axisName][0])\
						*(condition - output.axes[axisName][0]) \
					+ output[firstSlice]
		return output

	def extract_data(self, **kwargs) :
		# prepare to slice the data array
		slices = OrderedDict()
		for axisName in self.axes :
			# default behaviour : leave this dimension intact
			slices[axisName] = slice(None)
		# the new variable's axes
		newAxes = self.axes.copy()
		# dispatch the conditions to the axes
		for axisName, condition in kwargs.iteritems() :
			item, newAxis = self.axes[axisName](condition)
			# replace the default slice(None) by the item returned by the axis
			slices[axisName] = item
			# if it's a single item, not a slice, get rid of the axis
			if newAxis == None :
				del newAxes[axisName]
				self.metadata[axisName] = condition
			else :
				newAxes[axisName] = newAxis
		# twisted longitudes...
		if 'longitude' in kwargs :
			# Parallel objects return a tuple of two slices when they're asked
			# for longitudes that span across the Greenwich meridian or
			# the date line : slices from either end of the array
			if type(slices['longitude']) == tuple :
				secondSlices = slices.copy()
				secondSlices['longitude'] = slices['longitude'][1]
				slices['longitude'] = slices['longitude'][0]
				longitudeIndex = self.axes.index('longitude')
				# longitude is assumed to be the last axis
				return Variable(
						np.concatenate((
							self.data[tuple(slices.values())],
							self.data[tuple(secondSlices.values())]),
							axis=longitudeIndex),
						self.metadata, newAxes)
		return Variable(
				self.data[tuple(slices.values())],
				self.metadata.copy(), newAxes)
	
	def copy(self) :

		return Variable(self.data.copy(),
			self.metadata.copy(), self.axes.copy())
	
	def close(self) :
		pass

	def write(self, filePath) :
		from file import File
		if 'shortName' not in self.metadata :
			self.shortName = 'unknown'
		fileOut = File(axes=self.axes, variables={self.shortName:self})
		fileOut.write(filePath)


	def _get_basemap(self) :
		if '_basemap' not in self.__dict__ :
			import matplotlib.pyplot as plt
			from mpl_toolkits.basemap import Basemap
			# Are we mapping the North Pole ?
			if self.lats.max() > 85 and self.lats.min() > 10 and \
					self.lons.max() - self.lons.min() > 355 :
				self._basemap = Basemap(
						projection = 'nplaea',
						boundinglat = self.lats.min(),
						lon_0 = 0,
						round = True)
			# the South Pole ?
			elif self.lats.min() < -85 and self.lats.max() < -10 and \
					self.lons.max() - self.lons.min() > 355 :
				self._basemap = Basemap(
						projection = 'splaea',
						boundinglat = self.lats.max(),
						lon_0 = 0,
						round = True)
			else :
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

	def plot(self, kind='pcolormesh', **kwargs) :
		import matplotlib.pyplot as plt
		from mpl_toolkits.basemap import addcyclic
		if len(self.axes) == 1 :
			if 'level' in self.axes :
				# make sure pressures decrease with height
				if not plt.gca().yaxis_inverted() :
					plt.gca().invert_yaxis()
				if 'label' in kwargs :
					#plt.legend()
					return plt.plot(self.data, self.axes['level'],
							label = kwargs['label'])
				else :
					return plt.plot(self.data, self.axes['level'])
			if 'time' in self.axes :
				return plt.plot(self.dts, self.data)
			else :
				#####################
				# LONGITUDE PROFILE #
				#####################
				if 'longitude' in self.axes :
					if len(plt.gcf()._axstack._elements) == 0 :
						import matplotlib.gridspec as gridspec
						from mpl_toolkits.basemap import Basemap
						plotGrid = gridspec.GridSpec(2, 1, hspace=0, height_ratios=[6,1])
						mapSubPlot = plt.subplot(plotGrid[1])
						if 'latitude' in self.metadata :
							if isinstance(self.metadata['latitude'], tuple) :
								lats = self.metadata['latitude']
							else :
								lats = tuple([self.metadata['latitude']]*2)
						else :
							lats = (50, 50)
						background = Basemap(
							projection = 'cyl',
							llcrnrlon = self.lons[0],
							llcrnrlat = min(lats[0] - 10, 90),
							urcrnrlon = self.lons[-1],
							urcrnrlat = max(lats[1] + 10, -90))
						background.drawcoastlines()
						background.drawparallels(lats, color='red')
						p = plt.Polygon(
									[(0, lats[0]),
									(0, lats[1]),
									(360, lats[1]),
									(360, lats[0])],
	    						facecolor='red', alpha=0.5)
						plt.gca().add_patch(p)
						background.drawmeridians(np.arange(0, 360, 30), labels=[0, 0, 0, 1])
						plt.gca().set_aspect('auto')
						mainPlot = plt.subplot(plotGrid[0])
					#plt.xlabel(r'longitude ($^{\circ}$)')	
					plt.xlim(self.lons[0], self.lons[-1])
					plt.setp(plt.gca().get_xticklabels(), visible=False)
					plt.setp(plt.gca().get_xticklines(), visible=False)
				elif 'latitude' in self.axes :
					plt.xlabel(r'latitude ($^{\circ}$)')	
				if 'label' in kwargs :
					#plt.legend()
					return plt.plot(self.axes.values()[0], self.data,
							label = kwargs['label'])
				else :
					return plt.plot(self.axes.values()[0], self.data)
		elif len(self.axes) == 2 :
			##########
			# 2D MAP #
			##########
			if 'latitude' in self.axes and \
					'longitude' in self.axes :
				self.basemap.drawcoastlines()
				# need addcyclic if n/s-plaea
				if self.basemap.projection in ['nplaea', 'splaea'] :
					data, lons = addcyclic(self.data, np.array(self.lons))
					x, y = self.basemap(
						*np.meshgrid(lons, self.lats))
				else :
					x, y = self.basemap(
						*np.meshgrid(np.array(self.lons), self.lats))
					data = self.data
				if self.data.min() < 0 and False :
					cs = plt.contour(x, y, data, [0])
					plt.clabel(cs, fontsize=6, fmt='%1.0f')
					graph = getattr(self.basemap, kind)(x, y, data, 
							cmap=plt.cm.seismic, norm=ccb(), **kwargs)
					#cmax = max(abs(self.data.min()), abs(self.data.max()))
					#plt.clim(-cmax, cmax)
				else :
					graph = getattr(self.basemap, kind)(x, y, data, **kwargs)
				colorBar = plt.colorbar()
				if 'units' in self.__dict__ :
					colorBar.set_label(self.units)
				return graph, colorBar
			#####################
			# HOVMOLLER DIAGRAM #
			#  LON-LEV PROFILE  #
			#####################
			if 'longitude' in self.axes and \
					('time' in self.axes or 'level' in self.axes) :
				import matplotlib.gridspec as gridspec
				from mpl_toolkits.basemap import Basemap
				plotGrid = gridspec.GridSpec(2, 2, hspace=0, width_ratios=[20,1], height_ratios=[6,1])
				mapSubPlot = plt.subplot(plotGrid[1, 0])
				if 'latitude' in self.metadata :
					if isinstance(self.metadata['latitude'], tuple) :
						lats = self.metadata['latitude']
					else :
						lats = tuple([self.metadata['latitude']]*2)
				else :
					lats = (50, 50)
				background = Basemap(
					projection = 'cyl',
					llcrnrlon = self.lons[0],
					llcrnrlat = min(lats[0] - 10, 90),
					urcrnrlon = self.lons[-1],
					urcrnrlat = max(lats[1] + 10, -90))
				background.drawcoastlines()
				background.drawparallels(lats, color='red')
				p = plt.Polygon(
							[(self.lons[0], lats[0]),
							(self.lons[0], lats[1]),
							(self.lons[-1], lats[1]),
							(self.lons[-1], lats[0])],
						facecolor='red', alpha=0.5)
				plt.gca().add_patch(p)
				background.drawmeridians(np.arange(0, 360, 30), labels=[0, 0, 0, 1])
				plt.gca().set_aspect('auto')
				mainPlot = plt.subplot(plotGrid[0, 0])
				if 'level' in self.axes and \
						self.levs[0] < self.levs[1] :
					origin = 'upper'
					print 'coucou', origin
				else :
					origin = 'lower'
				if self.data.min() < 0 and False :
					cs = plt.contour(self.data, [0])
					plt.clabel(cs, fontsize=6, fmt='%1.0f')
					#import pdb ; pdb.set_trace()
					plt.draw()
					graph = plt.imshow(self.data, norm=ccb(),
							origin=origin, cmap=plt.cm.seismic)
					#cmax = max(abs(self.data.min()), abs(self.data.max()))
					#plt.clim(-cmax, cmax)
				else :
					graph = plt.imshow(self.data, origin=origin)
				plt.gca().set_aspect('auto')
				plt.xlim(0, len(self.lon))
				if 'time' in self.axes :
					yaxis = self.dts
				elif 'level' in self.axes :
					yaxis = self.levs
					#plt.gca().invert_yaxis()
				plt.ylim(0, len(yaxis)-1)
				# required to set the tick labels
				plt.draw()
				ylabels = [item.get_text() for item in mainPlot.get_yticklabels()]
				# last label is an empty string
				for i in range(len(ylabels)-1) :
					ylabels[i] = yaxis[int(ylabels[i])]
				plt.gca().set_yticklabels(ylabels)
				plt.setp(plt.gca().get_xticklabels(), visible=False)
				plt.setp(plt.gca().get_xticklines(), visible=False)
				cbarPlot = plt.subplot(plotGrid[0, 1])
				colorBar = plt.colorbar(graph, cax=cbarPlot)
				if 'units' in self.__dict__ :
					colorBar.set_label(self.units)
				return graph, colorBar
		else :
			raise Exception, "Variable has too many axes or none"
	
	def quiver(zonal, meridional, nx=15, ny=15, **kwargs) :
		import matplotlib.pyplot as plt
		zonal = zonal(lon=(-179, 179))
		meridional = meridional(lon=(-179, 179))
		zonal.basemap.drawcoastlines()
		order = slice(None)
		if zonal.lats[0] > zonal.lats[1] :
			order = slice(None, None, -1)
		u, v, x, y = zonal.basemap.transform_vector(
				zonal.data[order], meridional.data[order], zonal.lons,
				zonal.lats[order], nx, ny, 	returnxy = True, masked=True)
		graph = zonal.basemap.quiver(x, y, u, v, **kwargs)
		#plt.quiverkey(graph, 0...
		
	def __getattr__(self, attributeName) :
		if 'metadata' in self.__dict__ :
			if attributeName in self.metadata :
				return self.metadata[attributeName]
		if 'axes' in self.__dict__ :
			return self.axes[attributeName]
		raise AttributeError

	def mean(self, axisNames) :
		# input can either either be like 'zy' or like ['lev', 'lat']
		# turn the 'zy' into ['z', 'y']
		axisNames = list(axisNames)
		for i in range(len(axisNames)) :
			axisNames[i] = Axes.standardize(axisNames[i])
			# levels must be averaged first
			# 'level' must be at the top of the list
			if axisNames[i] == 'level' :
				del axisNames[i]
				axisNames = ['level'] + axisNames
		return self.averager(axisNames)
	
	def averager(self, axisNames) :
		# still axes needing averaging
		if len(axisNames) > 0 :
			# extract the name of the axis to be averaged
			axisName = axisNames.pop(0)
			newAxes = self.axes.copy()
			# get its position and weights
			axisIndex = newAxes.index(axisName)
			weights = newAxes[axisName].weights
			self.metadata[axisName] = (newAxes[axisName].data.min(),
					newAxes[axisName].data.max())
			# and delete it
			del newAxes[axisName]
			if axisName == 'level' and 'surfacePressure' in self.metadata :
				thickness = self.copy()*0
				sp = self.surfacePressure
				levels = self.levs
				if 'time' in self.axes :
					standUp = [slice(None)] + [None] + [slice(None)]*(len(sp.shape)-1)
					lieDown = [None] + [slice(None)] + [None]*(len(sp.shape)-1)
					lieBack = [None] + [slice(None, None, -1)] + [None]*(len(sp.shape)-1)
					shiftZ = [slice(None), slice(1, None, None)]
					antiShiftZ = [slice(None), slice(None, -1, None)]
					zAxis = 1
				else : 
					standUp = [None] + [slice(None)]*len(sp.shape)
					lieDown = [slice(None)] + [None]*len(sp.shape)
					lieBack = [slice(None, None, -1)] + [None]*len(sp.shape)
					shiftZ = [slice(1, None, None)]
					antiShiftZ = [slice(None, -1, None)]
					zAxis = 0
				if levels[0] < levels[1] :
					lowerIndex = len(levels) - 1 - np.argmax(levels[lieBack]*100
							< sp.data[standUp], axis=zAxis)
					LEVELs = np.where(
							np.arange(len(levels))[lieDown] >= lowerIndex[standUp],
							sp.data[standUp],
							levels[lieDown]*100)
				else :
					lowerIndex = np.argmax(levels[lieDown]*100 < sp.data[standUp], axis=zAxis)
					LEVELs = np.where(
							np.arange(len(levels))[lieDown] <= lowerIndex[standUp],
							sp.data[standUp],
							levels[lieDown]*100)
				thickness.data[shiftZ] += 0.5*np.abs(np.diff(LEVELs, axis=zAxis))
				thickness.data[antiShiftZ] += 0.5*np.abs(np.diff(LEVELs, axis=zAxis))
				self.metadata['thickness'] = thickness
			if axisName == 'level' and 'thickness' in self.metadata :
				newMetaData = self.metadata.copy()
				del newMetaData['thickness']
				return Variable(
							(self.data*self.thickness.data).sum(axis=axisIndex)/9.81,
							newMetaData, newAxes
						).averager(axisNames)
			elif axisName == 'level' :
				weightSlice = [None]*len(self.shape)
				weightSlice[axisIndex] = slice(None)
				return Variable(
							(self.data*weights[weightSlice])\
								.sum(axis=axisIndex),
							self.metadata.copy(),
							newAxes
						).averager(axisNames)
			else :
				weightSlice = [None]*len(self.shape)
				weightSlice[axisIndex] = slice(None)
				return Variable(
							(self.data*weights[weightSlice]/weights.mean())\
									.mean(axis=axisIndex),
							self.metadata.copy(),
							newAxes
						).averager(axisNames)
		# no axes left to average : return the result
		else :
			return self
	
class ccb(Normalize):
	def __init__(self, vmin=None, vmax=None, midpoint=0, clip=False):
		self.midpoint = midpoint
		Normalize.__init__(self, vmin, vmax, clip)
	
	def __call__(self, value, clip=None):
		import numpy.ma as ma
		# I'm ignoring masked values and all kinds of edge cases to make a
		# simple example...
		x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
		return ma.masked_array(np.interp(value, x, y))

# allow operations on variables e.g. add, substract, etc.
def wrap_operator(operatorName) :
	# a function factory
	def operator(self, operand) :
		# the operator expects a Variable or a numpy-compatible input
		if isinstance(operand, Variable) :
			operand = operand.data
		# use the numpy operator on the Variable's data
		# and return as a new varaible
		return Variable(
					getattr(self.data, operatorName)(operand),
					self.metadata.copy(), self.axes.copy())
	return operator
for operatorName in ['__add__', '__sub__', '__div__', '__mul__', '__pow__',
			'__radd__', '__rsub__', '__rdiv__', '__rmul__', '__rpow__'] :
	setattr(Variable, operatorName, wrap_operator(operatorName))
