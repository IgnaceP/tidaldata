""" Script to define classes
    Class 1: TideData - object to store and manipulate water level data"""

# Import the necessary toolboxes and libraries
import numpy as np
import datetime
from datetime import datetime
import pandas as pd
import astral
from astral.sun import sun
import requests
import pandas as pd
import pickle
from datetime import datetime, timedelta
import Functions as fun
import matplotlib.pyplot as plt

# class to hold tide data
#-------------------------------------------------------------
class TideData:
    def __init__(self, station_name, time_series = [], tide_series = [], lat = -2.52230, lon = -79.733539, timezone = 'America/Guayaquil', location = 'Churute', country = 'Ecuador'):
        """

        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Class object to describe tide gauge data or in general water levels
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        :param station_name: Name of the station
        :param time_series: list of times (datetime objects)
        :param tide_series: water levels
        :param lat: latitude in wgs84
        :param lon: longitude in wgs84
        :param timezone: timezone, to get a list of all possible timezones: pytz.all_timezones
        :param location: location name
        :param country: name of the country

        default location parameters refer to the Churute reserve in the Guayas delta in Ecuador
        """
        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Class object to describe tide gauge data or in general water levels
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        :param station_name: Name of the station
        :param time_series: list of times (datetime objects)
        :param tide_series: water levels
        """

        self.name = station_name
        self.times = time_series
        self.tides = np.asarray(tide_series)

        self.lat = lat
        self.lon = lon
        self.country = country
        self.location = location
        self.timezone = timezone


        if len(self.times) > 0 and len(self.tides) == len(self.times):
            self.start_time = self.times[0]
            self.end_time = self.times[-1]

            self.calculateTideStatistics()

    def calculateTideStatistics(self):
        """
        Method to calcualte basic statics for the tide series
        :return: attributes are affected
        """

        self.tide_mean = np.nanmean(self.tides)
        self.tide_range = np.nanmax(self.tides) - np.nanmin(self.tides)
        self.tide_max = np.nanmax(self.tides)
        self.tide_min = np.nanmin(self.tides)

    def getTidesBasedOnPeriod(self, start_time, end_time):
        """
        Method to extract water levels from a given period
        :param start_time: datetime object with the starting date of the requested period
        :param end_time: datetime object with the ending date of the requested period
        :return: list of times and list of tides (lengths are equal)
        """

        start = np.argmin((np.asarray([t.timestamp() for t in self.times])-start_time.timestamp())**2)
        end = np.argmin((np.asarray([t.timestamp() for t in self.times])-end_time.timestamp())**2)

        return self.times[start:end],self.tides[start:end]

    def getTide(self, date):
        """
        Method to extract a water level at a certain date. If the requested timing is none of the timings in
        the times series, the water level be interpolated from the two most closest timings.
        :param date: datetime object with the requested date and time
        :return: requested water level
        """
        """ method to derive the tidal value at a specific moment entered as a datetime """

        date_ts = date.timestamp()
        times_np = np.asarray([t.timestamp() for t in self.times])

        if len(np.where(times_np == date_ts)[0]) >0 :
            print(date_ts)
            requested_tide= self.tides[np.where(times_np == date_ts)[0][0]]

        else:

            times_diff = times_np - date_ts

            int_bot = np.where(times_diff < 0, times_diff, -np.inf).argmax()
            int_top = np.where(times_diff > 0, times_diff, np.inf).argmin()

            time_bot = self.times[int_bot]
            time_top = self.times[int_top]

            diff_top = (time_top - time_bot).total_seconds()
            diff_date = (date - time_bot).total_seconds()

            requested_tide = np.interp(diff_date, [0, diff_top],[self.tides[int_bot],self.tides[int_top]])

        return requested_tide

    def getLows(self, start_time = 0, end_time = 0, window_size = 50):
        """
        Method to retrieve low water (both times and water levels)
        :param start_time: datetime object of start of the requested period
        :param end_time: datetime object of end of the requested period
        :param window_size: parameter to define peaks
        :return:  times and tides series with the times and water levels of the requested lows
        """
        if start_time == 0:
            start_time = self.start_time
        if end_time == 0:
            end_time = self.end_time

        times, tides = self.getTidesBasedOnPeriod(start_time, end_time)
        mean_tide = np.nanmean(tides)

        one_hour = datetime(2000,1,1,2)-datetime(2000,1,1,1)

        Lows_tides = []
        Lows_times = []

        for i in range(window_size, len(tides) - window_size):
            middle = tides[i]
            if middle < mean_tide:
                left = np.nanmin(tides[i - window_size:i])
                right = np.nanmin(tides[i + 1:i + window_size + 1])

                if middle <= left and middle <= right:
                    if len(Lows_times) > 0:
                        if times[i]-Lows_times[-1] > one_hour:
                            Lows_tides.append(middle)
                            Lows_times.append(times[i])
                    else:
                        Lows_tides.append(middle)
                        Lows_times.append(times[i])

        return Lows_times, Lows_tides

    def getPeaks(self, start_time = 0, end_time = 0, window_size = 50, tresh = -999):
        """
        Method to retrieve high water (both times and water levels)
        :param start_time: datetime object of start of the requested period
        :param end_time: datetime object of end of the requested period
        :param window_size: parameter to define peaks
        :param tresh: minimum value for a peak
        :return:  times and tides series with the times and water levels of the requested peaks
        """
        if start_time == 0:
            start_time = self.start_time
        if end_time == 0:
            end_time = self.end_time

        times, tides = self.getTidesBasedOnPeriod(start_time, end_time)
        mean_tide = np.nanmean(tides)
        Peaks_tides = []
        Peaks_times = []

        one_hour = datetime(2000,1,1,2)-datetime(2000,1,1,1)

        for i in range(window_size,len(tides)-window_size):
            middle = tides[i]
            if middle > mean_tide:
                left = np.nanmax(tides[i-window_size:i])
                right = np.nanmax(tides[i+1:i+window_size+1])

                if middle >= left and middle >= right:
                    if len(Peaks_times) > 0:
                        if times[i]-Peaks_times[-1] > one_hour:
                            Peaks_tides.append(middle)
                            Peaks_times.append(times[i])
                    else:
                        if middle > tresh:
                            Peaks_tides.append(middle)
                            Peaks_times.append(times[i])

        return Peaks_times, Peaks_tides

    def standardize(self, print_mean = True):
        """
        Method to standardize all water levels to its mean.
        Original water levels are stored as a class attribute 'tides_original'
        """

        self.tides_original = self.tides.copy()
        self.tides -= self.tide_mean

        if print_mean:
            print('Mean water level: %.3f m' % self.tide_mean)

    def toLiquidBoundaryFile(self, start_time = 0, end_time = 0, output_path = 'LiquidBoundaryFile.lqd', base_level = 0):
        """
        Method to export a tidal series to a liquid boundary file for the TELEMAC 2D software
        :param start_time: datetime object of start of the requested period
        :param end_time: datetime object of end of the requested period
        :param output_path: filepath to store the newly generated liquid boundary file (no required extension but .lqd is recommended)
        :param base_level: reference level of the tides to add to all water levels
        :return: saves a .lqd file in the apointed location
        """

        if start_time == 0:
            start_time = self.start_time
        if end_time == 0:
            end_time = self.end_time

        times, tides = self.getTidesBasedOnPeriod(start_time, end_time)

        tides_upd = []
        for t in tides:
            tides_upd.append(t+base_level)
        tides = tides_upd

        dT = [0]
        for i in range(1,len(times)):
            dt = times[i]-times[0]
            dt_s = dt.total_seconds()
            dT.append(dt_s)

        f = open(output_path, "w+")
        f.write('# Liquid Boundary File from the period ' + str(self.start_time) + ' to ' + str(self.end_time))
        f.write('\n# One boundary managed')
        f.write('\n#')
        f.write('\nT        SL(1)\n')
        f.write('s        m\n')
        for i in range(len(dT)):
            line = '%d' % (dT[i])
            while len(line)<9:
                line += ' '
            line += str(tides[i])+'\n'
            f.write(line)

        f.close()

    def getSunRisesAndSets(self):
        """
        Method to add two attribute lists to the object: times of sunrises and sunsets (default is for Churute in the Guayas delta, Ecuador)
        """

        loc = astral.LocationInfo((self.location, self.country, self.lat, self.lon, self.timezone))

        Sunsets = []
        Sunrises = []

        for t in self.times:
            s = sun(loc.observer, date=t)
            if s['sunset'].timestamp() != Sunsets[-1]:
                Sunsets.append(s['sunset'].timestamp())
                Sunrises.append(s['sunrise'].timestamp())

        Sunsets_or = np.unique(Sunsets)
        Sunrises_or = np.unique(Sunrises)

        Sunsets = []
        Sunrises = []

        for s in Sunsets_or:
            Sunsets.append(datetime.fromtimestamp(s))
        for s in Sunrises_or:
            Sunrises.append(datetime.fromtimestamp(s))

        self.sunsets = Sunsets
        self.sunrises = Sunrises

    def save(self, pathname):
        """
        Method to save data as a pickle
        :param pathname: directory and filename to save as
        :return:
        """

        with open(pathname, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

        """
        df = pd.DataFrame({'Name': self.name, 'Times': self.times, 'Tides': self.tides})
        df.to_pickle(pathname)
        """

    @staticmethod
    def load(pathname):
        """
        Method to load data from a pickle
        :param pathname: directory and filename to load
        :return:
        """

        with open(pathname, 'rb') as input:
            TideDataInstance = pickle.load(input)

        return TideDataInstance

    def loadFromPanda(self, pathname):
        """
        Method to load data from a pickled panda
        :param pathname: directory and filename to load
        :return:
        """

        df = pd.read_pickle(pathname)

        station_name = df.Name[0]
        time_series = list(df.Times)
        tide_series = list(df.Tides)

        self.name = station_name
        self.times = time_series
        self.tides = np.asarray(tide_series)

        if len(self.times) > 0 and len(self.tides) == len(self.times):
            self.start_time = min(self.times)
            self.end_time = self.times[-1]

            self.calculateTideStatistics()

    def loadRuggedTrollData(self, pathname_sensor, pathname_atm):
        """
        Method to populate an empty TideData object
        :param pathname_sensor: name of the path referring to the htm file of the sensor which measured hydrostatic pressure
        :param pathname_atm: name of the path referring to the htm file of the sensor which measured atmospheric pressure
        :return:
        """

        # Load atmospheric pressure data into panda dataframe
        #------------------------------------------------------------------------------------
        if pathname_atm[0] != '/': pathname_atm = '/' + pathname_atm
        url = 'file://' + pathname_atm
        data = pd.read_html(url, skiprows=27)
        df = data[0].dropna()
        col = df.columns
        df = df.rename(columns={col[0]: "Time", col[1]: 'P', col[2]: 'T'})

        # transform time format
        Time_dt = []
        for t in df.Time:
            year, month, day= int(t[0:4]), int(t[5:7]), int(t[8:10])
            hr, min, sec, msec = int(t[11:13]), int(t[14:16]), int(t[17:19]), int(int(t[20:]) * 1e3)
            Time_dt.append(datetime(year, month, day, hr, min, sec, msec))
        df.Time = Time_dt

        Atm = df

        # Load hydrostatic pressure from submerged sensor into panda dataframe
        #------------------------------------------------------------------------------------
        if pathname_sensor[0] != '/': pathname_sensor = '/' + pathname_sensor
        url = 'file://'+pathname_sensor
        data = pd.read_html(url, skiprows=27)
        df = data[0].dropna()
        col = df.columns
        df = df.rename(columns={col[0]: "Time", col[1]: 'P', col[2]: 'T'})

        # transform time format
        Time_dt = []
        for t in df.Time:
            year, month, day= int(t[0:4]), int(t[5:7]), int(t[8:10])
            hr, min, sec, msec = int(t[11:13]), int(t[14:16]), int(t[17:19]), int(int(t[20:]) * 1e3)
            Time_dt.append(datetime(year, month, day, hr, min, sec, msec))
        df.Time = Time_dt

        df.Time = Time_dt
        Hydro = df

        # interpolate atmospheric pressures to the times from the hydro sensor
        #------------------------------------------------------------------------------------
        Atm_P_hydrotimes = np.interp(Hydro['Time'], Atm['Time'], Atm['P'])

        # correct for atmospheric P
        #------------------------------------------------------------------------------------
        P = np.asarray(Hydro['P']) - Atm_P_hydrotimes
        T = []
        for t in list(Hydro['Time']):
            T.append(datetime(t.year, t.month, t.day, t.hour, t.minute, t.second))

        # conversion from hydrostatic pressure to water depth
        #------------------------------------------------------------------------------------
        rho = 996.783  # density of water in kg/m3 at average recorded water temperature
        g = 9.80665  # gravitation accelaration
        D = P * 1e5 / (rho * g)  # in m

        self.times = T
        self.tides = np.asarray(D)

        self.start_time = T[0]
        self.end_time = T[-1]

        self.calculateTideStatistics()

    def loadFromTextFile(self, pathname_file, seperator = "\t"):
        """
        Method to populate an empty TideData object based on values from a text file.
        The columns should be ordered: year, month, day, hour, minute, second, waterlevel
        :param pathname_file: Directory of the text file
        :param seperator: seperator between columns in the txt file, default is a tab
        :return:
        """
        df = pd.read_csv(pathname_file, sep=seperator)
        Times = []
        WaterLevels = []
        for i in range(len(df)):
            year = df[df.columns[0]][i]
            month = df[df.columns[1]][i]
            day = df[df.columns[2]][i]
            hr = df[df.columns[3]][i]
            if len(df.columns) >= 7:
                min = df[df.columns[4]][i]
                sec = df[df.columns[5]][i]
                T = datetime(year, month, day, hr, min, sec)
            else: T = datetime(year, month, day, hr)
            Times.append(T)

            wl = df[df.columns[-1]][i]
            if wl == 'NaN':
                WaterLevels.append(np.nan)
            else:
                try:
                    WaterLevels.append(float(wl))
                except:
                    WaterLevels.append(np.nan)
        WaterLevels = [wl for _, wl in sorted(zip(Times, WaterLevels))]
        Times = sorted(Times)

        # remove all first lines with nan
        number = False
        while number == False:
            if np.isnan(WaterLevels[0]):
                del WaterLevels[0]; del Times[0]
            else:
                number = True

        # remove all last lines with nan
        number = False
        while number == False:
            if np.isnan(WaterLevels[-1]):
                del WaterLevels[-1]; del Times[-1]
            else:
                number = True

        # appoint values to attribute lists

        self.times = Times
        self.tides = np.asarray(WaterLevels)

        self.start_time = Times[0]
        self.end_time = Times[-1]

        self.calculateTideStatistics()

    def scrapeFromINOCAR(self, station_name = 'instance name', start_time = 0, end_time = 0):
        """
        Method to populate an empty tideDataProject based on data from the INOCAR website
        :param station_name: name of the station. Pick out of the following list:

                Palma Real          San Lorenzo             Esmeraldas
                Muisne              Bahia de Caraquez       Manta
                Puerto Lopez        Monteverde              La Libertad
                Anconcito           Data de Posorja         Posorja
                Puerto Nuevo        Guayaquil Rio           Puna
                Puerto Bolivar      Isla Baltra             Isla Isabela
                Isla Santa Cruz     Isla San Cristobal

        :param start_time: starting date of requested time (datetime-object)
        :param end_time: ending date of requested time (datetime-object)
        :return:
        """

        # Default the station name
        if station_name == 'instance name':
            station_name = self.name

        # Default time values
        if start_time == 0:
            start_time = self.start_time
        if end_time == 0:
            end_time = self.end_time
        dt = end_time - start_time

        # Make a date list
        Dates = []
        for i in range(0, dt.days+1, 3):
            t = start_time + timedelta(days=i)
            Dates.append(str(t)[:10])

        # Request the data from the url
        url = "https://www.inocar.mil.ec/mareas/diario_mareas.php"

        # Station IDs
        Station_IDs = {'Palma Real': '65', 'San Lorenzo': '61', 'Esmeraldas': '377', 'Muisne': '392', 'Bahia de Caraquez': '378',
                       'Manta': '379', 'Puerto Lopez': '393', 'Monteverde': '397', 'La Libertad': '71','Anconcito':'399',
                       'Data de Posorja': '381', 'Posorja': '382', 'Puerto Nuevo': '383', 'Guayaquil Rio': '374', 'Puna': '375',
                       'Puerto Bolivar': '384', 'Isla Baltra': '385', 'Isla Isabela': '394', 'Isla Santa Cruz': '30', 'Isla San Cristobal': '387'}

        station_id = Station_IDs[station_name]

        Times, WaterLevels = [], []

        t = 0

        print('Scraping data from the INOCAR servers...')
        for date in Dates:

            t +=1
            Functions.printProgressBar(t, len(Dates))

            params = {"cp": station_id, "fecha": date}
            r = requests.get(url=url, params=params)

            df = pd.read_html(r.text)

            for i in range(3):
                df_day = df[i]
                hrs = df_day[df_day.columns[0]][1:]
                hrs = [h for h in hrs if h != 'ND']
                lvls = list(df_day[df_day.columns[1]][1:])
                lvls = [float(l[:4]) for l in lvls if l != 'ND']

                year = int(date[:4])
                month = int(date[5:7])
                day = int(date[8:10])
                for h in hrs:
                    hr = int(h[:2])
                    min = int(h[3:])
                    Times.append(datetime(year, month, day, hr, min) + (i - 1) * timedelta(days=1))

                WaterLevels += lvls

        # appoint values to attribute lists

        self.times = Times
        self.tides = np.asarray(WaterLevels)

        self.start_time = Times[0]
        self.end_time = Times[-1]

        self.calculateTideStatistics()
        print('Scraped!')

    def scrapeFromDHN(self, station_name = "instance name", start_time = 0, end_time = 0):
        """
        Method to populate an empty tideDataProject based on data from the DHN website (Peruvian Navy)
        :param station_name: name of the station. Overview at https://www.dhn.mil.pe/secciones/mareas/index.php?f=2015-08-13
        :param start_time: starting date of requested time (datetime-object)
        :param end_time: ending date of requested time (datetime-object)
        :return:
        """

        # Default the station name
        if station_name == 'instance name':
            station_name = self.name

        # Default time values
        if start_time == 0:
            start_time = self.start_time
        if end_time == 0:
            end_time = self.end_time
        dt = end_time - start_time

        # Make a date list
        Dates = []
        for i in range(0, dt.days+1, 2):
            t = start_time + timedelta(days=i)
            Dates.append(t)

        # intialize lists to store the times and water levels
        Times, WaterLevels = [], []

        # Request the data from the url
        for date in Dates:
            # convert datetime to string
            year = str(date.year)
            month = str(date.month)
            if len(month) == 1: month = '0' + month
            day = str(date.day)
            if len(day) == 1: day = '0' + day
            date_str = '%s-%s-%s' % (year, month, day)

            # build url
            url = "https://www.dhn.mil.pe/secciones/mareas/res.php?f=%s&p=%s" % (date_str, station_name)

            # send a get request to the url
            r = requests.get(url=url)
            # convert to dataframe
            df = pd.read_html(r.text)[0]
            # rename columns
            df.columns = {'Time', 'Waterlevel'}

            # loop over all lins of the obtained dataframe
            for i in range(len(df.Time)):
                line = df.Time[i]
                if len(df.Time[i]) >=5:
                    if line[4] == '-':
                        # get the date
                        d = df.Time[i]
                        year = int(d[:4])
                        month = int(d[5:7])
                        day = int(d[8:10])
                    elif line[2] == ':':
                        # get the time
                        t = df.Time[i]
                        hour = int(t[:2])
                        min = int(t[3:5])
                        sec = int(t[6:8])
                        t = datetime(year, month, day, hour, min, sec)
                        print(t)
                        Times.append(t)
                        # get the waterlevel (in m)
                        wl = df.Waterlevel[i]
                        wl = wl.split(' ')
                        wl = int(wl[0]) / 100
                        WaterLevels.append(wl)

        self.times = Times
        self.tides = np.asarray(WaterLevels)

        self.start_time = Times[0]
        self.end_time = Times[-1]

        self.calculateTideStatistics()
        print('Scraped!')

    def merge(self, path):
        """
        Method to merge an existing tidal data set instance into the active one
        :param path: path to .tid file to merge
        :return:
        """

        t2 = self.load(path)

        t1_start_time = self.start_time
        t1_end_time = self.end_time
        t2_start_time = t2.start_time
        t2_end_time = t2.end_time

        self.start_time = min(t1_start_time, t2_start_time)
        self.end_time = max(t1_end_time, t2_end_time)

        if t1_start_time < t2_start_time:
            self.times += t2.times
            self.tides = np.concatenate((self.tides, t2.tides))
        else:
            self.times = t2.times + self.times
            self.tides = np.concatenate((t2.tides, self.tides))

        self.calculateTideStatistics()

class Functions:
    def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
        """
        Call in a loop to create terminal progress bar
        source: https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
        # Print New Line on Complete
        if iteration == total:
            print()

    def linkHWLs(TideData1, TideData2, rel_timing = None, time_window = timedelta(hours = 2), window_size = [50,50], start_time = 0, end_time = 0):
        """
        Method to link the high water levels of two locations
        :param TideData1: Tide data object
        :param TideData2: Tide data object
        :param rel_timing: HWLs in tidadata2 are always 'later', 'earlier' or not defined (default)
                            The peaks of T1 are earlier/later than the peaks of T2.
        :param time_window: Time window in which two HWLs should lay to be linked (should be timedelta instance)
        :return: 2 Tidedata objects with the same number of times and tides (!!! these Tidedata objects only contain the peaks)
        """

        if start_time == 0:
            start_time = np.max([TideData1.start_time, TideData2.start_time]) - time_window
        if end_time == 0:
            end_time = np.min([TideData1.end_time, TideData2.end_time]) + time_window

        T1_Peaks_t, T1_Peaks_d = TideData1.getPeaks(start_time= start_time, end_time= end_time, window_size= window_size[0])
        T2_Peaks_t, T2_Peaks_d = TideData2.getPeaks(start_time= start_time, end_time= end_time, window_size= window_size[1])

        T1_t_np = np.asarray(T1_Peaks_t)
        T2_t_np = np.asarray(T2_Peaks_t)

        zero = np.timedelta64(0, 's')

        T1_t_linked, T1_d_linked = [], []
        T2_t_linked, T2_d_linked = [], []

        i = 0
        for t in T1_t_np:
            T1_d = T1_Peaks_d[i]
            i += 1

            # Calculate the differences between the times of T2 and the selected time of T1
            dt = t - T2_t_np

            # Get the close values according to the relative timing parameter
            if rel_timing == 'Later': dt = T2_t_np[(dt > zero) * (dt < time_window)]
            elif rel_timing == 'Earlier': dt = T2_t_np[(dt < zero) * (abs(dt) < time_window)]
            else: dt = T2_t_np[(abs(dt) < time_window)]

            if dt:
                # if there is a link, add to lists
                d = np.where(T2_t_np == dt)[0][0]
                T2_d = T2_Peaks_d[d]

                # populate T1
                T1_t_linked.append(t)
                T1_d_linked.append(T1_d)

                # populate T2
                T2_t_linked.append(dt)
                T2_d_linked.append(T2_d)

        T1_result = TideData(TideData1.name, time_series= T1_t_linked, tide_series= T1_d_linked,
                             lat = TideData1.lat, lon= TideData1.lon, timezone= TideData1.timezone,
                             country = TideData1.country, location = TideData1.location)

        T2_result = TideData(TideData2.name, time_series= T2_t_linked, tide_series= T2_d_linked,
                             lat = TideData2.lat, lon= TideData2.lon, timezone= TideData2.timezone,
                             country = TideData2.country, location = TideData2.location)


        return T1_result, T2_result
