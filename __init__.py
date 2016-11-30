
"""
Initialisation code for package aa
Contains the critical 'open' function
"""

from axis import *
from file import File
from variable import Variable

import numpy as np

# set to False if you do want 'open' to return the file object
# even if it contains only a single variable
returnSingleVariable = True

def open(filePath, mode='r', reopen=False, returnSingleVariable=returnSingleVariable) :
	"Picks the appropriate file_ subclass to model a gridded data file"
	##################
	# MULTIPLE FILES #
	##################
	if isinstance(filePath, list) :
		from aa import multi
		file_ = multi.File(filePath)
	else :
		##########
		# NETCDF #
		##########
		if filePath.endswith('nc') :
			from aa import netcdf
			file_ = netcdf.File(filePath, mode)
		#elif filePath.endswith('grib') or filePath.endswith('grb') \
				#or filePath.endswith('grb2') :
		##########
		# PICKLE #
		##########
		elif filePath.endswith('.p') :
			import __builtin__
			import cPickle as pickle
			inFile = __builtin__.open(filePath)
			output = pickle.load(inFile)
			inFile.close()
			return output
		else :
		########
		# GRIB #
		########
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
	if returnSingleVariable and len(file_.variables) == 1 :
		#print "WARNING : output is the only variable this file contains"
		variable = file_.variables.values()[0]
		variable.metadata['shortName'] = file_.variables.keys()[0]
		return variable
	else :
		return file_

def dump(array, path) :
	"a wrapper around pickle.dump"
	import __builtin__
	import cPickle as pickle
	with __builtin__.open(path, 'w') as outFile :
		pickle.dump(array, outFile)
	

def cos(angleInDegrees) :
	return np.cos(angleInDegrees*np.pi/180.0)

def sin(angleInDegrees) :
	return np.sin(angleInDegrees*np.pi/180.0)

###########################
# ADAPT TO YOUR OWN NEEDS #
#   	                  #
# 	 |	|  	  #
# 	 |	|  	  #
# 	 |	|  	  #
# 	 \      /         #
#   	  \    /          #
#   	   \  /           #
#   	    \/            #
#   	                  #
###########################

reanalyses = ['ncar', 'doe', 'jra25', 'era', 'cfsr', 'merra', 'jra55']

reanalysisNames = {
'ncar':'NCEP NCAR R1', 
'doe':'NCEP DOE R2', 
'jra25':'JRA 25', 
'era':'ERA Interim', 
'cfsr':'NCEP CFSR',
'merra':'MERRA', 
'jra55':'JRA 55',
'igra':'IGRA'}

shortNames = {
'ncar':'NCAR R1', 
'doe':'DOE R2', 
'jra25':'JRA 25', 
'era':'ERA I', 
'cfsr':'CFSR',
'merra':'MERRA', 
'igra':'IGRA', 
'jra55':'JRA 55'}

reanalysisColours = {
'ncar':'#1b9e77',
'doe':'#d95f02',
'jra25':'#7570b3',
'era':'#e7298a',
'cfsr':'#66a61e',
'merra':'#e6ab02',
'jra55':'#a6761d',
'igra':'#000000'}

"""
# ggplot2 style colours
reanalysisColours = {}
from colorsys import hls_to_rgb
for idx, dataset in enumerate(reanalyses) :
	reanalysisColours[dataset] = hls_to_rgb(np.linspace(0, 1, 8)[idx], 0.65, 1)
"""


