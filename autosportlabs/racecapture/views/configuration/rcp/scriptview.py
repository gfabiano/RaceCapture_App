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
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from pygments.formatters.bbcode import BBCodeFormatter  # explicit import to make pyinstaller work. do not remove
from kivy.uix.codeinput import CodeInput
from kivy.uix.textinput import TextInput
from pygments.lexers import PythonLexer
from kivy.app import Builder
from kivy.extras.highlight import KivyLexer
from pygments import lexers
from kivy.logger import Logger
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.uix.toast.kivytoast import toast
from iconbutton import IconButton, LabelIconButton
from settingsview import SettingsMappedSpinner
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.uix.button.widgetbuttons import LabelButton

from utils import paste_clipboard, is_mobile_platform


LOGFILE_POLL_INTERVAL = 1
LOGWINDOW_MAX_LENGTH_MOBILE = 1000
LOGWINDOW_MAX_LENGTH_DESKTOP = 10000

class LogLevelSpinner(SettingsMappedSpinner):
    '''
    A customized SettingsMappedSpinner to set the value for log levels
    '''
    def __init__(self, **kwargs):
        super(LogLevelSpinner, self).__init__(**kwargs)
        self.setValueMap({3: 'Error', 6: 'Info', 7:'Debug', 8:'Trace'}, 'Info')
        self.text = 'Info'

