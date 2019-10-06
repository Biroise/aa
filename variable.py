
import numpy as np
import graphics
from axis import Axes
from collections import OrderedDict
import statistics


class Variable(object) :
    def __init__(self, data=None, axes=Axes(), metadata={}) :
        self.axes = axes
        self.metadata = metadata
        if type(data) != type(None) :
            self._data = data

    def _get_data(self) :
        return self._data
    def _set_data(self, newValue) :
        self._data = newValue
    data = property(_get_data, _set_data)

    def __getitem__(self, item) :
        # make item iterable, even when it's a singleton
        if not isinstance(item, tuple) :
            if not isinstance(item, list) :
                item = (item,)
        newData = self.data[item].copy()
        newAxes = self.axes.copy()
        newMetadata = self.metadata.copy()
        # loop through axes in their correct order
        # and match axis with a sub-item
        for axisIndex, axis in enumerate(self.axes) :
            # there may be more axes than sub-items
            # do not overshoot
            if axisIndex < len(item) :
                newAxis = self.axes[axis][item[axisIndex]]
                if newAxis != None :
                    newAxes[axis] = newAxis
                else :
                    del newAxes[axis]
                    newMetadata[axis] = self.axes[axis].data[item[axisIndex]]
        return Variable(
                data = newData,
                axes = newAxes,
                metadata = newMetadata)

    @property
    def shape(self) :
        return self.data.shape

    def __call__(self, **kwargs) :
        # input : {axisName: condition, ...}
        # standardize the axisNames
        for axisName, condition in kwargs.iteritems() :
            del kwargs[axisName]
            if type(condition) == tuple :
                condition = tuple(sorted(condition[:2]))+condition[2:]
            kwargs[Axes.standardize(axisName)] = condition
        output = self.extract_data(**kwargs)
        # do we need to interpolate along an axis ?
        for axisName, condition in kwargs.iteritems() :
            # did we ask for a single value for an axis
            # yet still have this axis in the output variable ?
            # this means extract_data returned the neighbouring points
            # because this single value is not on the grid
            if type(condition) != tuple and axisName in output.axes :
                output.data # kludge for grib files
                firstSlice = [slice(None)]*len(output.shape)
                secondSlice = [slice(None)]*len(output.shape)
                firstSlice[output.axes.index(axisName)] = 0
                secondSlice[output.axes.index(axisName)] = 1
                # linear interpolation !
                try :
                    output = \
                        (output[secondSlice] - output[firstSlice])/\
                                (output.axes[axisName].data[1] - \
                                        output.axes[axisName].data[0])\
                            *(condition - output.axes[axisName].data[0]) \
                        + output[firstSlice]
                except IndexError :
                    # sometimes, due to rounding errors, extract_data will return one
                    # value when two were expected, thus output...[1] fails
                    output = output[firstSlice]
                output.metadata[axisName] = condition
        return output

    def extract_data(self, **kwargs) :
        # prepare to slice the data array
        slices = OrderedDict()
        for axisName in self.axes :
            # default behaviour : leave this dimension intact
            slices[axisName] = slice(None)
        # the new variable's axes and metadata
        newAxes = self.axes.copy()
        newMetadata = self.metadata.copy()
        # dispatch the conditions to the axes
        for axisName, condition in kwargs.iteritems() :
            item, newAxis = self.axes[axisName](condition)
            # replace the default slice(None) by the item returned by the axis
            slices[axisName] = item
            # if it's a single item, not a slice, get rid of the axis
            if newAxis == None :
                del newAxes[axisName]
                newMetadata[axisName] = condition
            else :
                newAxes[axisName] = newAxis
        # twisted longitudes...
        if 'longitude' in kwargs :
            # Parallel objects return a tuple of two slices when they're asked
            # for longitudes that span across the Greenwich meridian or
            # the date line : slices from either end of the array
            if type(slices['longitude']) == tuple :
                secondSlices = slices.copy()
                secondSlices['longitude'] = slices['longitude'][1]
                slices['longitude'] = slices['longitude'][0]
                longitudeIndex = newAxes.index('longitude')
                # longitude is assumed to be the last axis
                return Variable(
                        data = np.concatenate((
                            self.data[tuple(slices.values())],
                            self.data[tuple(secondSlices.values())]),
                            axis=longitudeIndex),
                        axes = newAxes,
                        metadata = newMetadata)
        return Variable(
                data = self.data[tuple(slices.values())],
                axes = newAxes,
                metadata = newMetadata)
    
    def copy(self) :
        return Variable(
                data = self.data.copy(),
                axes = self.axes.copy(),
                metadata = self.metadata.copy())
    
    def empty(self) :
        return Variable(
                data = np.empty(self.shape),
                axes = self.axes.copy(),
                metadata = {})
    
    def zeros(self) :
        return Variable(
                data = np.zeros(self.shape),
                axes = self.axes.copy(),
                metadata = {})
    
    def close(self) :
        pass

    def write(self, filePath) :
        from file import File
        if 'shortName' not in self.metadata :
            self.metadata['shortName'] = 'unknown'
        fileOut = File(axes=self.axes, variables={self.shortName:self})
        fileOut.write(filePath)

    def __getattr__(self, attributeName) :
        if 'metadata' in self.__dict__ :
            if attributeName in self.metadata :
                return self.metadata[attributeName]
        if 'axes' in self.__dict__ :
            return self.axes[attributeName]
        raise AttributeError

    def mean(self, axisNames) :
        # input can either either be like 'zy' or like ['lev', 'lat']
        # turn the 'zy' into ['z', 'y']
        axisNames = list(axisNames)
        for i in range(len(axisNames)) :
            axisNames[i] = Axes.standardize(axisNames[i])
            # levels must be averaged first
            # 'level' must be at the top of the list
            if axisNames[i] == 'level' :
                del axisNames[i]
                axisNames = ['level'] + axisNames
        return self.averager(axisNames)
    
    def averager(self, axisNames) :
        # still axes needing averaging
        if len(axisNames) > 0 :
            # extract the name of the axis to be averaged
            axisName = axisNames.pop(0)
            newAxes = self.axes.copy()
            # get its position and weights
            axisIndex = newAxes.index(axisName)
            weights = newAxes[axisName].weights
            self.metadata[axisName] = (newAxes[axisName].data.min(),
                    newAxes[axisName].data.max())
            # and delete it
            del newAxes[axisName]
            if axisName == 'level' and 'surfacePressure' in self.metadata :
                self.metadata['thickness'] = statistics.sp2thck(self)
            if axisName == 'level' and 'thickness' in self.metadata :
                newMetaData = self.metadata.copy()
                del newMetaData['thickness']
                return Variable(
                            data = np.nansum(self.data*self.thickness.data,
                                    axis=axisIndex)/9.81,
                            axes = newAxes,
                            metadata = newMetaData 
                        ).averager(axisNames)
            elif axisName == 'level' :
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                return Variable(
                            data = np.nansum(self.data*weights[weightSlice],
                                    axis=axisIndex),
                            axes = newAxes,
                            metadata = self.metadata.copy()
                        ).averager(axisNames)
            else :
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                return Variable(
                            data = np.nanmean(self.data*weights[weightSlice]/np.nanmean(weights),\
                                    axis=axisIndex),
                            axes = newAxes,
                            metadata = self.metadata.copy()
                        ).averager(axisNames)
        # no axes left to average : return the result
        else :
            return self
    
    basemap = property(graphics._get_basemap, graphics._set_basemap)
    minimap = property(graphics._get_minimap, graphics._set_minimap)
    #plot = property(graphics.plot)
    trend = property(statistics.trend)
    slope = property(statistics.slope)
    significance = property(statistics.significance)
    line = property(statistics.line)
    ante = property(statistics.ante)
    post = property(statistics.post)
    eof1 = property(statistics.eof1)
    
    def mean(self, axisNames) :
        # input can either either be like 'zy' or like ['lev', 'lat']
        # turn the 'zy' into ['z', 'y']
        axisNames = list(axisNames)
        for i in range(len(axisNames)) :
            axisNames[i] = Axes.standardize(axisNames[i])
            # levels must be averaged first
            # 'level' must be at the top of the list
            if axisNames[i] == 'level' :
                del axisNames[i]
                axisNames = ['level'] + axisNames
        return self.averager(axisNames)
    
    def averager(self, axisNames) :
        # still axes needing averaging
        if len(axisNames) > 0 :
            # extract the name of the axis to be averaged
            axisName = axisNames.pop(0)
            newAxes = self.axes.copy()
            # get its position and weights
            axisIndex = newAxes.index(axisName)
            weights = newAxes[axisName].weights
            self.metadata[axisName] = (newAxes[axisName].data.min(),
                    newAxes[axisName].data.max())
            # and delete it
            del newAxes[axisName]
            if axisName == 'level' and 'surfacePressure' in self.metadata :
                self.metadata['thickness'] = statistics.sp2thck(self)
            if axisName == 'level' and 'thickness' in self.metadata :
                newMetaData = self.metadata.copy()
                del newMetaData['thickness']
                return Variable(
                            data = np.nansum(self.data*self.thickness.data,
                                    axis=axisIndex)/9.81,
                            axes = newAxes,
                            metadata = newMetaData 
                        ).averager(axisNames)
            elif axisName == 'level' :
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                return Variable(
                            data = np.nansum(self.data*weights[weightSlice],
                                    axis=axisIndex),
                            axes = newAxes,
                            metadata = self.metadata.copy()
                        ).averager(axisNames)
            else :
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                return Variable(
                            data = np.nanmean(self.data*weights[weightSlice]/np.nanmean(weights),\
                                    axis=axisIndex),
                            axes = newAxes,
                            metadata = self.metadata.copy()
                        ).averager(axisNames)
        # no axes left to average : return the result
        else :
            return self
    
    basemap = property(graphics._get_basemap, graphics._set_basemap)
    minimap = property(graphics._get_minimap, graphics._set_minimap)
    plot = property(graphics.plot)
    trend = property(statistics.trend)
    slope = property(statistics.slope)
    significance = property(statistics.significance)
    line = property(statistics.line)
    ante = property(statistics.ante)
    post = property(statistics.post)
    eof1 = property(statistics.eof1)
    
