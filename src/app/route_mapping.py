from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.mapview import MapMarkerPopup, Coordinate
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
import json

from common import API_URL
from interactive_map import InteractiveMap


MAP_ROUTING_SCREEN = '''
#:import MapView kivy_garden.mapview.MapView

<RouteInformation>:
    orientation: "vertical"
    spacing: "12dp"
    size_hint_y: None
    height: "120dp"

    MDTextField:
        hint_text: "Route name"

    MDTextField:
        hint_text: "Route description"
        multiline: True

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
                map_routing.connect_all_pins()

        MDFloatingActionButton:
            icon: "upload"
            pos_hint: {"center_x": 0.875, "center_y": 0.235}
            on_release:
                map_routing.confirm_route()
        
'''

class RouteInformation(BoxLayout):
    pass


class RouteMapping(InteractiveMap):
    # Button to confirm route and upload
        # Upon pressing, user will be asked to name the route and add description (additional info)
        # User will also be asked of the time range that the route is available
        # User will also be asked of the vicinity of the route (Brgy, City, Province, Region) for database design purposes

    class RoutePin(MapMarkerPopup):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.remove_button = OneLineListItem(text="Remove")
            self.remove_button.bind(on_release=self.remove_marker)

            self.options = MDList(
                md_bg_color="#000000"
            )

            self.options.add_widget(self.remove_button)
            self.add_widget(self.options)

            self.disabled = True
            Clock.schedule_once(self.enable_input, 0.2)


        def remove_marker(self, *args):
            self.parent.parent.pins.remove(self)

            if len(self.parent.parent.pins) >= 2:
                self.parent.parent.connect_all_pins()

            if len(self.parent.parent.pins) >= 1:
                self.parent.parent.remove_route()
                
            self.parent.parent.remove_marker(self)      


        def enable_input(self, *args):
            self.disabled = False


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pins = []
        self.graphed_route = []
        self.graph_line = None
        self.waiting_for_route = False
        self.dialog = MDDialog(
            title="Route Information",
            type="custom",
            content_cls=RouteInformation(),
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    on_release=self.cancel_confirmation,
                ),
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=self.upload_route,
                ),
            ],
        )


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap and not self.waiting_for_route:
                # place pin
                coord = self.get_latlon_at(touch.x, touch.y, self.zoom)
                self.place_route_pin(coord)
                

                # get nearest node

                # check if nearest node is last node
                # if not, pathfind from last node to chosen node
                # graph pathfinded route
                # add pathfinded route to route_nodes

        return super().on_touch_down(touch)


    def place_route_pin(self, coord: Coordinate):
        route_pin = self.RoutePin(
            lat=coord.lat,
            lon=coord.lon,
        )

        self.pins.append(route_pin)                
        self.add_widget(route_pin)

        if len(self.pins) <= 1:
            return
        
        url = f"{API_URL}/route"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins[-2:]]
        body = json.dumps({
            "pins": pin_coords,
        })

        UrlRequest(url=url, req_headers=headers, req_body=body, on_success=self.connect_route)

        self.waiting_for_route = True


    def connect_route(self, urlrequest, result):  
        if len(self.pins) == 2:
            self.graphed_route += result["route"]
            self.draw_route(self.graphed_route)
        else:
            self.graphed_route += result["route"][1:]
            self.redraw_route()

        self.waiting_for_route = False


    def connect_all_pins(self):
        url = f"{API_URL}/route"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins]
        body = json.dumps({
            "pins": pin_coords,
        })

        UrlRequest(url=url, req_headers=headers, req_body=body, on_success=self.redraw_all)
        
        self.waiting_for_route = True


    def redraw_all(self, urlrequest, result):
        self.draw_directions(urlrequest, result)
        self.waiting_for_route = False


    def confirm_route(self):
        self.dialog.open()


    def cancel_confirmation(self, *args):
        self.dialog.dismiss()


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
