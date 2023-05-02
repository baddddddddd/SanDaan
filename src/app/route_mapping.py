from kivy.network.urlrequest import UrlRequest
from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup, Coordinate
from kivymd.uix.list import MDList, OneLineListItem
import json

from common import API_URL
from interactive_map import InteractiveMap


MAP_ROUTING_SCREEN = '''
#:import MapView kivy_garden.mapview.MapView

MDScreen:
    name: "map_routing"

    FloatLayout:
        RouteMapping:
            id: map_routing
            lat: 13.78530
            lon: 121.07339
            zoom: 15

        
        MDFloatingActionButton:
            icon: "map-plus"
            pos_hint: {"center_x": 0.875, "center_y": 0.125}
            on_release:
                map_routing.submit_pins()

        MDFloatingActionButton:
            icon: "upload"
            pos_hint: {"center_x": 0.875, "center_y": 0.235}
            on_release:
                map_routing.upload_route()
        
'''

class RouteMapping(InteractiveMap):

    # Defined GUI Controls
    # Double tap to add pin
    # Tap pin to open pin options
    # Pin options include:
    #   * Remove Pin
    #   * Move Pin
    #   * Rearrange Order (Change index of Pin)
    # Button to draw route
    # Button to confirm route and upload
        # Upon pressing, user will be asked to name the route and add description (additional info)
        # User will also be asked of the time range that the route is available
        # User will also be asked of the vicinity of the route (Brgy, City, Province, Region) for database design purposes

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.route_nodes = []

        self.pins = []
        self.graphed_route = None
        self.graph_line = None


    class RoutePin(MapMarkerPopup):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.remove_button = OneLineListItem(text="Remove")
            self.remove_button.bind(on_release=self.remove_marker)

            self.popup_layout = MDList(

            )
            self.add_widget(self.remove_button)

        def remove_marker(self, *args):
            self.parent.parent.pins.remove(self)
            self.parent.parent.remove_marker(self)


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                # place pin
                coord = self.get_latlon_at(touch.x, touch.y, self.zoom)
                route_pin = self.RoutePin(
                    lat=coord.lat,
                    lon=coord.lon,
                    
                )

                self.pins.append(route_pin)                
                self.add_widget(route_pin)

                # get nearest node

                # check if nearest node is last node
                # if not, pathfind from last node to chosen node
                # graph pathfinded route
                # add pathfinded route to route_nodes

        return super().on_touch_down(touch)


    def place_pin(self, coordinate: Coordinate):
        self.pinned_location_pin = MapMarker(
            lat=coordinate.lat,
            lon=coordinate.lon,
        )
        self.add_widget(self.pinned_location_pin)


    def submit_pins(self):
        url = f"{API_URL}/route"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins]
        body = json.dumps({
            "pins": pin_coords,
        })

        UrlRequest(url=url, req_headers=headers, req_body=body, on_success=self.draw_directions)

        print('awdawd')


    def upload_route(self):
        url = f"{API_URL}/add_route"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        body = json.dumps({
            "name": "gch",
            "description": "wala lang",
            "coords": self.graphed_route,
        })

        UrlRequest(url=url, req_headers=headers, req_body=body, on_success=self.draw_directions)


    def check(self, urlrequest, result):
        print(urlrequest)
        print(result)
