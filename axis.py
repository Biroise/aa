
import numpy as np
import operator as op
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta

earthRadius = 6371000

class Axes(OrderedDict) :
    aliases = {'latitude':'latitude', 'latitudes':'latitude',
        'lat':'latitude', 'longitude':'longitude',
        'XDim':'longitude', 'YDim':'latitude',
        'g4_lat_1':'latitude', 'g4_lon_2':'longitude',
        'longitudes':'longitude', 'lon':'longitude',
        'level':'level', 'levels':'level', 'lev':'level',
        'Height':'level',
        'time':'time', 'dt':'time', 't':'time',
        'Time':'time', 'TIME':'time',
        'initial_time0_hours':'time',
        'x':'longitude', 'y':'latitude', 'z':'level', 'm':'member',
        'level0':'level', 'PRES':'level'}
    shortcuts = {'lats':'latitude', 'lons':'longitude',
        'levs':'level', 'dts':'time', 'mbr':'member'}
    ncStandard = {'latitude':'lat', 'longitude':'lon',
            'level':'lev', 'time':'time'}
    
    @staticmethod
    def ncStandardize (axisName) :
        if axisName in Axes.ncStandard :
            return Axes.ncStandard[axisName]
        else :
            return axisName

    @staticmethod
    def standardize(axisName) :
        if axisName in Axes.aliases :
            return Axes.aliases[axisName]
        elif axisName in Axes.shortcuts :
            return Axes.shortcuts[axisName]
        else :
            return axisName

    def __setitem__(self, axisName, value) :
        return super(Axes, self).__setitem__(
                Axes.standardize(axisName), value)

    def __getitem__(self, attributeName) :
        # dealing with the most common aliases
        if attributeName in Axes.aliases :
            return super(Axes, self).__getitem__(
                    Axes.aliases[attributeName])
        elif attributeName in Axes.shortcuts :
            return super(Axes, self).__getitem__(
                    Axes.shortcuts[attributeName]).data
        else :
            # an except clause to change the KeyError into a AttributeError
            try :
                return super(Axes, self).__getitem__(attributeName)
            except :
                raise AttributeError

    
    def copy(self) :
        newAxes = Axes()
        for axisName, axis in self.items() :
            newAxes[axisName] = axis.copy()
        return newAxes

    def index(self, axisName) :
        return list(self).index(Axes.standardize(axisName))

    @property
    def shape(self) :
        output = []
        for axis in self.values() :
            output.append(len(axis))
        return tuple(output)


class Axis(object) :
    def __init__(self, data, units=None) :
        self.data = np.array(data)
        self.units = units
    
    def __getitem__(self, item) :
        # call the child constructor
        output =  self.__class__(
                    self.data.__getitem__(item),
                    self.units)
        if isinstance(output.data, np.ndarray) :
            if output.data.size > 1 :
                return output
        else :
            return None

    def min(self) :
        return self.data.min()

    def max(self) :
        return self.data.max()

    def __len__(self) :
        return len(self.data)

    def condition_matched(self, condition) :
        index = np.argmax(self.data == condition)
        notMatched = index == 0 and self.data[0] != condition
        return index, notMatched

    def __call__(self, condition) :
        # should a range of indices be extracted ?
        if type(condition) == tuple :
            # if the user does not provide the type of boundaries
            if len(condition) > 1 :
                minValue = condition[0]
                maxValue = condition[1]
            if len(condition) == 2 :
                # default boundaries are "closed-closed" unlike numpy
                condition = condition + ('cc',)
            # if the lower boundary is closed...
            if condition[2][0] == 'c' :
                minType = op.ge
            else :
                minType = op.gt
            # if the upper boundary is closed...
            if condition[2][1] == 'c' :
                maxType = op.le
            else :
                maxType = op.lt
            # the following tasks are given to a function that can be over-ridden
            # by the subclasses of Axis (e.g. Parallel)
            return self.process_call(minValue, maxValue, minType, maxType)
        # extract a single index only
        else :
            index, notMatched = self.condition_matched(condition)
            # if there is no exact match, send the neighbours
            if notMatched :
                newCondition = (condition - self.step, \
                            condition + self.step, 'cc')
                slice_, axis = self(newCondition)
                # clause to catch likely bug if position very close to gridpoint
                # slice_ could be actually be a tuple of slices (in case of longitudes)
                if type(slice_) == slice : 
                    if slice_.stop - slice_.start == 1 :
                        if abs(self.data[slice_.start] - condition) < 0.05*self.step :
                            return slice_.start, None
                        # BUG : may return a single point if it is just outside the bounds
                        else :
                            print('conditions out of bound')
                            raise Exception
                            
                return slice_, axis
            else :
                return index, None
                # don't add this axis to newAxes
    
    def process_call(self, minValue, maxValue, minType, maxType) :
        lower_mask = minType(self.data - minValue,
                        # adapt 0 to axis unit : number / timedelta(0)
                        type(self.data[0] - minValue)(0))
        upper_mask = maxType(self.data - minValue,
                        maxValue - minValue)
        mask = np.logical_and(lower_mask, upper_mask)
        #case where both conditions are out of bounds
        if not lower_mask.any() or not upper_mask.any() :
            print('conditions out of bound')
            raise Exception
        # now extract the sub-axis corresponding to the condition
        return (slice(np.argmax(mask),
                        len(mask) - np.argmax(mask[::-1])),
                self[mask])

    def __eq__(self, other) :
        answer = False
        if hasattr(other, 'data') and hasattr(other, 'units') :
            if len(self) == len(other) and self.units == self.units :
                if (self.data == other.data).all() :
                    answer = True
        # if other has no data/units attributes e.g. "self == None ?"
        # if self WAS of NoneType (or any other type), this method would not be called
        # hence the answer is always False in this case
        return answer

    @property
    def step(self) :
        # extremely basic, won't work for irregular axes such as levels
        a = np.abs(np.diff(self.data))
        assert (a.min() - a.max())/a[0] < 0.05
        return a[0]
    
    @property
    def edges(self) :
        if self.data[0] < self.data[1] :
            return np.concatenate(
                    (self.data - self.step/2,
                    [self.data[-1] + self.step/2]))
        else :
            return np.concatenate(
                    (self.data + self.step/2,
                    [self.data[-1] - self.step/2]))
    
    @property
    def weights(self) :
        return np.ones(1)
    
    def copy(self) :
        return self.__class__(self.data.copy(), self.units)


