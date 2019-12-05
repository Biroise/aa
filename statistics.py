
import numpy as np
from datetime import datetime

def cycle(self, harmonics=3) :
    dts = self.dt.total_seconds/(3600*24)
    spatialize = [slice(None)] + [None]*len(self.shape[1:])
    temporalize = [None] + [slice(None)]*len(self.shape[1:])
    output = self.zeros()
    for i in range(1, harmonics+1) :
        A = np.nanmean(self.data*
                (np.cos(2*np.pi*dts*i/365.25))[spatialize],
                0)[temporalize]*2
        B = np.nanmean(self.data*
                (np.sin(2*np.pi*dts*i/365.25))[spatialize],
                0)[temporalize]*2
        output.data += A*np.cos(2*np.pi*dts*i/365.25)[spatialize] \
                + B*np.sin(2*np.pi*dts*i/365.25)[spatialize]
    return output

def auto_corr (Y) :
    # works on numpy arrays
    beginning = Y[:-1]
    end = Y[1:]
    return np.nanmean(
                (beginning - np.nanmean(beginning, 0))*\
                        (end - np.nanmean(end, 0))/\
                        (np.nanstd(beginning, 0)*np.nanstd(end, 0)),
                0)

def corr (self, other) :
    # swap the names of the variables if "other" is larger than "self"
    if len(self.shape) < len(other.shape) :
        self, other = other, self
    from variable import Variable
    if type(other) == Variable :
        other = other.data
    # the case where the larger input is not a Variable is not considered
    adjust = len(other.shape)*[slice(None)] + (len(self.shape) - len(other.shape))*[None]
    # we do not take into accout negative auto-correlation (an oddity)
    autocorr = np.maximum(auto_corr(self.data), auto_corr(other[adjust]))
    #corrceof = self[0].empty()
    corrcoef = ((self - self.mean('t'))*(other - np.nanmean(other, 0))[adjust]).mean('t')/(
                ((self - self.mean('t'))**2).mean('t')**0.5*
                np.nanmean((other - np.nanmean(other, 0))**2, 0)**0.5)
    # taking autocorrelation into account
    effectiveSampleSize = self.shape[0]*(1 - autocorr)/(1 + autocorr)
    # two parameters have been estimated : -2
    # test statistic under the null hypothesis slope == 0
    # see https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
    t_stat = corrcoef*((effectiveSampleSize - 2)/(1 - corrcoef.data**2))**0.5
    from scipy.stats import t as student
    # two sided student test p = 0.95 becomes a one sided p = 0.975
    # what test statistics should we surpass ?
    # minus two degrees of freedom, again
    t_level = student.ppf(0.975, effectiveSampleSize - 2)
    # also possible : use cdf to determine p-value of t_stat
    #p_value = student.cdf(t_stat.data, effectiveSampleSize - 2)
    #print slope.data, sigmaSlope, p_value
    # per decade rates
    return corrcoef, t_stat > t_level

def trend (self) :
    if self.dt.step.days < 365 :
        Y = self.yearly
    else :
        Y = self
    beginning = Y.data[:-1]
    end = Y.data[1:]
    autocorr = np.nanmean(
            (beginning - np.nanmean(beginning, 0))*\
                    (end - np.nanmean(end, 0))/\
                    (np.nanstd(beginning, 0)*np.nanstd(end, 0)),
            0)
    # predictor
    X = Y.dt.total_seconds/3600
    spatialize = [slice(None)] + [None]*len(Y.shape[1:])
    # slope = covariance(x, y)/variance(x)
    slope = ((Y - Y.mean('t'))*((X - np.nanmean(X))/X.var())[spatialize]).mean('t')
    # residuals = Y - AX - B
    residuals = Y.data - slope.data*(X - np.nanmean(X))[spatialize] - np.nanmean(Y.data, 0)
    # taking autocorrelation into account
    effectiveSampleSize = len(Y.dts)*(1 - autocorr)/(1 + autocorr)
    # variance of the residuals
    # mean(residuals) = 0
    # two parameters have been estimated : -2
    varianceResiduals = np.nansum(
            (residuals - 0)**2, 0)/(effectiveSampleSize - 2)
    # std of the sampling distribution of the slope
    sigmaSlope = (varianceResiduals/((X - X.mean())**2).sum())**0.5
    # test statistic under the null hypothesis slope == 0
    # see Wilks page 141
    t_stat = (slope.abs() - 0)/sigmaSlope
    from scipy.stats import t as student
    # two sided student test p = 0.95 becomes a one sided p = 0.975
    # what test statistics should we surpass ?
    # minus two degrees of freedom, again
    t_level = student.ppf(0.975, effectiveSampleSize - 2)
    # also possible : use cdf to determine p-value of t_stat
    p_value = student.cdf(t_stat.data, effectiveSampleSize - 2)
    #print slope.data, sigmaSlope, p_value
    # per decade rates
    return slope*24*365.25*10, t_stat > t_level

