#
# Race Capture App
#
# Copyright (C) 2014-2017 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

import json
from copy import copy
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from kivy.logger import Logger
from distutils.version import StrictVersion

RCP_COMPATIBLE_MAJOR_VERSION = 2
RCP_MINIMUM_MINOR_VERSION = 8

class BaseChannel(object):
    def __init__(self, **kwargs):
        self.name = 'Unknown'
        self.units = ''
        self.min = -1000
        self.max = 1000
        self.precision = 0
        self.sampleRate = 0
        self.stale = False

    def fromJson(self, json_dict):
        self.name = json_dict.get('nm', self.name)
        self.units = json_dict.get('ut', self.units)
        self.min = json_dict.get('min', self.min)
        self.max = json_dict.get('max', self.max)
        self.precision = json_dict.get('prec', self.precision)
        self.sampleRate = json_dict.get('sr', self.sampleRate)

    def appendJson(self, json_dict):
        json_dict['nm'] = self.name
        json_dict['ut'] = self.units
        json_dict['min'] = self.min
        json_dict['max'] = self.max
        json_dict['prec'] = self.precision
        json_dict['sr'] = self.sampleRate

    def equals(self, other):
        return other is not None and (
                    self.name == other.name and
                    self.units == other.units and
                    self.min == other.min and
                    self.max == other.max and
                    self.sampleRate == other.sampleRate)



class ScalingMapException(Exception):
    pass

class ScalingMap(object):
    SCALING_MAP_POINTS = 5
    SCALING_MAP_MIN_VOLTS = 0
    def __init__(self, **kwargs):
        points = ScalingMap.SCALING_MAP_POINTS
        raw = []
        scaled = []
        for i in range(points):
            raw.append(0)
            scaled.append(0)
        self.points = points
        self.raw = raw
        self.scaled = scaled

    def fromJson(self, mapJson):
        rawJson = mapJson.get('raw', None)
        if rawJson:
            i = 0
            for rawValue in rawJson:
                self.raw[i] = rawValue
                i += 1

        scaledJson = mapJson.get('scal', None)
        if scaledJson:
            i = 0
            for scaledValue in scaledJson:
                self.scaled[i] = scaledValue
                i += 1

    def toJson(self):
        mapJson = {}
        rawBins = []
        scaledBins = []
        for rawValue in self.raw:
            rawBins.append(rawValue)

        for scaledValue in self.scaled:
            scaledBins.append(scaledValue)

        mapJson['raw'] = rawBins
        mapJson['scal'] = scaledBins

        return mapJson

    def getVolts(self, mapBin):
        return self.raw[mapBin]

    def setVolts(self, map_bin, value):
        try:
            value = float(value)
        except:
            raise ScalingMapException("Value must be numeric")
        if map_bin < ScalingMap.SCALING_MAP_POINTS - 1:
            next_value = self.raw[map_bin + 1]
            if value > next_value:
                raise ScalingMapException("Must be less or equal to {}".format(next_value))
        if map_bin > 0:
            prev_value = self.raw[map_bin - 1]
            if value < prev_value:
                raise ScalingMapException("Must be greater or equal to {}".format(prev_value))
        if value < ScalingMap.SCALING_MAP_MIN_VOLTS:
            raise ScalingMapException('Must be greater than {}'.format(ScalingMap.SCALING_MAP_MIN_VOLTS))

        self.raw[map_bin] = value

    def getScaled(self, mapBin):
        try:
            return self.scaled[mapBin]
        except IndexError:
            Logger.error('ScalingMap: Index error getting scaled value')
            return 0

    def setScaled(self, mapBin, value):
        try:
            self.scaled[mapBin] = float(value)
        except IndexError:
            Logger.error('ScalingMap: Index error setting bin')

ANALOG_SCALING_MODE_RAW = 0
ANALOG_SCALING_MODE_LINEAR = 1
ANALOG_SCALING_MODE_MAP = 2

class AnalogChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(AnalogChannel, self).__init__(**kwargs)
        self.scalingMode = 0
        self.linearScaling = 0
        self.linearOffset = 0
        self.alpha = 0
        self.scalingMap = ScalingMap()

    def fromJson(self, json_dict):
        if json_dict:
            super(AnalogChannel, self).fromJson(json_dict)
            self.scalingMode = json_dict.get('scalMod', self.scalingMode)
            self.linearScaling = json_dict.get('scaling', self.linearScaling)
            self.linearOffset = json_dict.get('offset', self.linearOffset)
            self.alpha = json_dict.get('alpha', self.alpha)
            scaling_map_json = json_dict.get('map', None)
            if scaling_map_json:
                self.scalingMap.fromJson(scaling_map_json)
            self.stale = False

    def toJson(self):
        json_dict = {}
        super(AnalogChannel, self).appendJson(json_dict)
        json_dict['scalMod'] = self.scalingMode
        json_dict['scaling'] = self.linearScaling
        json_dict['offset'] = self.linearOffset
        json_dict['alpha'] = self.alpha
        json_dict['map'] = self.scalingMap.toJson()
        return json_dict

DEFAULT_ANALOG_CHANNEL_COUNT = 8

class AnalogConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = DEFAULT_ANALOG_CHANNEL_COUNT
        self.channels = []
        self.build_channels()

    def fromJson(self, analogCfgJson, capabilities=None):
        if capabilities:
            self.channelCount = capabilities.channels.analog
            self.build_channels()

        for i in range(self.channelCount):
            analogChannelJson = analogCfgJson.get(str(i), None)
            if analogChannelJson:
                self.channels[i].fromJson(analogChannelJson)

    def toJson(self):
        analogCfgJson = {}
        for i in range(self.channelCount):
            analogChannel = self.channels[i]
            analogCfgJson[str(i)] = analogChannel.toJson()
        return {'analogCfg':analogCfgJson}

    def build_channels(self):
        initialized_channel_count = len(self.channels)
        required_channel_count = self.channelCount

        if initialized_channel_count == required_channel_count:
            return
        else:
            # Probably got a new capabilities, make a new channels array
            self.channels = []
            for i in range(required_channel_count):
                self.channels.append(AnalogChannel())

    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False

    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value

class ImuChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(ImuChannel, self).__init__(**kwargs)
        self.mode = 0
        self.chan = 0
        self.zeroValue = 0
        self.alpha = 0

    def fromJson(self, json_dict):
        if json_dict:
            super(ImuChannel, self).fromJson(json_dict)
            self.mode = json_dict.get('mode', self.mode)
            self.chan = json_dict.get('chan', self.chan)
            self.zeroValue = json_dict.get('zeroVal', self.zeroValue)
            self.alpha = json_dict.get('alpha', self.alpha)
            self.stale = False

    def toJson(self):
        json_dict = {}
        super(ImuChannel, self).appendJson(json_dict)
        json_dict['mode'] = self.mode
        json_dict['chan'] = self.chan
        json_dict['zeroVal'] = self.zeroValue
        json_dict['alpha'] = self.alpha
        return json_dict

