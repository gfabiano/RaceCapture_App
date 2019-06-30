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
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import SpinnerOption
from kivy.uix.image import Image
from kivy.uix.anchorlayout import AnchorLayout
from autosportlabs.help.helpmanager import HelpInfo
from kivy.properties import StringProperty, NumericProperty
from garden_androidtabs import AndroidTabsBase, AndroidTabs
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.views.util.viewutils import clock_sequencer
from autosportlabs.racecapture.views.configuration.channels.channelnameselectorview import ChannelNameSelectorView
from autosportlabs.uix.layout.sections import SectionBoxLayout
from fieldlabel import FieldLabel
from utils import *
from valuefield import FloatValueField, IntegerValueField, HexIntegerValueField
from mappedspinner import MappedSpinner

class LargeSpinnerOption(SpinnerOption):
    Builder.load_string("""
<LargeSpinnerOption>:
    font_size: self.height * 0.5
""")

class LargeMappedSpinner(MappedSpinner):
    Builder.load_string("""
<LargeMappedSpinner>:
    font_size: self.height * 0.4
    option_cls: 'LargeSpinnerOption'
""")

class LargeIntegerValueField(IntegerValueField):
    Builder.load_string("""
<LargeIntegerValueField>:
    font_size: self.height * 0.5
    input_type: 'number'
""")

class LargeHexIntegerValueField(HexIntegerValueField):
    Builder.load_string("""
<LargeHexIntegerValueField>:
    font_size: self.height * 0.5
    input_type: 'number'
""")

class LargeFloatValueField(FloatValueField):
    Builder.load_string("""
<LargeFloatValueField>:
    font_size: self.height * 0.5
    input_type: 'number'
""")

class SymbolFieldLabel(FieldLabel):
    Builder.load_string("""
<SymbolFieldLabel>:
    font_size: self.height * 0.6
    font_name: 'resource/fonts/Roboto-Bold.ttf'
    shorten: False
""")

class CANChannelMappingTab(AnchorLayout, AndroidTabsBase):
    """
    Wrapper class to allow customization and styling
    """
    Builder.load_string("""
<CANChannelMappingTab>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background()
        Rectangle:
            pos: self.pos
            size: self.size

    tab_font_name: "resource/fonts/ASL_light.ttf"
    tab_font_size: sp(20)
""")
    tab_font_name = StringProperty()
    tab_font_size = NumericProperty()

    def on_tab_font_name(self, instance, value):
        self.tab_label.font_name = value

    def on_tab_font_size(self, instance, value):
        self.tab_label.font_size = value

class CANChannelCustomizationTab(CANChannelMappingTab):
    Builder.load_string("""
<CANChannelCustomizationTab>:
    text: 'Channel'
    BoxLayout:
        BoxLayout:
            size_hint_x: 0.1
        BoxLayout:
            size_hint_x: 0.6
            orientation: 'vertical'
            spacing: dp(5)
            SectionBoxLayout:
                ChannelNameSelectorView:
                    id: chan_id
                    on_channel: root._on_channel_selected(*args)
            SectionBoxLayout:
                FieldLabel:
                    halign: 'right'
                    text: 'Rate'
                SampleRateSpinner:
                    id: sr
                    size_hint_x: None
                    width: dp(100)
                BoxLayout:
                    size_hint_x: None
                    width: dp(40)
        BoxLayout:
            size_hint_x: 0.1

""")

    def __init__(self, **kwargs):
        super(CANChannelCustomizationTab, self).__init__(**kwargs)
        self.register_event_type('on_channel')
        self._loaded = False

    def on_channel(self, channel_name):
        pass

    def set_channel_filter_list(self, filter_list):
        self.ids.chan_id.filter_list = filter_list

    def init_view(self, channel_cfg, channels, max_sample_rate):
        self._loaded = False
        self.channel_cfg = channel_cfg

        channel_editor = self.ids.chan_id
        channel_editor.on_channels_updated(channels)
        channel_editor.setValue(self.channel_cfg)

        sample_rate_spinner = self.ids.sr
        sample_rate_spinner.set_max_rate(max_sample_rate)
        sample_rate_spinner.setFromValue(self.channel_cfg.sampleRate)
        sample_rate_spinner.bind(text=self._on_sample_rate)

        self._loaded = True

    def _on_sample_rate(self, instance, value):
        if self._loaded:
            self.channel_cfg.sampleRate = instance.getValueFromKey(value)

    def _on_channel_selected(self, instance, value):
        if self._loaded:
            self.dispatch('on_channel', value)

