
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
	A = (self.data*
			(np.cos(2*np.pi*years*dts/span)*deltas)[spatialize]
			*2./span).sum(0)[temporalize]
	B = (self.data*
			(np.sin(2*np.pi*years*dts/span)*deltas)[spatialize]
			*2./span).sum(0)[temporalize]
	output = self.copy()
	output.data = A*np.cos(2*np.pi*years*dts/span)[spatialize] \
			+ B*np.sin(2*np.pi*years*dts/span)[spatialize]
	return output

def trend (self) :
	Y = self - self.cycle
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
	t_stat = slope.abs()*((X - X.mean())**2).sum()**0.5/varRes_2
	from scipy.stats import t as student
	t_level = student.ppf(0.975, effectiveSampleSize - 1)
	return slope*24*365.25, t_stat > t_level

def slope(self) :
	if '_slope' not in self.__dict__ :
		self._slope, self._significance = self.trend
	return self._slope

def significance(self) :
	if '_significance' not in self.__dict__ :
		self._slope, self._significance = self.trend
	return self._significance

def line (self) :
	X = np.array([(dt - self.dts[0]).total_seconds()/(3600*24*365.25) \
			for dt in self.dts])
	spatialize = [slice(None)] + [None]*len(self.slope.shape)
	temporalize = [None] + [slice(None)]*len(self.slope.shape)
	output = self.copy()
	output.data = self.slope.data[temporalize]*\
					(X - X.mean())[spatialize] \
			+ self.data.mean(0)[temporalize]
	return output

def monthly(variable) :
	pass

def yearly(variable) :
	pass

def sp2thck(variable) :
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

