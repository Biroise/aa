
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

def yr(year) :
    return datetime(year, 1, 1)

###########################
# ADAPT TO YOUR OWN NEEDS #
#                         #
#      |    |        #
#      |    |        #
#      |    |        #
#      \      /         #
#         \    /          #
#          \  /           #
#           \/            #
#                         #
###########################

reanalyses = ['ncar', 'doe', 'jra25', 'era', 'cfsr', 'merra', 'merra2', 'jra55']

reanalysisNames = {
'ncar':'NCEP NCAR R1', 
'doe':'NCEP DOE R2', 
'jra25':'JRA 25', 
'era':'ERA Interim', 
'cfsr':'NCEP CFSR',
'merra':'MERRA 1', 
'merra2':'MERRA 2', 
'jra55':'JRA 55',
'series':'IGRA',
'igra':'IGRA'}

shortNames = {
'ncar':'NCAR R1', 
'doe':'DOE R2', 
'jra25':'JRA 25', 
'era':'ERA I', 
'cfsr':'CFSR',
'merra':'MERRA 1', 
'merra2':'MERRA 2', 
'igra':'IGRA', 
'jra55':'JRA 55'}

reanalysisColours = {
'doe':'#1f78b4',
'era':'#33a02c',
'cfsr':'#e31a1c',
'jra55':'#ff7f00',
'series':'#000000',
'merra2':'#6a3d9a'}

experiments = ['bold_control', 'bold_scenario', 'boldT63_scenario', 'conundrum',
        'core_control', 'core_scenario', 'coreT127_scenario']

"""
reanalysisColours = {
'doe':'#1b9e77',
'era':'#d95f02',
'cfsr':'#7570b3',
'jra55':'#e7298a',
'series':'#000000',
'merra2':'#66a61e'}
"""

