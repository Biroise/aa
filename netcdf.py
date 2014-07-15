
from scipy.io.netcdf import netcdf_file

import aa

class File(aa.File) :
	def __init__(self, filePath) :
		self.fileFormat = 'nc'
		self.raw = netcdf_file(filePath, 'r')
		self.dimensionNames = set(self.raw.dimensions.keys())
		self.variableNames = set(self.raw.variables.keys()) \
				- self.dimensionNames
		########
		# AXES #
		########
		for dimensionName in self.dimensionNames :
			if dimensionName == 'time' :
				setattr(self, dimensionName, aa.TimeAxis(
					self.raw.variables[dimensionName].data,
					self.raw.variables[dimensionName].units
					))
			else :
				setattr(self, dimensionName, aa.Axis(
					self.raw.variables[dimensionName].data,
					self.raw.variables[dimensionName].units
					))

	def __getattr__(self, attributeName) :
		"Load variables on demand"
		if attributeName in self.variableNames :
			return aa.Variable(
				self.raw.variables[attributeName].data,
				self.raw.variables[attributeName].units,
				[getattr(self, dimensionName) for dimensionName in
					self.raw.variables[attributeName].dimensions]
				)
		else :
			raise AttributeError
	
if __name__ == "__main__" :
	f = aa.open('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
	
