
import numpy as np
import operator as op
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta

earthRadius = 6371000

class Axes(OrderedDict) :
	aliases = {'latitude':'latitude', 'latitudes':'latitude',
		'lat':'latitude', 'longitude':'longitude',
		'longitudes':'longitude', 'lon':'longitude',
		'level':'level', 'levels':'level', 'lev':'level',
		'time':'time', 'dt':'time', 't':'time',
		'Time':'time',
		'x':'longitude', 'y':'latitude', 'z':'level',
		'level0':'level', 'PRES':'level'}
	shortcuts = {'lats':'latitude', 'lons':'longitude',
		'levs':'level', 'dts':'time'}
	ncStandard = {'latitude':'lat', 'longitude':'lon',
			'level':'lev', 'time':'time'}
	
	@staticmethod
	def ncStandardize (axisName) :
		if axisName in Axes.ncStandard :
			return Axes.ncStandard[axisName]
		else :
			return axisName

	@staticmethod
	def standardize(axisName) :
		if axisName in Axes.aliases :
			return Axes.aliases[axisName]
		elif axisName in Axes.shortcuts :
			return Axes.shortcuts[axisName]
		else :
			return axisName

	def __setitem__(self, axisName, value) :
		return super(Axes, self).__setitem__(
				Axes.standardize(axisName), value)

	def __getitem__(self, attributeName) :
		# dealing with the most common aliases
		if attributeName in Axes.aliases :
			return super(Axes, self).__getitem__(
					Axes.aliases[attributeName])
		elif attributeName in Axes.shortcuts :
			return super(Axes, self).__getitem__(
					Axes.shortcuts[attributeName])[:]
		else :
			# an except clause to change the KeyError into a AttributeError
			try :
				return super(Axes, self).__getitem__(attributeName)
			except :
				raise AttributeError

	
	def copy(self) :
		newAxes = Axes()
		for axisName, axis in self.iteritems() :
			newAxes[axisName] = axis.copy()
		return newAxes

	def index(self, axisName) :
		return self.keys().index(Axes.standardize(axisName))

	@property
	def shape(self) :
		output = []
		for axis in self.values() :
			output.append(len(axis))
		return tuple(output)


class Axis(object) :
	def __init__(self, data, units) :
		self.data = np.array(data)
		self.units = units
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)
	def __setitem__(self, *args, **kwargs) :
		return self.data.__setitem__(*args, **kwargs)

	def __len__(self) :
		return len(self.data)

	def __call__(self, condition) :
		# should a range of indices be extracted ?
		if type(condition) == tuple :
			# if the user does not provide the type of boundaries
			if len(condition) > 1 :
				minValue = condition[0]
				maxValue = condition[1]
			if len(condition) == 2 :
				# default boundaries are "closed-closed" unlike numpy
				condition = condition + ('cc',)
			# if the lower boundary is closed...
			if condition[2][0] == 'c' :
				minType = op.ge
			else :
				minType = op.gt
			# if the upper boundary is closed...
			if condition[2][1] == 'c' :
				maxType = op.le
			else :
				maxType = op.lt
			# the following tasks are given to a function that can be over-ridden
			# by the subclasses of Axis (e.g. Parallel)
			return self.process_call(minValue, maxValue, minType, maxType)
		# extract a single index only
		else :
			index = np.argmax(self[:] == condition)
			# if there is no exact match, send the neighbours
			if index == 0 and self[0] != condition :
				newCondition = (condition - self.step, \
							condition + self.step, 'cc')
				return self(newCondition)
			else :
				return index, None
				# don't add this axis to newAxes

	def process_call(self, minValue, maxValue, minType, maxType) :
		mask = np.logical_and(
				minType(self[:] - minValue,
						# adapt 0 to axis unit : number / timedelta(0)
						type(self[0] - minValue)(0)),
				maxType(self[:] - minValue,
						maxValue - minValue))
		# now extract the sub-axis corresponding to the condition
		return (slice(np.argmax(mask),
						len(mask) - np.argmax(mask[::-1])),
				Axis(self[mask], self.units))

	def __eq__(self, other) :
		answer = False
		if hasattr(other, 'data') and hasattr(other, 'units') :
			if len(self.data) == len(other.data) and self.units == self.units :
				if (self.data == other.data).all() :
					answer = True
		# if other has no data/units attributes e.g. "self == None ?"
		# if self WAS of NoneType (or any other type), this method would not be called
		# hence the answer is always False in this case
		return answer

	@property
	def step(self) :
		# extremely basic, won't work for irregular axes such as levels
		a = np.abs(np.diff(self.data))
		assert (a.min() - a.max())/a[0] < 0.05
		return a[0]
	
	@property
	def edges(self) :
		if self.data[0] < self.data[1] :
			return np.concatenate(
					(self.data - self.step/2,
					[self.data[-1] + self.step/2]))
		else :
			return np.concatenate(
					(self.data + self.step/2,
					[self.data[-1] - self.step/2]))
	
	@property
	def weights(self) :
		return np.ones(1)
	
	def copy(self) :
		if isinstance(self.data, list) :
			return self.__class__(self.data[:], self.units)
		else :
			return self.__class__(self.data.copy(), self.units)


