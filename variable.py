
import numpy as np
import aa.graphics as graphics
from aa.axis import Axes
from collections import OrderedDict
import aa.statistics as statistics


class Variable(object) :
    #def __init__(self, data=None, axes=Axes(), metadata=dict()) :
    def __init__(self, data=None, axes=Axes(), metadata = dict()) :
        self.axes = axes
        self.metadata = metadata
        if type(data) != type(None) :
            self._data = np.array(data)

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
        newMetadata = {}
        for key, target in self.metadata.items() :
            if key in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction'] :
                newMetadata[key] = target[item]
            else :
                newMetadata[key] = target
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
        for axisName, condition in kwargs.copy().items() :
            del kwargs[axisName]
            if type(condition) == tuple :
                condition = tuple(sorted(condition[:2]))+condition[2:]
            kwargs[Axes.standardize(axisName)] = condition
        output = self.extract_data(**kwargs)
        # do we need to interpolate along an axis ?
        for axisName, condition in kwargs.items() :
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
                firstSlice = tuple(firstSlice)
                secondSlice = tuple(secondSlice)
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
        # lazy copy of the metadata
        #newMetadata = self.metadata.copy()
        # ideally : slice the pressure field as well except! level slice
        # for now let's play it safe
        newMetadata = {key:value for key, value in self.metadata.items()
                if key not in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction']}
        # slice the maskedFraction exactly the same way
        if 'maskedFraction' in self.metadata :
            newMetadata['maskedFraction'] = self.metadata['maskedFraction'](**kwargs).copy()
        # daughter variable does not inherit surfacePressure, etc. if 'level' is sliced
        if 'level' not in kwargs :
            if 'thickness' in self.metadata :
                newMetadata['thickness'] = self.metadata['thickness'](**kwargs)
            if 'surfacePressure' in self.metadata :
                newMetadata['surfacePressure'] = self.metadata['surfacePressure'](**kwargs)
            if 'oceanDepth' in self.metadata :
                newMetadata['oceanDepth'] = self.metadata['oceanDepth'](**kwargs)
        # dispatch the conditions to the axes
        for axisName, condition in kwargs.items() :
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

    def write(self, filePath, compress = True) :
        from aa.file import File
        if 'shortName' not in self.metadata :
            self.metadata['shortName'] = 'unknown'
        fileOut = File(axes=self.axes, variables={self.shortName:self})
        fileOut.write(filePath, compress = compress)

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
            # does not affect the indices of subsequent items
        return self.averager(axisNames)
    
    def averager(self, axisNames) :
        # still axes needing averaging
        if len(axisNames) > 0 :
            # copy the metadata (by reference) - no point in copying surface pressure
            newMetadata = {key:value for key, value in self.metadata.items()
                    if key not in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction']}
            # extract the name of the axis to be averaged
            axisName = axisNames.pop(0)
            newAxes = self.axes.copy()
            # get the axis' position and weights
            axisIndex = newAxes.index(axisName)
            weights = newAxes[axisName].weights
            newMetadata[axisName] = (newAxes[axisName].data.min(),
                    newAxes[axisName].data.max())
            # and delete the axis
            del newAxes[axisName]
            if axisName == 'level' and 'surfacePressure' in self.metadata :
                self.metadata['thickness'] = statistics.sp2thck(self)
            if axisName == 'level' and 'oceanDepth' in self.metadata :
                self.metadata['thickness'] = statistics.od2thck(self)
            if axisName == 'level' and 'thickness' in self.metadata :
                return Variable(
                            data = np.array(np.nansum(self.data*self.thickness.data,
                                    axis=axisIndex)),
                            axes = newAxes,
                            metadata = newMetadata 
                        ).averager(axisNames)
            elif axisName == 'level' :
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                return Variable(
                            data = np.array(np.nansum(self.data*weights[weightSlice],
                                    axis=axisIndex)),
                            axes = newAxes,
                            metadata = newMetadata
                        ).averager(axisNames)
            else :
                # check for nans and the prior existence of maskedFraction
                if np.isnan(self.data).any() and 'maskedFraction' not in self.metadata :
                        newMetadata['maskedFraction'] = Variable(
                                data = np.isnan(self.data).mean(axisIndex),
                                axes = newAxes.copy())
                # if there has already been some averaging going on involving nans
                elif 'maskedFraction' in self.metadata :
                        newMetadata['maskedFraction'] = Variable(
                                data = self.metadata['maskedFraction'].data.mean(axisIndex),
                                axes = newAxes.copy())
                # if you average first along the horizontal and then the vertical
                # and hope to mask underground levels, the script will fail (as it should)
                weightSlice = [None]*len(self.shape)
                weightSlice[axisIndex] = slice(None)
                reverseSlice = [slice(None)]*len(self.shape)
                reverseSlice[axisIndex] = None
                # a modifier : on veut garder les nans des slices vides
                return Variable(
                            data = np.nanmean(self.data*weights[tuple(weightSlice)]/np.nanmean(weights),\
                                    axis=axisIndex),
                            axes = newAxes,
                            metadata = newMetadata
                        ).averager(axisNames)
        # no axes left to average : return the result
        else :
            return self

    def censor_nans(self, ratio=1./3) :
        if 'maskedFraction' in self.metadata :
            self.data[self.metadata['maskedFraction'].data > ratio] = np.nan
            """
            try :
                self.data[self.metadata['maskedFraction'].data > ratio] = np.nan
            # kludge in case variable is a scalar
            except TypeError :
                if len(self.data.shape) == 0 :
                    self.data = np.nan
                else :
                    raise Exception
            """
    
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
            '__add__', '__sub__', '__truediv__', '__mul__', '__pow__',
            '__radd__', '__rsub__', '__rtruediv__', '__rmul__', '__rpow__'] :
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
        newMetadata = {}
        for key, target in self.metadata.items() :
            if key in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction'] :
                #newMetadata[key] = wrap_extractor(monthNumbers)(target)
                newMetadata[key] = target.wrap_extractor(monthNumbers)
            else :
                newMetadata[key] = target
        return Variable(
                data=self.data[tuple(maskSlice)],
                axes=newAxes,
                metadata=self.metadata.copy())
    return extractor
for periodName, monthNumbers in periods.items() :
    setattr(Variable, periodName, wrap_extractor(monthNumbers))

@property
def yearly(self) :
    # set of years covered by the dataset
    years = range(self.dts[0].year, self.dts[-1].year + 1)
    # array containing each time step's year
    YEARS = self.dt.years
    newAxes = self.axes.copy()
    from aa.axis import TimeAxis
    from datetime import datetime
    newAxes['time'] = TimeAxis([
            datetime(year, 1, 1) for year in years])
    newData = np.empty(newAxes.shape)
    newData[:] = np.nan
    # dump companion variables
    newMetadata = {key:value for key, value in self.metadata.items()
            if key not in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction']}
    if np.isnan(self.data).any() and 'maskedFraction' not in self.metadata :
            self.metadata['maskedFraction'] = Variable(
                    data = np.isnan(self.data),
                    axes = self.axes.copy(),
                    metadata = {})
    if 'maskedFraction' in self.metadata :
            newMetadata['maskedFraction'] = Variable(
                    data = np.empty(newAxes.shape),
                    axes = newAxes.copy(),
                    # kludge
                    metadata = {})
            newMetadata['maskedFraction'].data[:] = np.nan
    for idx, year in enumerate(years) :
        assert list(self.axes.keys())[0] == 'time'
        mask = YEARS == year
        newData[idx] = np.nanmean(self.data[mask], axis=0)
        if 'maskedFraction' in self.metadata :
            newMetadata['maskedFraction'].data[idx] = self.metadata['maskedFraction'].data[mask].mean(0)
    return Variable(
            data = newData,
            axes = newAxes,
            metadata = newMetadata)
setattr(Variable, 'yearly', yearly)
    
@property
def monthly(self) :
    # more rigid than before : starts in January, ends in December
    # for some reason, a full slice was supplied to the source data
    from datetime import datetime
    if self.dts[0].year != self.dts[-1].year :
        yearMonths = [datetime(year, month, 1)
                for year in range(self.dts[0].year, self.dts[-1].year + 1)
                for month in range(1, 13)]
    else :
        yearMonths = [datetime(self.dts[0].year, month, 1)
                for month in range(self.dts[0].month, self.dts[-1].month + 1)]
    # array containing each time step's year
    YEARS = self.dt.years
    # array containing each time step's month
    MONTHS = self.dt.months
    newAxes = self.axes.copy()
    from aa.axis import TimeAxis
    newAxes['time'] = TimeAxis(yearMonths)
    newData = np.empty(newAxes.shape)
    newData[:] = np.nan
    # dump companion variables
    newMetadata = {key:value for key, value in self.metadata.items()
            if key not in ['oceanDepth', 'surfacePressure', 'thickness', 'maskedFraction']}
    # check for nans and the prior existence of maskedFraction
    if np.isnan(self.data).any() and 'maskedFraction' not in self.metadata :
            self.metadata['maskedFraction'] = Variable(
                    data = np.isnan(self.data),
                    axes = self.axes.copy(),
                    # kludge to avoid recursion (why?)
                    metadata = {})
    if 'maskedFraction' in self.metadata :
            newMetadata['maskedFraction'] = Variable(
                    data = np.empty(newAxes.shape),
                    axes = newAxes.copy(),
                    metadata = {})
            newMetadata['maskedFraction'].data[:] = np.nan
    for idx, yearMonth in enumerate(yearMonths) :
        mask = np.logical_and(
                        YEARS == yearMonth.year,
                        MONTHS == yearMonth.month)
        newData[idx] = np.nanmean(self.data[mask], 0)
        if 'maskedFraction' in self.metadata :
            newMetadata['maskedFraction'].data[idx] = self.metadata['maskedFraction'].data[mask].mean(0)
    return Variable(
            data = newData,
            axes = newAxes,
            metadata = newMetadata)
setattr(Variable, 'monthly', monthly)
    
@property
def seasonal(self) :
    from aa.file import File
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
    from aa.axis import Axis
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
    from aa.axis import TimeAxis
    from datetime import timedelta
    output.axes['time'] = TimeAxis(output.dts + timedelta(days = 31))
    return output.yearly
setattr(Variable, 'DJF_yearly', DJF_yearly)

def cycle(self) :
    assert 'time' in self.axes
    axes = Axes()
    from aa.axis import Calendar
    axes['month'] = Calendar()
    for axisName, axis in self.axes.items() :
        if axisName != 'time' :
            axes[axisName] = axis.copy()
    data = np.nanmean(self.monthly.data.reshape((-1, 12) + self.shape[1:]), 0)
    return Variable(data = data, axes = axes)
setattr(Variable, 'cycle', cycle)
    

"""
def wrap_smoother(monthNumbers) :
    @property
    def smoother(self) :
        return Variable(
                )
    return smoother
for periodName, monthNumbers in periods.items() :
    setattr(Variable, periodName, wrap_smoother(monthNumbers))
"""

def absolute(self) :
    return Variable(
            data = abs(self.data), 
            metadata = self.metadata.copy(),
            axes = self.axes.copy())
setattr(Variable, 'abs', absolute)

def _get_sp(self) :
    return self.metadata['surfacePressure']
def _set_sp(self, sp) :
    self.metadata['surfacePressure'] = sp
    # this would give the user the option not to mask underground levels... not so useful
    #self.metadata['secretPressure'] = self.surfacePressure
    if 'time' in self.axes :
        standUp = tuple([slice(None), None] + [slice(None)]*(len(self.surfacePressure.shape)-1))
        lieDown = tuple([None, slice(None)] + [None]*(len(self.surfacePressure.shape)-1))
    else :
        standUp = tuple([None] + [slice(None)]*len(sp.shape))
        lieDown = tuple([slice(None)] + [None]*len(sp.shape))
    self.data[self.surfacePressure.data[standUp] < self.levs[lieDown]*100] = np.nan
def _del_sp(self) :
    del self.metadata['surfacePressure']
sp = property(_get_sp, _set_sp, _del_sp)
setattr(Variable, 'surfacePressure', sp)

def _get_od(self) :
    return self.metadata['oceanDepth']
def _set_od(self, od) :
    self.metadata['oceanDepth'] = od
    if 'time' in self.axes :
        # unlike pressure, depth is constant in time
        standUp = tuple([None, None] + [slice(None)]*(len(self.oceanDepth.shape)-1))
        lieDown = tuple([None, slice(None)] + [None]*(len(self.oceanDepth.shape)-1))
    else :
        standUp = tuple([None] + [slice(None)]*len(od.shape))
        lieDown = tuple([slice(None)] + [None]*len(od.shape))
    self.data[self.oceanDepth.data[standUp] < self.levs[lieDown]] = np.nan
def _del_od(self) :
    del self.metadata['oceanDepth']
od = property(_get_od, _set_od, _del_od)
setattr(Variable, 'oceanDepth', od)

# import Variable methods from other python files
setattr(Variable, 'quiver', graphics.quiver)
setattr(Variable, 'streamplot', graphics.streamplot)
setattr(Variable, 'draw_minimap', graphics.draw_minimap)
setattr(Variable, 'taylor', graphics.taylor)
setattr(Variable, 'xyz', graphics.xyz)
setattr(Variable, 'XYZ', graphics.XYZ)
setattr(Variable, 'plot', graphics.plot)
setattr(Variable, 'plot_trend', graphics.plot_trend)
setattr(Variable, 'plot_cycle', graphics.plot_cycle)
setattr(Variable, 'plot_delta', graphics.plot_delta)
setattr(Variable, 'div', statistics.div)
setattr(Variable, 'corr', statistics.corr)
setattr(Variable, 'rot', statistics.rot)
setattr(Variable, 'fourier', statistics.fourier)
setattr(Variable, 'smooth', statistics.smooth)
setattr(Variable, 'corr', statistics.corr)
