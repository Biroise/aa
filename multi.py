
import numpy as np

import aa

class File(aa.File) :
	def __init__(self, fileNames) :
		super(File, self).__init__()
		if type(fileNames[0]) == str :
			self.files = [aa.open(fileName, fileOnly=True)
					for fileName in fileNames]
		else :
			self.files = fileNames
		# first file serves as template
		# make sure files are consistent
		self.axes = self.files[0].axes.copy()
		self.axes['time'] = aa.TimeAxis(np.concatenate(
				[file.dts for file in self.files]))
		for variableName, variable in self.files[0].variables.iteritems() :
			newAxes = variable.axes
			newAxes['time'] = self.axes['time'].copy()
			self.variables[variableName] = Variable(
				axes = newAxes,
				metadata = variable.metadata,
				conditions = {},
				subVariables = [file[variableName]
						for file in self.files])
			

class Variable(aa.Variable) :
	def __init__(self, axes, metadata, conditions, subVariables) :
		super(Variable, self).__init__()
		self.axes = axes
		self.full_axes = axes.copy()
		self.metadata = metadata
		self.conditions = conditions
		self.subVariables = subVariables
		
	@property
	def shape(self) :
		if "_data" not in self.__dict__ :
			dimensions = []
			for axis in self.axes.values() :
				dimensions.append(len(axis))
			return tuple(dimensions)	
		else :
			return super(Variable, self).shape
	
	def extract_data(self, **kwargs) :
		"Extract a subset via its axes"
		# if the variable is still in pure "multi" mode
		if "_data" not in self.__dict__ :
			# conditions and axes for the output variable
			# multi conditions are just call arguments
			newConditions = self.conditions.copy()
			newAxes = self.axes.copy()
			for axisName, condition in kwargs.iteritems() :
				if axisName == 'time' :
					raise NotImplementedError, "Can't select times yet"
				# update axes but don't store item (a slice)
				item, newAxis = self.full_axes[axisName](condition)
				newConditions[axisName] = condition
				# if item is scalar, there will be no need for an axis
				if newAxis == None :
					del newAxes[axisName]
					self.metadata[axisName] = condition
				# otherwise, load newAxis in the new variable's axes
				else :
					newAxes[axisName] = newAxis
			return Variable(newAxes, self.metadata.copy(),
					newConditions, self.subVariables)
		# if _data already exists (as a numpy array), follow standard protocol
		else :
			return super(Variable, self).extract_data(**kwargs)
	
	def _get_data(self) :
		if '_data' not in self.__dict__ :
			self._data = np.concatenate(
					[subVariable(**self.conditions).data
					for subVariable in self.subVariables])
		return self._data
	def _set_data(self, newValue) :
		self._data = newValue
	data = property(_get_data, _set_data)

