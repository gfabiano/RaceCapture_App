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

import re
from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.app import Builder

VALUE_FIELD_KV = """
<ValueField>:
    font_size: self.height * 0.6
    multiline: False
    write_tab: False
"""
class ValueField(TextInput):

    Builder.load_string(VALUE_FIELD_KV)

    def __init__(self, *args, **kwargs):
        self.next = kwargs.pop('next', None)
        super(ValueField, self).__init__(*args, **kwargs)

    def on_focus(self, instance, value):
        if value:
            Window.bind(on_keyboard=self._on_keyboard)
        else:
            Window.unbind(on_keyboard=self._on_keyboard)
            self.dispatch('on_text_validate')

    def set_next(self, next):
        self.next = next

    def _on_keyboard(self, keyboard, keycode, *args):
        if keycode == 9:  # tab
            if self.next is not None:
                self.next.focus = True
            self.dispatch('on_text_validate')

class TextValueField(ValueField):
    max_len = NumericProperty(100)

    def insert_text(self, substring, from_undo=False):
        if len(self.text) < self.max_len:
            # strip out any tabs
            if len(substring) > 0 and substring[-1] == '\t':
                substring = substring[:-1]
            super(TextValueField, self).insert_text(substring, from_undo=from_undo)

class NumericValueField(ValueField):
    min_value = NumericProperty(None, allownone=True)
    max_value = NumericProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        super(NumericValueField, self).__init__(*args, **kwargs)
        self.bind(on_text_validate=self.validate_minmax)
        self.input_type = 'number'

    def validate_minmax(self, *args):
        try:
            value = int(self.text)
            if self.min_value is not None and value < self.min_value:
                self.text = str(self.min_value)
            if self.max_value is not None and value > self.max_value:
                self.text = str(self.max_value)
        except:
            pass

class IntegerValueField(NumericValueField):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        if '-'  in substring and not '-' in self.text:
            return super(IntegerValueField, self).insert_text(substring, from_undo=from_undo)

        s = re.sub(self.pat, '', substring)
        super(IntegerValueField, self).insert_text(s, from_undo=from_undo)

class HexIntegerValueField(NumericValueField):
    pat = re.compile('[^a-fA-F0-9]')

    def insert_text(self, substring, from_undo=False):
        if '-'  in substring and not '-' in self.text:
            return super(HexIntegerValueField, self).insert_text(substring, from_undo=from_undo)

        s = re.sub(self.pat, '', substring)
        super(HexIntegerValueField, self).insert_text(s, from_undo=from_undo)

class FloatValueField(NumericValueField):
    pat = re.compile('[^0-9]')

    def insert_text(self, substring, from_undo=False):
        if '-' in substring and not '-' in self.text:
            return super(FloatValueField, self).insert_text(substring, from_undo=from_undo)
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        super(FloatValueField, self).insert_text(s, from_undo=from_undo)