class CANIDMappingTab(CANChannelMappingTab):
    Builder.load_string("""
<CANIDMappingTab>:
    text: 'CAN ID Match'
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            spacing: dp(5)

            AnchorLayout:
                size_hint_x: 0.55
                BoxLayout:
                    size_hint_y: 0.8
                    orientation: 'vertical'
                    spacing: dp(5)
                    SectionBoxLayout:
                        FieldLabel:
                            size_hint_x: 0.3
                            text: 'CAN ID'
                            halign: 'right'

                        LargeHexIntegerValueField:
                            id: can_id
                            size_hint_x: 0.7
                            on_text: root._on_can_id(*args)

                    SectionBoxLayout:
                        FieldLabel:
                            size_hint_x: 0.3
                            text: 'Mask'
                            halign: 'right'

                        LargeIntegerValueField:
                            id: mask
                            size_hint_x: 0.7
                            on_text: root._on_mask(*args)

            AnchorLayout:
                size_hint_x: 0.45
                BoxLayout:
                    size_hint_y: 0.8
                    orientation: 'vertical'
                    spacing: dp(5)
                    SectionBoxLayout:
                        FieldLabel:
                            text: 'Sub ID'
                            halign: 'right'
                            size_hint_x: 0.45
                        LargeMappedSpinner:
                            id: sub_id
                            size_hint_x: 0.55
                            on_text: root._on_sub_id(*args)
                    SectionBoxLayout:
                        FieldLabel:
                            text: 'CAN Bus'
                            halign: 'right'
                            size_hint_x: 0.45
                        LargeMappedSpinner:
                            id: can_bus_channel
                            size_hint_x: 0.55
                            on_text: root._on_can_bus(*args)

""")

    def __init__(self, **kwargs):
        super(CANIDMappingTab, self).__init__(**kwargs)
        self._loaded = False

    def init_view(self, channel_cfg):
        self._loaded = False
        self.channel_cfg = channel_cfg
        self.ids.can_bus_channel.setValueMap({0: '1', 1: '2'}, '1')

        self.ids.sub_id.setValueMap({i:'Disabled' if i < 0 else str(i) for i in range(-1, 100)},
                                    'Disabled')
        # CAN bus
        self.ids.can_bus_channel.setFromValue(self.channel_cfg.mapping.can_bus)

        # CAN ID
        self.ids.can_id.text = '%X' % self.channel_cfg.mapping.can_id

        # CAN Sub ID
        self.ids.sub_id.setFromValue(self.channel_cfg.mapping.sub_id)

        # CAN mask
        self.ids.mask.text = str(self.channel_cfg.mapping.can_mask)
        self._loaded = True

    def _on_can_bus(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.can_bus = instance.getValueFromKey(value)

    def _on_can_id(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.can_id = int(value, 16)

    def _on_sub_id(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.sub_id = instance.getValueFromKey(value)

    def _on_mask(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.can_mask = int(value)

class CANValueMappingTab(CANChannelMappingTab):
    Builder.load_string("""
<CANValueMappingTab>:
    text: 'Raw Value Mapping'

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(5)
        BoxLayout:
            orientation: 'horizontal'
            spacing: dp(5)

            SectionBoxLayout:
                FieldLabel:
                    text: 'Offset'
                    halign: 'right'
                LargeMappedSpinner:
                    id: offset
                    on_text: root._on_mapping_offset(*args)
            SectionBoxLayout:
                FieldLabel:
                    halign: 'right'
                    text: 'Length'
                LargeMappedSpinner:
                    id: length
                    on_text: root._on_mapping_length(*args)
            SectionBoxLayout:
                FieldLabel:
                    text: 'Bit Mode'
                    halign: 'right'
                    size_hint_x: 0.7
                CheckBox:
                    id: bitmode
                    on_active: root._on_bit_mode(*args)
                    size_hint_x: 0.3
        BoxLayout:
            orientation: 'horizontal'
            spacing: dp(5)

            SectionBoxLayout:
                size_hint_x: 0.66
                FieldLabel:
                    text: 'Source Type'
                    halign: 'right'
                MappedSpinner:
                    id: source_type
                    on_text: root._on_source_type(*args)

            SectionBoxLayout:
                size_hint_x: 0.33
                FieldLabel:
                    text: 'Endian'
                    halign: 'right'
                MappedSpinner:
                    id: endian
                    on_text: root._on_endian(*args)
""")

    def __init__(self, **kwargs):
        super(CANValueMappingTab, self).__init__(**kwargs)
        self._loaded = False

    def init_view(self, channel_cfg):
        self._loaded = False
        self.channel_cfg = channel_cfg

        self.ids.endian.setValueMap({1: 'Big', 0: 'Little'}, 'Big')

        self.ids.source_type.setValueMap({CANMapping.CAN_MAPPING_TYPE_UNSIGNED: 'Unsigned',
                                          CANMapping.CAN_MAPPING_TYPE_SIGNED: 'Signed',
                                          CANMapping.CAN_MAPPING_TYPE_FLOAT: 'Float',
                                          CANMapping.CAN_MAPPING_TYPE_SIGN_MAGNITUDE: 'Sign-Magnitude'},
                                         'Unsigned')

        self.update_mapping_spinners()

        # CAN offset
        self.ids.offset.setFromValue(self.channel_cfg.mapping.offset)

        # CAN length
        self.ids.length.setFromValue(self.channel_cfg.mapping.length)

        # Bit Mode
        self.ids.bitmode.active = self.channel_cfg.mapping.bit_mode

        # Endian
        self.ids.endian.setFromValue(self.channel_cfg.mapping.endian)

        # source data type
        self.ids.source_type.setFromValue(self.channel_cfg.mapping.type)

        self._loaded = True

    def update_mapping_spinners(self):
        bit_mode = self.channel_cfg.mapping.bit_mode
        self.set_mapping_choices(bit_mode)

    def set_mapping_choices(self, bit_mode):
        offset_choices = 63 if bit_mode else 7
        length_choices = 32 if bit_mode else 4
        self.ids.offset.setValueMap(self.create_bit_choices(0, offset_choices), '0')
        self.ids.length.setValueMap(self.create_bit_choices(1, length_choices), '1')

    def create_bit_choices(self, starting, max_choices):
        bit_choices = {}
        for i in range(starting, max_choices + 1):
            bit_choices[i] = str(i)
        return bit_choices

    def _on_bit_mode(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.bit_mode = self.ids.bitmode.active
            self.update_mapping_spinners()

    def _on_mapping_offset(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.offset = instance.getValueFromKey(value)

    def _on_mapping_length(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.length = instance.getValueFromKey(value)

    def _on_endian(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.endian = instance.getValueFromKey(value)

    def _on_source_type(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.type = instance.getValueFromKey(value)

class CANFormulaMappingTab(CANChannelMappingTab):
    Builder.load_string("""
<CANFormulaMappingTab>:
    text: 'Formula'

    AnchorLayout:
        size_hint_y: 0.5
        SectionBoxLayout:
            orientation: 'horizontal'
            spacing: dp(5)
            FieldLabel:
                size_hint_x: 0.1
                halign: 'right'
                text: 'Raw'
            SymbolFieldLabel:
                size_hint_x: 0.1
                halign: 'center'
                text: u' \u00D7 '
            AnchorLayout:
                size_hint_x: 0.2
                LargeFloatValueField:
                    id: multiplier
                    size_hint_y: 0.7
                    on_text: root._on_multiplier(*args)
            SymbolFieldLabel:
                halign: 'center'
                text: u' \u00F7 '
                size_hint_x: 0.1
            AnchorLayout:
                size_hint_x: 0.2
                LargeFloatValueField:
                    id: divider
                    size_hint_y: 0.7
                    on_text: root._on_divider(*args)
            SymbolFieldLabel:
                text: ' + '
                halign: 'center'
                size_hint_x: 0.1
            AnchorLayout:
                size_hint_x: 0.2
                LargeFloatValueField:
                    id: adder
                    size_hint_y: 0.7
                    on_text: root._on_adder(*args)
""")

    def __init__(self, **kwargs):
        super(CANFormulaMappingTab, self).__init__(**kwargs)
        self._loaded = False

    def init_view(self, channel_cfg):
        self._loaded = False
        self.channel_cfg = channel_cfg

        # Multiplier
        self.ids.multiplier.text = str(self.channel_cfg.mapping.multiplier)

        # Divider
        self.ids.divider.text = str(self.channel_cfg.mapping.divider)

        # Adder
        self.ids.adder.text = str(self.channel_cfg.mapping.adder)

        self._loaded = True


    def _on_multiplier(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.multiplier = float(value)

    def _on_divider(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.divider = float(value)

    def _on_adder(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.adder = float(value)

class CANUnitsConversionMappingTab(CANChannelMappingTab):
    Builder.load_string("""
<CANUnitsConversionMappingTab>:
    text: 'Units Conversion'

    AnchorLayout:
        size_hint_y: 0.5
        BoxLayout:
            BoxLayout:
                size_hint_x: 0.1
            SectionBoxLayout:
                size_hint_x: 0.8
                FieldLabel:
                    halign: 'right'
                    size_hint_x: 0.6
                    text: 'Units Conversion'
                MappedSpinner:
                    id: filters
                    size_hint_x: 0.4
                    on_text: root._on_filter(*args)
            BoxLayout:
                size_hint_x: 0.1
    """)
    def __init__(self, **kwargs):
        super(CANUnitsConversionMappingTab, self).__init__(**kwargs)
        self._loaded = False

    def init_view(self, channel_cfg, units_conversion_filter):
        self._loaded = False
        self.channel_cfg = channel_cfg

        self.ids.filters.setValueMap(units_conversion_filter.filter_labels, units_conversion_filter.default_key)

        # Conversion Filter ID
        self.ids.filters.setFromValue(self.channel_cfg.mapping.conversion_filter_id)

        self.units_conversion_filter = units_conversion_filter

        self._loaded = True

    def _on_filter(self, instance, value):
        if self._loaded:
            filter_id = instance.getValueFromKey(value)
            self.channel_cfg.mapping.conversion_filter_id = filter_id
            from_units, to_units = self.units_conversion_filter.get_filter(int(filter_id))

            # automatically update the channel units to ensure consistency
            if to_units:
                self.channel_cfg.units = to_units

class CANChannelConfigView(BoxLayout):

    Builder.load_string("""
<CANChannelConfigView>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_accent()
        Rectangle:
            pos: self.pos
            size: self.size
    AndroidTabs:
        tab_indicator_color: ColorScheme.get_light_primary()
        id: tabs
""")

    def __init__(self, **kwargs):
        super(CANChannelConfigView, self).__init__(**kwargs)
        self.can_channel_customization_tab = CANChannelCustomizationTab()
        self.can_id_tab = CANIDMappingTab()
        self.can_value_map_tab = CANValueMappingTab()
        self.can_formula_tab = CANFormulaMappingTab()
        self.can_units_conversion_tab = CANUnitsConversionMappingTab()
        self.init_tabs()
        self.can_channel_customization_tab.bind(on_channel=self.on_channel_selected)

    def on_channel_selected(self, instance, channel_cfg):
        Clock.schedule_once(lambda dt: HelpInfo.help_popup('can_mapping_help', self, arrow_pos='left_mid'), 1.0)

    def init_tabs(self):
        self.ids.tabs.add_widget(self.can_channel_customization_tab)
        self.ids.tabs.add_widget(self.can_id_tab)
        self.ids.tabs.add_widget(self.can_value_map_tab)
        self.ids.tabs.add_widget(self.can_formula_tab)
        self.ids.tabs.add_widget(self.can_units_conversion_tab)


    def init_config(self, channel_cfg, can_filters, max_sample_rate, channels):
        self.channel_cfg = channel_cfg
        self.can_filters = can_filters
        self.max_sample_rate = max_sample_rate
        self.channels = channels
        self.load_tabs()

    def load_tabs(self):
        clock_sequencer([lambda dt: self.can_channel_customization_tab.init_view(self.channel_cfg, self.channels, self.max_sample_rate),
                         lambda dt: self.can_id_tab.init_view(self.channel_cfg),
                         lambda dt: self.can_value_map_tab.init_view(self.channel_cfg),
                         lambda dt: self.can_formula_tab.init_view(self.channel_cfg),
                         lambda dt: self.can_units_conversion_tab.init_view(self.channel_cfg, self.can_filters)
                         ])
