
"""
An interface between scipy, pandas, pygrib and matplotlib's basemap
"""

#import numpy as np
import matplotlib.pyplot as plt
from scipy.io.netcdf import netcdf_file

class Dataset :
	def __init__(self, filePath, mode = 'r') :
		if filePath.endswith('nc') :
			self.dataFormat = 'nc'
			self.raw = netcdf_file(filePath, mode)

			self.variableNames = self.raw.variables.keys()
		else :
			print "Format not supported"

	def __getattr__(self, attributeName) :
		if attributeName in self.variableNames :
			return Variable(
				self,
				self.raw.variables[attributeName].data)
		else :
			raise AttributeError


class Variable :
	def __init__(self, data) :
		if dataset.dataFormat == 'nc' :
			self.data = data
		else :
			print "Format not supported"
	
	def __getitem__(self, *args, **kwargs) :
		return self.data.__getitem__(*args, **kwargs)


