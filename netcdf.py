
import aa
import numpy as np
import netCDF4 as nc
import operator as op
#from scipy.io.netcdf import netcdf_file


class File(aa.File) :
    def __init__(self, filePath, mode) :
        super(File, self).__init__()
        #self._raw = netcdf_file(filePath)
        self._raw = nc.Dataset(filePath, mode)
        ########
        # AXES #
        ########
        for dimensionName in self._raw.dimensions :
            if dimensionName in self._raw.variables :
                if hasattr(self._raw.variables[dimensionName], 'units') :
                    units = self._raw.variables[dimensionName].units
                else :
                    units = None
                args = [self._raw.variables[dimensionName][:], units]
                if aa.Axes.standardize(dimensionName) == 'time' :
                    self.axes['time'] = aa.TimeAxis(*args)
                elif aa.Axes.standardize(dimensionName) == 'longitude' :
                    self.axes['longitude'] = aa.Parallel(*args)
                elif aa.Axes.standardize(dimensionName) == 'latitude' :
                    self.axes['latitude'] = aa.Meridian(*args)
                elif aa.Axes.standardize(dimensionName) == 'level' :
                    # convert pascals to hectopascals
                    if (args[0] > 10000).any() :
                        args[0] /= 100
                    self.axes['level'] = aa.Vertical(*args)
                # it's not a conventional axis
                else :
                    self.axes[aa.Axes.standardize(dimensionName)] = aa.Axis(*args)
            # no variable goes by this dimension's name : create an axis of indices
            else :
                self.axes[dimensionName] = aa.Axis(
                        np.arange(len(self._raw.dimensions[dimensionName])),
                        units = 'indices')
        #############
        # VARIABLES #
        #############
        for variableName in set(self._raw.variables.keys()) \
                - set(self._raw.dimensions.keys()) :
            variableAxes = aa.Axes()
            for axisName in self._raw.variables[variableName].dimensions :
                # conventional axes...
                if axisName in aa.Axes.aliases :
                    axisName = aa.Axes.aliases[axisName]
                # should always be true technically
                if axisName in self.axes :
                    variableAxes[axisName] = self.axes[axisName]
            variableMetaData = {'shortName':variableName}
            if 'units' in self._raw.variables[variableName].__dict__ :
                variableMetaData['units'] = \
                        self._raw.variables[variableName].units
            if 'long_name' in self._raw.variables[variableName].__dict__ :
                variableMetaData['name'] = \
                        self._raw.variables[variableName].long_name
            if 'description' in self._raw.variables[variableName].__dict__ :
                variableMetaData['name'] = \
                        self._raw.variables[variableName].description
            self.variables[variableName] = \
                    Variable(
                        #data=self._raw.variables[variableName][:],
                        label = variableName,
                        axes=variableAxes,
                        metadata=variableMetaData, 
                        rawFile=self._raw)
    
    def close(self) :
        self._raw.close()


class Variable(aa.Variable) :
    def __init__(self, axes, metadata, rawFile, **kwargs)    :
        if 'data' not in kwargs :
            kwargs['data'] = None
        super(Variable, self).__init__(kwargs['data'], axes, metadata = metadata)
        self._raw = rawFile
        if 'label' in kwargs :
            self.label = kwargs['label']

    @property 
    def data(self) :
        # if the variable is still untouched
        if "_data" not in self.__dict__ :
            self._data = self._raw.variables[self.label][:],
        return self._data

    def close(self) :
        self._raw.close()