class LuaScriptingView(BaseConfigView):
    '''
    Script configuration and logfile view
    '''
    Builder.load_string("""
<LuaScriptingView>:
    BoxLayout:
        spacing: dp(10)
        padding: (dp(10), dp(10))
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.9
            id: lua_log_wrapper
            LuaCodeInput:
                id: lua_script
                size_hint_y: 0.75
                font_name: 'resource/fonts/RobotoMono-Regular.ttf'
                font_size: sp(16)
                on_text: root.on_script_changed(*args)
            Splitter:
                horizontal: False
                sizable_from: 'top'
                id: splitter
                ScrollContainer:
                    size_hint_y: 0.25
                    id: logfile_sv
                    do_scroll_x:False
                    TextInput:
                        id: logfile
                        font_name: 'resource/fonts/RobotoMono-Regular.ttf'
                        foreground_color: ColorScheme.get_light_primary_text()
                        background_color: ColorScheme.get_dark_background()
                        size_hint_y: None
                        height: max(self.minimum_height, logfile_sv.height)
        BoxLayout:
            height: dp(30)
            size_hint_y: None
            orientation: 'horizontal'
            id: buttons
            BoxLayout:
                size_hint_x: 0.3
                orientation: 'horizontal'
                CheckBox:
                    id: poll_log
                    size_hint_x: 0.25
                    on_active: root.enable_polling(*args)
                LabelButton:
                    size_hint_x: 0.75
                    halign: 'left'
                    text: 'Poll log'
                    on_press: root.toggle_polling()

            BoxLayout:
                size_hint_x: 0.25
                spacing: dp(5)
                orientation: 'horizontal'
                LogLevelSpinner:
                    size_hint_x: 0.5
                    size_hint_y: 1.0
                    id: log_level
                    on_control: root.set_logfile_level(*args)
            Label:
                size_hint_x: 0.1
            LabelIconButton:
                size_hint_x: None
                width: dp(90)
                title: "Copy"
                icon: u'\uf0c5'
                on_press: root.copy_log()
            BoxLayout:
                size_hint_x: 0.03
            LabelIconButton:
                size_hint_x: None
                width: dp(90)
                title: "Clear"
                icon: "\357\200\215"
                on_press: root.clear_log()
            BoxLayout:
                size_hint_x: 0.03                                                   
            LabelIconButton:
                id: run_script
                size_hint_x: None
                width: dp(90)
                title: "Run"
                icon: "\357\200\241"
                on_press: root.run_script()    
    """)

    def __init__(self, capabilities, **kwargs):
        super(LuaScriptingView, self).__init__(**kwargs)
        self.script_cfg = None
        self.register_event_type('on_config_updated')
        self._logwindow_max_length = LOGWINDOW_MAX_LENGTH_MOBILE\
            if is_mobile_platform() else LOGWINDOW_MAX_LENGTH_DESKTOP
        self.rc_api.addListener('logfile', lambda value, source: Clock.schedule_once(lambda dt: self.on_logfile(value)))
        self._capabilities = capabilities

        if not capabilities.has_script:
            self._hide_lua()

    def _hide_lua(self):
        self.ids.buttons.remove_widget(self.ids.run_script)
        self.ids.lua_log_wrapper.remove_widget(self.ids.lua_script)
        self.ids.splitter.strip_size = 0

    def on_config_updated(self, rcp_cfg):
        '''
        Callback when the configuration is updates
        :param rcp_cfg the RaceCapture configuration object
        :type RcpConfig
        '''
        cfg = rcp_cfg.scriptConfig

        if self._capabilities.has_script:
            self.ids.lua_script.text = cfg.script
            self.script_cfg = cfg

    def on_script_changed(self, instance, value):
        '''
        Callback when the script text changes
        :param instance the widget sourcing this event
        :type instance widget
        :param value the updated script value
        :type value string
        '''
        if self.script_cfg:
            self.script_cfg.script = value
            self.script_cfg.stale = True
            self.dispatch('on_modified')

    def copy_log(self):
        '''
        Copies the current logfile text to the system clipboard
        '''
        try:
            paste_clipboard(self.ids.logfile.text)
            toast('RaceCapture log copied to clipboard')
        except Exception as e:
            Logger.error("ApplicationLogView: Error copying RaceCapture log to clipboard: " + str(e))
            toast('Unable to copy to clipboard\n' + str(e), True)
            # Allow crash handler to report on exception
            raise e

    def on_logfile(self, logfile_rsp):
        '''
        Extracts the logfile response and updates the logfile window
        :param logfile_rsp the API response with the logfile response
        :type dict
        '''
        value = logfile_rsp.get('logfile').replace('\r', '').replace('\0', '')

        logfile_view = self.ids.logfile
        current_text = logfile_view.text
        current_text += str(value)
        overflow = len(current_text) - self._logwindow_max_length
        if overflow > 0:
            current_text = current_text[overflow:]
        logfile_view.text = current_text
        self.ids.logfile_sv.scroll_y = 0.0

    def clear_log(self):
        '''
        Clears the log file window
        '''
        self.ids.logfile.text = ''

    def toggle_polling(self, *args):
        '''
        Toggle polling state
        '''
        checkbox = self.ids.poll_log
        checkbox.active = True if checkbox.active == False else False

    def enable_polling(self, instance, value):
        '''
        Enables or disables logfile polling
        :param instance the widget instance performing the call
        :type instance widget
        :param value indicates True or False to enable polling
        :type level bool
        '''
        if value:
            Clock.schedule_interval(self.poll_logfile, LOGFILE_POLL_INTERVAL)
        else:
            Clock.unschedule(self.poll_logfile)

    def poll_logfile(self, *args):
        '''
        Sends the API command to poll the log file
        '''
        self.rc_api.getLogfile()

    def set_logfile_level(self, instance, level):
        '''
        Sends the API command to set the logfile level
        :param instance the widget instance performing the call
        :type instance widget
        :param level the numeric log file level
        :type level int
        '''
        self.rc_api.setLogfileLevel(level, None, self.on_set_logfile_level_error)

    def on_set_logfile_level_error(self, detail):
        '''
        Callback for error condition of setting the logfile
        :param detail the description of the error
        :type detail string
        '''
        toast('Error Setting Logfile Level:\n\n{}'.format(detail), length_long=True)

    def run_script(self, *args):
        '''
        Sends the API command to re-run the script.
        '''
        self.rc_api.runScript(self.on_run_script_complete, self.on_run_script_error)

    def on_run_script_complete(self, result):
        '''
        Callback when the script has been restarted successfully
        :param result the result of the API call
        :type result dict
        '''
        toast('Script restarted')

    def on_run_script_error(self, detail):
        '''
        Callback when the script fails to restart
        :param detail the description of the error
        :type detail string
        '''
        toast('Error Running Script:\n\n{}'.format(str(detail)), length_long=True)

class LuaCodeInput(CodeInput):
    '''
    Wrapper class for CodeInput that sets the Lua Lexer
    '''
    def __init__(self, **kwargs):
        super(LuaCodeInput, self).__init__(**kwargs)
        self.lexer = lexers.get_lexer_by_name('lua')


