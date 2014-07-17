
import numpy as np
from mpl_toolkits.basemap import Basemap

class Variable(object) :
	def __init__(self) :
		self.axes = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		else :
			raise AttributeError

	def __getitem__() :
		raise NotImplementedError
	def __call__() :
		raise NotImplementedError
	
	def get_basemap(self) :
		# assign to self a standard basemap
		self._basemap = Basemap(
				projection = 'cyl',
				llcrnrlon = self.longitude.data.min(),
				llcrnrlat = self.latitude.data.min(),
				urcrnrlon = self.longitude.data.max(),
				urcrnrlat = self.latitude.data.max())
		return self._basemap
	def set_basemap(self, someMap) :
		# user may set basemap himself
		self._basemap = someMap
	basemap = property(get_basemap, set_basemap)

	@property
	def plot(self) :
		if len(self.axes) == 1 :
			if self.axes.keys()[0] == 'levels' :
				return plt.plot(self.data, self.axes['levels'])
			else :
				return plt.plot(self.axes.values()[0], self.data)
		elif len(self.axes) == 2 :
			if 'latitude' in self.axes.keys() and \
					'longitude' in self.axes.keys() :
				self.basemap.drawcoastlines()
				x, y = self.basemap(
					*np.meshgrid(self.longitude.data, self.latitude.data))
				return self.basemap.pcolormesh(x, y, self.data)
		else :
			print "Variable has too many axes or none"


