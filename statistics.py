
import numpy as np
from datetime import datetime

def cycle(self) :
	years = ((self.dts[-1] - self.dts[0]).days/365 + 1)
	start = self.dts[0]
	end = datetime(start.year + years, start.month, start.day)
	dts = [(dt - start).total_seconds()/3600 for dt in list(self.dts) + [end]] 
	deltas = np.diff(dts)
	span = deltas.sum()
	dts = np.array(dts[:-1])
	spatialize = [slice(None)] + [None]*len(self.shape[1:])
	temporalize = [None] + [slice(None)]*len(self.shape[1:])
	A = np.nanmean(self.data*
			(np.cos(2*np.pi*years*dts/span)*deltas)[spatialize]
			*2./span, 0)[temporalize]*self.shape[0]
	B = np.nanmean(self.data*
			(np.sin(2*np.pi*years*dts/span)*deltas)[spatialize]
			*2./span, 0)[temporalize]*self.shape[0]
	output = self.copy()
	output.data = A*np.cos(2*np.pi*years*dts/span)[spatialize] \
			+ B*np.sin(2*np.pi*years*dts/span)[spatialize]
	return output

def trend (self) :
	if self.dt.step.days < 365 :
		Y = self - self.cycle
	# no use in substracting the annual cycle for annual values
	else :
		Y = self
	beginning = Y.data[:-1]
	end = Y.data[1:]
	autocorr = ((beginning - beginning.mean(0))*(end - end.mean(0))/\
			(beginning.std(0)*end.std(0))).mean(0)
	# predictor
	X = np.array([(dt - Y.dts[0]).total_seconds()/3600 for dt in Y.dts])
	spatialize = [slice(None)] + [None]*len(Y.shape[1:])
	slope = ((Y - Y.mean('t'))*((X - X.mean())/X.var())[spatialize]).mean('t')
	residuals = Y.data - slope.data*(X - X.mean())[spatialize] - Y.data.mean(0)
	# taking autocorrelation into account
	effectiveSampleSize = len(Y.dts)*(1 - autocorr)/(1 + autocorr)
	varRes_2 = ((residuals - residuals.mean(0))**2).sum(0)/(effectiveSampleSize - 2)
	t_stat = slope.abs()*(((X - X.mean())**2).sum()/varRes_2)**0.5
	from scipy.stats import t as student
	# two sided student test p = 0.95 (check)
	t_level = student.ppf(0.975, effectiveSampleSize - 1)
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

def line(self) :
	X = np.array([(dt - self.dts[0]).total_seconds()/(3600*24*365.25) \
			for dt in self.dts])
	spatialize = [slice(None)] + [None]*len(self.slope.shape)
	temporalize = [None] + [slice(None)]*len(self.slope.shape)
	output = self.copy()
	output.data = self.slope.data[temporalize]*\
					(X - X.mean())[spatialize] \
			+ self.data.mean(0)[temporalize]
	return output

def sp2thck(self) :
	thickness = self.copy()*0
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
	

