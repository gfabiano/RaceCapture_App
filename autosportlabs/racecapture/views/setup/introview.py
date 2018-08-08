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
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.views.setup.infoview import InfoView

INTRO_VIEW_KV = """
<IntroView>:
    background_source: 'resource/setup/background_intro.jpg'
    info_text: 'This guide will help you set up your system and provide a short tour of the features.\\n\\nLet\\'s get started!'
"""

class IntroView(InfoView):
    """
    Introductory / Welcome screen. 
    """
    Builder.load_string(INTRO_VIEW_KV)
    def __init__(self, **kwargs):
        super(IntroView, self).__init__(**kwargs)

    def on_enter(self, *args):
        self.ids.next.pulsing = True
