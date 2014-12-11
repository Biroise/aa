
import numpy as np
from matplotlib.colors import Normalize

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

def _get_minimap(self) :
	if '_basemap' not in self.__dict__ :
		import matplotlib.pyplot as plt
		from mpl_toolkits.basemap import Basemap
		if 'latitude' in self.metadata :
			if isinstance(self.metadata['latitude'], tuple) :
				lats = self.metadata['latitude']
			else :
				lats = tuple([self.metadata['latitude']]*2)
		else :
			raise NotImplementedError, 'Only longitude profiles are implemented'
		self._minimap = Basemap(
			projection = 'cyl',
			llcrnrlon = self.lons[0],
			llcrnrlat = max(lats[0] - 10, -90),
			urcrnrlon = self.lons[-1],
			urcrnrlat = min(lats[1] + 10, 90))
	return self._minimap
def _set_minimap(self, someMap) :
	# user may set basemap himself
	self._basemap = someMap

def draw_minimap(self, colorbar = False) :
	import matplotlib.gridspec as gridspec
	import matplotlib.pyplot as plt
	if isinstance(self.metadata['latitude'], tuple) :
		lats = self.metadata['latitude']
	else :
		lats = tuple([self.metadata['latitude']]*2)
	if colorbar :
		plotGrid = gridspec.GridSpec(2, 2, hspace=0, height_ratios=[8, 1],
				width_ratios=[20, 1])
		axs = [plt.subplot(plotGrid[0, 0]), plt.subplot(plotGrid[1, 0]),
				plt.subplot(plotGrid[0, 1])]
	else :
		plotGrid = gridspec.GridSpec(2, 1, hspace=0, height_ratios=[6, 1])
		axs = [plt.subplot(plotGrid[0]), plt.subplot(plotGrid[1])]
	plt.sca(axs[1])
	self.minimap.drawcoastlines()
	self.minimap.drawparallels(lats, color='red')
	p = plt.Polygon(
				[(0, lats[0]),
				(0, lats[1]),
				(360, lats[1]),
				(360, lats[0])],
			facecolor='red', alpha=0.5)
	plt.gca().add_patch(p)
	self.minimap.drawmeridians(np.arange(0, 360, 30), labels=[0, 0, 0, 1])
	plt.gca().set_aspect('auto')
	plt.sca(axs[0])
	plt.setp(axs[0].get_xticklabels(), visible=False)
	plt.setp(axs[0].get_xticklines(), visible=False)
	return axs

def xyz(self) :
	# need addcyclic if n/s-plaea
	if self.basemap.projection in ['nplaea', 'splaea'] :
		self._z, lons = addcyclic(self.data, np.array(self.lons))
		self._x, self._y = self.basemap(
			*np.meshgrid(lons, self.lats))
	else :
		self._x, self._y = self.basemap(
			*np.meshgrid(np.array(self.lons), self.lats))
		self._z = self.data

def x(self) :
	if '_x' not in self.__dict__ :
		self.xyz()
	return self._x

def y(self) :
	if '_y' not in self.__dict__ :
		self.xyz()
	return self._y

def z(self) :
	if '_z' not in self.__dict__ :
		self.xyz()
	return self._z

def plot(self) :
	import matplotlib.pyplot as plt
	from mpl_toolkits.basemap import addcyclic
	if len(self.axes) == 1 :
		####################
		# VERTICAL PROFILE #
		####################
		if 'level' in self.axes :
			# make sure pressures decrease with height
			if not plt.gca().yaxis_inverted() :
				plt.gca().invert_yaxis()
			else :
				return plt.plot(self.data, self.axes['level'])
		###############
		# TIME SERIES #
		###############
		if 'time' in self.axes :
			return plt.plot(self.dts, self.data)
		#####################
		# LONGITUDE PROFILE #
		#####################
		if 'longitude' in self.axes :
			ax_0, ax_1 = self.draw_minimap()
			plt.xlim(self.lons.min(), self.lons.max())
			return ax_0, ax_1, plt.plot(self.lons, self.data)
		####################
		# LATITUDE PROFILE #
		####################
		if 'latitude' in self.axes :
			self.draw_minimap()
			return plt.plot(self.lats, self.data)
	elif len(self.axes) == 2 :
		#######
		# MAP #
		#######
		if 'latitude' in self.axes and \
				'longitude' in self.axes :
			self.basemap.drawcoastlines()
			graph = self.basemap.pcolormesh(self.x, self.y, self.z)
			colorBar = plt.colorbar()
			if 'units' in self.__dict__ :
				colorBar.set_label(self.units)
			return graph, colorBar
		#####################
		# HOVMOLLER DIAGRAM #
		#####################
		if 'longitude' in self.axes and 'time' in self.axes :
			axs = self.draw_minimap(True)
			plt.xlim(0, len(self.lons))
			plt.ylim(0, len(self.dts))
			graph = plt.pcolormesh(self.data)
			plt.draw()
			tickLabels = [tckL.get_text() 
					for tckL in plt.gca().get_yticklabels()]
			for idx, tickLabel in enumerate(tickLabels) :
				if tickLabel != '' :
					tickLabels[idx] = \
							self.dts[int(tickLabel)].isoformat()[:10]
			plt.gca().set_yticklabels(tickLabels)
			plt.colorbar(graph, cax=axs[2])
			return graph
		#####################
		#  LON-LEV PROFILE  #
		#####################
		if 'longitude' in self.axes and 'level' in self.axes :
			axs = self.draw_minimap(True)
			plt.xlim(0, len(self.lons))
			plt.ylim(0, len(self.levs))
			if self.levs[0] < self.levs[1] :
				order = slice(None, None, -1)
			else :
				order = slice(None)
			graph = plt.pcolormesh(self.data[order])
			plt.draw()
			tickLabels = [tckL.get_text() 
					for tckL in plt.gca().get_yticklabels()]
			for idx, tickLabel in enumerate(tickLabels) :
				if tickLabel != '' :
					tickLabels[idx] = str(
							self.levs[int(tickLabel)])
			plt.gca().set_yticklabels(tickLabels[order])
			plt.colorbar(graph, cax=axs[2])
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