# allow operations on variables e.g. add, substract, etc.
def wrap_operator(operatorName) :
    # a function factory
    def operator(self, operand) :
        # the operator expects a Variable or a numpy-compatible input
        if isinstance(operand, Variable) :
            operand = operand.data
        # use the numpy operator on the Variable's data
        # and return as a new varaible
        return Variable(
                    data = getattr(self.data, operatorName)(operand),
                    axes = self.axes.copy(),
                    metadata = self.metadata.copy())
    return operator
for operatorName in [
            '__gt__', '__lt__', '__ge__', '__le__', '__eq__', '__ne__',
            '__add__', '__sub__', '__div__', '__mul__', '__pow__',
            '__radd__', '__rsub__', '__rdiv__', '__rmul__', '__rpow__'] :
    setattr(Variable, operatorName, wrap_operator(operatorName))

"""
# maybe later
def wrap_function(functionName) :
    def function(argument) :
        original = getattr(np, functionName)
        if isinstance(argument, Variable) :
            return Variable(
                        data = original(argument.data),
                        axes = argument.axes.copy(),
                        metadata = argument.metadata.copy())
        else :
            return original(argument)
    return function
for functionName in ['log', 'cos', 'sin', 'abs'] :
    function = wrap_function(functionName)
    setattr(np, functionName, function)
    #globals()[functionName] = function
"""

