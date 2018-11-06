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

import kivy
kivy.require('1.10.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel, AutoShrinkFieldLabel
from kivy.properties import BoundedNumericProperty, StringProperty, ObjectProperty, NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge, SingleChannelGauge
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from autosportlabs.uix.gauge.gaugeframe import GaugeFrame
MIN_LAP_TIME = 0
MAX_LAP_TIME = 99.99

class Laptime(SingleChannelGauge):
    Builder.load_string("""
<Laptime>:
    anchor_x: 'center'
    anchor_y: 'center'
    value_size: self.height
    AutoShrinkFieldLabel:
        text: root.NULL_LAP_TIME
        id: value
        font_size: root.font_size
    """)

    NULL_LAP_TIME = '--:--.--'
    value = BoundedNumericProperty(0, min=MIN_LAP_TIME, max=MAX_LAP_TIME, errorhandler=lambda x: MAX_LAP_TIME if x > MAX_LAP_TIME else MIN_LAP_TIME)
    font_size = NumericProperty()

    def __init__(self, **kwargs):
        super(Laptime, self).__init__(**kwargs)

    def on_value(self, instance, value):
        view = self.valueView
        if view:
            view.text = format_laptime(value)
        self.update_colors()

    def on_normal_color(self, instance, value):
        self.valueView.color = value

class CurrentLaptime(Gauge):
    Builder.load_string("""
<CurrentLaptime>:
    anchor_x: 'center'
    anchor_y: 'center'
    value_size: self.height
    AutoShrinkFieldLabel:
        text: root.NULL_LAP_TIME
        id: value
        font_size: root.font_size
        shorten: False
        max_lines: 1
    """)

    _FLASH_INTERVAL = 0.25
    _FLASH_COUNT = 10
    NULL_LAP_TIME = '--:--.--'
    _elapsed_time = 0
    _lap_time = 0
    _predicted_time = 0
    _current_lap = 0
    _lap_count = 0

    _new_lap = False
    _flash_count = 0
    _value_view = None

    halign = StringProperty(None)
    valign = StringProperty(None)
    value = ObjectProperty(None)
    font_size = NumericProperty()

    def on_halign(self, instance, value):
        self.valueView.halign = value

    def on_valign(self, instance, value):
        self.valueView.valign = value

    def on_normal_color(self, instance, value):
        self.valueView.color = value

    def on_value_size(self, instance, value):
        view = self.valueView
        if view:
            view.font_size = value

    def on_data_bus(self, instance, value):
        data_bus = self.data_bus
        if data_bus:
            data_bus.addMetaListener(self.on_channel_meta)
            data_bus.addChannelListener("ElapsedTime" , self.set_elapsed_time)
            data_bus.addChannelListener("LapTime", self.set_lap_time)
            data_bus.addChannelListener("PredTime", self.set_predicted_time)
            data_bus.addChannelListener("CurrentLap", self.set_current_lap)
            data_bus.addChannelListener("LapCount", self.set_lap_count)

    def set_lap_time(self, value):
        self._lap_time = value

    def set_elapsed_time(self, value):
        self._elapsed_time = value
        self.update_value()

    def set_predicted_time(self, value):
        self._predicted_time = value
        self.update_value()

    def set_lap_count(self, value):
        if value > self._lap_count and self._current_lap > 0:
            self._new_lap = True
            self._flash_count = 0
            self.flash_value()
        self._lap_count = value

    def set_current_lap(self, value):
        self._current_lap = value
        self.update_value()

    def flash_value(self):
        self.value = self._lap_time if self._flash_count % 2 == 0 else ''
        self._flash_count += 1
        if self._flash_count < self._FLASH_COUNT * 2:
            Clock.schedule_once(lambda dt: self.flash_value(), self._FLASH_INTERVAL)
        else:
            self._new_lap = False

    """"
    Display logic:
    if we haven't completed a lap yet, only display elapsed time to give a stopwatch effect
    if we've completed a lap, flash last lap time for 5 seconds,
    then show predicted time, if present in stream. if not present, show last lap time statically
    """
    def update_value(self):
        if not self._new_lap:
            if self._lap_count == 0:
                self.value = self._elapsed_time
            else:
                if self._predicted_time > 0:
                    self.value = self._predicted_time
                else:
                    self.value = self._lap_time

    @property
    def valueView(self):
        if not self._value_view:
            self._value_view = self.ids.value
        return self._value_view

    def on_value(self, instance, value):
        view = self.valueView
        if view:
            if value == '':
                view.text = ''
            else:
                view.text = format_laptime(value)

