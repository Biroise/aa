
import numpy as np
import graphics
from axis import Axes
from collections import OrderedDict
import statistics


class Variable(object) :
	def __init__(self, data=None, axes=Axes(), metadata={}) :
		self.axes = axes
		self.metadata = metadata
		if type(data) != type(None) :
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
				try :
					output = \
						(output[secondSlice]-output[firstSlice])/\
								(output.axes[axisName][1] - output.axes[axisName][0])\
							*(condition - output.axes[axisName][0]) \
						+ output[firstSlice]
				except IndexError :
					# sometimes, due to rounding errors, extract_data will return one
					# value when two were expected, thus output...[1] fails
					output = output[firstSlice]
				output.metadata[axisName] = condition
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
						data = np.concatenate((
							self.data[tuple(slices.values())],
							self.data[tuple(secondSlices.values())]),
							axis=longitudeIndex),
						axes = newAxes,
						metadata = self.metadata)
		return Variable(
				data = self.data[tuple(slices.values())],
				axes = newAxes,
				metadata = self.metadata.copy())
	
	def copy(self) :
		return Variable(
				data = self.data.copy(),
				axes = self.axes.copy(),
				metadata = self.metadata.copy())
	
	def empty(self) :
		return Variable(
				data = np.empty(self.data.shape),
				axes = self.axes.copy(),
				metadata = {})
	
	def zeros(self) :
		return Variable(
				data = np.zeros(self.data.shape),
				axes = self.axes.copy(),
				metadata = {})
	
	def close(self) :
		pass

	def write(self, filePath) :
		from file import File
		if 'shortName' not in self.metadata :
			self.metadata['shortName'] = 'unknown'
		fileOut = File(axes=self.axes, variables={self.shortName:self})
		fileOut.write(filePath)

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
				self.metadata['thickness'] = statistics.sp2thck(self)
			if axisName == 'level' and 'thickness' in self.metadata :
				newMetaData = self.metadata.copy()
				del newMetaData['thickness']
				return Variable(
							data = np.nansum(self.data*self.thickness.data,
									axis=axisIndex)/9.81,
							axes = newAxes,
							metadata = newMetaData 
						).averager(axisNames)
			elif axisName == 'level' :
				weightSlice = [None]*len(self.shape)
				weightSlice[axisIndex] = slice(None)
				return Variable(
							data = np.nansum(self.data*weights[weightSlice],
									axis=axisIndex),
							axes = newAxes,
							metadata = self.metadata.copy()
						).averager(axisNames)
			else :
				weightSlice = [None]*len(self.shape)
				weightSlice[axisIndex] = slice(None)
				return Variable(
							data = np.nanmean(self.data*weights[weightSlice]/weights.mean(),\
									axis=axisIndex),
							axes = newAxes,
							metadata = self.metadata.copy()
						).averager(axisNames)
		# no axes left to average : return the result
		else :
			return self
	
	basemap = property(graphics._get_basemap, graphics._set_basemap)
	minimap = property(graphics._get_minimap, graphics._set_minimap)
	plot = property(graphics.plot)
	cycle = property(statistics.cycle)
	trend = property(statistics.trend)
	slope = property(statistics.slope)
	significance = property(statistics.significance)
	line = property(statistics.line)
	
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
					data = getattr(self.data, operatorName)(operand),
					axes = self.axes.copy(),
					metadata = self.metadata.copy())
	return operator
for operatorName in [
			'__gt__', '__lt__', '__ge__', '__le__', '__eq__', '__ne__',
			'__add__', '__sub__', '__div__', '__mul__', '__pow__',
			'__radd__', '__rsub__', '__rdiv__', '__rmul__', '__rpow__'] :
	setattr(Variable, operatorName, wrap_operator(operatorName))

seasons = ['DJF', 'MAM', 'JJA', 'SON']


def wrap_extractor(monthNumbers) :
	@property
	def extractor(self) :
		from variable import Variable
		mask = np.zeros(len(self.dts), dtype=bool)
		for monthNumber in monthNumbers :
			mask += self.dt.months == monthNumber
		newAxes = self.axes.copy()
		newAxes['time'].data = self.dts[mask]
		return Variable(
				data=self.data[mask],
				axes=newAxes,
				metadata=self.metadata.copy())
	return extractor
periods = {monthName:[monthNumber+1] for monthNumber, monthName in 
		enumerate(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 
		'SEP', 'OCT', 'NOV', 'DEC'])}
periods['DJF'] = [12, 1, 2]
periods['MAM'] = [3, 4, 5]
periods['JJA'] = [6, 7, 8]
periods['SON'] = [9, 10, 11]
for periodName, monthNumbers in periods.iteritems() :
	setattr(Variable, periodName, wrap_extractor(monthNumbers))

def absolute(self) :
	return Variable(abs(self.data), 
			self.metadata.copy(), self.axes.copy())
setattr(Variable, 'abs', absolute)
	
setattr(Variable, 'quiver', graphics.quiver)
setattr(Variable, 'streamplot', graphics.streamplot)
setattr(Variable, 'draw_minimap', graphics.draw_minimap)
setattr(Variable, 'taylor', graphics.taylor)
setattr(Variable, 'xyz', graphics.xyz)
setattr(Variable, 'XYZ', graphics.XYZ)
setattr(Variable, 'plot_trend', graphics.plot_trend)
setattr(Variable, 'div', statistics.div)

