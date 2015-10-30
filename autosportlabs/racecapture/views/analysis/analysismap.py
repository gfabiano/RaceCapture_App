from kivy.properties import ObjectProperty
from kivy.app import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from autosportlabs.racecapture.views.analysis.analysiswidget import AnalysisWidget
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.racecapture.datastore import Filter
from iconbutton import IconButton

Builder.load_file('autosportlabs/racecapture/views/analysis/analysismap.kv')

class AnalysisMap(AnalysisWidget):
    SCROLL_FACTOR = 0.15
    track_manager = ObjectProperty(None)
    datastore = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AnalysisMap, self).__init__(**kwargs)
        self.track = None
        self.heat_enabed = False
        self.sources = []
        Window.bind(on_motion=self.on_motion)
                
    def on_center_map(self, *args):    
        scatter = self.ids.scatter
        scatter.scale = 1
        scatter.rotation = 0
        scatter.transform = Matrix().translate(self.pos[0], self.pos[1], 0)

    def add_option_buttons(self):
        self.append_option_button(IconButton(text=u'\uf096', on_press=self.on_center_map))
                    
    
    def on_options(self):
        if self.heat_enabed:
            for key in self.sources:
                self.remove_heat_values(key)
            self.heat_enabed = False
        else:
            for key in self.sources:
                self.add_heat_values('TPS', key)
            self.heat_enabed = True
        
    def on_motion(self, instance, event, motion_event):
        if motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            scatter = self.ids.scatter
            try:
                button = motion_event.button
                scale = scatter.scale
                if button == 'scrollup':
                    scale += self.SCROLL_FACTOR
                else:
                    if button == 'scrolldown':
                        scale -= self.SCROLL_FACTOR
                if scale < self.SCROLL_FACTOR:
                    scale = self.SCROLL_FACTOR
                scatter.scale = scale
            except:
                pass #no scrollwheel support
        
    def select_map(self, latitude, longitude):
        if self.track_manager:
            point = GeoPoint.fromPoint(latitude, longitude)
            track = self.track_manager.find_nearby_track(point)
            if track != None:
                self.ids.track.setTrackPoints(track.map_points)
                self.track = track

    def remove_reference_mark(self, source):
        self.ids.track.remove_marker(source)

    def add_reference_mark(self, source, color):
        self.ids.track.add_marker(source, color)

    def update_reference_mark(self, source, point):
        self.ids.track.update_marker(str(source), point)

    def add_map_path(self, source_key, path, color):
        self.sources.append(source_key)
        self.ids.track.add_path(str(source_key), path, color)

    def remove_map_path(self, source_key):
        self.ids.track.remove_path(str(source_key))
        self.sources.remove(source_key)

    def add_heat_values(self, channel, lap_ref):
        lap = lap_ref.lap
        session = lap_ref.session
        f = Filter().eq('LapCount', lap)
        dataset = self.datastore.query(sessions=[session], channels=[channel], data_filter=f)
        records = dataset.fetch_records()

        values = []
        for record in records:
            #pluck out just the channel value
            values.append(record[1])

        self.heat_values = values
        self.ids.track.add_heat_values(str(lap_ref), values)

    def remove_heat_values(self, lap_ref):
        self.ids.track.remove_heat_values(str(lap_ref))
