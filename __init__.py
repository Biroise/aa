
"""
An interface between scipy, netCDF4, pygrib and matplotlib's basemap
"""

from axis import *
from file import File
from variable import Variable

import numpy as np


def open(filePath, mode='r', reopen=False, fileOnly=False) :
	"Picks the appropriate file_ subclass to model a gridded data file"
	if isinstance(filePath, list) :
		from aa import multi
		file_ = multi.File(filePath)
	else :
		if filePath.endswith('nc') :
			from aa import netcdf
			file_ = netcdf.File(filePath, mode)
		elif filePath.endswith('grib') or filePath.endswith('grb') \
				or filePath.endswith('grb2') :
			import os
			filePath = os.path.abspath(filePath)
			fileName = os.path.splitext(filePath)[0]
			picklePath = fileName + '.p'
			indexPath = fileName + '.idx'
			if os.path.isfile(picklePath) and os.path.isfile(indexPath) \
					and not reopen :
				import __builtin__
				import cPickle as pickle
				malossol = __builtin__.open(picklePath)
				file_ = pickle.load(malossol)
			else :
				from aa import grib
				file_ = grib.File(filePath)
	if not fileOnly and len(file_.variables) == 1 :
		#print "WARNING : output is the only variable this file contains"
		variable = file_.variables.values()[0]
		variable.metadata['shortName'] = file_.variables.keys()[0]
		return variable
	else :
		return file_

def cos(angleInDegrees) :
	return np.cos(angleInDegrees*np.pi/180.0)

def sin(angleInDegrees) :
	return np.sin(angleInDegrees*np.pi/180.0)

yearMonths = [(year, month) for year in range(1979, 2014)
				for month in range(1, 13)]

def stamp(year, month) :
	return str(year)+str(month).zfill(2)


reanalyses = ['era', 'merra', 'doe', 'ncar', 'jra25']

def load(variable, dataset, year=None, month=None, region=None, reopen=False, fileOnly=False) :
	"customizable load function"

	###############
	# CLIMATOLOGY #
	###############
	if year == None and month == None :
		if region == 'Aa' and \
				dataset in ['merra', 'era', 'cfsr'] and \
				variable in ['qu', 'qv', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
			return open('/media/POMNITIE/climatology/Aa/'+variable+'_'+dataset+'.nc', fileOnly=fileOnly)
		else :
			return open('/media/POMNITIE/climatology/'+variable+'_'+dataset+'.nc', fileOnly=fileOnly)

	#################
	# MONTHLY MEANS #
	#################
	if year == 'all' and month == None :
		return open('/media/POMNITIE/ensemble/'+dataset+'/'+variable+'.nc', fileOnly=fileOnly)

	################
	# FULL DATASET #
	################
	if month == 'all' :
		return open([load(variable, dataset, year, month, fileOnly=True)
				for month in range(1, 13)])

	#######
	# ERA #
	#######
	if dataset == 'era' :
		if variable in ['q', 'u', 'v'] :
			output = open('/media/POMNITIE/era/3D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, fileOnly=fileOnly)
			# open will return the variable since the file is otherwise empty
			#output.levs /= 100
			#output.lev.units = 'hPa'
		variables2D = ['sp', 'div', 'qu', 'qv', 'tcw', 'pwat']
		for prefix in ['tcw', 'e', 'p', 'pwat'] :
			for step in ['03', '06', '09', '12'] :
				variables2D.append(prefix+step)
		if variable in variables2D :
			output =  open('/media/POMNITIE/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, fileOnly=fileOnly)
		if variable in ['p', 'e'] :
			output =  open('/media/POMNITIE/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if variable == 'thck' :
			if region == 'Ar' :
				return open('/media/POMNITIE/era/3D/thck_Ar/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
			elif region == 'Aa' :
				return open('/media/POMNITIE/era/3D/thck_Aa/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
			else : 
				raise Exception
		if region == 'Ar' :
			return output(lat=(60, 90))
		if region == 'Aa' :
			return output(lat=(-90, -60))
		else :
			return output

	########
	# NCAR #
	########
	if dataset == 'ncar' :
		if variable in ['u', 'v', 'q', 'T', 'rh', 'thck'] :
			output = open('/media/SOUVIENSTOI/ncar/3D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)[:, :8]
		if variable in ['e', 'p', 'sp', 'pwat', 'qu', 'qv'] :
			output = open('/media/SOUVIENSTOI/ncar/2D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if region == 'Ar' :
			return output(lat=(60, 90))
		if region == 'Aa' :
			return output(lat=(-90, -60))
		else :
			return output

	#######
	# DOE #
	#######
	if dataset == 'doe' :
		if variable in ['u', 'v', 'q', 'T', 'rh', 'thck'] :
			output = open('/media/SOUVIENSTOI/doe/3D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if variable in ['e', 'p', 'sp', 'pwat', 'qu', 'qv'] :
			output = open('/media/SOUVIENSTOI/doe/2D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if variable == 'e' :
			output = output['lhtfl']
		if variable == 'p' :
			output = output['prate']
		if region == 'Ar' :
			return output(lat=(60, 90))
		if region == 'Aa' :
			return output(lat=(-90, -60))
		else :
			return output


	#########
	# MERRA #
	#########
	if dataset == 'merra' :
		# 2D variables first
		if variable in ['pwat', 'qu', 'qv', 'e', 'p'] :
			output = open('/media/REMEMBER/merra/'+variable+'/'
					+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		# 3D variables now
		if region == 'Ar' :
			if variable in ['q', 'u', 'v', 'sp', 'thck'] :
				return open('/media/REMEMBER/merra/Ar/'+variable+'/'
						+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
			else :
				return output(lat=(60, 90))
		elif region == 'Aa' :
			if variable in ['q', 'u', 'v', 'sp', 'thck'] :
				return open('/media/REMEMBER/merra/Aa/'+variable+'/'
						+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
			else :
				return output(lat=(-90, -60))
		else :
			if variable in ['q', 'u', 'v', 'thck'] :
				return load(variable, 'merra', year, month, 'Ar')
			else :
				return output

	#########
	# JRA25 #
	#########
	if dataset == 'jra25' :
		if variable in ['q', 'u', 'v', 'T'] :
			if variable == 'T' :
				variable = 't'
			output = open('/home/adufour/jra25/3D/'
					+str(year)+str(month).zfill(2)+'.grb', fileOnly=fileOnly)[variable][:, :12]
		if variable in ['sp', 'qu', 'qv'] :
			output = open('/home/adufour/jra25/2D/'+variable+'/'
					+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if variable == 'thck' :
			output = open('/media/REMEMBER/jra25/thck/'
					+str(year)+str(month).zfill(2)+'.nc', fileOnly=fileOnly)
		if variable in ['pwat', 'e', 'p'] :
			output = open('/home/adufour/jra25/2D/'
					+str(year)+str(month).zfill(2)+'.grb', fileOnly=fileOnly)
			if variable == 'p' :
				output = output['lsp'] + output['acpcp']
			elif variable == 'e' :
				output = output['slhf']
			else :
				output = output[variable]
		if region == 'Ar' :
			return output(lat=(60, 90))
		if region == 'Aa' :
			return output(lat=(-90, -60))
		else :
			return output
