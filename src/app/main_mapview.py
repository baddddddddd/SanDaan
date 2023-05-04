from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.network.urlrequest import UrlRequest
from kivy_garden.mapview import MapLayer, MapMarker, Coordinate
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.bottomsheet import MDListBottomSheet
from urllib import parse

from interactive_map import InteractiveMap
from route_mapping import ROUTE_MAPPING_TAB


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

    FloatLayout:
        MainMapView:
            id: map
            lat: 13.78530
            lon: 121.07339
            zoom: 15

        MDTextField:
            id: search_location
            hint_text: "Search location"
            mode: "round"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.98}
            on_text_validate: 
                map.get_coordinates_by_address(search_location.text)

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


class MainMapView(InteractiveMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pinned_location = None
        self.pinned_location_pin = None

        self.route_bottomsheet = MDListBottomSheet()

        for i in range(1, 11):
            self.route_bottomsheet.add_item(
                f"Standart Item {i}",
                lambda x, y=i: self.callback_for_menu_items(
                    f"Standart Item {y}"
                ),
            )


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                if self.pinned_location is None:
                    self.place_pin(self.get_latlon_at(touch.x, touch.y, self.zoom))
                else:
                    self.remove_pin()

        return super().on_touch_down(touch)


    def place_pin(self, coordinate: Coordinate):
        self.pinned_location = coordinate
        self.pinned_location_pin = MapMarker(
            lat=coordinate.lat,
            lon=coordinate.lon,
        )
        self.add_widget(self.pinned_location_pin)


    def remove_pin(self):
        if self.graphed_route is not None:
            self.graphed_route = None
            self.canvas.remove(self.graph_line)
        
        self.pinned_location = None
        self.remove_widget(self.pinned_location_pin)


    def request_directions(self):
        self.route_bottomsheet.open()

        if self.pinned_location is not None:
            self.get_directions(self.current_location, self.pinned_location, "drive")


    def get_coordinates_by_address(self, address):
        address = parse.quote(address)

        # Use a unique user agent
        headers = {'User-Agent': 'SanDaan/1.0'}

        # Used Nominatim for easier Geocoding instead of OSM API because it doesn't have geocoding and reverse geocoding
        url = f'https://nominatim.openstreetmap.org/search?q={address}&format=json&addressdetails=1&limit=1'
        UrlRequest(url, on_success=self.success, on_failure=self.failure, on_error=self.error, req_headers=headers)


    def handle_connection_error(self, urlrequest, result):
        print(urlrequest)
        print(result)
        print("Connection Error")


    def success(self, urlrequest, result):
        latitude = float(result[0]['lat'])
        longitude = float(result[0]['lon'])
        self.centralize_map_on(Coordinate(latitude, longitude))
        self.zoom = 15


    def failure(self, urlrequest, result):
        print("Failed")
        print(result)


    def error(self, urlrequest, result):
        print("Error")
        print(result)