def slope(self) :
    if '_slope' not in self.__dict__ :
        self._slope, self._significance = self.trend
    return self._slope

def significance(self) :
    if '_significance' not in self.__dict__ :
        self._slope, self._significance = self.trend
    return self._significance

def ante(self) :
    X = np.array([(dt - self.dts[0]).total_seconds()/(3600*24*365.25*10) 
            for dt in self.dts])
    output = self.slope.empty()
    output.data = self.slope.data*\
                    (X[0] - np.nanmean(X)) \
            + np.nanmean(self.data, 0)
    return output

def post(self) :
    X = np.array([(dt - self.dts[0]).total_seconds()/(3600*24*365.25*10) 
            for dt in self.dts])
    output = self.slope.empty()
    output.data = self.slope.data*\
                    (X[-1] - np.nanmean(X)) \
            + np.nanmean(self.data, 0)
    return output

def line(self) :
    X = np.array([(dt - self.dts[0]).total_seconds()/(3600*24*365.25*10) 
            for dt in self.dts])
    if len(self.slope.shape) == 0 :
        output = self.empty()
        output.data = self.slope.data*\
                        (X - X.mean()) \
                + self.data.mean(0)
    else :
        spatialize = [slice(None)] + [None]*len(self.slope.shape)
        temporalize = [None] + [slice(None)]*len(self.slope.shape)
        output = self.empty()
        output.data = self.slope.data[temporalize]*\
                        (X - X.mean())[spatialize] \
                + self.data.mean(0)[temporalize]
    return output

def sp2thck(self) :
    thickness = self.zeros()
    sp = self.surfacePressure
    levels = self.levs
    if 'time' in self.axes :
        standUp = [slice(None)] + [None] + [slice(None)]*(len(sp.shape)-1)
        lieDown = [None] + [slice(None)] + [None]*(len(sp.shape)-1)
        lieBack = [None] + [slice(None, None, -1)] + [None]*(len(sp.shape)-1)
        shiftZ = [slice(None), slice(1, None, None)]
        antiShiftZ = [slice(None), slice(None, -1, None)]
        zAxis = 1
    else : 
        standUp = [None] + [slice(None)]*len(sp.shape)
        lieDown = [slice(None)] + [None]*len(sp.shape)
        lieBack = [slice(None, None, -1)] + [None]*len(sp.shape)
        shiftZ = [slice(1, None, None)]
        antiShiftZ = [slice(None, -1, None)]
        zAxis = 0
    if levels[0] < levels[1] :
        lowerIndex = len(levels) - 1 - np.argmax(levels[lieBack]*100
                < sp.data[standUp], axis=zAxis)
        LEVELs = np.where(
                np.arange(len(levels))[lieDown] >= lowerIndex[standUp],
                sp.data[standUp],
                levels[lieDown]*100)
    else :
        lowerIndex = np.argmax(levels[lieDown]*100 < sp.data[standUp], axis=zAxis)
        LEVELs = np.where(
                np.arange(len(levels))[lieDown] <= lowerIndex[standUp],
                sp.data[standUp],
                levels[lieDown]*100)
    thickness.data[shiftZ] += 0.5*np.abs(np.diff(LEVELs, axis=zAxis))
    thickness.data[antiShiftZ] += 0.5*np.abs(np.diff(LEVELs, axis=zAxis))
    return thickness

def zonal_diff(variable) :
    output = np.empty(variable.shape)
    padding = [None]*(len(output.shape) - 1)
    #minipad = [None]*(len(output.shape) - 2)
    output[..., :, 0] = (variable.data[..., :, 1] - variable.data[..., :, 0])/\
            (variable.lons[1] - variable.lons[0])*180/np.pi
    output[..., :, -1] = (variable.data[..., :, -1] - variable.data[..., :, -2])/\
            (variable.lons[-1] - variable.lons[-2])*180/np.pi
    output[..., :, 1:-1] = (variable.data[..., :, 2:] - variable.data[..., :, :-2])/\
            (variable.lons[padding + [slice(2, None)]] - variable.lons[padding + [slice(None, -2)]])*180/np.pi
    return output

