
import pygrib
import numpy as np
#import cPickle as pickle
import pickle
from operator import itemgetter
from os.path import splitext
from datetime import datetime
from datetime import timedelta
import aa


class File(aa.File) :
    def __init__(self, filePath) :
        super(File, self).__init__()
        fileName = splitext(filePath)[0]
        rawFile = pygrib.open(filePath)
        # read the first line of the file
        gribLine = rawFile.readline()
        firstInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
                    gribLine.hour, gribLine.minute, gribLine.second)

        ################
        # SURVEY SHAPE #
        ################
        # sometimes there are several types of level
        # 2D data is followed by 3D data e.g. jra25
        variablesLevels = {}                    # variable - level type - level
        variablesEnsembleSize = {}
        variablesMetaData = {}
        # loop through the variables and levels of the first time step
        # default : grib has a time axis
        timeDimension = True
        while datetime(gribLine.year, gribLine.month, gribLine.day,
                    gribLine.hour, gribLine.minute, gribLine.second)\
                    == firstInstant :
            # is it the first time this variable is met ?
            if gribLine.shortName not in variablesLevels :
                # create a dictionary for that variable
                # that will contain different level types
                variablesLevels[gribLine.shortName] = {}
                variablesMetaData[gribLine.shortName] = {}
                variablesMetaData[gribLine.shortName]['shortName'] = gribLine.shortName
                variablesMetaData[gribLine.shortName]['units'] = gribLine.units
                variablesMetaData[gribLine.shortName]['name'] = gribLine.name
            # is this the first time this type of level is met ?
            if gribLine.typeOfLevel not in \
                    variablesLevels[gribLine.shortName] :
                    # create a list that will contain the level labels
                variablesLevels[gribLine.shortName][gribLine.typeOfLevel] = [gribLine.level]
                # set the ensemble member counter to 1
                variablesEnsembleSize[gribLine.shortName] = 1
            # level type already exists :
            else :
                # is this the second time this level label is met ?
                if variablesLevels[gribLine.shortName][gribLine.typeOfLevel][-1] == gribLine.level :
                    # increment one ensemble member
                    variablesEnsembleSize[gribLine.shortName] += 1
                    # assume that it is square : levType*lev*mbr (easy to fix if needed)
                else :
                    # append the level label to the variable / level type
                    variablesLevels[gribLine.shortName][gribLine.typeOfLevel]\
                            .append(gribLine.level)
                    # set the ensemble member counter to 1
                    variablesEnsembleSize[gribLine.shortName] = 1
            # move to the next line
            gribLine = rawFile.readline()
            if gribLine == None :
                timeDimension = False
                break

        if timeDimension :
            #############
            # TIME AXIS #
            #############
            # "seek/tell" index starts with 1
            # but we've moved on the next instant at the end of the while loop
            # hence the minus one
            linesPerInstant = rawFile.tell() - 1
            # determine the interval between two samples
            secondInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
                        gribLine.hour, gribLine.minute, gribLine.second)
            timeStep = secondInstant - firstInstant
            # go to the end of the file
            rawFile.seek(0, 2)
            lastIndex = rawFile.tell()
            # this index points at the last message
            # e.g. f.message(lastIndex) returns the last message
            # indices start at 1 meaning that lastIndex is also the
            # number of messages in the file
            # for consistency checks
            gribLine = rawFile.message(lastIndex)
            lastInstant = datetime(gribLine.year, gribLine.month, gribLine.day,
                        gribLine.hour, gribLine.minute, gribLine.second)
            if timeStep.days >= 28 :
                #if gribLine.stepType == 'avgfc' and firstInstant.month == 12 :
                if firstInstant.month == 12 :
                    #forecasted = firstInstant + aa.timedelta(hours = int(gribLine.stepRange))
                    self.axes['time'] = aa.TimeAxis(
                            np.array([aa.datetime(firstInstant.year + 1 + (1 + timeIndex-1)//12,
                                            (1 + timeIndex-1)%12+1, 1)
                                            - aa.datetime(firstInstant.year + 1, 1, 1)
                                            + aa.datetime(firstInstant.year, firstInstant.month, firstInstant.day, firstInstant.hour)
                                for timeIndex in range(int(lastIndex/linesPerInstant))]), None) 
                else :
                    self.axes['time'] = aa.TimeAxis(
                            np.array([aa.datetime(firstInstant.year + (firstInstant.month + timeIndex-1)//12,
                                    (firstInstant.month + timeIndex-1)%12+1, 1)
                                for timeIndex in range(int(lastIndex/linesPerInstant))]), None) 
                """
                # attempt at reading "regular monthly means" i.e. average of all XX UTC values
                try :
                    forecasted = firstInstant + aa.timedelta(hours = int(gribLine.stepRange))
                    self.axes['time'] = aa.TimeAxis(
                            np.array([aa.datetime(forecasted.year + (forecasted.month + timeIndex-1)//12,
                                    (forecasted.month + timeIndex-1)%12+1, 1) - aa.timedelta(hours = int(gribLine.stepRange))
                                for timeIndex in range(int(lastIndex/linesPerInstant))]), None)
                except (RuntimeError, ValueError) as error :
                    self.axes['time'] = aa.TimeAxis(
                            np.array([aa.datetime(firstInstant.year + (firstInstant.month + timeIndex-1)//12,
                                    (firstInstant.month + timeIndex-1)%12+1, 1, firstInstant.hour)
                                for timeIndex in range(int(lastIndex/linesPerInstant))]), None)
                """
            else :
                self.axes['time'] = aa.TimeAxis(
                        np.array([firstInstant + timeIndex*timeStep
                        for timeIndex in range(int(lastIndex/linesPerInstant))]), None)

                if lastInstant != self.dts[-1] or \
                        lastIndex % linesPerInstant != 0 :
                    print("Error in time axis")
                    raise Exception

        ############
        # VERTICAL #
        ############
        # find the longest vertical axis
        maxLevelNumber = 0
        for variableName, levelKinds in variablesLevels.items() :
            for levelType, levels in levelKinds.items() :
                # does levels look like a proper axis ?
                if len(levels) > 1 :
                    variablesLevels[variableName][levelType] \
                            = aa.Vertical(np.array(levels), levelType)
                # is levels longer than the previous longest axis ?
                if len(levels) > maxLevelNumber :
                    maxLevelNumber = len(levels)
                    mainLevels = aa.Vertical(np.array(levels), levelType)
        # find the longest ensemble
        self.axes['level'] = mainLevels
        # the longest vertical axis gets to be the file's vertical axis

        ############
        # ENSEMBLE #
        ############
        maxEnsembleSize = 1
        for variableName, ensembleSize in variablesEnsembleSize.items() :
            if ensembleSize > maxEnsembleSize :
                maxEnsembleSize = ensembleSize
        if maxEnsembleSize > 1 :
            self.axes['member'] = aa.Axis(np.arange(maxEnsembleSize))

        ###################
        # HORIZONTAL AXES #
        ###################
        rawFile.rewind()
        # maybe it is necessary to rewind after this, methinks not
        gribLine = rawFile.readline()
        # assumes the first grib messages has spatial dimensions
        lats, lons = gribLine.latlons()
        # why the first and not the last ? in case there is no time dimension and gribLine is None
        if lats.shape[1] > 1 :
            if lats[0, 0] == lats[0, 1] :
                self.axes['latitude'] = aa.Meridian(lats[:, 0], 'degrees')
                self.axes['longitude'] = aa.Parallel(lons[0, :], 'degrees')
            else :
                self.axes['latitude'] = aa.Meridian(lats[0, :], 'degrees')
                self.axes['longitude'] = aa.Parallel(lons[:, 0], 'degrees')
        else :
            if lats[0, 0] == lats[1, 0] :
                self.axes['latitude'] = aa.Meridian([lats[0, 0]], 'degrees')
                self.axes['longitude'] = aa.Parallel(lons[:, 0], 'degrees')
            else :
                self.axes['latitude'] = aa.Meridian(lats[:, 0], 'degrees')
                self.axes['longitude'] = aa.Parallel([lons[0, 0]], 'degrees')
            

        #############
        # VARIABLES #
        #############
        self.variables = {}
        for variableName, levelKinds in variablesLevels.items() :
            for levelType, verticalAxis in levelKinds.items() :
                conditions = {'shortName' : variableName,
                        'typeOfLevel' : levelType}
                axes = aa.Axes()
                if timeDimension :
                    axes['time'] = self.axes['time']
                else :
                    conditions['time'] = firstInstant
                # do we need to add a suffix to the variable's name ?
                if len(levelKinds) > 1 :
                    variableLabel = variableName + '_' + levelType
                else : 
                    variableLabel = variableName
                # does this variable have a vertical extension ?
                # it may not be the file's vertical axis
                if len(verticalAxis) > 1 :
                    axes['level'] = verticalAxis
                    # in case of homonyms, only the variable with the main 
                    # vertical axis gets to keep the original shortname
                    if verticalAxis.units == mainLevels.units :
                        variableLabel = variableName
                else :
                    # flat level i.e. 2D data
                    # the condition is a list to be iterable
                    conditions['level'] = verticalAxis
                # is this variable an ensemble ?
                if variablesEnsembleSize[variableName] > 1 :
                    axes['member'] = aa.Axis(np.arange(variablesEnsembleSize[variableName]))
                else :
                    conditions['member'] = [0]
                axes['latitude'] = self.axes['latitude']
                axes['longitude'] = self.axes['longitude']
                self.variables[variableLabel] = \
                        Variable(axes, variablesMetaData[variableName],
                                conditions, fileName)

        ##################
        # PICKLE & INDEX #
        ##################
        rawFile.close()
        pickleFile = open(fileName+'.p', 'wb')
        #import pdb ; pdb.set_trace()
        pickle.dump(self, pickleFile)
        pickleFile.close()
        gribIndex = pygrib.index(filePath,
                        'shortName', 'level', 'typeOfLevel',
                        'year', 'month', 'day', 'hour')
        gribIndex.write(fileName+'.idx')
        gribIndex.close()    