class TimeAxis(Axis) :
	def __init__(self, data, unitDefinition=None) :
		data = np.array(data)
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
			self.data = np.array(
				[epoch + timedelta(**{units: np.asscalar(offset)})
				for offset in self.data])
			self.units = None
	
	@property
	def step(self) :
		# extremely basic, won't work for irregular axes such as levels
		a = np.abs(np.diff(self.data))
		assert (a.min() - a.max()).total_seconds()/a[0].total_seconds() < 0.05
		return a[0]
	
	@property
	def years(self) :
		return np.array([dt.year for dt in self.data])

	@property
	def months(self) :
		return np.array([dt.month for dt in self.data])

	@property
	def hours(self) :
		return np.array([dt.hour for dt in self.data])


class Parallel(Axis) :
	# the parallel being the longitudinal axis
	def __init__(self, data, units='degrees') :
		super(Parallel, self).__init__(data, units)
	
	def process_call(self, minValue, maxValue, minType, maxType) :
		# (x - x0)% 360 + x0 places x between x0 and x0 + 360
		firstMask = minType(
				self[:],
				(minValue - self[0])%360 + self[0])
		secondMask = maxType(
				self[:],
				(maxValue - self[0])%360 + self[0])
		# slice loops from end to beginning of array
		if maxValue - minValue >= 360 :
			offset = minValue - (minValue - self[0])%360 - self[0]
			firstSlice = slice(-np.argmax(~firstMask[::-1]), None)
			secondSlice = slice(0, np.argmax(~secondMask)) 
			return (
					(firstSlice, secondSlice), 
					Parallel(
							np.hstack((
								self[firstMask] + offset,
								self[secondMask] + offset + 360))))
		elif maxValue - minValue <= 360 :
			mask = np.logical_and(firstMask, secondMask)
			return (
					slice(np.argmax(mask),
							len(mask) - np.argmax(mask[::-1])),
					Parallel(
							(self[mask] - minValue)%360 + minValue,
							self.units))
	
	@property
	def edges(self) :
		data = np.array(list(self.data))
		if data[0] < data[1] :
			return np.concatenate(
					(data - self.step/2,
					[data[-1] + self.step/2]))
		else :
			return np.concatenate(
					(data + self.step/2,
					[data[-1] - self.step/2]))
		

class Meridian(Axis) :
	def __init__(self, data, units='degrees') :
		super(Meridian, self).__init__(data, units)
	
	@property
	def weights(self) :
		return np.cos(self.data*np.pi/180.0)
	
	@property
	def edges(self) :
		default = super(Meridian, self).edges
		for endIndex in [0, -1] :
			if default[endIndex] > 90 :
				default[endIndex] = 90
			if default[endIndex] < -90 :
				default[endIndex] = -90
		return default


class Vertical(Axis) :
	@property
	def weights(self) :
		output = np.zeros(len(self))
		output[:-1] += 0.5*np.abs(np.diff(self.data))
		output[1:] += 0.5*np.abs(np.diff(self.data))
		output *= 100/9.81
		return output


def month(year, monthIndex) :
	return (datetime(year, monthIndex, 1),
			datetime(year + (monthIndex+1)/12, (monthIndex+1)%12, 1),
			'co')
	

def angle_sub(a, b) :
	return (a - b + 180)%360 -180

@np.vectorize
def in_seconds(delta) :
	return delta.seconds


