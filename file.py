

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
	
	def write(self, fileName) :
		import netCDF4	
		pass



