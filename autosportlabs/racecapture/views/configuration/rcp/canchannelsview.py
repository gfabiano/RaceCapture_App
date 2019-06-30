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
import os
from kivy.metrics import dp
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from garden_androidtabs import AndroidTabsBase, AndroidTabs
from iconbutton import IconButton
from settingsview import SettingsSwitch
from autosportlabs.racecapture.views.configuration.rcp.canmappingview import CANChannelConfigView
from autosportlabs.racecapture.data.unitsconversion import UnitsConversionFilters
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.uix.layout.sections import SectionBoxLayout
from autosportlabs.racecapture.views.util.alertview import confirmPopup, choicePopup, editor_popup
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.presets.presetview import PresetBrowserView
from fieldlabel import FieldLabel
from utils import *
from valuefield import FloatValueField, IntegerValueField
from mappedspinner import MappedSpinner
import copy

class CANChannelView(BoxLayout):
    Builder.load_string("""
<CANChannelView>:
    size_hint_y: None
    height: dp(30)
    orientation: 'horizontal'
    FieldLabel:
        id: name
        size_hint_x: 0.18
    FieldLabel:
        id: sample_rate
        size_hint_x: 0.10
    FieldLabel:
        id: can_id
        size_hint_x: 0.14
    FieldLabel:
        id: can_offset_len
        size_hint_x: 0.15
    FieldLabel:
        size_hint_x: 0.30
        id: can_formula
    IconButton:
        size_hint_x: 0.09        
        text: u'\uf044'
        on_release: root.on_edit()
    IconButton:
        size_hint_x: 0.09        
        text: u'\uf014'
        on_release: root.on_delete()
""")

    def __init__(self, channel_index, channel_cfg, channels, **kwargs):
        super(CANChannelView, self).__init__(**kwargs)
        self.channel_index = channel_index
        self.channel_cfg = channel_cfg
        self.channels = channels
        self.register_event_type('on_delete_channel')
        self.register_event_type('on_edit_channel')
        self.register_event_type('on_modified')
        self._loaded = False
        self.set_channel()

    def on_modified(self):
        pass

    def on_delete_channel(self, channel_index):
        pass

    def on_edit_channel(self, channel_index):
        pass

    def on_delete(self):
        self.dispatch('on_delete_channel', self.channel_index)

    def on_edit(self):
        self.dispatch('on_edit_channel', self.channel_index)

    def set_channel(self):
        self.ids.name.text = self.channel_cfg.name

        self.ids.sample_rate.text = '{}Hz'.format(self.channel_cfg.sampleRate)

        can_mapping = self.channel_cfg.mapping
        self.ids.can_id.text = '0x%X' % can_mapping.can_id

        self.ids.can_offset_len.text = u'{}({})'.format(can_mapping.offset, can_mapping.length)

        sign = '-' if can_mapping.adder < 0 else '+'
        self.ids.can_formula.text = u'\u00D7 {} \u00F7 {} {} {}'.format(can_mapping.multiplier, can_mapping.divider, sign, abs(can_mapping.adder))
        self._loaded = True

