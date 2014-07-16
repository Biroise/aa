
"""
An interface between scipy, pygrib and matplotlib's basemap
"""

import numpy as np
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

from variable import Variable
from axis import Axis
from axis import TimeAxis


class File(object) :
	def __init__(self) :
		self.axes = {}
		self.variables = {}

	def __getattr__(self, attributeName) :
		if attributeName in self.axes.keys() :
			return self.axes[attributeName]
		elif attributeName in self.variables.keys() :
			return self.variables[attributeName]
		else :
			raise AttributeError

	def close(self) :
		self._raw.close()
		del self


def open(filePath) :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		import netcdf
		return netcdf.File(filePath)
	if filePath.endswith('grib') :
		import grib
		return grib.File(filePath)


if __name__ == "__main__" :
	f = open('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
	#f = open('/home/ambroise/atelier/anniversaire/tmp.grib')
	h = f.h(time=datetime(1988, 7, 11, 9), levels=1000)
	h.plot()
