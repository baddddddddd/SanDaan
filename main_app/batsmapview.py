from kivy_garden.mapview import MapView
from kivy_garden.mapview.source import MapSource
from kivy.clock import Clock
from kivy.app import App

class BatsMapView(MapView):
    def __init__(self, **kwargs):
        # For displaying the copyright of OSM
        attribution_text = "Copyright © OpenStreetMap contributors. " \
                           "Licensed under the Open Data Commons Open Database License (ODbL)."
        source = MapSource(attribution=attribution_text)
        super().__init__(map_source=source, **kwargs)