IMU_CHANNEL_COUNT = 6
IMU_ACCEL_CHANNEL_IDS = [0, 1, 2]
IMU_GYRO_CHANNEL_IDS = [3, 4, 5]
IMU_MODE_DISABLED = 0
IMU_MODE_NORMAL = 1
IMU_MODE_INVERTED = 2

class ImuConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = IMU_CHANNEL_COUNT
        self.channels = []

        for i in range(self.channelCount):
            self.channels.append(ImuChannel())

    def fromJson(self, imuConfigJson):
        for i in range (self.channelCount):
            imuChannelJson = imuConfigJson.get(str(i), None)
            if imuChannelJson:
                self.channels[i].fromJson(imuChannelJson)

    def toJson(self):
        imuCfgJson = {}
        for i in range (self.channelCount):
            imuChannel = self.channels[i]
            imuCfgJson[str(i)] = imuChannel.toJson()

        return {'imuCfg':imuCfgJson}


    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False

    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value

class LapConfigChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(LapConfigChannel, self).__init__(**kwargs)

    def fromJson(self, json_dict):
        super(LapConfigChannel, self).fromJson(json_dict)

    def toJson(self):
        json_dict = {}
        super(LapConfigChannel, self).appendJson(json_dict)
        return json_dict

class LapConfig(object):
    DEFAULT_PREDICTED_TIME_SAMPLE_RATE = 5
    def __init__(self, **kwargs):
        self.stale = False
        self.lapCount = LapConfigChannel()
        self.lapTime = LapConfigChannel()
        self.predTime = LapConfigChannel()
        self.sector = LapConfigChannel()
        self.sectorTime = LapConfigChannel()
        self.elapsedTime = LapConfigChannel()
        self.currentLap = LapConfigChannel()

    def primary_stats_enabled(self):
        return (self.lapCount.sampleRate > 0 or
            self.lapTime.sampleRate > 0 or
            self.sector.sampleRate > 0 or
            self.sectorTime.sampleRate > 0 or
            self.elapsedTime.sampleRate > 0 or
            self.currentLap.sampleRate > 0)

    def set_primary_stats(self, rate):
        self.lapCount.sampleRate = rate
        self.lapTime.sampleRate = rate
        self.sector.sampleRate = rate
        self.sectorTime.sampleRate = rate
        self.elapsedTime.sampleRate = rate
        self.currentLap.sampleRate = rate
        self.stale = True

    def predtime_stats_enabled(self):
        return self.predTime.sampleRate > 0

    def fromJson(self, jsonCfg):
        if jsonCfg:
            lapCount = jsonCfg.get('lapCount')
            if lapCount:
                self.lapCount.fromJson(lapCount)

            lapTime = jsonCfg.get('lapTime')
            if lapTime:
                self.lapTime.fromJson(lapTime)

            predTime = jsonCfg.get('predTime')
            if predTime:
                self.predTime.fromJson(predTime)

            sector = jsonCfg.get('sector')
            if sector:
                self.sector.fromJson(sector)

            sectorTime = jsonCfg.get('sectorTime')
            if sectorTime:
                self.sectorTime.fromJson(sectorTime)

            elapsedTime = jsonCfg.get('elapsedTime')
            if elapsedTime:
                self.elapsedTime.fromJson(elapsedTime)

            currentLap = jsonCfg.get('currentLap')
            if currentLap:
                self.currentLap.fromJson(currentLap)

            self.sanitize_config()

            self.stale = False

    """some config files are sneaking in bad values and they're making
    it up to the firmware config. UI doesn't allow editing of all of these
    values b/c we simplified the interface, so we need to compensate.
    This function will sanitize the configuration upon loading.

    Yes, this is a hack, for now. LapStats will change in the future
    when we break the API with a major version. When that breaks, lapstats
    will be updated to have only have two boolean values:
    stats_enabled and pred_time_enabled, and this sanitize function can
    be removed.

    Channel configuration data will not be editable.

    TODO: remove this sanitization upon 3.x API
    """
    def sanitize_config(self):
        self.lapCount.name = "LapCount"
        self.lapCount.units = ""
        self.lapCount.min = 0
        self.lapCount.max = 0
        self.lapCount.precision = 0

        self.lapTime.name = "LapTime"
        self.lapTime.units = "Min"
        self.lapTime.min = 0
        self.lapTime.max = 0
        self.lapTime.precision = 4

        self.sector.name = "Sector"
        self.sector.units = ""
        self.sector.min = 0
        self.sector.max = 0
        self.sector.precision = 0

        self.sectorTime.name = "SectorTime"
        self.sectorTime.units = "Min"
        self.sectorTime.min = 0
        self.sectorTime.max = 0
        self.sectorTime.precision = 4

        self.predTime.name = "PredTime"
        self.predTime.units = "Min"
        self.predTime.min = 0
        self.predTime.max = 0
        self.predTime.precision = 4

        self.elapsedTime.name = "ElapsedTime"
        self.elapsedTime.units = "Min"
        self.elapsedTime.min = 0
        self.elapsedTime.max = 0
        self.elapsedTime.precision = 4

        self.currentLap.name = "CurrentLap"
        self.currentLap.units = ""
        self.currentLap.min = 0
        self.currentLap.max = 0
        self.currentLap.precision = 0

    def toJson(self):
        lapCfgJson = {'lapCfg':{
                                  'lapCount': self.lapCount.toJson(),
                                  'lapTime': self.lapTime.toJson(),
                                  'predTime': self.predTime.toJson(),
                                  'sector': self.sector.toJson(),
                                  'sectorTime': self.sectorTime.toJson(),
                                  'elapsedTime': self.elapsedTime.toJson(),
                                  'currentLap': self.currentLap.toJson()
                                  }
                        }
        return lapCfgJson