def meridional_diff(variable) :
    output = np.empty(variable.shape)
    padding = [None]*(len(output.shape) - 2)
    output[..., 0, :] = (variable.data[..., 1, :] - variable.data[..., 0, :])/\
            (variable.lats[padding + [1, None]] - variable.lats[padding + [0, None]])*180/np.pi
    output[..., -1, :] = (variable.data[..., -1, :] - variable.data[..., -2, :])/\
            (variable.lats[padding + [-1, None]] - variable.lats[padding + [-2, None]])*180/np.pi
    output[..., 1:-1, :] = (variable.data[..., 2:, :] - variable.data[..., :-2, :])/\
            (variable.lats[padding + [slice(2, None), None]] - variable.lats[padding + [slice(None, -2), None]])*180/np.pi
    return output

def div(zonal, meridional) :
    output = zonal.empty()
    output.data = zonal_diff(zonal) + meridional_diff(
            meridional*np.cos(meridional.lats[:, None]*np.pi/180))
    output.data /=  6371000*np.cos(meridional.lats[:, None]*np.pi/180)
    #output.data[0] /=  6371000*np.cos(meridional.lats[:2].mean()*np.pi/180)
    #output.data[-1] /=  6371000*np.cos(meridional.lats[-2:].mean()*np.pi/180)
    if output.lats[0] in [-90, 90] :
        output.data[..., 0, :] =  output.data[..., 1, :]
    if output.lats[-1] in [-90, 90] :
        output.data[..., -1, :] =  output.data[..., -2, :]
    return output

def rot(zonal, meridional) :
    output = zonal.empty()
    output.data = zonal_diff(meridional) - meridional_diff(
            zonal*np.cos(meridional.lats[:, None]*np.pi/180))
    output.data /=  6371000*np.cos(meridional.lats[:, None]*np.pi/180)
    #output.data[0] /=  6371000*np.cos(meridional.lats[:2].mean()*np.pi/180)
    #output.data[-1] /=  6371000*np.cos(meridional.lats[-2:].mean()*np.pi/180)
    if output.lats[0] in [-90, 90] :
        output.data[..., 0, :] =  output.data[..., 1, :]
    if output.lats[-1] in [-90, 90] :
        output.data[..., -1, :] =  output.data[..., -2, :]
    return output

def grad(variable) :
    output = variable.empty(), variable.empty()
    output[0].data = zonal_diff(variable)
    output[1].data = meridional_diff(variable)
    output[0].data /=  6371000*np.cos(variable.lats[:, None]*np.pi/180)
    output[1].data /=  6371000
    #output.data[0] /=  6371000*np.cos(meridional.lats[:2].mean()*np.pi/180)
    #output.data[-1] /=  6371000*np.cos(meridional.lats[-2:].mean()*np.pi/180)
    if variable.lats[0] in [-90, 90] :
        output[0].data[..., 0, :] =  output[0].data[..., 1, :]
        output[1].data[..., 0, :] =  output[1].data[..., 1, :]
    if variable.lats[-1] in [-90, 90] :
        output[0].data[..., -1, :] =  output[0].data[..., -2, :]
        output[1].data[..., -1, :] =  output[1].data[..., -2, :]
    return output

def eof1(self) :
    if '_eof1' not in self.__dict__ :
        self._eof1 = eof(self)
    return self._eof1

def eof(variable) :
    from eofs.standard import Eof
    wgts = np.cos(variable.lats*np.pi/180)**0.5
    solver = Eof(variable.data, weights = wgts[:, None])
    eof1 = solver.eofs(eofscaling=2, neofs=1)
    print solver.varianceFraction(neigs=1)[0]*100, '%'
    output = variable[0].empty()
    output.data = eof1[0]
    return output

def smooth(variable, window) :
    from axis import Axes, TimeAxis
    from variable import Variable
    if len(variable.shape) > 1 :
        raise NotImplementedError    
    try :
        variable.dts
    except :
        raise NotImplementedError    
    if window%2 == 0 :
        raise NotImplementedError    
    mask = np.ones(window)
    #mask[int(window/2)] = 1    
    mask /= window*1.0
    newAxes = Axes()
    newAxes['time'] = TimeAxis(variable.dts[int(window/2):-int(window/2)])
    return Variable(
            data = np.convolve(variable.data, mask, mode='valid'),
            axes = newAxes,
            metadata = variable.metadata)
    from eofs.standard import Eof
    wgts = np.cos(variable.lats*np.pi/180)**0.5
    solver = Eof(variable.data, weights = wgts[:, None])
    eof1 = solver.eofs(eofscaling=2, neofs=1)
    print solver.varianceFraction(neigs=1)[0]*100, '%'
    output = variable[0].empty()
    output.data = eof1[0]
    return output

    

    
