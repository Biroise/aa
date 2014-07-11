
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

#import numpy as np
import matplotlib.pyplot as plt
from scipy.io.netcdf import netcdf_file


class DataFile :
	def __init__(self, filePath, mode = 'r') :
		if filePath.endswith('nc') :
			self.fileFormat = 'nc'
			self.raw = netcdf_file(filePath, mode)
			self.dimensionNames = self.raw.dimensions.keys()
			self.variableNames = self.raw.variables.keys()
			# create axes
			for dimensionName in self.dimensionNames :
					setattr(self, dimensionName, Axis(
						self.raw.variables[dimensionName].data))
		else :
			print "Format not supported"

	# load variables on demand
	def __getattr__(self, attributeName) :
		if attributeName in self.variableNames :
			return Variable(
				self.raw.variables[attributeName].data)
		else :
			raise AttributeError


class Variable :
	def __init__(self, data) :
		self.data = data
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


class Axis :
	def __init__(self, data) :
		self.data = data
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


f = DataFile('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
