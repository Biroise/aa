
"""
An interface between scipy, netCDF4, pygrib and matplotlib's basemap
"""

from axis import *
from file import File
from variable import Variable

import numpy as np


def open(filePath, mode='r') :
	"Picks the appropriate File subclass to model a gridded data file"
	if filePath.endswith('nc') :
		from aa import netcdf
		File = netcdf.File(filePath, mode)
	elif filePath.endswith('grib') or filePath.endswith('grb') \
			or filePath.endswith('grb2') :
		import os
		fileName = os.path.splitext(filePath)[0]
		picklePath = fileName + '.p'
		indexPath = fileName + '.idx'
		if os.path.isfile(picklePath) and os.path.isfile(indexPath) :
			import __builtin__
			import cPickle as pickle
			malossol = __builtin__.open(picklePath)
			File = pickle.load(malossol)
		else :
			from aa import grib
			File = grib.File(filePath)
	if len(File.variables) == 1 :
		print "WARNING : output is the only variable this file contains"
		return File.variables.values()[0]
	else :
		return File


def load(variable, dataset, year, month) :
		#######
		# ERA #
		#######
		if dataset == 'era' :
			if variable in ['q', 'u', 'v'] :
				f = open('/media/POMNITIE/era/3D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb')
				# open will return the variable since the file is otherwise empty
				#f.levs /= 100
				#f.lev.units = 'hPa'
				return f
			if variable in ['prs', 'tcw', 'tcwv', 'qu', 'qv'] :
				return open('/media/POMNITIE/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb')

		########
		# NCAR #
		########
		if dataset == 'ncar' :
			if variable in ['u', 'v'] :
				f = open('/media/SOUVIENSTOI/ncar/3D/'+variable+'wnd.'+str(year)+'.nc')
				return f[variable+'wnd'](time=month(year, month))
			if variable == 'q' :
				f = open('/media/SOUVIENSTOI/ncar/3D/'+str(year)+str(month).zfill(2)+'.nc')
				return f['q']

		#######
		# DOE #
		#######
		if dataset == 'doe' :
			if variable in ['u', 'v'] :
				f = open('/media/SOUVIENSTOI/doe/3D/'+variable+'wnd.'+str(year)+'.nc')
				return f[variable+'wnd'](time=month(year, month))
			if variable == 'q' :
				f = open('/media/SOUVIENSTOI/doe/3D/shum.'+str(year)+str(month).zfill(2)+'.nc')
				return f['q']

		#########
		# MERRA #
		#########
		if dataset == 'merra' :
			f = open('/media/REMEMBER/merra/3D/'+str(year)+str(month).zfill(2)+'.nc')
			if variable in ['u', 'v'] :
				return f[variable]
			if variable in ['q'] :
				return f['qv']

		#########
		# JRA25 #
		#########
		if dataset == 'jra25' :
			f = open('/home/adufour/jra25/3D/'+str(year)+str(month).zfill(2)+'.grb')
			return f[variable]

