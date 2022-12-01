#! /usr/bin/env python 

"""Read and process .trk files containing cyclone tracks"""

import aa
import numpy as np
from datetime import datetime
from datetime import timedelta

time_step = 6
earthRadius = 6371000


def trk2latlon (x, y) :
    "Convert the orthographic (x, y) in .trk files to (lat, lon) in degrees"
    x = x-90
    y = 90-y
    lon = np.arctan2(y, x)*180/np.pi
    lat = np.arccos(np.sqrt(x**2+y**2)/90.0)*180/np.pi
    return lat, lon

def latlon2xy (lat, lon) :
        "Convert the orthographic (x, y) in .trk files to (lat, lon) in degrees"
        lat *= np.pi/180
        lon *= np.pi/180
        x = 90*(np.cos(lat)*np.cos(lon) + 1)
        y = 90*(1 - np.cos(lat)*np.sin(lon))
        return x, y

def gc_dist (lat1, lon1, lat2, lon2) :
    "Compute the great circle distance between two points on the Earth \
    (input in degrees ; output in meters)"
    if lat1==lat2 and lon1==lon2 :
        return 0
    else :
        return earthRadius*\
            np.arccos(
                np.sin(np.radians(lat1))*np.sin(np.radians(lat2)) +
                np.cos(np.radians(lat1))*np.cos(np.radians(lat2))
                        *np.cos(np.radians(lon2-lon1)))

def GC_DIST (lat1, lon1, lat2, lon2) :
    "Compute the great circle distance between two points on the Earth \
    (input in degrees ; output in meters)"
    return earthRadius*\
        np.arccos(
            np.sin(np.radians(lat1))*np.sin(np.radians(lat2)) +
            np.cos(np.radians(lat1))*np.cos(np.radians(lat2))
                    *np.cos(np.radians(lon2-lon1)))


class File :
    "Abstraction of the .trk files"
    def __init__(self, trk_file_path, no_mountains = True, year=None, lonlat=False) :
        if no_mountains :
            #elevation = aa.load('ice')
            #elevation = aa.open('/home/dufour/AcuerdaTe/topo/era_topo.nc')
            elevation = aa.open('era_topo.nc')
        trk_file = open(trk_file_path)
        if year == None :
            # most likely, this is a standard .trk file name
            self.year = int(trk_file_path.split('.')[-3])
        else :
            self.year = year
        try :
            # meaning of the first line is not clear : skip it
            float(trk_file.readline())
        except ValueError :
            # sometimes, the file starts right away, return to the beginning
            trk_file.seek(0, 0)
        self.list = []
        # keep track of the number of cyclone events
        self.event_nbr = 0
        # iterate over the file, from time stamp to time stamp
        time_stamp = trk_file.readline()
        # unless this is the end, create a new cyclone
        while time_stamp != '' :
            step_nbr = int(trk_file.readline())
            # call the Cyclone object constructor
            cy = Cyclone(time_stamp, step_nbr, trk_file, lonlat=lonlat)
            # check it fulfills the various criteria
            if step_nbr*time_step > 24*2 :
                if gc_dist(\
                            cy.lats[0], cy.lons[0],
                            cy.lats[-1], cy.lons[-1]
                        ) > 1e6 :
                        if no_mountains :
                            if elevation(
                                    lat = cy.lats[cy.prssrs.argmin()],
                                    lon = cy.lons[cy.prssrs.argmin()]
                                    ).data.mean() < 1500 :
                                # the mean() is a kludge in case data returns two values
                                self.list.append(cy)
                                self.event_nbr += step_nbr
                        else :
                            self.list.append(cy)
                            self.event_nbr += step_nbr
            # move to the next cyclone
            time_stamp = trk_file.readline()
        if no_mountains :
            elevation.close()
    
    def __getitem__(self, key) :
        return self.list[key]

    def __delitem__(self, key) :
        del self.list[key]
    
    def __len__(self) :
        return len(self.list)

    def plot_all (self, basemap = None, color = 'red', alpha = 1) :
        if basemap == None :
            from mpl_toolkits.basemap import Basemap
            basemap = Basemap(
                    projection = 'nplaea',
                    boundinglat = 30,
                    lon_0 = 0,
                    round = True)
            basemap.drawcoastlines()
        for cy in self :
            cy.plot(basemap = basemap, color = color, alpha = alpha)

    def _make_array(self) :
        self._lats = np.empty(self.event_nbr, dtype=float)
        self._lons = np.empty(self.event_nbr, dtype=float)
        self._prssrs = np.empty(self.event_nbr, dtype=float)
        self._times = np.empty(self.event_nbr, dtype=object)
        self._identities = np.empty(self.event_nbr, dtype=int)
        event_idx = 0
        for cy_idx, cy in enumerate(self) :
            self._lats[event_idx : event_idx + cy.step_nbr] = cy.lats
            self._lons[event_idx : event_idx + cy.step_nbr] = cy.lons
            self._prssrs[event_idx : event_idx + cy.step_nbr] = cy.prssrs
            self._identities[event_idx : event_idx + cy.step_nbr] = cy_idx
            self._times[event_idx : event_idx + cy.step_nbr] = cy.times
            event_idx += cy.step_nbr

    @property
    def lats(self) :
        if '_lats' not in self.__dict__ :
            self._make_array()
        return self._lats

    @property
    def lons(self) :
        if '_lons' not in self.__dict__ :
            self._make_array()
        return self._lons

    @property
    def prssrs(self) :
        if '_prssrs' not in self.__dict__ :
            self._make_array()
        return self._prssrs

    @property
    def times(self) :
        if '_times' not in self.__dict__ :
            self._make_array()
        return self._times

    @property
    def identities(self) :
        if '_identities' not in self.__dict__ :
            self._make_array()
        return self._identities

    def plot(self, time, basemap=None, *args, **kwargs) :
        "Draw the positions of all cyclones at a given instant"
        if basemap == None :
            from mpl_toolkits.basemap import Basemap
            basemap = Basemap(
                    projection = 'nplaea',
                    boundinglat = 30,
                    lon_0 = 0,
                    round = True)
            basemap.drawcoastlines()
        lats = self.lats[self.times==time]
        lons = self.lons[self.times==time]
        #for lat, lon in self.events[self.times==time] :
        return basemap.scatter(
                *(basemap(lons, lats) + args),
                **kwargs
                )
    
    def write(self, filePath) :
        import pickle
        with open(filePath, 'w') as outFile :
            pickle.dump(self, outFile)