class Variable(aa.Variable) :

    def __init__(self, axes, metadata, conditions,
            fileName, full_axes = None) :
        super(Variable, self).__init__()
        self.axes = axes
        if full_axes == None :
            self.full_axes = axes.copy()
        else :
            self.full_axes = full_axes
        self.metadata = metadata
        self.conditions = conditions
        self.fileName = fileName
    
    @property
    def shape(self) :
        if "_data" not in self.__dict__ :
            dimensions = []
            for axis in list(self.axes.values()) :
                dimensions.append(len(axis))
            return tuple(dimensions)    
        else :
            return super(Variable, self).shape
    
    def __getitem__(self, item) :
        # if the variable is still in pure grib mode
        if "_data" not in self.__dict__ :
            conditions = {}
            # make item iterable, even when it's a singleton
            if not isinstance(item, tuple) :
                if not isinstance(item, list) :
                    if isinstance(item, np.ndarray) :
                        # don't bother if request is an array
                        self._get_data()
                        return super(Variable, self).__getitem__(item)
                    else :
                        item = (item,)
            # loop through axes in their correct order
            # and match axis with a sub-item
            for axisIndex, axisName in enumerate(self.axes) :
                # there may be more axes than sub-items
                # do not overshoot
                if axisIndex < len(item) :
                    # if it's a single index slice
                    if not isinstance(item[axisIndex], slice) :
                        conditions[axisName] = \
                            self.axes[axisName].data[item[axisIndex]]
                    else :
                        # it's a slice
                        # if it's a ':' slice, do nothing
                        if item[axisIndex] != slice(None) :
                            conditions[axisName] = \
                                    (self.axes[axisName][item[axisIndex]].min(),
                                    self.axes[axisName][item[axisIndex]].max())
            return self(**conditions)
        # if _data already exists (as a numpy array), follow standard protocol
        else :
            return super(Variable, self).__getitem__(item)

    def __init__(self, axes, metadata, conditions,
            fileName, full_axes = None) :
        super(Variable, self).__init__()
        self.axes = axes
        if full_axes == None :
            self.full_axes = axes.copy()
        else :
            self.full_axes = full_axes
        self.metadata = metadata
        self.conditions = conditions
        self.fileName = fileName
    
    @property
    def shape(self) :
        if "_data" not in self.__dict__ :
            dimensions = []
            for axis in list(self.axes.values()) :
                dimensions.append(len(axis))
            return tuple(dimensions)    
        else :
            return super(Variable, self).shape
    
    def __getitem__(self, item) :
        # if the variable is still in pure grib mode
        if "_data" not in self.__dict__ :
            conditions = {}
            # make item iterable, even when it's a singleton
            if not isinstance(item, tuple) :
                if not isinstance(item, list) :
                    item = (item,)
            # loop through axes in their correct order
            # and match axis with a sub-item
            for axisIndex, axisName in enumerate(self.axes) :
                # there may be more axes than sub-items
                # do not overshoot
                if axisIndex < len(item) :
                    # if it's a single index slice
                    if not isinstance(item[axisIndex], slice) :
                        conditions[axisName] = \
                            self.axes[axisName].data[item[axisIndex]]
                    else :
                        # it's a slice
                        # if it's a ':' slice, do nothing
                        if item[axisIndex] != slice(None) :
                            conditions[axisName] = \
                                    (self.axes[axisName][item[axisIndex]].min(),
                                    self.axes[axisName][item[axisIndex]].max())
            return self(**conditions)
        # if _data already exists (as a numpy array), follow standard protocol
        else :
            return super(Variable, self).__getitem__(item)

    def extract_data(self, **kwargs) :
        "Extract a subset via its axes"
        # if the variable is still in pure grib mode
        if "_data" not in self.__dict__ :
            # conditions and axes of the output variable
            newConditions = self.conditions.copy()
            newMetadata = self.metadata.copy()
            newAxes = self.axes.copy()
            for axisName, condition in kwargs.items() :
                # lat/lon get a special treatment within grib messages (array)
                if axisName in ['latitude', 'longitude'] :
                    # there may already be restrictions on lat/lon from former calls
                    # refer to the complete axes to define the new slice
                    item, newAxis = self.full_axes[axisName](condition)
                    newConditions[axisName] = item
                # time and level slices need to be made explicit
                else :
                    # given the condition, call axis for a new version
                    item, newAxis = self.axes[axisName](condition)
                    # to what datetimes and pressures
                    # do the conditions correspond ? slice former axis
                    newConditions[axisName] = \
                        self.axes[axisName].data[item]
                    # make sure newConditions is still iterable though
                    if not isinstance(newConditions[axisName], list) :
                        if not isinstance(newConditions[axisName], np.ndarray) :
                            newConditions[axisName] = \
                                [newConditions[axisName]]
                # if item is scalar, there will be no need for an axis
                if newAxis == None :
                    del newAxes[axisName]
                    newMetadata[axisName] = condition
                # otherwise, load newAxis in the new variable's axes
                else :
                    newAxes[axisName] = newAxis
            return Variable(newAxes, newMetadata,
                        newConditions, self.fileName, self.full_axes.copy())
        # if _data already exists (as a numpy array), follow standard protocol
        else :
            return super(Variable, self).extract_data(**kwargs)

    def _get_data(self) :
        if '_data' not in self.__dict__ :
            # dummy conditions to play with
            newConditions = self.conditions.copy()
            # scalar conditions only (input for the gribIndex)
            subConditions = self.conditions.copy()
            #########################
            # TIME & LEVEL & MEMBER #
            #########################
            if 'time' not in self.conditions :
                newConditions['time'] = self.axes['time'].data
            else :
                # gribIndex won't want lists of datetimes
                # but rather individual year/month/day/hour
                del subConditions['time']
                # make sure time condition is iterable
                if not isinstance(newConditions['time'], list) :
                    if not isinstance(newConditions['time'], np.ndarray) :
                        newConditions['time'] = [newConditions['time']]
            # if data is 2D, it will have already have a level condition
            # idem if it's 3D and has already been sliced
            # if not, that means the user wants all available levels
            if 'level' not in self.conditions :
                newConditions['level'] = self.axes['level'].data
            # same reasoning with ensemble members
            if 'member' not in self.conditions :
                newConditions['member'] = self.axes['member'].data
            else :
                # gribIndex won't want lists of ensemble members
                del subConditions['member']
            ########################
            # LATITUDE & LONGITUDE #
            ########################
            ### MASK ###
            # mask is used to slice the netcdf array contained in gribMessages
            mask = []
            if 'latitude' in self.conditions :
                del subConditions['latitude']
                mask.append(self.conditions['latitude'])
            else :
                mask.append(slice(None))
            twistedLongitudes = False
            if 'longitude' in self.conditions :
                del subConditions['longitude']
                # twisted longitudes...
                if type(self.conditions['longitude']) == tuple :
                    twistedLongitudes = True
                    secondMask = mask[:]
                    mask.append(self.conditions['longitude'][0])
                    #slice1 = slice(0, -mask[-1].start)
                    slice1 = slice(0, mask[-1].stop - mask[-1].start)
                    secondMask.append(self.conditions['longitude'][1])
                    slice2 = slice(-secondMask[-1].stop, None)
                else :
                    mask.append(self.conditions['longitude'])
            else :
                mask.append(slice(None))
            mask = tuple(mask)
            ### HORIZONTAL SHAPE ###
            # shape of the output array : (time, level, horizontalShape)
            horizontalShape = []
            #if hasattr(self, 'lats') :
            if 'latitude' in self.axes :
                horizontalShape.append(len(self.lats))
            #if hasattr(self, 'lons') :
            if 'longitude' in self.axes :
                horizontalShape.append(len(self.lons))
            horizontalShape = tuple(horizontalShape)
            #####################
            # GET GRIB MESSAGES #
            #####################
            shape = ()
            for axisName, axis in self.axes.items() :
                shape = shape + (len(axis),)
            # build the output numpy array
            self._data = np.empty(shape, dtype=float)
            # flatten time and level and ensemble dimensions
            # that's in case there's neither of either
            self._data.shape = (-1,) + horizontalShape
            # load the grib index
            gribIndex = pygrib.index(self.fileName+'.idx')
            lineIndex = 0
            for instant in newConditions['time'] :
                subConditions['year'] = instant.year
                subConditions['month'] = instant.month
                subConditions['day'] = instant.day
                subConditions['hour'] = instant.hour
                for level in newConditions['level'] :
                    subConditions['level'] = \
                        np.asscalar(np.array(level))
                        # converts numpy types to standard types
                        # standard types are converted to numpy
                    # normally, there should be as many lines
                    # that answer our query as there are ensemble members
                    gribLines = gribIndex(**subConditions)
                    # catching a bug involving cfsr gribs confusing u & v winds
                    if gribLines[0].shortName != subConditions['shortName'] :
                        gribLines = gribIndex(**subConditions)
                    assert gribLines[0].shortName == subConditions['shortName']
                    for member in newConditions['member'] :
                        if twistedLongitudes :
                            self._data[tuple([lineIndex, Ellipsis, slice1])] = \
                                gribLines[member].values[mask]
                            self._data[tuple([lineIndex, Ellipsis, slice2])] = \
                                gribLines[member].values[tuple(secondMask)]
                        else :
                            self._data[lineIndex] = gribLines[member].values[mask]
                        lineIndex += 1
            gribIndex.close()
            self._data.shape = shape
        return self._data
    def _set_data(self, newValue) :
        self._data = newValue
    data = property(_get_data, _set_data)

