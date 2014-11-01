
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
				condition = tuple(sorted(condition))
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
		slices = Axes()
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

	@property
	def plot(self) :
		import matplotlib.pyplot as plt
		from mpl_toolkits.basemap import addcyclic
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
				# need addcyclic if n/splaea
				if self.basemap.projection in ['nplaea', 'splaea'] :
					data, lons = addcyclic(self.data, np.array(self.lons))
					x, y = self.basemap(
						*np.meshgrid(lons, self.lats))
					graph = self.basemap.pcolormesh(x, y, data)
				else :
					x, y = self.basemap(
						*np.meshgrid(np.array(self.lons), self.lats))
					graph = self.basemap.pcolormesh(x, y, self.data)
				colorBar = plt.colorbar()
				if 'units' in self.__dict__ :
					colorBar.set_label(self.units)
				return graph, colorBar
		else :
			raise Exception, "Variable has too many axes or none"
	
	def quiver(zonal, meridional, nx=15, ny=15) :
		import matplotlib.pyplot as plt
		zonal = zonal(lon=(-179, 180))
		meridional = meridional(lon=(-179, 180))
		zonal.basemap.drawcoastlines()
		order = slice(None)
		if zonal.lats[0] > zonal.lats[1] :
			order = slice(None, None, -1)
		u, v, x, y = zonal.basemap.transform_vector(
				zonal.data[order], meridional.data[order], zonal.lons,
				zonal.lats[order], nx, ny, 	returnxy = True, masked=True)
		graph = zonal.basemap.quiver(x, y, u, v)
		#plt.quiverkey(graph, 0...
		
		
	
	def __getattr__(self, attributeName) :
		if 'metadata' in self.__dict__ :
			if attributeName in self.metadata :
				return self.metadata[attributeName]
		if 'axes' in self.__dict__ :
			return self.axes[attributeName]
		raise AttributeError

	def mean(self, axisNames, surfacePressure=None) :
		# input can either either be like 'zy' or like ['lev', 'lat']
		# turn the 'zy' into ['z', 'y']
		if not isinstance(surfacePressure, type(None)) :
			self.metadata['surfacePressure'] = np.array(surfacePressure)
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
			# and delete it
			del newAxes[axisName]
			if axisName == 'level' and 'thickness' in self.metadata :
				newMetaData = self.metadata.copy()
				del newMetaData['thickness']
				return Variable(
							(self.data*self.thickness.data).sum(axis=axisIndex)/9.81,
							newMetaData, newAxes
						).averager(axisNames)
			elif axisName == 'level' and 'surfacePressure' in self.metadata :
				# default is vertical integration, not average, ye be warned
				# won't work if there's still a time dimension
				levels = np.empty(self.shape)
				weights = np.zeros(self.shape)
				standUp = [slice(None)]*len(self.shape)
				lieDown = [None]*len(self.shape)
				axisIndex = self.axes.index('level')
				standUp[axisIndex] = None
				lieDown[axisIndex] = slice(None)
				levels = np.where(
						self.levs[tuple(lieDown)]
								< self.surfacePressure[tuple(standUp)],
						self.levs[tuple(lieDown)],
						self.surfacePressure[tuple(standUp)])\
				# in case all prescribed levels are inferior
				# to the surfacePressure
				standUp[axisIndex] = np.argmax(self.levs)
				levels[tuple(standUp)] = self.surfacePressure
				standUp[axisIndex] = slice(0, -1, None)
				weights[tuple(standUp)] += 0.5*np.abs(np.diff(levels,
							axis=axisIndex))
				standUp[axisIndex] = slice(1, None, None)
				weights[tuple(standUp)] += 0.5*np.abs(np.diff(levels,
							axis=axisIndex))
				newMetaData = self.metadata.copy()
				del newMetaData['surfacePressure']
				return Variable(
							(self.data*weights*100/9.8)\
									.sum(axis=axisIndex),
							newMetaData,
							newAxes
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
