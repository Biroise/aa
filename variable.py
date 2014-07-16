

class Variable(object) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.variables.keys() :
			return self.variables[attributeName]
		elif attributeName in self.axes.keys() :
			return self.axes[attributeName]
		else :
			raise AttributeError

	def __getitem__() :
		raise NotImplementedError
	def __call__() :
		raise NotImplementedError
	
	def plot(self) :
		if len(self.axes) == 1 :
			pass
		elif len(self.axes) == 2 :
			self.basemap = Basemap(
				projection = 'cyl',
				llcrnrlon = self.longitude.data.min(),
				llcrnrlat = self.latitude.data.min(),
				urcrnrlon = self.longitude.data.max(),
				urcrnrlat = self.latitude.data.max())
			bm.drawcoastlines()
		else :
			print "Variable has too many axes or none"