class TimeAxis(Axis) :
    def __init__(self, data, units=None) :
        data = np.array(data)
        super(TimeAxis, self).__init__(data, units)
        if units != None :
            # unit definition is conventionally :
            # seconds/hours/days since YYYY-MM-DD HH
            words = units.split()
            #if words[1] != 'since' :
            if len(words) < 3 :
                #print("Unconventional definition of time units")
                if words[0].startswith('year') :
                    self.data = np.array([datetime(int(year), 1, 1) for year in self.data])
                    self.units = None
            elif words[1] == 'since' :
                units = words[0]
                date = [int(bits) for bits in words[2].split('-')]
                epoch = datetime(date[0], date[1], date[2])
                self.data = np.array(
                    [epoch + timedelta(**{units: np.asscalar(offset)})
                    for offset in self.data])
                self.units = None
    
    @property
    def step(self) :
        # extremely basic, won't work for irregular axes such as levels
        a = np.abs(np.diff(self.data))
        assert (a.min() - a.max()).total_seconds()/a[0].total_seconds() < 0.05
        return a[0]
    
    @property
    def years(self) :
        return np.array([dt.year for dt in self.data])

    @property
    def months(self) :
        return np.array([dt.month for dt in self.data])

    @property
    def hours(self) :
        return np.array([dt.hour for dt in self.data])

    @property
    def total_seconds(self) :
        return np.array([(dt - self.data[0]).total_seconds() for dt in self.data])

class Parallel(Axis) :

    # the parallel being the longitudinal axis
    def __init__(self, data, units='degree_east') :
        super(Parallel, self).__init__(data, units)
    
    def condition_matched(self, condition) :
        dataStd = (self.data - self.data[0])%360 + self.data[0]
        conditionStd = (condition - self.data[0])%360 + self.data[0]
        index = np.argmax(dataStd == conditionStd)
        notMatched = index == 0 and dataStd[0] != conditionStd
        return index, notMatched

    def process_call(self, minValue, maxValue, minType, maxType) :
        # (x - x0)% 360 + x0 places x between x0 and x0 + 360
        firstMask = minType(
                self.data,
                (minValue - self.data[0])%360 + self.data[0])
        secondMask = maxType(
                self.data,
                (maxValue - self.data[0])%360 + self.data[0])
        # argmax will return 0 if the array is all False
        # not the expected result for the slicing later on
        if firstMask.any() :
            firstTrue = np.argmax(firstMask)
        else :
            firstTrue = len(firstMask)
        if secondMask.all() :
            firstFalse = len(secondMask)
        else :
            firstFalse = np.argmax(~secondMask)
        offset = minValue - (minValue - self.data[0])%360 - self.data[0]
        # 00011111 (firstMask)
        # 11111100 (secondMask)
        if firstTrue < firstFalse and maxValue - minValue < 360 :
            # return : 00011100
            mask = np.logical_and(firstMask, secondMask)
            return (
                    slice(np.argmax(mask),
                            len(mask) - np.argmax(mask[::-1])),
                    Parallel(
                            (self.data[mask] - minValue)%360 + minValue,
                            self.units))
        # firstMask is empty (it happens when slicing near the beginning)
        elif firstTrue == len(firstMask) and maxValue - minValue < 360 :
            mask = secondMask
            return (
                    slice(np.argmax(mask),
                            len(mask) - np.argmax(mask[::-1])),
                    Parallel(
                            (self.data[mask] - minValue)%360 + minValue,
                            self.units))
        else :
            # return : 00011111 + 11111100
            #firstSlice = slice(firstTrue, None)
            firstSlice = slice(firstTrue, len(self))
            lastSlice = slice(0, firstFalse)
            return (
                    (firstSlice, lastSlice), 
                    Parallel(
                            np.hstack((
                                self.data[firstMask] + offset,
                                self.data[secondMask] + offset + 360))))
            
    @property
    def edges(self) :
        data = np.array(list(self.data))
        if data[0] < data[1] :
            return np.concatenate(
                    (data - self.step/2,
                    [data[-1] + self.step/2]))
        else :
            return np.concatenate(
                    (data + self.step/2,
                    [data[-1] - self.step/2]))
        

