
"""
Initialisation code for package aa
Contains the critical 'open' function
"""

from file import File

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

from load import *

