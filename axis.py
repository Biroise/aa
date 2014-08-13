
import numpy as np
import operator as op
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta


class Axes(OrderedDict) :
	aliases = {'latitude':'latitude', 'latitudes':'latitude',
		'lat':'latitude', 'longitude':'longitude',
		'longitudes':'longitude', 'lon':'longitude',
		'level':'level', 'levels':'level', 'lev':'level',
		'time':'time', 'dt':'time', 't':'time',
		'x':'longitude', 'y':'latitude', 'z':'level'}
	shortcuts = {'lats':'latitude', 'lons':'longitude',
		'levs':'level', 'dts':'time'}

	def __setitem__(self, attributeName, value) :
		if attributeName in Axes.aliases :
			return super(Axes, self).__setitem__(
					Axes.aliases[attributeName], value)
		if attributeName in Axes.shortcuts :
			return super(Axes, self).__setitem__(
					Axes.shortcuts[attributeName], value)

	def __getitem__(self, attributeName) :
		# dealing with the most common aliases
		if attributeName in Axes.aliases :
			return super(Axes, self).__getitem__(
					Axes.aliases[attributeName])
		if attributeName in Axes.shortcuts :
			return super(Axes, self).__getitem__(
					Axes.shortcuts[attributeName])[:]
		# if no cases fit
		raise AttributeError


class Axis(object) :
	def __init__(self, data, units) :
		self.data = data
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
			if len(condition) == 2 :
				# default boundaries are "closed-closed" unlike numpy
				condition = condition + ('cc',)
			# if the lower boundary is closed...
			if condition[2][0] == 'c' :
				lowerCondition = op.ge
			else :
				lowerCondition = op.gt
			# if the upper boundary is closed...
			if condition[2][1] == 'c' :
				upperCondition = op.le
			else :
				upperCondition = op.lt
			# extract the sub-axis related to the newConditions
			mask = np.logical_and(
				lowerCondition(self[:] - condition[0],
						# adapt 0 to axis unit : number / timedelta(0)
						type(self[0] - condition[0])(0)),
				upperCondition(self[:] - condition[0], 
					condition[1]-condition[0]))
			# now extract the sub-axis corresponding to the condition
			return self.make_slice(mask, condition)
		# extract a single index only
		else :
			return self.find_index(condition), None
			# don't add this axis to newAxes

	def copy(self) :
		newAxes = Axes()
		for axisName, axis in self.iteritems() :
			newAxes[axisName] = axis.copy()

	@property
	def weights(self) :
		# trapezoidal integration
		output = np.zeros(self.data.shape)
		output[1:] += 0.5*np.abs(np.diff(self.data))
		output[:-1] += 0.5*np.abs(np.diff(self.data))
		return output
		

	def make_slice(self, mask, condition) :
		return (slice(np.argmax(mask),
				len(mask) - np.argmax(mask[::-1])),
			Axis(self[mask], self.units))

	def find_index(self, condition) :
		index = np.argmax(self[:] == condition)
		if index == 0 and self[0] != condition :
			print IndexError
		return index


@np.vectorize
def in_seconds(delta) :
	return delta.seconds


class TimeAxis(Axis) :
	def __init__(self, data, unitDefinition=None) :
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
				[epoch + timedelta(**{units: offset})
				for offset in self.data])

	@property
	def weights(self) :
		# trapezoidal integration
		output = np.zeros(self.data.shape)
		output[1:] += 0.5*np.abs(in_seconds(np.diff(self.data)))
		output[:-1] += 0.5*np.abs(in_seconds(np.diff(self.data)))
		return output
		

class Longitudes(np.ndarray) :
	def __eq__(self, toBeCompared) :
		return super(Longitudes, self%360).__eq__(toBeCompared%360)
	def __gt__(self, toBeCompared) :
		return super(Longitudes, self%360).__gt__(toBeCompared%360)
	def __ge__(self, toBeCompared) :
		return super(Longitudes, self%360).__ge__(toBeCompared%360)
	def __lt__(self, toBeCompared) :
		return super(Longitudes, self%360).__lt__(toBeCompared%360)
	def __le__(self, toBeCompared) :
		return super(Longitudes, self%360).__le__(toBeCompared%360)
	def __sub__(self, toSubstract) :
		return super(Longitudes,
				(super(Longitudes, self).__sub__(toSubstract) + 180)%360
			).__sub__(180)
	def min(self) :
		return np.float(super(Longitudes, self).min())
	def max(self) :
		return np.float(super(Longitudes, self).max())


def angle_sub(a, b) :
	return (a - b + 180)%360 -180


class Parallel(Axis) :
	# the parallel being the longitudinal axis
	def __init__(self, data, units, latitudes=[0]) :
		self.data = data.view(Longitudes)
		self.units = units
		# an extra argument to get the weights right
		self.latitudes = latitudes
	
	def make_slice(self, mask, condition) :
		# selected longitudes are at the beginning and end of the axis
		if mask[0] and mask[-1] and not mask.all() :
			# first slice, the end part
			firstSlice = slice(-np.argmax(~mask[::-1]), None)
			firstOffset = round((condition[0] - self[-1])/360)*360
			secondSlice = slice(0, np.argmax(~mask)) 
			secondOffset = round((condition[0] - self[0])/360)*360
			return ((firstSlice, secondSlice), 
				Parallel(np.hstack((
						self[firstSlice] + firstOffset, 
						self[secondSlice] + secondOffset)),
					self.units))
		else :
			return (slice(np.argmax(mask), len(mask) - np.argmax(mask[::-1])),
				Parallel(
					self[mask] + round((condition[0]-self[mask][0])/360)*360,
					self.units))

	@property
	def weights(self) :
		output = super(Parallel, self).weights
		if angle_sub(self.data[0], self.data[-1]) \
				<= np.mean(np.diff(self.data)) :
			output[0] += 0.5*angle_sub(self[0], self[-1])
			output[-1] += 0.5*angle_sub(self[0], self[-1])
		#return 6371000*np.cos(self.latitudes[:, None]*np.pi/180)\
				#*output[None, :]*np.pi/180
		# leave the cos(lat) to average
		return 6371000*output*np.pi/180


class Meridian(Axis) :
	def weights(self) :
		return super(Meridian, self).weights*np.pi/180


def month(year, monthIndex) :
	return (datetime(year, monthIndex, 1),
			datetime(year + (monthIndex+1)/12, (monthIndex+1)%12, 1),
			'co')
	