monthNames = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 
        'SEP', 'OCT', 'NOV', 'DEC']
seasonNames = ['DJF', 'MAM', 'JJA', 'SON']
periods = {monthName:[monthNumber+1] for monthNumber, monthName in 
        enumerate(monthNames)}
periods['DJF'] = [12, 1, 2]
periods['MAM'] = [3, 4, 5]
periods['JJA'] = [6, 7, 8]
periods['SON'] = [9, 10, 11]
periods['OND'] = [10, 11, 12]
periods['JFMA'] = [1, 2, 3, 4]
periods['JASO'] = [7, 8, 9, 10]
periods['ONDJFM'] = [10, 11, 12, 1, 2, 3]
periods['ONDJF'] = [10, 11, 12, 1, 2]
periods['JFM'] = [1, 2, 3]
periods['JAS'] = [7, 8, 9]

def wrap_extractor(monthNumbers) :
    @property
    def extractor(self) :
        mask = np.zeros(len(self.dts), dtype=bool)
        for monthNumber in monthNumbers :
            mask += self.dt.months == monthNumber
        newAxes = self.axes.copy()
        newAxes['time'] = self.dt[mask]
        maskSlice = []
        for axis in newAxes :
            if axis == 'time' :
                maskSlice.append(mask)
            else : 
                maskSlice.append(slice(None))
        return Variable(
                data=self.data[maskSlice],
                axes=newAxes,
                metadata=self.metadata.copy())
    return extractor
for periodName, monthNumbers in periods.iteritems() :
    setattr(Variable, periodName, wrap_extractor(monthNumbers))