class CANChannelsView(BaseConfigView):
    preset_manager = ObjectProperty()
    DEFAULT_CAN_SAMPLE_RATE = 1
    Builder.load_string("""
<CANChannelsView>:
    spacing: dp(20)
    orientation: 'vertical'
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.20
        SettingsView:
            id: can_channels_enable
            size_hint_y: 0.6
            label_text: 'CAN channels'
            help_text: ''
        BoxLayout:
            padding: (dp(10), dp(0))
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(40)        
            BoxLayout:
            LabelIconButton:
                size_hint_x: None
                width: dp(120)
                id: load_preset
                title: 'Presets'
                icon_size: self.height * 0.7
                title_font_size: self.height * 0.5
                icon: u'\uf150'
                on_press: root.load_preset_view()
        
    BoxLayout:
        size_hint_y: 0.85
        orientation: 'vertical'        
        HSeparator:
            text: 'CAN Channels'
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.1
            padding: [dp(5), dp(0)]            
            FieldLabel:
                text: 'Channel'
                halign: 'left'
                size_hint_x: 0.18
            FieldLabel:
                text: 'Rate'
                halign: 'left'
                size_hint_x: 0.10
                
            FieldLabel:
                text: 'CAN ID'
                size_hint_x: 0.14
            FieldLabel:
                text: 'Offset(Len)'
                size_hint_x: 0.15
            FieldLabel:
                text: 'Formula'
                size_hint_x: 0.30
            FieldLabel:
                text: ''
                size_hint_x: 0.18
            
        AnchorLayout:                
            AnchorLayout:
                ScrollContainer:
                    canvas.before:
                        Color:
                            rgba: 0.05, 0.05, 0.05, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size                
                    id: scroller
                    size_hint_y: 0.95
                    do_scroll_x:False
                    do_scroll_y:True
                    GridLayout:
                        id: can_grid
                        padding: [dp(5), dp(5)]                        
                        spacing: [dp(0), dp(10)]
                        size_hint_y: None
                        height: max(self.minimum_height, scroller.height)
                        cols: 1
                FieldLabel:
                    halign: 'center'
                    id: list_msg
                    text: ''
            AnchorLayout:
                anchor_y: 'bottom'
                IconButton:
                    size_hint: (None, None)
                    height: root.height * .12
                    text: u'\uf055'
                    color: ColorScheme.get_accent()
                    on_release: root.on_add_can_channel()
                    disabled: True
                    id: add_can_channel
""")

    def __init__(self, **kwargs):
        super(CANChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.can_channels_cfg = None
        self.max_sample_rate = 0
        self.can_filters = None
        self.can_grid = self.ids.can_grid
        self._base_dir = kwargs.get('base_dir')
        self.max_can_channels = 0
        can_channels_enable = self.ids.can_channels_enable
        can_channels_enable.bind(on_setting=self.on_can_channels_enabled)
        can_channels_enable.setControl(SettingsSwitch())
        self.update_view_enabled()
        self.can_filters = UnitsConversionFilters(self._base_dir)

    def on_modified(self, *args):
        if self.can_channels_cfg:
            self.can_channels_cfg.stale = True
            self.dispatch('on_config_modified', *args)

    def on_can_channels_enabled(self, instance, value):
        if self.can_channels_cfg:
            self.can_channels_cfg.enabled = value
            self.dispatch('on_modified')

    def on_config_updated(self, rc_cfg):
        can_channels_cfg = rc_cfg.can_channels

        max_sample_rate = rc_cfg.capabilities.sample_rates.sensor
        max_can_channels = rc_cfg.capabilities.channels.can_channel
        self.ids.can_channels_enable.setValue(can_channels_cfg.enabled)
        self.reload_can_channel_grid(can_channels_cfg)
        self.max_sample_rate = max_sample_rate
        self.max_can_channels = max_can_channels
        self.can_channels_cfg = can_channels_cfg
        self.update_view_enabled()

    def update_view_enabled(self):
        add_disabled = True
        if self.can_channels_cfg:
            if len(self.can_channels_cfg.channels) < self.max_can_channels:
                add_disabled = False

        self.ids.add_can_channel.disabled = add_disabled

    def _refresh_channel_list_notice(self, cfg):
        channel_count = len(cfg.channels)
        self.ids.list_msg.text = 'Press (+) to map a CAN channel' if channel_count == 0 else ''

    def reload_can_channel_grid(self, can_channels_cfg):
        self.can_grid.clear_widgets()
        channel_count = len(can_channels_cfg.channels)
        for i in range(channel_count):
            channel_cfg = can_channels_cfg.channels[i]
            self.append_can_channel(i, channel_cfg)
        self.update_view_enabled()
        self._refresh_channel_list_notice(can_channels_cfg)

    def append_can_channel(self, index, channel_cfg):
        channel_view = CANChannelView(index, channel_cfg, self.channels)
        channel_view.bind(on_delete_channel=self.on_delete_channel)
        channel_view.bind(on_edit_channel=self.on_edit_channel)
        channel_view.bind(on_modified=self.on_modified)
        self.can_grid.add_widget(channel_view)

    def on_add_can_channel(self):
        if not self.can_channels_cfg:
            return

        can_channel = CANChannel()
        can_channel.sampleRate = self.DEFAULT_CAN_SAMPLE_RATE

        content = CANChannelConfigView()
        content.init_config(can_channel, self.can_filters, self.max_sample_rate, self.channels)

        popup = None
        def _on_answer(instance, answer):
            if answer:
                self.add_can_channel(can_channel)
                self.dispatch('on_modified')
                self.reload_can_channel_grid(self.can_channels_cfg)
            popup.dismiss()

        popup = editor_popup('Add CAN Channel Mapping', content, _on_answer, size=(dp(500), dp(300)))

    def add_can_channel(self, can_channel):
        self.can_channels_cfg.channels.append(can_channel)
        new_channel_index = len(self.can_channels_cfg.channels) - 1
        self.append_can_channel(new_channel_index, can_channel)
        self.update_view_enabled()
        self.dispatch('on_modified')
        return new_channel_index

    def _delete_all_channels(self):
        del self.can_channels_cfg.channels[:]
        self.reload_can_channel_grid(self.can_channels_cfg)
        self.dispatch('on_modified')

    def _delete_can_channel(self, channel_index):
        del self.can_channels_cfg.channels[channel_index]
        self.reload_can_channel_grid(self.can_channels_cfg)
        self.dispatch('on_modified')

    def on_delete_channel(self, instance, channel_index):
        popup = None
        def _on_answer(instance, answer):
            if answer:
                self._delete_can_channel(channel_index)
            popup.dismiss()
        popup = confirmPopup('Confirm', 'Delete CAN Channel?', _on_answer)

    def _replace_config(self, to_cfg, from_cfg):
        to_cfg.__dict__.update(from_cfg.__dict__)

    def _edit_channel(self, channel_index):
        content = CANChannelConfigView()
        working_channel_cfg = copy.deepcopy(self.can_channels_cfg.channels[channel_index])
        content.init_config(working_channel_cfg, self.can_filters, self.max_sample_rate, self.channels)

        def _on_answer(instance, answer):
            if answer:
                self._replace_config(self.can_channels_cfg.channels[channel_index], working_channel_cfg)
                self.dispatch('on_modified')

            self.reload_can_channel_grid(self.can_channels_cfg)
            popup.dismiss()

        popup = editor_popup('Edit CAN Channel Mapping', content, _on_answer, size=(dp(500), dp(300)))

    def on_edit_channel(self, instance, channel_index):
        self._edit_channel(channel_index)

    def _on_preset_selected(self, instance, preset_id):
        popup = None
        def _on_answer(instance, answer):
            if answer == True:
                self._delete_all_channels()
            self._import_preset(preset_id)
            popup.dismiss()

        if len(self.can_channels_cfg.channels) > 0:
            popup = choicePopup('Confirm', 'Overwrite or append existing channels?', 'Overwrite', 'Append', _on_answer)
        else:
            self._import_preset(preset_id)

    def _import_preset(self, id):
        try:
            preset = self.preset_manager.get_preset_by_id(id)
            if preset:
                mapping = preset.mapping
                for channel_json in mapping['chans']:
                    new_channel = CANChannel()
                    new_channel.from_json_dict(channel_json)
                    self.add_can_channel(new_channel)
            self._refresh_channel_list_notice(self.can_channels_cfg)
        except Exception as e:
            alertPopup('Error', 'There was an error loading the preset:\n\n{}'.format(e))
            raise

    def load_preset_view(self):
        def popup_dismissed(*args):
            pass
            # self.reload_can_channel_grid(self.can_channels_cfg)

        content = PresetBrowserView(self.preset_manager, 'can')
        content.bind(on_preset_selected=self._on_preset_selected)
        content.bind(on_preset_close=lambda *args:popup.dismiss())
        popup = Popup(title='Import a preset configuration', content=content, size_hint=(0.7, 0.8))
        popup.bind(on_dismiss=popup_dismissed)
        popup.open()
