from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy_garden.mapview import Coordinate
from kivymd.uix.bottomnavigation import MDBottomNavigation
from kivymd.uix.bottomsheet import MDListBottomSheet
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
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
            directions_button: directions_button
            steps_button: steps_button

        TopScreenLoadingBar:
            id: loading

        SearchBar:
            map: map

        MDFloatingActionButton:
            id: steps_button
            icon: "view-agenda"
            pos_hint: {"center_x": 0.875, "center_y": 0.43}
            disabled: True
            on_release:
                map.view_route_steps()
                
        MDFloatingActionButton:
            id: directions_button
            icon: "directions"
            pos_hint: {"center_x": 0.875, "center_y": 0.32}
            disabled: True
            on_release:
                map.request_directions()

        MDFloatingActionButton:
            icon: "crosshairs-gps"
            pos_hint: {"center_x": 0.875, "center_y": 0.21}
            on_release:
                map.follow_user()

        MDFloatingActionButton:
            icon: "help"
            pos_hint: {"center_x": 0.875, "center_y": 0.10}
            on_release:
                map.help_dialog.open() 
'''


class NavBar(MDBottomNavigation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Clock.schedule_once(self.on_widget_built)


    def on_widget_built(self, dt):
        self.add_widget(Builder.load_string(ROUTE_FINDING_TAB))
        self.add_widget(Builder.load_string(ROUTE_MAPPING_TAB))


class RouteFinding(InteractiveMap):
    directions_button = ObjectProperty(None)
    steps_button = ObjectProperty(None)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pinned_location = None
        self.pinned_location_pin = None

        self.route_bottomsheet = MDListBottomSheet()

        self.selected_route = None
        self.start_walk = None
        self.end_walk = None

        tutorial_message = '''1. Place a pin (double tap) at the destination that you want to go to.
2. Press the "Directions" (arrow) button then wait for the results.
3. A list of different route combinations will show up. Select the route combination that you want to view.
4. After selecting a route combination, a list of individual transport routes will be shown, select these routes one by one to view the route in the map.
5. To go back to the list of individual transport routes, click the "View Panel" (two rectangles) button 
6. To change target destination, double tap again anywhere on the map.
7. To remove a pin, click on the pin then select "Remove"
'''

        def disable_focus():
            content_cls.focus = False

        content_cls = MDTextField(
            text=tutorial_message,
            multiline=True,
            text_color_normal="white",
        )
        content_cls.bind(focus=lambda *_: disable_focus())

        self.help_dialog = MDDialog(
            title="Route Finding Manual",
            type="custom",
            content_cls=content_cls,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=lambda _: self.help_dialog.dismiss(),
                ),
            ],
        )


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

        self.directions_button.disabled = False


    def remove_pin(self):
        if len(self.graphed_route) > 0:
            self.graphed_route = []
            self.canvas.remove(self.graph_line)
        
        self.pinned_location = None
        self.remove_marker(self.pinned_location_pin)

        self.directions_button.disabled = True
        self.steps_button.disabled = True


    def request_directions(self):
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
            on_failure=lambda _, result: self.show_route_finding_error(result),
            loading_indicator=self.loading_bar,
        )


    def show_viable_routes(self, result):        
        viable_routes = result["routes"]
        start_walk = result["start_walk"]
        end_walk = result["end_walk"]

        if len(viable_routes) == 0:
            self.show_popup_dialog(
                title="No routes found",
                content=MDLabel(
                    text="There are currently no routes in the database that connects you to your destination, consider contributing! :D",
                ),
            )
            return
        
        self.route_bottomsheet = MDListBottomSheet()

        for route_steps in viable_routes:
            name = " + ".join([route_step["name"] for route_step in route_steps])

            self.route_bottomsheet.add_item(
                text=f"{name}",
                callback=lambda _, route_steps=route_steps: self.select_route(route_steps, start_walk, end_walk),
            )

        self.route_bottomsheet.open()


    def view_route_steps(self):
        self.route_bottomsheet = MDListBottomSheet()

        if len(self.start_walk) > 1:
            self.route_bottomsheet.add_item(
                text=f"Walk from current location",
                callback=lambda _, coords=self.start_walk: self.draw_route_step(coords),
            )

        for route in self.selected_route:
            name = route["name"]
            desc = route["description"]
            uploader = route["uploader_id"]
            coords = route["coords"]

            self.route_bottomsheet.add_item(
                text=f"{name}",
                callback=lambda _, coords=coords: self.draw_route_step(coords),
            )   

        if len(self.end_walk) > 1:
            self.route_bottomsheet.add_item(
                text=f"Walk to destination",
                callback=lambda _, coords=self.end_walk: self.draw_route_step(coords),
            )         

        self.route_bottomsheet.open()


    def draw_route_step(self, coords):
        self.remove_route()
        self.draw_route(coords)


    def select_route(self, route_steps, start_walk, end_walk):
        self.start_walk = start_walk
        self.end_walk = end_walk
        self.selected_route = route_steps
        self.steps_button.disabled = False
        self.view_route_steps()


    def show_route_finding_error(self, result):
        self.show_popup_dialog(
            title="Route finding error",
            content=MDLabel(
                text=result.get("msg", "An unknown error occured."),
            ),
        )