@property
def yearly(self) :
    # set of years covered by the dataset
    years = range(self.dts[0].year, self.dts[-1].year + 1)
    # array containing each time step's year
    YEARS = self.dt.years
    newAxes = self.axes.copy()
    from axis import TimeAxis
    from datetime import datetime
    newAxes['time'] = TimeAxis([
            datetime(year, 1, 1) for year in years])
    newData = np.empty(newAxes.shape)
    newData[:] = np.nan
    for idx, year in enumerate(years) :
        assert self.axes.keys()[0] == 'time'
        newData[idx] = np.nanmean(self.data[YEARS == year], axis=0)
    return Variable(
            data = newData,
            axes = newAxes,
            metadata = self.metadata.copy())
setattr(Variable, 'yearly', yearly)
    
@property
def monthly(self) :
    from datetime import datetime
    yearMonths = [datetime(year, month, 1)
            for year in range(self.dts[0].year, self.dts[-1].year + 1)
            for month in range(1, 13)]
    # array containing each time step's year
    YEARS = self.dt.years
    # array containing each time step's month
    MONTHS = self.dt.months
    # adjust first months
    while yearMonths[0].month != self.dts[0].month :
        del yearMonths[0]
    # adjust last months
    while yearMonths[-1].month != self.dts[-1].month :
        del yearMonths[-1]
    newAxes = self.axes.copy()
    from axis import TimeAxis
    newAxes['time'] = TimeAxis(yearMonths)
    newData = np.empty(newAxes.shape)
    newData[:] = np.nan
    for idx, yearMonth in enumerate(yearMonths) :
        maskSlice = []
        for axis in newAxes :
            if axis == 'time' :
                maskSlice.append(
                        np.logical_and(
                                YEARS == yearMonth.year,
                                MONTHS == yearMonth.month))
            else : 
                maskSlice.append(slice(None))
        newData[idx] = np.nanmean(self.data[maskSlice], 0)
    return Variable(
            data = newData,
            axes = newAxes,
            metadata = self.metadata.copy())
setattr(Variable, 'monthly', monthly)
    
@property
def seasonal(self) :
    from file import File
    # seasonal returns a file to avoid ambiguities
    # on which is the first season
    variables = {}
    for ssn in seasonNames :
        variables[ssn] = getattr(self, ssn).yearly.mean('t')
    axes = variables[ssn].axes.copy()
    return File(axes=axes, variables=variables)
setattr(Variable, 'seasonal', seasonal)

@property
def annual(self) :
    from axis import Axis
    axes = Axes()
    axes['month'] = Axis(range(1, 13))
    for axisName in self.axes :
        if axisName != 'time' :
            axes[axisName] = self.axes[axisName].copy()
    data = np.empty(axes.shape)
    for idx, month in enumerate(monthNames) :
        data[idx] = getattr(self, month).yearly.mean('t').data
    return Variable(data, axes)
setattr(Variable, 'annual', annual)

@property
def DJF_yearly(self) :
    # extract winter month labelling intuitively last year's December as new year's
    output = self.DJF
    from axis import TimeAxis
    from datetime import timedelta
    output.axes['time'] = TimeAxis(output.dts + timedelta(days = 31))
    return output.yearly
setattr(Variable, 'DJF_yearly', DJF_yearly)

"""
def wrap_smoother(monthNumbers) :
    @property
    def smoother(self) :
        return Variable(
                )
    return smoother
for periodName, monthNumbers in periods.iteritems() :
    setattr(Variable, periodName, wrap_smoother(monthNumbers))
"""

def absolute(self) :
    return Variable(
            data = abs(self.data), 
            metadata = self.metadata.copy(),
            axes = self.axes.copy())
setattr(Variable, 'abs', absolute)
    
setattr(Variable, 'quiver', graphics.quiver)
setattr(Variable, 'streamplot', graphics.streamplot)
setattr(Variable, 'draw_minimap', graphics.draw_minimap)
setattr(Variable, 'taylor', graphics.taylor)
setattr(Variable, 'xyz', graphics.xyz)
setattr(Variable, 'XYZ', graphics.XYZ)
setattr(Variable, 'plot_trend', graphics.plot_trend)
setattr(Variable, 'plot', graphics.plot)
setattr(Variable, 'div', statistics.div)
setattr(Variable, 'rot', statistics.rot)
setattr(Variable, 'cycle', statistics.cycle)
setattr(Variable, 'smooth', statistics.smooth)
setattr(Variable, 'corr', statistics.corr)

