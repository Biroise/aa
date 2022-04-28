
"""
Initialisation code for package aa
Contains the critical 'open' function
"""

from aa.axis import *
from aa.file import File
from aa.variable import Variable

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
        try :
            import __builtin__
            import cPickle as pickle
        except ModuleNotFoundError :
            import builtins as __builtin__
            import pickle
        inFile = __builtin__.open(filePath, 'rb')
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
            try :
                import __builtin__
                import cPickle as pickle
            except ModuleNotFoundError :
                import builtins as __builtin__
                import pickle
            malossol = __builtin__.open(picklePath, 'rb')
            # kludgy exception for old python2 pickles
            try :
                file_ = pickle.load(malossol)
            except UnicodeDecodeError :
                from aa import grib
                file_ = grib.File(filePath)
        else :
            from aa import grib
            file_ = grib.File(filePath)
    if returnSingleVariable and len(file_.variables) == 1 :
        #print("WARNING : output is the only variable this file contains")
        variable = list(file_.variables.values())[0]
        variable.metadata['shortName'] = list(file_.variables.keys())[0]
        return variable
    else :
        return file_

def dump(array, path) :
    "a wrapper around pickle.dump"
    try :
        import __builtin__
        import cPickle as pickle
    except ModuleNotFoundError :
        import builtins as __builtin__
        import pickle
    with __builtin__.open(path, 'wb') as outFile :
        pickle.dump(array, outFile)
    

def cos(angleInDegrees) :
    return np.cos(angleInDegrees*np.pi/180.0)

def sin(angleInDegrees) :
    return np.sin(angleInDegrees*np.pi/180.0)

try :
    from aa.load import *
except ImportError :
    pass

def mkdir(path) :
    import os
    prefix = ''
    if not path.startswith('/') :
        prefix = '.'
    if path.split('/')[-1] not in os.listdir(prefix + '/' + '/'.join(path.split('/')[:-1])) :
        os.mkdir(path)

monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 
        'SEP', 'OCT', 'NOV', 'DEC']
seasonNames = ['DJF', 'MAM', 'JJA', 'SON']