class Meridian(Axis) :
    def __init__(self, data, units='degree_north') :
        super(Meridian, self).__init__(data, units)
    
    @property
    def weights(self) :
        return np.cos(self.data*np.pi/180.0)
    
    @property
    def edges(self) :
        default = super(Meridian, self).edges
        for endIndex in [0, -1] :
            if default[endIndex] > 90 :
                default[endIndex] = 90
            if default[endIndex] < -90 :
                default[endIndex] = -90
        return default

    # the parallel being the longitudinal axis
    def __init__(self, data, units='degrees') :
        super(Parallel, self).__init__(data, units)
    
    def condition_matched(self, condition) :
        dataStd = (self.data - self.data[0])%360 + self.data[0]
        conditionStd = (condition - self.data[0])%360 + self.data[0]
        index = np.argmax(dataStd == conditionStd)
        notMatched = index == 0 and dataStd[0] != conditionStd
        return index, notMatched

    def process_call(self, minValue, maxValue, minType, maxType) :
        # (x - x0)% 360 + x0 places x between x0 and x0 + 360
        firstMask = minType(
                self.data,
                (minValue - self.data[0])%360 + self.data[0])
        secondMask = maxType(
                self.data,
                (maxValue - self.data[0])%360 + self.data[0])
        # argmax will return 0 if the array is all False
        # not the expected result for the slicing later on
        if firstMask.any() :
            firstTrue = np.argmax(firstMask)
        else :
            firstTrue = len(firstMask)
        if secondMask.all() :
            firstFalse = len(secondMask)
        else :
            firstFalse = np.argmax(~secondMask)
        offset = minValue - (minValue - self.data[0])%360 - self.data[0]
        # 00011111 (firstMask)
        # 11111100 (secondMask)
        if firstTrue < firstFalse and maxValue - minValue < 360 :
            # return : 00011100
            mask = np.logical_and(firstMask, secondMask)
            return (
                    slice(np.argmax(mask),
                            len(mask) - np.argmax(mask[::-1])),
                    Parallel(
                            (self.data[mask] - minValue)%360 + minValue,
                            self.units))
        # firstMask is empty (it happens when slicing near the beginning)
        elif firstTrue == len(firstMask) and maxValue - minValue < 360 :
            mask = secondMask
            return (
                    slice(np.argmax(mask),
                            len(mask) - np.argmax(mask[::-1])),
                    Parallel(
                            (self.data[mask] - minValue)%360 + minValue,
                            self.units))
        else :
            # return : 00011111 + 11111100
            #firstSlice = slice(firstTrue, None)
            firstSlice = slice(firstTrue, len(self))
            lastSlice = slice(0, firstFalse)
            return (
                    (firstSlice, lastSlice), 
                    Parallel(
                            np.hstack((
                                self.data[firstMask] + offset,
                                self.data[secondMask] + offset + 360))))
            
    @property
    def edges(self) :
        data = np.array(list(self.data))
        if data[0] < data[1] :
            return np.concatenate(
                    (data - self.step/2,
                    [data[-1] + self.step/2]))
        else :
            return np.concatenate(
                    (data + self.step/2,
                    [data[-1] - self.step/2]))
        

class Meridian(Axis) :
    def __init__(self, data, units='degrees') :
        super(Meridian, self).__init__(data, units)
    
    @property
    def weights(self) :
        return np.cos(self.data*np.pi/180.0)
    
    @property
    def edges(self) :
        default = super(Meridian, self).edges
        for endIndex in [0, -1] :
            if default[endIndex] > 90 :
                default[endIndex] = 90
            if default[endIndex] < -90 :
                default[endIndex] = -90
        return default


class Vertical(Axis) :
    @property
    def weights(self) :
        output = np.zeros(len(self))
        output[:-1] += 0.5*np.abs(np.diff(self.data))
        output[1:] += 0.5*np.abs(np.diff(self.data))
        output *= 100/9.81
        return output


def month(year, monthIndex) :
    return (datetime(year, monthIndex, 1),
            datetime(year + (monthIndex+1)/12, (monthIndex+1)%12, 1),
            'co')
    

def angle_sub(a, b) :
    return (a - b + 180)%360 -180

@np.vectorize
def in_seconds(delta) :
    return delta.seconds


