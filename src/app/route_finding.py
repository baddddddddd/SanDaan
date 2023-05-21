from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy_garden.mapview import MapMarkerPopup, Coordinate
from kivymd.uix.bottomnavigation import MDBottomNavigation
from kivymd.uix.bottomsheet import MDListBottomSheet
from kivymd.uix.list import MDList, OneLineListItem
import json

from common import API_URL, SendRequest, TopScreenLoadingBar
from interactive_map import InteractiveMap
from route_mapping import ROUTE_MAPPING_TAB
from search_view import SearchBar


MAPVIEW_SCREEN = '''
#:import MapView kivy_garden.mapview.MapView

<NavBar>:
    #panel_color: "#eeeaea"
    selected_color_background: "orange"
    text_color_active: "lightgrey"


MDScreen:
    name: "mapview"        

    NavBar:
        #
'''

ROUTE_FINDING_TAB = '''
MDBottomNavigationItem:
    name: "route_finding"
    text: "Routes"
    icon: "routes"

    MDFloatLayout:
        RouteFinding:
            id: map
            lat: 13.78530
            lon: 121.07339
            zoom: 15
            loading_bar: loading

        TopScreenLoadingBar:
            id: loading

        SearchBar:
            map: map

        MDFloatingActionButton:
            icon: "crosshairs-gps"
            pos_hint: {"center_x": 0.875, "center_y": 0.235}
            on_release:
                map.follow_user()

        MDFloatingActionButton:
            icon: "directions"
            pos_hint: {"center_x": 0.875, "center_y": 0.125}
            on_release:
                map.request_directions() 
'''


class NavBar(MDBottomNavigation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Clock.schedule_once(self.on_widget_built)


    def on_widget_built(self, dt):
        self.add_widget(Builder.load_string(ROUTE_FINDING_TAB))
        self.add_widget(Builder.load_string(ROUTE_MAPPING_TAB))


class RouteFinding(InteractiveMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pinned_location = None
        self.pinned_location_pin = None

        self.route_bottomsheet = MDListBottomSheet()


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.place_pin(self.get_latlon_at(touch.x, touch.y, self.zoom))

        return super().on_touch_down(touch)


    def place_pin(self, coordinate: Coordinate):
        if self.pinned_location is not None:
            self.remove_pin()

        self.pinned_location = coordinate
        self.pinned_location_pin = self.MapPin(
            lat=coordinate.lat,
            lon=coordinate.lon,
            remove_callback=lambda _: self.remove_pin(),
        )
        self.add_widget(self.pinned_location_pin)


    def remove_pin(self):
        if len(self.graphed_route) > 0:
            self.graphed_route = []
            self.canvas.remove(self.graph_line)
        
        self.pinned_location = None
        self.remove_marker(self.pinned_location_pin)


    def request_directions(self):
        if self.pinned_location is not None:
            self.get_origin_address()


    def get_origin_address(self):
        self.get_address_by_location(self.current_location, lambda _, result: self.get_destination_address(result))


    def get_destination_address(self, result):
        origin_address = result["address"]
        origin_address["city_id"] = result["place_id"]
        self.get_address_by_location(self.pinned_location, lambda _, result: self.get_directions(result, origin_address))


    def get_directions(self, result, origin_address):
        destination_address = result["address"]
        destination_address["city_id"] = result["place_id"]

        origin_region = origin_address["region"]
        origin_state = origin_address["state"]
        origin_city_id = origin_address["city_id"]
        destination_region = destination_address["region"]
        destination_state = destination_address["state"]
        destination_city_id = destination_address["city_id"]

        region = None
        state = None
        city_id = None

        if origin_region == destination_region:
            region = origin_region

            if origin_state == destination_state:
                state = origin_state

                if origin_city_id == destination_city_id:
                    city_id = origin_city_id


        url = f"{API_URL}/directions"

        origin = self.current_location
        destination = self.pinned_location
        
        body = json.dumps({
            "origin": [origin.lat, origin.lon],
            "destination": [destination.lat, destination.lon],
            "route_area": {
                "city_id": city_id,
                "state": state,
                "region": region,
            },
        })

        SendRequest(
            url=url,
            body=body,
            on_success=lambda _, result: self.show_viable_routes(result), 
            on_failure=self.handle_connection_error,
            loading_indicator=self.loading_bar,
        )


    def show_viable_routes(self, result):
        viable_routes = result["routes"]

        for route_steps in viable_routes:
            name = " + ".join([route["name"] for route in route_steps])

            test_coords = []
            for route in route_steps:
                test_coords += route["coords"]
            #test_coords = [route["coords"] for route in route_steps]
            self.route_bottomsheet.add_item(
                text=f"{name}",
                callback=lambda _, coords=test_coords: self.draw_route(coords),
            )
        self.route_bottomsheet.open()


    def handle_connection_error(self, urlrequest, result):
        print(urlrequest)
        print(result)
        print("Connection Error")
