
"""
An interface between scipy, pandas, pygrib and matplotlib's basemap
"""

#import numpy as np
#import pandas as pd
import matplotlib.pyplot as plt
from scipy.io.netcdf import netcdf_file

class Dataset :
	def __init__(self, filePath, mode = 'r') :
		if filePath.endswith('nc') :
			self.kind = 'nc'
			self.raw = netcdf_file(filePath, mode)

			self.variableNames = self.raw.variables.keys()
		else :
			print "Not supported"

	def __getattr__(self, attributeName) :
		if attributeName in self.variableNames :
			return self.raw.variables[attributeName]
		else :
			raise AttributeError