class GpsConfig(object):
    GPS_QUALITY_NO_FIX = 0
    GPS_QUALITY_2D = 1
    GPS_QUALITY_3D = 2
    GPS_QUALITY_3D_DGNSS = 3
    DEFAULT_GPS_SAMPLE_RATE = 10

    def __init__(self, **kwargs):
        self.stale = False
        self.sampleRate = GpsConfig.DEFAULT_GPS_SAMPLE_RATE
        self.positionEnabled = False
        self.speedEnabled = False
        self.distanceEnabled = False
        self.altitudeEnabled = False
        self.satellitesEnabled = False
        self.qualityEnabled = False
        self.DOPEnabled = False

    def fromJson(self, json):
        if json:
            self.sampleRate = int(json.get('sr', self.sampleRate))
            self.positionEnabled = int(json.get('pos', self.positionEnabled))
            self.speedEnabled = int(json.get('speed', self.speedEnabled))
            self.distanceEnabled = int(json.get('dist', self.distanceEnabled))
            self.altitudeEnabled = int(json.get('alt', self.altitudeEnabled))
            self.satellitesEnabled = int(json.get('sats', self.satellitesEnabled))
            self.qualityEnabled = int(json.get('qual', self.qualityEnabled))
            self.DOPEnabled = int(json.get('dop', self.DOPEnabled))
            self.stale = False

    def toJson(self):
        gpsJson = {'gpsCfg':{
                              'sr' : self.sampleRate,
                              'pos' : self.positionEnabled,
                              'speed' : self.speedEnabled,
                              'dist' : self.distanceEnabled,
                              'alt' : self.altitudeEnabled,
                              'sats' : self.satellitesEnabled,
                              'qual' : self.qualityEnabled,
                              'dop' : self.DOPEnabled
                              }
                    }

        return gpsJson

class GpsSample(object):
    """
    Represents a GPS sample with accompanying quality indicator
    """
    def __init__(self, **kwargs):
        self.gps_qual = 0
        self.latitude = 0
        self.longitude = 0

    @property
    def is_locked(self):
        """
        :return True if the GPS is fixed and latitude / longitude values are valid.
        """
        return self.gps_qual >= GpsConfig.GPS_QUALITY_NO_FIX and self.latitude != 0 and self.longitude != 0

    @property
    def geopoint(self):
        """
        Convert the GPS sample to a GeoPoint
        :return GeoPoint 
        """
        return GeoPoint.fromPoint(self.latitude, self.longitude)

TIMER_CHANNEL_COUNT = 3

class TimerChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(TimerChannel, self).__init__(**kwargs)
        self.mode = 0
        self.speed = 0
        self.pulsePerRev = 0
        self.slowTimer = 0
        self.alpha = 0

    def fromJson(self, json_dict):
        if json_dict:
            super(TimerChannel, self).fromJson(json_dict)
            self.mode = json_dict.get('mode', self.mode)
            self.speed = json_dict.get('speed', self.speed)
            self.pulsePerRev = json_dict.get('ppr', self.pulsePerRev)
            self.slowTimer = json_dict.get('st', self.slowTimer)
            self.alpha = json_dict.get('alpha', self.alpha)
            self.stale = False

    def toJson(self):
        json_dict = {}
        super(TimerChannel, self).appendJson(json_dict)
        json_dict['mode'] = self.mode
        json_dict['ppr'] = self.pulsePerRev
        json_dict['speed'] = self.speed
        json_dict['st'] = self.slowTimer
        json_dict['alpha'] = self.alpha
        return json_dict

class TimerConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = TIMER_CHANNEL_COUNT
        self.channels = []
        self.build_channels()


    def build_channels(self):
        initialized_channel_count = len(self.channels)
        required_channel_count = self.channelCount

        if initialized_channel_count == required_channel_count:
            return
        else:
            # Probably got a new capabilities, make a new channels array
            self.channels = []
            for i in range(required_channel_count):
                self.channels.append(TimerChannel())

    def fromJson(self, json, capabilities=None):
        if capabilities:
            self.channelCount = capabilities.channels.timer
            self.build_channels()

        for i in range (self.channelCount):
            timerChannelJson = json.get(str(i), None)
            if timerChannelJson:
                self.channels[i].fromJson(timerChannelJson)

    def toJson(self):
        timerCfgJson = {}
        for i in range(self.channelCount):
            timerChannel = self.channels[i]
            timerCfgJson[str(i)] = timerChannel.toJson()

        return {'timerCfg':timerCfgJson}

    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False

    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value

class GpioChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(GpioChannel, self).__init__(**kwargs)
        self.mode = 0

    def fromJson(self, json_dict):
        if json_dict:
            super(GpioChannel, self).fromJson(json_dict)
            self.mode = json_dict.get('mode', self.mode)
            self.stale = False

    def toJson(self):
        json_dict = {}
        super(GpioChannel, self).appendJson(json_dict)
        json_dict['mode'] = self.mode
        return json_dict

GPIO_CHANNEL_COUNT = 3

class GpioConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = GPIO_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(GpioChannel())

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)

    def toJson(self):
        gpioCfgJson = {}
        for i in range(GPIO_CHANNEL_COUNT):
            gpioChannel = self.channels[i]
            gpioCfgJson[str(i)] = gpioChannel.toJson()
        return {'gpioCfg':gpioCfgJson}

    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False

    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value

class PwmChannel(BaseChannel):
    def __init__(self, **kwargs):
        super(PwmChannel, self).__init__(**kwargs)
        self.outputMode = 0
        self.loggingMode = 0
        self.startupPeriod = 0
        self.startupDutyCycle = 0

    def fromJson(self, json_dict):
        if json_dict:
            super(PwmChannel, self).fromJson(json_dict)
            self.outputMode = json_dict.get('outMode', self.outputMode)
            self.loggingMode = json_dict.get('logMode', self.loggingMode)
            self.startupDutyCycle = json_dict.get('stDutyCyc', self.startupDutyCycle)
            self.startupPeriod = json_dict.get('stPeriod', self.startupPeriod)
            self.stale = False

    def toJson(self):
        json_dict = {}
        super(PwmChannel, self).appendJson(json_dict)
        json_dict['outMode'] = self.outputMode
        json_dict['logMode'] = self.loggingMode
        json_dict['stDutyCyc'] = self.startupDutyCycle
        json_dict['stPeriod'] = self.startupPeriod
        return json_dict

PWM_CHANNEL_COUNT = 4

class PwmConfig(object):
    def __init__(self, **kwargs):
        self.channelCount = PWM_CHANNEL_COUNT
        self.channels = []

        for i in range (self.channelCount):
            self.channels.append(PwmChannel())

    def fromJson(self, json):
        for i in range (self.channelCount):
            channelJson = json.get(str(i), None)
            if channelJson:
                self.channels[i].fromJson(channelJson)

    def toJson(self):
        pwmCfgJson = {}
        for i in range(PWM_CHANNEL_COUNT):
            pwmChannel = self.channels[i]
            pwmCfgJson[str(i)] = pwmChannel.toJson()
        return {'pwmCfg':pwmCfgJson}

    @property
    def stale(self):
        for channel in self.channels:
            if channel.stale:
                return True
        return False

    @stale.setter
    def stale(self, value):
        for channel in self.channels:
            channel.stale = value

CONFIG_SECTOR_COUNT = 20

TRACK_TYPE_CIRCUIT = 0
TRACK_TYPE_STAGE = 1

CONFIG_SECTOR_COUNT_CIRCUIT = 19
CONFIG_SECTOR_COUNT_STAGE = 18