"""
reanalysisColours = {
'ncar':'#1b9e77',
'doe':'#d95f02',
'jra25':'#7570b3',
'era':'#e7298a',
'cfsr':'#66a61e',
'merra':'#e6ab02',
'jra55':'#a6761d',
'merra2':'#000000',
'igra':'#000000'}
"""

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
            return open('/home/dufour/AcuerdaTe/topo/ETOPO1_Ice_g_gmt4.nc')
        else :
            #return open('/home/dufour/topo/' + dataset + '_ice.nc')
            raise Exception
    if variable == 'bed' :
        if dataset == None :
            return open('/home/dufour/topo/ETOPO1_Bed_g_gmt4.nc')
        else :
            return open('/home/dufour/topo/' + dataset + '_bed.nc')

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
    if (year == '8016' or year == 8016
            or year == '7917' or year == 7917
            or year == '7913' or year == 7913
            ) and month == None :
        year = str(year)
        # covariances were only computed for the polar regions
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/home/dufour/AcuerdaTe/clim_' + year + '/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        # CFSR fluxes are only available for the polar regions
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['cu', 'cv', 'qu', 'qv'] :
            return open('/home/dufour/AcuerdaTe/clim_' + year + '/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/home/dufour/AcuerdaTe/clim_' + year + '/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/home/dufour/AcuerdaTe/clim_' + year + '/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

    ################
    # YEARLY MEANS #
    ################
    if year == 'yearly' and month == None :
        # covariances were only computed for the polar regions
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/home/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        # CFSR fluxes are only available for the polar regions
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['qu', 'qv'] :
            return open('/home/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/home/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/home/dufour/AcuerdaTe/yearly/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

    #################
    # MONTHLY MEANS #
    #################
    if year == 'monthly' and month == None :
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/home/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['qu', 'qv', 'cu', 'cv'] :
            return open('/home/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/home/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/home/dufour/AcuerdaTe/monthly/'+dataset+'/'+variable+'.nc', returnSingleVariable=returnSingleVariable)

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
        output = open('/home/dufour/Remember/e/' + variable + '/' + dataset + '/' +
            str(year) + str(month).zfill(2) + '.nc')
        return output

    # useful for calls from sys.argv
    year = int(year)
    month = int(month)

    #######
    # ERA #
    #######
    if dataset == 'era' :
        if variable in ['q', 'u', 'v', 'w', 'T', 'gph'] :
            output = open('/home/dufour/Pomnitie/era/3D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
            # open will return the variable since the file is otherwise empty
            #output.levs /= 100
            #output.lev.units = 'hPa'
        variables2D = ['icec', 'eu', 'ev', 'mu', 'mv', 'slp', 'lDiv', 'sDiv', 'mDiv', 'su', 'lu', 'sv', 'lv', 'sp', 'div', 'qu', 'qv', 'tcw', 'pwat', 'T2m', 'skiT', 'pT2PVU', 'gphu', 'gphv', 'Tu', 'Tv', 'ec_u', 'ec_v']
        for prefix in ['tcw', 'e', 'p', 'pwat', 'dwn_lw', 'dwn_sw'] :
            for step in ['03', '06', '09', '12', '15', '18', '21', '24', '30', '36', '42', '48'] :
                variables2D.append(prefix+step)
        if variable in variables2D :
            output =  open('/home/dufour/SouviensToi/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
        if variable in ['p', 'e', 'sf', 'sh', 'cape', 'gph_500', 'gph_700'] :
            output =  open('/home/dufour/SouviensToi/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' :
            output = output(lat = (-90, -60))
        if region == 'Ar' :
            output = output(lat = (60, 90))
        if variable.startswith('gph') or variable.startswith('GPH') :
            output /= 9.80665
        return output

    ########
    # NCAR #
    ########
    if dataset == 'ncar' :
        ##### PROVISIONAL ######
        if variable == 'T12' :
            output = open('/media/dufour/SouviensToi1/ncar_fc_nc/T12/'
                    + str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)#[:, :8]
        if variable == 'T_absIncr' :
            output = load('T', 'ncar', year, month) - load('T12', 'ncar', year, month)
            output.data = abs(output.data)
        ########################
        if variable in ['gph', 'u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
            output = open('/home/dufour/SouviensToi/ncar/3D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)#[:, :8]
            #if variable == 'omega' :
                #output = output[:, 7]
        if variable in ['icec', 'Tsig995', 'skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv', 'slp'] :
            output = open('/home/dufour/SouviensToi/ncar/2D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        if output.dts[0].day != 1 :
            from datetime import timedelta
            output.dts -= timedelta(days = output.dts[0].day - 1)
        return output

    #######
    # DOE #
    #######
    if dataset == 'doe' :
        if variable in ['gph', 'u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
            output = open('/home/dufour/SouviensToi/doe/3D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            #if variable == 'omega' :
                #output = output[:, -1]
        if variable in ['slp', 'skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv'] :
            output = open('/home/dufour/SouviensToi/doe/2D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        if variable == 'p' :
            output = output['prate']
        if region == 'Aa' :
            output = output(lat = (-90, -60))
        if region == 'Ar' :
            output = output(lat = (60, 90))
        return output


    #########
    # MERRA #
    #########
    if dataset == 'merra' :
        # 2D variables first
        if variable in ['omega', 'pwat', 'lu', 'lv', 'su', 'sv', 'qu', 'qv', 'e', 'p', 'sp'] :
            output = open('/home/dufour/Remember/merra/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            return output
        # 3D variables now
        if variable in ['q', 'u', 'v'] :
            alias = {'q':'QV', 'u':'U', 'v':'V'}[variable]
            if region == 'Aa' :
                if year in [2014, 2015] :
                    output = open('/home/dufour/Remember/merra/Aa/1415/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                    output = output.variables[alias]
                else :
                    output = open('/home/dufour/Remember/merra/Aa/'+variable+'/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                output.data = output.data.filled(np.nan)
            else :
                if year in [2014, 2015] :
                    output = open('/home/dufour/Remember/merra/Ar/1415/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                    output = output.variables[alias]
                else :
                    output = open('/home/dufour/Remember/merra/Ar/'+variable+'/'
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
            output = open('/home/dufour/Remember/jra25/3D/'
                    +str(year)+str(month).zfill(2)+'.grb', returnSingleVariable=returnSingleVariable)[variable][:, :12]
        if variable in ['pwat', 'sp', 'e', 'qu', 'qv', 'cu', 'cv'] :
            output = open('/home/dufour/Remember/jra25/2D/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        #if variable in ['pwat', 'p'] :
        if variable in ['p'] :
            output = open('/home/dufour/Remember/jra25/2D/'
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
            output =  open('/home/dufour/asr/' + variable + 
                    '/' + str(year) + str(month).zfill(2) + '.nc')
            if 'level' in output.axes :
                output.axes['level'] = Vertical(output.levs/100, 'hPa')
            return output
    
    ########
    # CFSR #
    ########
    if dataset == 'cfsr' :
        if variable == 'sp' :
            if year in [2011, 2012, 2013] :
                ending = 'nc'
            else :
                ending = 'grb'
            output = open('/home/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2) + '.' + ending)
        if variable in ['pwat', 'p', 'T_0.995', 'skiT', 'snowCover'] :
            output = open('/home/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.grb')
        if variable in ['e'] :
            output = open('/home/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
        if variable in ['qu', 'qv'] :
            if region == 'Aa' :
                output = open('/home/dufour/SouviensToi/cfsr/Aa/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
            else :
                output = open('/home/dufour/SouviensToi/cfsr/NH/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
        if variable in ['q', 'u', 'v', 'T', 'gph'] :
            if region == 'Aa' :
                output = open('/home/dufour/SouviensToi/cfsr/'
                        + region + '/' + variable + '/'
                        + str(year)+str(month).zfill(2)+'.grb')
            else :
                output = open('/home/dufour/SouviensToi/cfsr/Ar/' + variable + '/'
                            +str(year)+str(month).zfill(2)+'.grb')
        return output
    
    ##########
    # JRA 55 #
    ##########
    if dataset == 'jra55' :
        from datetime import datetime
        if variable in ['p', 'e'] :
            return open('/home/dufour/SouviensToi/jra55/'+variable
                    +'/'+str(year)+str(month).zfill(2)+'.nc')
        elif variable in ['T2m'] :
            return open('/home/SouviensToi/jra55/'+variable
                    +'/'+str(year)+str(month).zfill(2)+'.grb')
        elif year in [2014, 2015, 2016, 2017] :
            if variable == 'qv' and year in [2014, 2015]     :
                ending = 'nc'
            else :
                ending = 'grb'
            output = open('/home/dufour/SouviensToi/jra55/' + variable
                    + '/' + str(year) + str(month).zfill(2) + '.' + ending
                    )
            if variable == 'qv' and year in [2014, 2015] :
                output = output.variables['VWV_GDS4_EATM']
            return output
  
        else :
            start = datetime(year, month, 1)
            stop = datetime(year + (month+1)/13, month%12 +1, 1)
            #if variable in ['qv', 'qu', 'e', 'sp'] :
            return open('/home/dufour/SouviensToi/jra55/'+variable
                            +'/'+str(year)+'.grb')(time=(start, stop, 'co'))

    ###########
    # MERRA 2 #
    ###########
    if dataset == 'merra2' :
        # 2D variables first
        if variable in ['prectotcorr', 'omega', 'pwat', 'lu', 'lv', 'su', 'sv', 'qu', 'qv', 'e', 'p', 'sp', 'enthalpy_u', 'enthalpy_v', 'pe_u', 'pe_v', 'T2m'] :
            output = open('/home/dufour/SouviensToi/merra2/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            return output
        # 3D variables now
        variableName = {'q':'QV', 'u':'U', 'v':'V'}
        if region == 'Aa' :
            if variable in ['q', 'u', 'v'] :
                output = open('/home/dufour/Remember/merra2/Aa/'
                        +str(year)+str(month).zfill(2)+'.nc').variables[variableName[variable]]
                output.data = output.data.filled(np.nan)
        else :
            if variable in ['q', 'u', 'v'] :
                output =  open('/home/dufour/Remember/merra2/Ar/'
                        +str(year)+str(month).zfill(2)+'.nc').variables[variableName[variable]]
                output.data = output.data.filled(np.nan)
            else :
                output =  open('/home/dufour/SouviensToi/merra2/Ar/' + variable + 
                        '/' + str(year)+str(month).zfill(2)+'.nc')
        return output

    raise Exception

    "customizable load function"

    if variable == 'ice' :
        if dataset == None :
            return open('/media/dufour/AcuerdaTe/topo/ETOPO1_Ice_g_gmt4.nc')
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
    if (year == '8016' or year == 8016) and month == None :
        # covariances were only computed for the polar regions
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/media/dufour/AcuerdaTe/clim_8016/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        # CFSR fluxes are only available for the polar regions
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['cu', 'cv', 'qu', 'qv'] :
            return open('/media/dufour/AcuerdaTe/clim_8016/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/media/dufour/AcuerdaTe/clim_8016/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/media/dufour/AcuerdaTe/clim_8016/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

    ###############
    # CLIMATOLOGY #
    ###############
    if (year == '7913' or year == 7913) and month == None :
        # covariances were only computed for the polar regions
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/media/dufour/AcuerdaTe/clim_7913/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        # CFSR fluxes are only available for the polar regions
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['cu', 'cv', 'qu', 'qv'] :
            return open('/media/dufour/AcuerdaTe/clim_7913/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/media/dufour/AcuerdaTe/clim_7913/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/media/dufour/AcuerdaTe/clim_7913/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

    ################
    # YEARLY MEANS #
    ################
    if year == 'yearly' and month == None :
        # covariances were only computed for the polar regions
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/media/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        # CFSR fluxes are only available for the polar regions
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['qu', 'qv'] :
            return open('/media/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/media/dufour/AcuerdaTe/yearly/Aa/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/media/dufour/AcuerdaTe/yearly/'+variable+'_'+dataset+'.nc', returnSingleVariable=returnSingleVariable)

    #################
    # MONTHLY MEANS #
    #################
    if year == 'monthly' and month == None :
        if region == 'Aa' and \
                dataset in ['merra', 'era', 'cfsr', 'jra55', 'merra2'] and \
                variable in ['qu_pl', 'qv_pl', 'qut', 'qvt', 'QU', 'QV', 'QUT', 'QVT'] :
            return open('/media/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset == 'cfsr' and \
                variable in ['qu', 'qv', 'cu', 'cv'] :
            return open('/media/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' and \
                dataset in ['cfsr', 'jra55', 'merra', 'merra2'] and \
                variable in ['q', 'u', 'v'] :
            return open('/media/dufour/AcuerdaTe/monthly/'+dataset+'/Aa/'+variable+'.nc', returnSingleVariable=returnSingleVariable)
        return open('/media/dufour/AcuerdaTe/monthly/'+dataset+'/'+variable+'.nc', returnSingleVariable=returnSingleVariable)

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
        output = open('/media/dufour/Remember/e/' + variable + '/' + dataset + '/' +
            str(year) + str(month).zfill(2) + '.nc')
        return output

    # useful for calls from sys.argv
    year = int(year)
    month = int(month)

    #######
    # ERA #
    #######
    if dataset == 'era' :
        if variable in ['q', 'u', 'v', 'w', 'T', 'gph'] :
            output = open('/media/dufour/Pomnitie/era/3D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
            # open will return the variable since the file is otherwise empty
            #output.levs /= 100
            #output.lev.units = 'hPa'
        variables2D = ['icec', 'eu', 'ev', 'mu', 'mv', 'slp', 'lDiv', 'sDiv', 'mDiv', 'su', 'lu', 'sv', 'lv', 'sp', 'div', 'qu', 'qv', 'tcw', 'pwat', 'T2m', 'skiT', 'pT2PVU', 'gphu', 'gphv', 'Tu', 'Tv', 'ec_u', 'ec_v']
        for prefix in ['tcw', 'e', 'p', 'pwat'] :
            for step in ['03', '06', '09', '12', '15', '18', '21', '24', '30', '36', '42', '48'] :
                variables2D.append(prefix+step)
        if variable in variables2D :
            output =  open('/media/dufour/AcuerdaTe/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.grb', reopen=reopen, returnSingleVariable=returnSingleVariable)
        if variable in ['p', 'e', 'sf', 'cape', 'gph_500', 'gph_700'] :
            output =  open('/media/dufour/AcuerdaTe/era/2D/'+variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        if region == 'Aa' :
            output = output(lat = (-90, -60))
        if region == 'Ar' :
            output = output(lat = (60, 90))
        return output

    ########
    # NCAR #
    ########
    if dataset == 'ncar' :
        if variable in ['gph', 'u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
            output = open('/media/dufour/SouviensToi/ncar/3D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)#[:, :8]
            #if variable == 'omega' :
                #output = output[:, 7]
        if variable in ['icec', 'Tsig995', 'skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv', 'slp'] :
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
        if variable in ['gph', 'u', 'v', 'q', 'T', 'rh', 'thck', 'omega'] :
            output = open('/media/dufour/SouviensToi/doe/3D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            #if variable == 'omega' :
                #output = output[:, -1]
        if variable in ['slp', 'skiT', 'lh', 'e', 'p', 'sp', 'pwat', 'qu', 'qv'] :
            output = open('/media/dufour/SouviensToi/doe/2D/'
                    +variable+'/'+str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        if variable == 'p' :
            output = output['prate']
        if region == 'Aa' :
            output = output(lat = (-90, -60))
        if region == 'Ar' :
            output = output(lat = (60, 90))
        return output


    #########
    # MERRA #
    #########
    if dataset == 'merra' :
        # 2D variables first
        if variable in ['omega', 'pwat', 'lu', 'lv', 'su', 'sv', 'qu', 'qv', 'e', 'p', 'sp'] :
            output = open('/media/dufour/Remember/merra/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            return output
        # 3D variables now
        if variable in ['q', 'u', 'v'] :
            alias = {'q':'QV', 'u':'U', 'v':'V'}[variable]
            if region == 'Aa' :
                if year in [2014, 2015] :
                    output = open('/media/dufour/Remember/merra/Aa/1415/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                    output = output.variables[alias]
                else :
                    output = open('/media/dufour/Remember/merra/Aa/'+variable+'/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                output.data = output.data.filled(np.nan)
            else :
                if year in [2014, 2015] :
                    output = open('/media/dufour/Remember/merra/Ar/1415/'
                            +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
                    output = output.variables[alias]
                else :
                    output = open('/media/dufour/Remember/merra/Ar/'+variable+'/'
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
            output = open('/media/dufour/Remember/jra25/3D/'
                    +str(year)+str(month).zfill(2)+'.grb', returnSingleVariable=returnSingleVariable)[variable][:, :12]
        if variable in ['pwat', 'sp', 'e', 'qu', 'qv', 'cu', 'cv'] :
            output = open('/media/dufour/Remember/jra25/2D/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
        #if variable in ['pwat', 'p'] :
        if variable in ['p'] :
            output = open('/media/dufour/Remember/jra25/2D/'
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
        if variable == 'sp' :
            if year in [2011, 2012, 2013] :
                ending = 'nc'
            else :
                ending = 'grb'
            output = open('/media/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2) + '.' + ending)
        if variable in ['pwat', 'p'] :
            output = open('/media/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.grb')
        if variable in ['e'] :
            output = open('/media/dufour/SouviensToi/cfsr/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
        if variable in ['qu', 'qv'] :
            if region == 'Aa' :
                output = open('/media/dufour/SouviensToi/cfsr/Aa/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
            else :
                output = open('/media/dufour/SouviensToi/cfsr/NH/' + variable + '/'
                        +str(year)+str(month).zfill(2)+'.nc')
        if variable in ['q', 'u', 'v', 'T', 'gph'] :
            if region == 'Aa' :
                output = open('/media/dufour/SouviensToi/cfsr/'
                        + region + '/' + variable + '/'
                        + str(year)+str(month).zfill(2)+'.grb')
            else :
                output = open('/media/dufour/SouviensToi/cfsr/Ar/' + variable + '/'
                            +str(year)+str(month).zfill(2)+'.grb')
        return output
    
    ##########
    # JRA 55 #
    ##########
    if dataset == 'jra55' :
        from datetime import datetime
        if variable in ['p', 'e'] :
            return open('/media/dufour/SouviensToi/jra55/'+variable
                    +'/'+str(year)+str(month).zfill(2)+'.nc')
        elif year in [2014, 2015, 2016] :
            if variable == 'qv' and year in [2014, 2015]     :
                ending = 'nc'
            else :
                ending = 'grb'
            output = open('/media/dufour/SouviensToi/jra55/'+variable
                    +'/'+str(year)+str(month).zfill(2) + '.' + ending
                    )
            if variable == 'qv' and year in [2014, 2015] :
                output = output.variables['VWV_GDS4_EATM']
            return output
  
        else :
            start = datetime(year, month, 1)
            stop = datetime(year + (month+1)/13, month%12 +1, 1)
            #if variable in ['qv', 'qu', 'e', 'sp'] :
            return open('/media/dufour/SouviensToi/jra55/'+variable
                            +'/'+str(year)+'.grb')(time=(start, stop, 'co'))

    ###########
    # MERRA 2 #
    ###########
    if dataset == 'merra2' :
        # 2D variables first
        if variable in ['prectotcorr', 'omega', 'pwat', 'lu', 'lv', 'su', 'sv', 'qu', 'qv', 'e', 'p', 'sp', 'enthalpy_u', 'enthalpy_v', 'pe_u', 'pe_v'] :
            output = open('/home/dufour/SouviensToi/merra2/'+variable+'/'
                    +str(year)+str(month).zfill(2)+'.nc', returnSingleVariable=returnSingleVariable)
            return output
        # 3D variables now
        variableName = {'q':'QV', 'u':'U', 'v':'V'}
        if region == 'Aa' :
            if variable in ['q', 'u', 'v'] :
                output = open('/media/dufour/Remember/merra2/Aa/'
                        +str(year)+str(month).zfill(2)+'.nc').variables[variableName[variable]]
                output.data = output.data.filled(np.nan)
        else :
            if variable in ['q', 'u', 'v'] :
                output =  open('/media/dufour/Remember/merra2/Ar/'
                        +str(year)+str(month).zfill(2)+'.nc').variables[variableName[variable]]
                output.data = output.data.filled(np.nan)
            else :
                output =  open('/media/dufour/SouviensToi/merra2/Ar/' + variable + 
                        '/' + str(year)+str(month).zfill(2)+'.nc')
        return output

    raise Exception

