
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
			print "Warning, default behaviour"
			lats = 60, 60
			#raise NotImplementedError, 'Only longitude profiles are implemented'
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
	if 'latitude' in self.metadata :
		if isinstance(self.metadata['latitude'], tuple) :
			lats = self.metadata['latitude']
		else :
			lats = tuple([self.metadata['latitude']]*2)
	else :
		lats = tuple([60]*2)
	if colorbar :
		plotGrid = gridspec.GridSpec(2, 2, hspace=0, height_ratios=[8, 1],
				width_ratios=[20, 1])
		axs = [plt.subplot(plotGrid[0, 0]), plt.subplot(plotGrid[1, 0]),
				plt.subplot(plotGrid[0, 1])]
	else :
		plotGrid = gridspec.GridSpec(2, 1, hspace=0, height_ratios=[6, 1])
		axs = [plt.subplot(plotGrid[0]), plt.subplot(plotGrid[1])]
	plt.sca(axs[1])
	plt.xlim(self.lons[0], self.lons[-1])
	self.minimap.drawcoastlines()
	self.minimap.drawparallels(lats, color='red')
	p = plt.Polygon(
				[(0, lats[0]),
				(0, lats[1]),
				(360, lats[1]),
				(360, lats[0])],
			facecolor='red', alpha=0.5)
	plt.gca().add_patch(p)
	#self.minimap.drawmeridians(np.arange(0, 360, 30), labels=[0, 0, 0, 1])
	self.minimap.drawmeridians(np.arange(0, 360, 45), labels=[0, 0, 0, 1])
	plt.gca().set_aspect('auto')
	plt.sca(axs[0])
	plt.setp(axs[0].get_xticklabels(), visible=False)
	plt.setp(axs[0].get_xticklines(), visible=False)
	return axs

def xyz(self) :
	x, y = self.basemap(
			*np.meshgrid(self.lon.edges, self.lat.edges))
	return x, y, self.data 

def XYZ(self) :
	from mpl_toolkits.basemap import addcyclic
	# need addcyclic if n/s-plaea
	if self.basemap.projection in ['nplaea', 'splaea'] :
		z, lons = addcyclic(self.data, np.array(self.lons))
		x, y = self.basemap(
			*np.meshgrid(lons, self.lats))
	else :
		x, y = self.basemap(
			*np.meshgrid(np.array(self.lons), self.lats))
		z = self.data
	return x, y, z

def plot(self) :
	import matplotlib.pyplot as plt
	if len(self.axes) == 1 :
		####################
		# VERTICAL PROFILE #
		####################
		if 'level' in self.axes :
			mask = ~np.isnan(self.data)
			output = plt.plot(self.data[mask], self.levs[mask])
			# make sure pressures decrease with height
			if not plt.gca().yaxis_inverted() :
				plt.gca().invert_yaxis()
			return output
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
			#self.draw_minimap()
			plt.xlim(self.lats.min(), self.lats.max())
			return plt.plot(self.lats, self.data)
	elif len(self.axes) == 2 :
		#######
		# MAP #
		#######
		if self.data.min() < 0 :
			cmap = plt.cm.seismic
			norm = ccb() 
		else :
			cmap = None
			norm = None
		if 'latitude' in self.axes and \
				'longitude' in self.axes :
			self.basemap.drawcoastlines()
			graph = self.basemap.pcolormesh(*self.xyz(),
				cmap = cmap, norm = norm)
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
			graph = plt.pcolormesh(self.data,
					cmap = cmap, norm = norm)
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
			x, y = np.meshgrid(self.lon.edges, self.lev.edges)
			graph = plt.pcolormesh(
					x, y, self.data,
					cmap = cmap, norm = norm)
			plt.xlim(self.lon[0], self.lon[-1])
			plt.ylim(self.lev.edges[0], self.lev.edges[-1])
			if self.levs[0] < self.levs[1] :
				plt.gca().invert_yaxis()
			plt.draw()
			plt.colorbar(graph, cax=axs[2])
		#####################
		#  LAT-LEV PROFILE  #
		#####################
		if 'latitude' in self.axes and 'level' in self.axes :
			x, y = np.meshgrid(self.lat.edges, self.lev.edges)
			graph = plt.pcolormesh(
					x, y, self.data,
					cmap = cmap, norm = norm)
			plt.xlim(self.lat[0], self.lat[-1])
			plt.ylim(self.lev.edges[0], self.lev.edges[-1])
			if self.levs[0] < self.levs[1] :
				plt.gca().invert_yaxis()
			plt.draw()
			plt.colorbar(graph)

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
	if zonal.basemap.projection == 'cyl' :
		x, y = np.meshgrid(zonal.lons, zonal.lats)
		graph = zonal.basemap.quiver(x, y, zonal.data, meridional.data, **kwargs)
	else :
		u, v, x, y = zonal.basemap.transform_vector(
				zonal.data[order], meridional.data[order], zonal.lons,
				zonal.lats[order], nx, ny, 	returnxy = True, masked=True)
		graph = zonal.basemap.quiver(x, y, u, v, **kwargs)
	#plt.quiverkey(graph, 0...
	return graph