class Cyclone :
    "Time sampled cyclone trajectory"
    def __init__(self, time_stamp, step_nbr, trk_file, lonlat) :
        # Initialized by the two first lines of the cyclone paragraph
        # i.e. : time stamp and number of time step_nbr
        # iterates over the following lines
        start = datetime.strptime(time_stamp, '  %d-%b-%Y %H:%M\n')
        # number of time steps
        self.step_nbr = step_nbr
        # prepare the arrays storing the cyclone's positions
        self.lats = np.zeros(self.step_nbr) 
        self.lons = np.zeros(self.step_nbr) 
        #steps = np.zeros(self.step_nbr) 
        self.prssrs = np.zeros(self.step_nbr) 
        # loop over the life of the cyclone
        for i in range(self.step_nbr) :
            split_string = trk_file.readline().split()
            if lonlat == True :
                lon, lat = float(split_string[0]), float(split_string[1])
            else :
                lat, lon = trk2latlon(float(split_string[0]), float(split_string[1]))
            self.lons[i] = lon%360
            self.lats[i] = lat
            #steps[i] = int(split_string[2])
            self.prssrs[i] = float(split_string[3])
        self.times = start + np.arange(step_nbr)*timedelta(hours=time_step)
    
    def plot (self, basemap = None, alpha=1, color='red') :
        if basemap == None :
            from mpl_toolkits.basemap import Basemap
            basemap = Basemap(
                    projection = 'nplaea',
                    boundinglat = 30,
                    lon_0 = 0,
                    round = True)
            basemap.drawcoastlines()
        """
        basemap.plot(*basemap(self.lons, self.lats),
                linewidth=2, color=color, alpha=0.3)
        """
        x, y = basemap(self.lons, self.lats)
        basemap.quiver(x[:-1], y[:-1], x[1:]-x[:-1], y[1:]-y[:-1],
            scale_units='xy', angles='xy', scale=1, width=3e-3, color=color, alpha=alpha)
    
    def _get_speeds(self) :
        self._zonals = np.empty(self.step_nbr)
        self._meridionals = np.empty(self.step_nbr)
        self._zonals[1:-1] = (self.lons[2:] - self.lons[:-2])%360*np.pi/180./(2.*time_step)
        self._zonals[0] = (self.lons[1] - self.lons[0])%360*np.pi/180./time_step
        self._zonals[-1] = (self.lons[-1] - self.lons[-2])%360*np.pi/180./time_step
        self._meridionals[1:-1] = (self.lats[2:] - self.lats[:-2])*np.pi/180./(2.*time_step)
        self._meridionals[0] = (self.lats[1] - self.lats[0])*np.pi/180./time_step
        self._meridionals[-1] = (self.lats[-1] - self.lats[-2])*np.pi/180./time_step
        self._zonals *= earthRadius*aa.cos(self.lats)
        self._meridionals *= earthRadius

    @property
    def zonals(self) :
        if '_zonals' not in self.__dict__ :
            self._get_speeds()
        return self._zonals

    @property
    def meridionals(self) :
        if '_meridionals' not in self.__dict__ :
            self._get_speeds()
        return self._meridionals
        

def load_raw(year, hemisphere='NH') :
    return File('/media/dufour/AcuerdaTe/cyclones/' + hemisphere + '/slp.'
            + str(year) + '.' + hemisphere + '.trk')
        
def load(year, hemisphere='NH') :
    import os
    filePath = '/home/dufoura/atelier/mechs/cy/trk/'
    fileName = 'slp.'+str(year)+'.NH.'
    if fileName + 'p' in os.listdir(filePath) :
        #import pickle
        #return pickle.load(open(filePath + fileName + 'p'))
        return aa.open(filePath + fileName + 'p')
    else :
        return File(filePath + fileName + 'trk')


