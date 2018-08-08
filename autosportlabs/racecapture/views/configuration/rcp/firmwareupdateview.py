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

from kivy.properties import ObjectProperty
from kivy import platform
from kivy.clock import Clock
from settingsview import SettingsMappedSpinner, SettingsSwitch
from mappedspinner import MappedSpinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import Builder
from kivy import platform
from kivy.logger import Logger
from autosportlabs.racecapture.views.util.alertview import confirmPopup
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup
from asl_f4_loader import fw_update
from time import sleep
from threading import Thread
import traceback

FIRMWARE_UPDATE_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/firmwareupdateview.kv'

RESET_DELAY = 1000
# TODO: MK1 support
class FirmwareUpdateView(BaseConfigView):
    progress_gauge = ObjectProperty(None)
    _settings = None
    Builder.load_file(FIRMWARE_UPDATE_VIEW_KV)

    def __init__(self, **kwargs):
        super(FirmwareUpdateView, self).__init__(**kwargs)
        self._settings = kwargs.get('settings', None)
        self.register_event_type('on_config_updated')
        self.ids.fw_progress.ids.add_gauge.text = ''

    def on_config_updated(self, rcpCfg):
        pass

    def check_online(self):
        popup = Popup(title='Check Online',
                      content=Label(text='Coming soon!'),
                      size_hint=(None, None), size=(400, 400))
        popup.open()

    def set_firmware_file_path(self, path):
        self._settings.userPrefs.set_pref('preferences', 'firmware_dir', path)

    def get_firmware_file_path(self):
        return self._settings.userPrefs.get_pref('preferences', 'firmware_dir')

    def _select_file(self):
        def _on_answer(instance):
            popup.dismiss()
            self._start_update_fw(instance)

        def dismiss_popup(self, *args):
            popup.dismiss()

        user_path = self.get_firmware_file_path()
        content = LoadDialog(ok=_on_answer,
                             cancel=dismiss_popup,
                             filters=['*' + '.ihex'],
                             user_path=user_path)
        popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def _update_progress_gauge(self, percent):
        def update_progress(pct):
            self.ids.fw_progress.value = int(pct)
        Clock.schedule_once(lambda dt: update_progress(percent))

    def _teardown_json_serial(self):
        Logger.info('FirmwareUpdateView: Disabling RaceCapture Communcications')
        # It's ok if this fails, in the event of no device being present,
        # we just need to disable the com port
        self.rc_api.disable_autorecover()
        try:
            # Windows workaround (because windows sucks at enumerating
            # USB in a timely fashion)
            self.rc_api.resetDevice(True, RESET_DELAY)
            self.rc_api.shutdown_comms()
        except:
            pass
        sleep(5)

    def _restart_json_serial(self):
        Logger.info('FirmwareUpdateView: Re-enabling RaceCapture Communications')
        self.rc_api.enable_autorecover()
        self.rc_api.run_auto_detect()

    def _update_thread(self, instance):
        try:
            selection = instance.selection
            filename = selection[0] if len(selection) else None
            if filename:
                # Even though we stopped the RX thread, this is OK
                # since it doesn't return a value
                self.ids.fw_progress.title = "Processing"

                self._teardown_json_serial()

                self.ids.fw_progress.title = "Progress"

                # Get our firmware updater class and register the
                # callback that will update the progress gauge
                fu = fw_update.FwUpdater(logger=Logger)
                fu.register_progress_callback(self._update_progress_gauge)

                retries = 5
                port = None
                while retries > 0 and not port:
                    # Find our bootloader
                    port = fu.scan_for_device()

                    if not port:
                        retries -= 1
                        sleep(2)

                if not port:
                    self.ids.fw_progress.title = ""
                    raise Exception("Unable to locate bootloader")

                # Go on our jolly way
                fu.update_firmware(filename, port)
                self.ids.fw_progress.title = "Restarting"

                # Sleep for a few seconds since we need to let USB re-enumerate
                sleep(3)
            else:
                alertPopup('Error Loading', 'No firmware file selected')
        except Exception as detail:
            alertPopup('Error Loading', 'Failed to Load Firmware:\n\n{}'.format(detail))
            Logger.error(traceback.format_exc())

        self._restart_json_serial()
        self.ids.fw_progress.value = ''
        self.ids.fw_progress.title = ""

    def update_pre_check(self):

        popup = None
        def _on_answer(inst, answer):
            popup.dismiss()
            if answer == True:
                self._select_file()
        popup = confirmPopup('Ready to update firmware',
                             'Please ensure your configuration is saved before continuing\n',
                             _on_answer)

    def _start_update_fw(self, instance):
        self.set_firmware_file_path(instance.path)
        # The comma is necessary since we need to pass in a sequence of args
        t = Thread(target=self._update_thread, args=(instance,))
        t.daemon = True
        t.start()