def streamplot(zonal, meridional, nx=15, ny=15, **kwargs) :
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
	graph = zonal.basemap.streamplot(x, y, u, v, **kwargs)
	return graph

def taylor(reference, variables, rect=111) :
	if not isinstance(variables, list) :
		variables = [variables]
	reference = reference.data
	variables = [variable.data for variable in variables]
	import matplotlib.pyplot as plt
	from matplotlib.projections import PolarAxes
	from mpl_toolkits.axisartist import SubplotHost
	from mpl_toolkits.axisartist.floating_axes import GridHelperCurveLinear
	from mpl_toolkits.axisartist.floating_axes import FloatingSubplot
	from mpl_toolkits.axisartist.grid_finder import FixedLocator, DictFormatter
	std_max = 1.2*max([variable.std() for variable in variables + [reference]])
	tr = PolarAxes.PolarTransform()
	corrLabels = np.concatenate((np.arange(0, 0.8, 0.2), [0.75, 0.85, 0.95, 0.99, 1]))
	thetaLocations = np.arccos(corrLabels)
	grid_locator1 = FixedLocator(thetaLocations)
	tick_formatter1 = DictFormatter(
			{thetaLocation:str(corrLabels) for thetaLocation, corrLabels
			in zip(thetaLocations, corrLabels)})
	grid_helper = GridHelperCurveLinear(tr,
			extremes=(0, 0.5*np.pi, 0, std_max),
			grid_locator1=grid_locator1,
			tick_formatter1=tick_formatter1)
	ax1 = FloatingSubplot(plt.gcf(), rect, grid_helper=grid_helper)
	#ax1 = SubplotHost(plt.gcf(), 111, grid_helper=grid_helper)
	ax1.set_aspect(1.)
	#plt.xlim(-0.2*std_max, 1.1*std_max)
	#plt.ylim(-0.2*std_max, 1.1*std_max)
	plt.gcf().add_subplot(ax1)
	ax1.axis["top"].set_axis_direction("bottom") # "Angle axis"
	ax1.axis["top"].toggle(ticklabels=True, label=True)
	ax1.axis["top"].major_ticklabels.set_axis_direction("top")
	ax1.axis["top"].label.set_axis_direction("top")
	ax1.axis["top"].label.set_text("Correlation")
	ax1.axis["left"].set_axis_direction("bottom") # "X axis"
	ax1.axis["left"].label.set_text("Standard deviation")
	ax1.axis["right"].set_axis_direction("top") # "Y axis"
	ax1.axis["right"].toggle(ticklabels=True)
	ax1.axis["right"].major_ticklabels.set_axis_direction("left") 
	ax1.axis["bottom"].set_visible(False)
	ax1.scatter(*to_cartesian(reference.std(), 1))
	for variable in variables :
		ax1.scatter(
				*to_cartesian(
					variable.std(),
					np.corrcoef(variable, reference)[0, 1]))

def to_cartesian(std, corr) :
	return std*corr, std*(1 - corr**2)**0.5

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

def plot_trend(self) :
	import matplotlib.pyplot as plt
	if len(self.slope.shape) == 0 :
		if self.significance.data :
			plt.plot(self.dts, self.line.data, lw=2)
		else :
			plt.plot(self.dts, self.line.data, ls='--')
	elif len(self.slope.shape) == 2 :
		if 'latitude' in self.slope.axes and\
				'longitude' in self.slope.axes :
			self.basemap.drawcoastlines()
			graph = self.basemap.pcolormesh(*(self.slope*self.significance).xyz(),
					cmap=plt.cm.seismic, norm=ccb())
			colorBar = plt.colorbar()
			if 'units' in self.__dict__ :
				colorBar.set_label(self.units + 'per year')
			graph = self.basemap.pcolormesh(*self.slope.xyz(),
					cmap=plt.cm.seismic, norm=ccb(), alpha=0.01)
			#cs = self.basemap.contour(*((-1)*self.significance+0.5).XYZ(), levels=[-0.1, 0])
			return graph, colorBar
		if 'longitude' in self.slope.axes and\
				'level' in self.slope.axes :
			axs = self.draw_minimap(True)
			plt.xlim(0, len(self.lons))
			plt.ylim(0, len(self.levs))
			if self.levs[0] < self.levs[1] :
				order = slice(None, None, -1)
			else :
				order = slice(None)
			graph = plt.pcolormesh((self.slope*self.significance).data[order],
					cmap=plt.cm.seismic, norm=ccb())
			plt.draw()
			plt.colorbar(graph, cax=axs[2])
			graph = plt.pcolormesh(self.slope.data[order],
					cmap=plt.cm.seismic, norm=ccb(), alpha=0.08)
			tickLabels = [tckL.get_text() 
					for tckL in plt.gca().get_yticklabels()]
			for idx, tickLabel in enumerate(tickLabels) :
				if tickLabel != '' :
					tickLabels[idx] = str(
							self.levs[int(tickLabel)])
			plt.gca().set_yticklabels(tickLabels[order])