class Track(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.trackId = None
        self.trackType = TRACK_TYPE_CIRCUIT
        self.sectorCount = CONFIG_SECTOR_COUNT
        self.startLine = GeoPoint()
        self.finishLine = GeoPoint()
        self.sectors = []

    def fromJson(self, trackJson):
        if trackJson:
            self.trackId = trackJson.get('id', self.trackId)
            self.trackType = trackJson.get('type', self.trackType)
            sectorsJson = trackJson.get('sec', None)
            del self.sectors[:]

            if self.trackType == TRACK_TYPE_CIRCUIT:
                self.startLine.fromJson(trackJson.get('sf', None))
                sectorCount = CONFIG_SECTOR_COUNT_CIRCUIT
            else:
                self.startLine.fromJson(trackJson.get('st', self.startLine))
                self.finishLine.fromJson(trackJson.get('fin', self.finishLine))
                sectorCount = CONFIG_SECTOR_COUNT_STAGE

            returnedSectorCount = len(sectorsJson)
            if sectorsJson:
                for i in range(sectorCount):
                    sector = GeoPoint()
                    if i < returnedSectorCount:
                        sectorJson = sectorsJson[i]
                        sector.fromJson(sectorJson)
                    self.sectors.append(sector)
            self.sectorCount = sectorCount
            self.stale = False

    @classmethod
    def fromTrackMap(cls, track_map):
        t = Track()
        t.import_trackmap(track_map)
        return t

    def import_trackmap(self, track_map):
        self.trackId = track_map.short_id
        self.trackType = TRACK_TYPE_STAGE if track_map.finish_point else TRACK_TYPE_CIRCUIT
        self.startLine = copy(track_map.start_finish_point)
        self.finishLine = GeoPoint() if self.trackType == TRACK_TYPE_CIRCUIT else copy(track_map.finish_point)
        max_sectors = CONFIG_SECTOR_COUNT_CIRCUIT if self.trackType == TRACK_TYPE_CIRCUIT else CONFIG_SECTOR_COUNT_STAGE

        del self.sectors[:]
        for i in range (0, max_sectors):
            if i < len(track_map.sector_points):
                self.sectors.append(copy(track_map.sector_points[i]))
            else:
                self.sectors.append(GeoPoint())
        self.stale = True

    def toJson(self):
        sectors = []
        for sector in self.sectors:
            sectors.append(sector.toJson())
        trackJson = {}
        trackJson['id'] = self.trackId
        trackJson['type'] = self.trackType
        trackJson['sec'] = sectors

        if self.trackType == TRACK_TYPE_STAGE:
            trackJson['st'] = self.startLine.toJson()
            trackJson['fin'] = self.finishLine.toJson()
        else:
            trackJson['sf'] = self.startLine.toJson()
        return trackJson

class TrackConfig(object):
    def __init__(self, **kwargs):
        self.stale = False
        self.track = Track()
        self.radius = 0
        self.autoDetect = 0

    def fromJson(self, trackConfigJson):
        if trackConfigJson:
            self.radius = trackConfigJson.get('rad', self.radius)
            self.autoDetect = trackConfigJson.get('autoDetect', self.autoDetect)

            trackJson = trackConfigJson.get('track', None)
            if trackJson:
                self.track = Track()
                self.track.fromJson(trackJson)
            self.stale = False

    def toJson(self):
        trackCfgJson = {}
        trackCfgJson['rad'] = self.radius
        trackCfgJson['autoDetect'] = 1 if self.autoDetect else 0
        trackCfgJson['track'] = self.track.toJson()

        return {'trackCfg':trackCfgJson}

class TracksDb(object):
    tracks = None
    def __init__(self, **kwargs):
        self.stale = False
        self.tracks = []

    def fromJson(self, tracksDbJson):
        if tracksDbJson:
            del self.tracks[:]
            tracksNode = tracksDbJson.get('tracks')
            if tracksNode:
                for trackNode in tracksNode:
                    track = Track()
                    track.fromJson(trackNode)
                    self.tracks.append(track)
            self.stale = False

    def toJson(self):
        tracksJson = []
        tracks = self.tracks
        for track in tracks:
            tracksJson.append(track.toJson())
        return {"trackDb":{'size':len(tracks), 'tracks': tracksJson}}

class CANMapping(object):
    CAN_MAPPING_TYPE_UNSIGNED = 0
    CAN_MAPPING_TYPE_SIGNED = 1
    CAN_MAPPING_TYPE_FLOAT = 2
    CAN_MAPPING_TYPE_SIGN_MAGNITUDE = 3
    ID_MASK_DISABLED = 0
    CONVERSION_FILTER_DISABLED = 0
    SUB_ID_DISABLED = -1

    def __init__(self, **kwargs):
        self.bit_mode = False
        self.type = CANMapping.CAN_MAPPING_TYPE_UNSIGNED
        self.can_bus = 0
        self.can_id = 0
        self.sub_id = CANMapping.SUB_ID_DISABLED
        self.can_mask = CANMapping.ID_MASK_DISABLED
        self.endian = False
        self.offset = 0
        self.length = 1
        self.multiplier = 1.0
        self.divider = 1.0
        self.adder = 0.0
        self.conversion_filter_id = CANMapping.CONVERSION_FILTER_DISABLED

    def from_json_dict(self, json_dict):
        if json_dict:
            self.bit_mode = bool(json_dict.get('bm', self.bit_mode))
            self.type = json_dict.get('type', self.type)
            self.can_bus = json_dict.get('bus', self.can_bus)
            self.can_id = json_dict.get('id', self.can_id)
            self.sub_id = json_dict.get('subId', self.sub_id)
            self.can_mask = json_dict.get('idMask', self.can_mask)
            self.offset = json_dict.get('offset', self.offset)
            self.length = json_dict.get('len', self.length)
            self.multiplier = json_dict.get('mult', self.multiplier)
            self.divider = json_dict.get('div', self.divider)
            self.adder = json_dict.get('add', self.adder)
            self.endian = bool(json_dict.get('bigEndian', self.endian))
            self.conversion_filter_id = json_dict.get('filtId', self.conversion_filter_id)
        return self

    def to_json_dict(self):
        json_dict = {}
        json_dict['bm'] = bool(self.bit_mode)
        json_dict['type'] = self.type
        json_dict['bus'] = self.can_bus
        json_dict['id'] = self.can_id
        json_dict['subId'] = self.sub_id
        json_dict['idMask'] = self.can_mask
        json_dict['offset'] = self.offset
        json_dict['len'] = self.length
        json_dict['mult'] = self.multiplier
        json_dict['div'] = self.divider
        json_dict['add'] = self.adder
        json_dict['bigEndian'] = bool(self.endian)
        json_dict['filtId'] = self.conversion_filter_id
        return json_dict

    def equals(self, other):
        return other is not None and (self.bit_mode == other.bit_mode and
                    self.type == other.type and
                    self.can_bus == other.can_bus and
                    self.can_id == other.can_id and
                    self.can_mask == other.can_mask and
                    self.endian == other.endian and
                    self.offset == other.offset and
                    self.length == other.length and
                    self.multiplier == other.multiplier and
                    self.divider == other.divider and
                    self.adder == other.adder and
                    self.conversion_filter_id == other.conversion_filter_id)
class CanConfig(object):
    DEFAULT_BAUD_RATE = [0, 0]
    DEFAULT_TERMINATION_ENABED = [0, 0]
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False
        self.baudRate = CanConfig.DEFAULT_BAUD_RATE
        self.termination_enabled = CanConfig.DEFAULT_TERMINATION_ENABED

    def fromJson(self, can_cfg_json):
        self.enabled = True if can_cfg_json.get('en', self.enabled) == 1 else False

        bauds = can_cfg_json.get('baud')
        self.baudRate = []
        for baud in bauds:
            self.baudRate.append(int(baud))

        terms = can_cfg_json.get('term', CanConfig.DEFAULT_TERMINATION_ENABED)
        if terms is not None:
            self.termination_enabled = []
            for t in terms:
                self.termination_enabled.append(int(t))

        self.stale = False

    def toJson(self):
        can_cfg_json = {}
        can_cfg_json['en'] = 1 if self.enabled else 0
        bauds = []
        for baud in self.baudRate:
            bauds.append(baud)
        can_cfg_json['baud'] = bauds

        terms = []
        for term in self.termination_enabled:
            terms.append(term)
        can_cfg_json['term'] = terms

        return {'canCfg':can_cfg_json}

class CANChannel(BaseChannel):

    def __init__(self, **kwargs):
        super(CANChannel, self).__init__(**kwargs)
        self.mapping = CANMapping()

    def from_json_dict(self, json_dict):
        if json_dict:
            super(CANChannel, self).fromJson(json_dict)
            self.mapping.from_json_dict(json_dict)
        return self

    def to_json_dict(self):
        json_dict = {}
        super(CANChannel, self).appendJson(json_dict)
        json_dict.update(self.mapping.to_json_dict())
        return json_dict

class CANChannels(object):

    def __init__(self, **kwargs):
        self.channels = []
        self.enabled = False
        self.stale = False
        self.enabled = False

    def from_json_dict(self, json_dict):
        if json_dict:
            self.enabled = json_dict.get('en', self.enabled)
            channels_json = json_dict.get("chans", None)
            if channels_json is not None:
                del self.channels[:]
                for channel_json in channels_json:
                    c = CANChannel()
                    c.from_json_dict(channel_json)
                    self.channels.append(c)
        return self

    def to_json_dict(self):
        channels_json = []
        channel_count = len(self.channels)
        for i in range(channel_count):
            channels_json.append(self.channels[i].to_json_dict())
        return {'canChanCfg':{'en': 1 if self.enabled else 0, 'chans':channels_json }}

class PidConfig(BaseChannel):
    OBDII_MODE_11_BIT_CAN_ID_RESPONSE = 0x7E8
    OBDII_MODE_29_BIT_CAN_ID_RESPONSE = 0x18DAF110

    def __init__(self, **kwargs):
        super(PidConfig, self).__init__(**kwargs)
        self.pid = 0
        self.mode = 0
        self.passive = False
        self.mapping = CANMapping()

    def fromJson(self, json_dict):
        if json_dict:
            super(PidConfig, self).fromJson(json_dict)
            self.pid = json_dict.get('pid', self.pid)
            self.mode = json_dict.get('mode', self.mode)
            self.passive = bool(json_dict.get('pass', self.passive))
            self.mapping.from_json_dict(json_dict)

    def toJson(self):
        json_dict = {}
        super(PidConfig, self).appendJson(json_dict)
        json_dict['pid'] = self.pid
        json_dict['mode'] = self.mode
        json_dict['pass'] = self.passive
        json_dict.update(self.mapping.to_json_dict())
        return json_dict

    def equals(self, other):
        return other is not None and (super(PidConfig, self).equals(other) and
                    self.pid == other.pid and
                    self.mode == other.mode and
                    self.passive == other.passive and
                    self.mapping.equals(other.mapping))

OBD2_CONFIG_MAX_PIDS = 20

class Obd2Config(object):
    pids = []
    enabled = False
    def __init__(self, **kwargs):
        self.stale = False
        self.enabled = False

    def fromJson(self, json_dict):
        self.enabled = json_dict.get('en', self.enabled)
        pidsJson = json_dict.get("pids", None)
        if pidsJson is not None:
            del self.pids[:]
            for pidJson in pidsJson:
                pid = PidConfig()
                pid.fromJson(pidJson)
                self.pids.append(pid)

    def toJson(self):
        pidsJson = []
        pidCount = len(self.pids)
        pidCount = pidCount if pidCount <= OBD2_CONFIG_MAX_PIDS else OBD2_CONFIG_MAX_PIDS

        for i in range(pidCount):
            pidsJson.append(self.pids[i].toJson())

        obd2Json = {'obd2Cfg':{'en': 1 if self.enabled else 0, 'pids':pidsJson }}
        return obd2Json

class LuaScript(object):
    script = ""
    def __init__(self, **kwargs):
        self.stale = False
        pass

    def fromJson(self, jsonScript):
        self.script = jsonScript['data']
        self.stale = False

    def toJson(self):
        scriptJson = {"scriptCfg":{'data':self.script, 'page':None}}
        return scriptJson

class BluetoothConfig(object):
    name = ""
    passKey = ""
    btEnabled = False
    def __init__(self, **kwargs):
        pass

    def fromJson(self, btCfgJson):
        self.btEnabled = btCfgJson['btEn'] == 1
        self.passKey = btCfgJson.get('pass', self.passKey)
        self.name = btCfgJson.get('name', self.name)

    def toJson(self):
        btCfgJson = {}
        btCfgJson['btEn'] = 1 if self.btEnabled else 0
        btCfgJson['pass'] = self.passKey
        btCfgJson['name'] = self.name
        return btCfgJson

class CellConfig(object):
    cellEnabled = False
    apnHost = ""
    apnUser = ""
    apnPass = ""
    def __init__(self, **kwargs):
        pass

    def fromJson(self, cellCfgJson):
        self.cellEnabled = cellCfgJson['cellEn'] == 1
        self.apnHost = cellCfgJson.get('apnHost', self.apnHost)
        self.apnUser = cellCfgJson.get('apnUser', self.apnUser)
        self.apnPass = cellCfgJson.get('apnPass', self.apnUser)

    def toJson(self):
        cellConfigJson = {}
        cellConfigJson['cellEn'] = 1 if self.cellEnabled else 0
        cellConfigJson['apnHost'] = self.apnHost
        cellConfigJson['apnUser'] = self.apnUser
        cellConfigJson['apnPass'] = self.apnPass
        return cellConfigJson

class TelemetryConfig(object):
    deviceId = ""
    backgroundStreaming = 0

    def fromJson(self, telCfgJson):
        self.deviceId = telCfgJson.get('deviceId', self.deviceId)
        self.backgroundStreaming = True if telCfgJson.get('bgStream', 0) == 1 else False

    def toJson(self):
        telCfgJson = {}
        telCfgJson['deviceId'] = self.deviceId
        telCfgJson['bgStream'] = 1 if self.backgroundStreaming else 0
        return telCfgJson


class WifiConfig(object):

    WIFI_CONFIG_MINIMUM_AP_PASSWORD_LENGTH = 8
    def __init__(self):
        self.active = False

        self.client_mode_active = False
        self.client_ssid = ''
        self.client_password = ''

        self.ap_mode_active = False
        self.ap_ssid = ''
        self.ap_password = ''
        self.ap_channel = 1
        self.ap_encryption = 'None'
        self.stale = False

    def from_json(self, json_config):
        Logger.debug("RCPConfig: got WiFi config: {}".format(json_config))
        self.active = json_config.get('active', self.active)

        client_config = json_config.get('client', False)

        if client_config:
            self.client_mode_active = client_config.get('active', self.client_mode_active)
            self.client_ssid = client_config.get('ssid', self.client_ssid)
            self.client_password = client_config.get('password', self.client_password)

        ap_config = json_config.get('ap', False)

        if ap_config:
            self.ap_mode_active = ap_config.get('active', self.ap_mode_active)
            self.ap_ssid = ap_config.get('ssid', self.ap_ssid)
            self.ap_password = ap_config.get('password', self.ap_password)
            self.ap_channel = ap_config.get('channel', self.ap_channel)
            self.ap_encryption = ap_config.get('encryption', self.ap_encryption)

    def to_json(self):
        wifi_config = {'active': self.active,
                       'client': {
                           'ssid': self.client_ssid,
                           'active': self.client_mode_active,
                           'password': self.client_password
                           },
                       'ap': {
                           'active': self.ap_mode_active,
                           'ssid': self.ap_ssid,
                           'password': self.ap_password,
                           'encryption': self.ap_encryption,
                           'channel': self.ap_channel
                       }
                       }

        return wifi_config


class ConnectivityConfig(object):
    stale = False
    bluetoothConfig = BluetoothConfig()
    cellConfig = CellConfig()
    telemetryConfig = TelemetryConfig()

    def fromJson(self, connCfgJson):
        btCfgJson = connCfgJson.get('btCfg')
        if btCfgJson:
            self.bluetoothConfig.fromJson(btCfgJson)

        cellCfgJson = connCfgJson.get('cellCfg')
        if cellCfgJson:
            self.cellConfig.fromJson(cellCfgJson)

        telCfgJson = connCfgJson.get('telCfg')
        if telCfgJson:
            self.telemetryConfig.fromJson(telCfgJson)

        self.stale = False

    def toJson(self):
        connCfgJson = {'btCfg' : self.bluetoothConfig.toJson(),
                       'cellCfg' : self.cellConfig.toJson(),
                       'telCfg' : self.telemetryConfig.toJson()
                       }

        return {'connCfg':connCfgJson}

class AutoControlConfig(object):
    def __init__(self, **kwargs):
        self.stale = False

        self.channel = 'Speed'
        self.enabled = False

        self.start_threshold = 15
        self.start_greater_than = True
        self.start_time = 5

        self.stop_threshold = 10
        self.stop_greater_than = False
        self.stop_time = 10

    def from_json_dict(self, json_dict):
        if json_dict:
            self.enabled = json_dict.get('en', self.enabled)
            self.channel = json_dict.get('channel', self.channel)

            start = json_dict.get('start')
            if start:
                self.start_threshold = start.get('thresh', float(self.start_threshold))
                self.start_time = start.get('time', int(self.start_time))
                self.start_greater_than = start.get('gt', bool(self.start_greater_than))

            stop = json_dict.get('stop')
            if stop:
                self.stop_threshold = stop.get('thresh', float(self.stop_threshold))
                self.stop_time = stop.get('time', int(self.stop_time))
                self.stop_greater_than = stop.get('gt', bool(self.stop_greater_than))

    def to_json_dict(self):
        json_dict = {'channel':self.channel,
                     'en':self.enabled,
                     'start':{'thresh': float(self.start_threshold),
                              'gt': bool(self.start_greater_than),
                              'time': int(self.start_time)
                              },
                     'stop':{'thresh': float(self.stop_threshold),
                             'gt': bool(self.stop_greater_than),
                             'time': int(self.stop_time) }
                     }
        return json_dict

class CameraControlConfig(AutoControlConfig):
    def __init__(self, **kwargs):
        super(CameraControlConfig, self).__init__(**kwargs)
        self.make_model = 0

    def from_json_dict(self, json_dict):
        super(CameraControlConfig, self).from_json_dict(json_dict)
        self.make_model = json_dict.get('makeModel', self.make_model)

    def to_json_dict(self):
        json_dict = super(CameraControlConfig, self).to_json_dict()
        json_dict['makeModel'] = self.make_model
        return {'camCtrlCfg':json_dict}

class SDLoggingControlConfig(AutoControlConfig):
    def __init__(self, **kwargs):
        super(SDLoggingControlConfig, self).__init__(**kwargs)

    def to_json_dict(self):
        json_dict = super(SDLoggingControlConfig, self).to_json_dict()
        return {'sdLogCtrlCfg':json_dict}

class VersionConfig(object):
    def __init__(self, **kwargs):
        self.name = ''
        self.friendlyName = ''
        self.serial = ''
        self.major = kwargs.get('major', 0)
        self.minor = kwargs.get('minor', 0)
        self.bugfix = kwargs.get('bugfix', 0)
        self.git_info = kwargs.get('git_info', '')

    def __str__(self):
        return '{} {}.{}.{} (s/n# {})'.format(self.name, self.major, self.minor, self.bugfix, self.serial)

    def version_string(self):
        return '{}.{}.{}'.format(self.major, self.minor, self.bugfix)

    @staticmethod
    def get_minimum_version():
        return VersionConfig(major=RCP_COMPATIBLE_MAJOR_VERSION, minor=RCP_MINIMUM_MINOR_VERSION, bugfix=0)

    def fromJson(self, versionJson):
        self.name = versionJson.get('name', self.name)
        self.friendlyName = versionJson.get('fname', self.friendlyName)
        self.major = versionJson.get('major', self.major)
        self.minor = versionJson.get('minor', self.minor)
        self.bugfix = versionJson.get('bugfix', self.bugfix)
        self.serial = versionJson.get('serial', self.serial)
        self.git_info = versionJson.get('git_info', self.git_info)

    def toJson(self):
        versionJson = {'name': self.name, 'fname': self.friendlyName, 'major': self.major, 'minor': self.minor,
                       'bugfix': self.bugfix, 'git_info': self.git_info}
        return {'ver': versionJson}

    def is_compatible_version(self):
        return self.major == RCP_COMPATIBLE_MAJOR_VERSION and self.minor >= RCP_MINIMUM_MINOR_VERSION

    @property
    def is_valid(self):
        '''
        Indicates if version data represents valid version data
        :returns True if version data is valid
        '''
        return self.major > 0 and len(self.name) > 0 and len(self.friendlyName) > 0


class ChannelCapabilities(object):

    def __init__(self):
        self.analog = 8
        self.imu = 6
        self.gpio = 3
        self.timer = 3
        self.pwm = 3
        self.can = 2
        self.can_channel = 0

    def from_json_dict(self, json_dict):
        if json_dict:
            self.analog = int(json_dict.get('analog', 0))
            self.imu = int(json_dict.get('imu', 0))
            self.gpio = int(json_dict.get('gpio', 0))
            self.pwm = int(json_dict.get('pwm', 0))
            self.can = int(json_dict.get('can', 0))
            self.timer = int(json_dict.get('timer', 0))
            self.can_channel = int(json_dict.get('canChan', 0))

    def to_json_dict(self):
        return {
            "analog": self.analog,
            "imu": self.imu,
            "gpio": self.gpio,
            "pwm": self.pwm,
            "can": self.can,
            "timer": self.timer,
            "canChan" : self.can_channel
        }

class SampleRateCapabilities(object):

    def __init__(self):
        self.sensor = 1000
        self.gps = 50

    def from_json_dict(self, json_dict):
        if json_dict:
            self.sensor = json_dict.get('sensor', 0)
            self.gps = json_dict.get('gps', 0)

    def to_json_dict(self):
        return {
            "sensor": self.sensor,
            "gps": self.gps
        }


class StorageCapabilities(object):

    def __init__(self):
        self.tracks = 200
        self.script = 100000

    def from_json_dict(self, json_dict):
        if json_dict:
            self.tracks = json_dict.get('tracks', 0)
            self.script = json_dict.get('script', False)

    def to_json_dict(self):
        return {
            "tracks": self.tracks,
            "script": self.script
        }


class LinksCapabilities(object):

    def __init__(self):
        self.bluetooth = True
        self.cellular = True
        self.wifi = True
        self.usb = True

    def from_flags(self, flags):
        self.bluetooth = 'bt' in flags
        self.cellular = 'cell' in flags
        self.usb = 'usb' in flags
        self.wifi = 'wifi' in flags

class Capabilities(object):

    MIN_BT_CONFIG_VERSION = "2.9.0"
    MIN_FLAGS_VERSION = "2.10.0"
    LEGACY_FLAGS = ['bt', 'cell', 'usb', 'gps']

    def __init__(self):
        self.channels = ChannelCapabilities()
        self.sample_rates = SampleRateCapabilities()
        self.storage = StorageCapabilities()
        self.links = LinksCapabilities()
        self.bluetooth_config = True
        self.flags = []

    def has_flag(self, flag):
        return flag in self.flags

    @property
    def has_gps(self):
        return 'gps' in self.flags

    @property
    def has_imu(self):
        return self.channels.imu > 0

    @property
    def has_analog(self):
        # We always have at least 1 analog channel for battery
        return self.channels.analog > 0

    @property
    def has_gpio(self):
        return self.channels.gpio > 0

    @property
    def has_pwm(self):
        return self.channels.pwm > 0

    @property
    def has_script(self):
        return self.storage.script > 0

    @property
    def has_timer(self):
        return self.channels.timer > 0

    @property
    def has_cellular(self):
        return self.links.cellular

    @property
    def has_wifi(self):
        return self.links.wifi

    @property
    def has_bluetooth(self):
        return self.links.bluetooth

    @property
    def has_can_channel(self):
        return self.channels.can_channel > 0

    @property
    def has_can_term(self):
        return 'can_term' in self.flags

    @property
    def has_streaming(self):
        return 'telemstream' in self.flags

    @property
    def has_camera_control(self):
        return 'camctl' in self.flags

    @property
    def has_sd_logging(self):
        return 'sd' in self.flags

    def from_json_dict(self, json_dict, version_config=None):
        if json_dict:
            Logger.debug("RCPConfig: Capabilities: {}".format(json_dict))

            self.flags = json_dict.get('flags', [])

            channels = json_dict.get('channels')
            if channels:
                self.channels.from_json_dict(channels)

            sample_rates = json_dict.get('sampleRates')
            if sample_rates:
                self.sample_rates.from_json_dict(sample_rates)

            storage = json_dict.get('db')
            if storage:
                self.storage.from_json_dict(storage)

        # For select features/capabilities we need to check RCP version because
        # the capability wasn't added to the API. Not ideal, but let's at least
        # insulate other code from inspecting the version string
        if version_config:
            rcp_version = StrictVersion(version_config.version_string())

            # Handle flags. Encapsulate legacy firmware versions that don't support flags
            min_flags_version = StrictVersion(Capabilities.MIN_FLAGS_VERSION)
            self.links.from_flags(self.flags if rcp_version >= min_flags_version else Capabilities.LEGACY_FLAGS)

            self.flags = self.flags if rcp_version >= min_flags_version else Capabilities.LEGACY_FLAGS

            # Handle BT version
            min_bt_config_version = StrictVersion(Capabilities.MIN_BT_CONFIG_VERSION)
            self.bluetooth_config = rcp_version >= min_bt_config_version

    def to_json_dict(self):
        return {
            "channels": self.channels.to_json_dict(),
            "db": self.storage.to_json_dict(),
            "sampleRates": self.sample_rates.to_json_dict(),
            "flags": self.flags
        }


class RcpConfig(object):
    loaded = False
    def __init__(self, **kwargs):

        self.versionConfig = VersionConfig()
        self.capabilities = Capabilities()
        self.analogConfig = AnalogConfig()
        self.imuConfig = ImuConfig()
        self.gpsConfig = GpsConfig()
        self.lapConfig = LapConfig()
        self.timerConfig = TimerConfig()
        self.gpioConfig = GpioConfig()
        self.pwmConfig = PwmConfig()
        self.trackConfig = TrackConfig()
        self.connectivityConfig = ConnectivityConfig()
        self.wifi_config = WifiConfig()
        self.canConfig = CanConfig()
        self.can_channels = CANChannels()
        self.obd2Config = Obd2Config()
        self.camera_control_config = CameraControlConfig()
        self.sd_logging_control_config = SDLoggingControlConfig()
        self.scriptConfig = LuaScript()
        self.trackDb = TracksDb()

    @property
    def stale(self):
        return  (self.analogConfig.stale or
                self.imuConfig.stale or
                self.gpsConfig.stale or
                self.lapConfig.stale or
                self.timerConfig.stale or
                self.gpioConfig.stale or
                self.pwmConfig.stale or
                self.trackConfig.stale or
                self.connectivityConfig.stale or
                self.wifi_config.stale or
                self.canConfig.stale or
                self.can_channels.stale or
                self.obd2Config.stale or
                self.scriptConfig.stale or
                self.camera_control_config.stale or
                self.sd_logging_control_config.stale or
                self.trackDb.stale)

    @stale.setter
    def stale(self, value):
        self.analogConfig.stale = value
        self.imuConfig.stale = value
        self.gpsConfig.stale = value
        self.lapConfig.stale = value
        self.timerConfig.stale = value
        self.gpioConfig.stale = value
        self.pwmConfig.stale = value
        self.trackConfig.stale = value
        self.connectivityConfig.stale = value
        self.wifi_config.stale = value
        self.canConfig.stale = value
        self.can_channels.stale = value
        self.obd2Config.stale = value
        self.scriptConfig.stale = value
        self.camera_control_config.stale = value
        self.sd_logging_control_config.stale = value
        self.trackDb.stale = value

    def fromJson(self, rcpJson):
        if rcpJson:
            rcpJson = rcpJson.get('rcpCfg', None)
            if rcpJson:
                versionJson = rcpJson.get('ver', None)
                if versionJson:
                    self.versionConfig.fromJson(versionJson)

                capabilities = rcpJson.get('capabilities', None)
                if capabilities:
                    self.capabilities.from_json_dict(capabilities, version_config=self.versionConfig)

                analogCfgJson = rcpJson.get('analogCfg', None)
                if analogCfgJson:
                    self.analogConfig.fromJson(analogCfgJson, capabilities=self.capabilities)

                timerCfgJson = rcpJson.get('timerCfg', None)
                if timerCfgJson:
                    self.timerConfig.fromJson(timerCfgJson, capabilities=self.capabilities)

                imuCfgJson = rcpJson.get('imuCfg', None)
                if imuCfgJson:
                    self.imuConfig.fromJson(imuCfgJson)

                lapCfgJson = rcpJson.get('lapCfg', None)
                if lapCfgJson:
                    self.lapConfig.fromJson(lapCfgJson)

                gpsCfgJson = rcpJson.get('gpsCfg', None)
                if gpsCfgJson:
                    self.gpsConfig.fromJson(gpsCfgJson)

                gpioCfgJson = rcpJson.get('gpioCfg', None)
                if gpioCfgJson:
                    self.gpioConfig.fromJson(gpioCfgJson)

                pwmCfgJson = rcpJson.get('pwmCfg', None)
                if pwmCfgJson:
                    self.pwmConfig.fromJson(pwmCfgJson)

                trackCfgJson = rcpJson.get('trackCfg', None)
                if trackCfgJson:
                    self.trackConfig.fromJson(trackCfgJson)

                connectivtyCfgJson = rcpJson.get('connCfg', None)
                if connectivtyCfgJson:
                    self.connectivityConfig.fromJson(connectivtyCfgJson)

                wifi_config_json = rcpJson.get('wifiCfg', None)
                if wifi_config_json:
                    self.wifi_config.from_json(wifi_config_json)

                canCfgJson = rcpJson.get('canCfg', None)
                if canCfgJson:
                    self.canConfig.fromJson(canCfgJson)

                can_chan_json = rcpJson.get('canChanCfg', None)
                if can_chan_json:
                    self.can_channels.from_json_dict(can_chan_json)

                obd2CfgJson = rcpJson.get('obd2Cfg', None)
                if obd2CfgJson:
                    self.obd2Config.fromJson(obd2CfgJson)

                scriptJson = rcpJson.get('scriptCfg', None)
                if scriptJson:
                    self.scriptConfig.fromJson(scriptJson)

                camera_ctrl_cfg_json = rcpJson.get('camCtrlCfg')
                if camera_ctrl_cfg_json:
                    self.camera_control_config.from_json_dict(camera_ctrl_cfg_json)

                sd_logging_ctrl_cfg = rcpJson.get('sdLogCtrlCfg')
                if sd_logging_ctrl_cfg:
                    self.sd_logging_control_config.from_json_dict(sd_logging_ctrl_cfg)

                trackDbJson = rcpJson.get('trackDb', None)
                if trackDbJson:
                    self.trackDb.fromJson(trackDbJson)

                Logger.info('RcpConfig: Config version ' + str(self.versionConfig.major) + '.' + str(self.versionConfig.minor) + '.' + str(self.versionConfig.bugfix) + ' Loaded')
                self.loaded = True

    def fromJsonString(self, rcpJsonString):
        rcpJson = json.loads(rcpJsonString)
        self.fromJson(rcpJson)

    def toJsonString(self, pretty=True):
        return json.dumps(self.toJson(), sort_keys=True, indent=2, separators=(',', ': '))

    def toJson(self):
        rcpJson = {'rcpCfg':{
                             'ver': self.versionConfig.toJson().get('ver'),
                             'capabilities': self.capabilities.to_json_dict(),
                             'gpsCfg':self.gpsConfig.toJson().get('gpsCfg'),
                             'lapCfg':self.lapConfig.toJson().get('lapCfg'),
                             'imuCfg':self.imuConfig.toJson().get('imuCfg'),
                             'analogCfg':self.analogConfig.toJson().get('analogCfg'),
                             'timerCfg':self.timerConfig.toJson().get('timerCfg'),
                             'gpioCfg':self.gpioConfig.toJson().get('gpioCfg'),
                             'pwmCfg':self.pwmConfig.toJson().get('pwmCfg'),
                             'canCfg':self.canConfig.toJson().get('canCfg'),
                             'canChanCfg':self.can_channels.to_json_dict().get('canChanCfg'),
                             'obd2Cfg':self.obd2Config.toJson().get('obd2Cfg'),
                             'connCfg':self.connectivityConfig.toJson().get('connCfg'),
                             'wifiCfg': self.wifi_config.to_json(),
                             'sdLogCtrlCfg': self.sd_logging_control_config.to_json_dict().get('sdLogCtrlCfg'),
                             'camCtrlCfg': self.camera_control_config.to_json_dict().get('camCtrlCfg'),
                             'trackCfg':self.trackConfig.toJson().get('trackCfg'),
                             'scriptCfg':self.scriptConfig.toJson().get('scriptCfg'),
                             'trackDb': self.trackDb.toJson().get('trackDb')
                             }
                   }
        return rcpJson
