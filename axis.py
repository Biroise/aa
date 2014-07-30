
import numpy as np
import operator as op
from datetime import datetime
from datetime import timedelta


class Axis(object) :
	def __init__(self, data, units) :
		self.data = data
		self.units = units
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)

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
			@np.vectorize
			def window(x) :
				return lowerCondition(
						x, condition[0]) and \
					upperCondition(
						x, condition[1])
			# now extract the sub-axis corresponding to the condition
			mask = window(self[:])
			item = slice(
					np.argmax(mask),
					len(mask) - np.argmax(mask[::-1]))
			newAxis = Axis(self[mask], self.units)
			return item, newAxis
		# extract a single index only
		else :
			index = np.argmax(self[:] == condition)
			if index == 0 and self[0] != condition :
				print "No match in axis slice"
			return index, None
			# don't add this axis to newAxes


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


class Parallel(Axis) :
	# a parallel being the longitudinal axis
	def __init__(self, data, units) :
		self.data = data.view(Longitudes)
		self.units = units

def month(year, monthIndex) :
	return (datetime(year, monthIndex, 1),
			datetime(year + (monthIndex+1)/12, (monthIndex+1)%12, 1),
			'co')
	