def load(variable, dataset=None, year=None, month=None, region=None, reopen=False, returnSingleVariable=True) :
	"customizable load function"

	if variable == 'ice' :
		if dataset == None :
			return open('/media/AcuerdaTe/topo/ETOPO1_Ice_g_gmt4.nc')
		else :
			#return open('/home/adufour/topo/' + dataset + '_ice.nc')
			raise Exception
	if variable == 'bed' :
		if dataset == None :
			return open('/home/adufour/topo/ETOPO1_Bed_g_gmt4.nc')
		else :
			return open('/home/adufour/topo/' + dataset + '_bed.nc')

	# composite variables
	if len(variable) == 3 :
		# net precipitation
		if variable == 'p-e' and dataset != 'cfsr' :
			return load('p', dataset, year, month, region, reopen, returnSingleVariable) - \
					load('e', dataset, year, month, region, reopen, returnSingleVariable)
		# stationary flux, qvs
		if variable[0] == 'q' and variable[2] == 's' :
			if dataset == 'merra' :
				qvt = load('q'+variable[1]+'t', dataset, year, month, region, reopen, returnSingleVariable)
				qv = load('q'+variable[1]+'_manual', dataset, year, month, region, reopen, returnSingleVariable)(lat = (
						qvt.lats.min(), qvt.lats.max()))
			else :
				qvt = load('q'+variable[1]+'t', dataset, year, month, region, reopen, returnSingleVariable)
				qv = load('q'+variable[1], dataset, year, month, region, reopen, returnSingleVariable)(lat = (
						qvt.lats.min(), qvt.lats.max()))
			return qv - qvt
		# stationary flux, QVS
		if variable[0] == 'Q' and variable[2] == 'S' :
			return load('Q'+variable[1], dataset, year, month, region, reopen, returnSingleVariable) - \
					load('Q'+variable[1]+'T', dataset, year, month, region, reopen, returnSingleVariable)

	###############
	# CLIMATOLOGY #
	###############
	if year == None and month == None :
		# covariances were only computed for the polar regions
		if region == 'Aa' and \
				dataset in ['merra', 'era', 'cfsr', 'jra55'] and \
				variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
			return open('/media/AcuerdaTe/climatology/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		# CFSR fluxes are only available for the polar regions
		if region == 'Aa' and \
				dataset == 'cfsr' and \
				variable in ['cu', 'cv', 'qu', 'qv'] :
			return open('/media/AcuerdaTe/climatology/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		if region == 'Aa' and \
				dataset in ['cfsr', 'jra55', 'merra'] and \
				variable in ['q', 'u', 'v'] :
			return open('/media/AcuerdaTe/climatology/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		return open('/media/AcuerdaTe/climatology/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

	################
	# YEARLY MEANS #
	################
	if year == 'yearly' and month == None :
		# covariances were only computed for the polar regions
		if region == 'Aa' and \
				dataset in ['merra', 'era', 'cfsr', 'jra55'] and \
				variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
			return open('/media/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		# CFSR fluxes are only available for the polar regions
		if region == 'Aa' and \
				dataset == 'cfsr' and \
				variable in ['qu', 'qv'] :
			return open('/media/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		if region == 'Aa' and \
				dataset in ['cfsr', 'jra55', 'merra'] and \
				variable in ['q', 'u', 'v'] :
			return open('/media/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
		return open('/media/AcuerdaTe/yearly/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

	#################
	# MONTHLY MEANS #
	#################
	if year == 'monthly' and month == None :
		if region == 'Aa' and \
				dataset in ['merra', 'era', 'cfsr', 'jra55'] and \
				variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
			return open('/media/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
		if region == 'Aa' and \
				dataset == 'cfsr' and \
				variable in ['qu', 'qv', 'cu', 'cv'] :
			return open('/media/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
		if region == 'Aa' and \
				dataset in ['cfsr', 'jra55', 'merra'] and \
				variable in ['q', 'u', 'v'] :
			return open('/media/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
		return open('/media/AcuerdaTe/monthly/'+dataset+'/'+variable+'.nc', returnSingleVariable=returnSingleVariable)

	###################
	# MOISTURE FLUXES #
	###################
	if variable in ['QU', 'QV'] :
		variable = variable.lower()
		return load(variable[0], dataset, year, month, region, reopen, returnSingleVariable)* \
				load(variable[1], dataset, year, month, region, reopen, returnSingleVariable)
	if variable in ['QUT', 'QVT'] :
		variable = variable.lower()
		q = load(variable[0], dataset, year, month, region, reopen, returnSingleVariable)
		wind = load(variable[1], dataset, year, month, region, reopen, returnSingleVariable)
		return (q-q.mean('t'))*(wind-wind.mean('t'))

	################
	# FULL DATASET #
	################
	if month == 'all' :
		return open([load(variable, dataset, year, month, returnSingleVariable=True)
				for month in range(1, 13)])

	######################################
	# STRICT EVAPORATION AND SUBLIMATION #
	######################################
	if variable in ['eMinus', 'ePlus'] :
		output = open('/media/Remember/e/' + variable + '/' + dataset + '/' +
			str(year) + str(month).zfill(2) + '.nc')
		return output

	#######
	# ERA #
	#######
	if dataset == 'era' :
		if variable in ['q', 'u', 'v', 'w', 'T', 'gph'] :
			output = open('/media/dufour/Pomnitie/era/3D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
			# open will return the variable since the file is otherwise empty
			#output.levs /= 100
			#output.lev.units = 'hPa'
		variables2D = ['omega', 'eu', 'ev', 'mu', 'mv', 'mslp', 'lDiv', 'sDiv', 'mDiv', 'su', 'lu', 'sv', 'lv', 'sp', 'div', 'qu', 'qv', 'tcw', 'pwat']
		for prefix in ['tcw', 'e', 'p', 'pwat'] :
			for step in ['03', '06', '09', '12', '15', '18', '21', '24', '30', '36', '42', '48'] :
				variables2D.append(prefix+step)
		if variable in variables2D :
			output =  open('/media/dufour/Pomnitie/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
		if variable in ['p', 'e'] :
			output =  open('/media/dufour/Pomnitie/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
		if variable == 'thck' :
			if region == 'Ar' :
				return open('/media/dufour/Pomnitie/era/3D/thck_Ar/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
			elif region == 'Aa' :
				return open('/media/dufour/Pomnitie/era/3D/thck_Aa/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
			else : 
				raise Exception
		return output

	########
	# NCAR #
	########
	if dataset == 'ncar' :
		if variable in ['u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
			output = open('/media/dufour/SouviensToi/ncar/3D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)[:, :8]
			if variable == 'omega' :
				output = output[:, 7]
		if variable in ['skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv', 'slp'] :
			output = open('/media/dufour/SouviensToi/ncar/2D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
		if output.dts[0].day != 1 :
			from datetime import timedelta
			output.dts -= timedelta(days = output.dts[0].day - 1)
		return output

	#######
	# DOE #
	#######
	if dataset == 'doe' :
		if variable in ['u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
			output = open('/media/dufour/SouviensToi/doe/3D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
			if variable == 'omega' :
				output = output[:, -1]
		if variable in ['skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv'] :
			output = open('/media/dufour/SouviensToi/doe/2D/'
					+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
		if variable == 'p' :
			output = output['prate']
		return output


	#########
	# MERRA #
	#########
	if dataset == 'merra' :
		# 2D variables first
		if variable in ['omega', 'pwat', 'lu', 'lv', 'su', 'sv', 'qu', 'qv', 'e', 'p', 'sp'] :
			output = open('/media/Remember/merra/'+variable+'/'
					+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
			return output
		# 3D variables now
		if region == 'Aa' :
			if variable in ['q', 'u', 'v'] :
				output = open('/media/Remember/merra/Aa/'+variable+'/'
						+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
				output.data = output.data.filled(np.nan)
		else :
			if variable in ['q', 'u', 'v'] :
				output =  open('/media/Remember/merra/Ar/'+variable+'/'
						+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
				output.data = output.data.filled(np.nan)
		return output

	##########
	# JRA 25 #
	##########
	if dataset == 'jra25' :
		if variable in ['q', 'u', 'v', 'T'] :
			if variable == 'T' :
				variable = 't'
			output = open('/media/Remember/jra25/3D/'
					+str(year)+str(month).zfill(2)+'.grb', returnSingleVariable=returnSingleVariable)[variable][:, :12]
		if variable in ['pwat', 'sp', 'e', 'qu', 'qv', 'cu', 'cv'] :
			output = open('/media/Remember/jra25/2D/'+variable+'/'
					+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
		#if variable in ['pwat', 'p'] :
		if variable in ['p'] :
			output = open('/media/Remember/jra25/2D/'
					+str(year)+str(month).zfill(2)+'.grb', returnSingleVariable=returnSingleVariable)
			if variable == 'p' :
				output = output['lsp'] + output['acpcp']
			else :
				output = output[variable]
		return output
	
	#######
	# ASR #
	#######
	if dataset == 'asr' :
		if variable in ['q', 'u', 'v', 'sp', 'thck'] :
			output =  open('/home/adufour/asr/' + variable + 
					'/' + str(year) + str(month).zfill(2) + '.nc')
			if 'level' in output.axes :
				output.axes['level'] = Vertical(output.levs/100, 'hPa')
			return output
	
	########
	# CFSR #
	########
	if dataset == 'cfsr' :
		if variable == 'e' :
			output = open('/media/Remember/cfsr/e/'
					+str(year)+str(month).zfill(2)+'.nc')
		if variable == 'sp' :
			output = open('/media/Remember/cfsr/sp/'
						+str(year)+str(month).zfill(2)+'.nc')
		return output
	
	##########
	# JRA 55 #
	##########
	if dataset == 'jra55' :
		from datetime import datetime
		start = datetime(year, month, 1)
		stop = datetime(year + (month+1)/13, month%12 +1, 1)
		if variable in ['qv', 'qu', 'e', 'sp'] :
				return open('/media/Remember/jra55/'+variable
						+'/'+str(year)+'.grb')(time=(start, stop, 'co'))

	raise Exception


