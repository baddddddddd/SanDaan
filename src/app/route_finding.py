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


# Kivy string for the mapview screen
MAPVIEW_SCREEN = '''
#:import MapView kivy_garden.mapview.MapView

<NavBar>:
    text_color_active: "lightgrey"


MDScreen:
    name: "mapview"        

    NavBar:
        #
'''

# Kivy string for the route finding view tab
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


# Create a navigation bar to allow switching between route finding and route mapping
class NavBar(MDBottomNavigation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        Clock.schedule_once(lambda _: self.on_widget_built())


    # Called when the navigation bar has finished building
    def on_widget_built(self):
        self.add_widget(Builder.load_string(ROUTE_FINDING_TAB))
        self.add_widget(Builder.load_string(ROUTE_MAPPING_TAB))


# Create a map with functionalities for finding routes
class RouteFinding(InteractiveMap):
    # Store reference to the "Get Directions" and "View Route Steps" button
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
7. To remove a pin, click on the pin then click on the delete icon
'''

        # Inner function to bind behaviour when user clicked on the tutorial message
        # Disables editing of the tutorial message for the user
        def disable_focus():
            content_cls.focus = False

        # Store the tutorial message in a text field
        content_cls = MDTextField(
            text=tutorial_message,
            multiline=True,
            text_color_normal="white",
        )
        content_cls.bind(focus=lambda *_: disable_focus())

        # Create a dialog popup for showing tutorial and usage instructions
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


    # Called when user touches the screen
    def on_touch_down(self, touch):
        # Check if the touch was directed to the map
        if self.collide_point(*touch.pos):
            # Check if the touch was a double tap, if yes, place a pin to where the user touched
            # the map, otherwise ignore
            if touch.is_double_tap:
                self.place_pin(self.get_latlon_at(touch.x, touch.y, self.zoom))

        # Call the default behaviour
        return super().on_touch_down(touch)


    # Called when user double taps on the map, which places a pin
    def place_pin(self, coordinate: Coordinate):
        # Check if there are existing pins places, if yes, remove first
        if self.pinned_location is not None:
            self.remove_pin()

        # Set the pinned location to the coordinate of the map where the pin was placed
        self.pinned_location = coordinate
        self.pinned_location_pin = self.MapPin(
            lat=coordinate.lat,
            lon=coordinate.lon,
            remove_callback=lambda _: self.remove_pin(),
        )
        self.add_widget(self.pinned_location_pin)

        # Enable the "Get Directions" button
        self.directions_button.disabled = False


    # Called when user clicks the "Delete" button of map pins
    def remove_pin(self):
        # Check if there is a graphed route associated with the pin
        # If yes, remove the graphed route
        if len(self.graphed_route) > 0:
            self.graphed_route = []
            self.canvas.remove(self.graph_line)
        
        # Reset variables related to the pin
        self.pinned_location = None
        self.remove_marker(self.pinned_location_pin)

        # Disable the "Get Directions" and "Show Route Steps" button
        self.directions_button.disabled = True
        self.steps_button.disabled = True


    # Called when the user clicks the "Get Directions" button
    def request_directions(self):
        self.get_origin_address()


    # Gets the address of the current location of the user
    def get_origin_address(self):
        self.get_address_by_location(self.current_location, lambda _, result: self.get_destination_address(result))


    # Called right after successfully getting the address of the user's current location
    # Gets the address of the target destination of the user
    def get_destination_address(self, result):
        origin_address = result["address"]
        origin_address["city_id"] = result["place_id"]
        self.get_address_by_location(self.pinned_location, lambda _, result: self.get_directions(result, origin_address))


    # Called right after successfully getting the address of the user's target location
    # Function to request directions from the SanDaan API
    def get_directions(self, result, origin_address):
        # Get all the required data for requesting directions
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

        # Get the vicinity that covers both the user's current location and target location
        if origin_region == destination_region:
            region = origin_region

            if origin_state == destination_state:
                state = origin_state

                if origin_city_id == destination_city_id:
                    city_id = origin_city_id


        # Endpoint for requesting directions in the SanDaan API
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


    # Called when successfully fetched directions from the SanDaan API
    def show_viable_routes(self, result):   
        # Get the results from the HTTP request     
        viable_routes = result["routes"]
        start_walk = result["start_walk"]
        end_walk = result["end_walk"]

        # Check if there was any routes found, if none, show a dialog message notifying the user
        if len(viable_routes) == 0:
            self.show_popup_dialog(
                title="No routes found",
                content=MDLabel(
                    text="There are currently no routes in the database that connects you to your destination, consider contributing! :D",
                ),
            )
            return
        
        # Create a widget for displaying the results
        self.route_bottomsheet = MDListBottomSheet()

        # Iterate each route combination from the result
        for route_steps in viable_routes:
            # Create a string to display the names of the route combination
            name = " + ".join([route_step["name"] for route_step in route_steps])

            # Add the route combination in list of results
            self.route_bottomsheet.add_item(
                text=f"{name}",
                callback=lambda _, route_steps=route_steps: self.select_route(route_steps, start_walk, end_walk),
            )

        self.route_bottomsheet.open()


    # Called when the user selects a route combination
    # Remembers the selected route combination of the user
    def select_route(self, route_steps, start_walk, end_walk):
        self.start_walk = start_walk
        self.end_walk = end_walk
        self.selected_route = route_steps
        self.steps_button.disabled = False
        self.view_route_steps()
        
    
    # Called when user clicks the "View Route Steps" button
    def view_route_steps(self):
        # Create a widget to display the route steps
        self.route_bottomsheet = MDListBottomSheet()

        # Check if the user has to walk a route to get to the main road or first transport route
        # If yes, add the walking route to the route steps
        if len(self.start_walk) > 1:
            self.route_bottomsheet.add_item(
                text=f"Walk from current location",
                callback=lambda _, coords=self.start_walk: self.draw_route_step(coords),
            )

        # Iterate each route in the selected route combination
        # Then add each route in the route steps
        for route in self.selected_route:
            name = route["name"]
            coords = route["coords"]

            self.route_bottomsheet.add_item(
                text=f"{name}",
                callback=lambda _, coords=coords: self.draw_route_step(coords),
            )   

        # Check if the user has to walk to get to the target location
        # If yes, add to the route steps
        if len(self.end_walk) > 1:
            self.route_bottomsheet.add_item(
                text=f"Walk to destination",
                callback=lambda _, coords=self.end_walk: self.draw_route_step(coords),
            )         

        self.route_bottomsheet.open()


    # Called when user requests to display a route step from the selected route combination
    # Draws the route in the screen for the user to view
    def draw_route_step(self, coords):
        self.remove_route()
        self.draw_route(coords)


    # Called when there was an error requesting for directions from the SanDaan API
    # Shows the error message as a popup dialog
    def show_route_finding_error(self, result):
        unknown_error_message = "An unknown error occured."
        error_message = result.get("msg", unknown_error_message) if isinstance(result, dict) else unknown_error_message
        
        self.show_popup_dialog(
            title="Route finding error",
            content=MDLabel(
                text=error_message,
            ),
        )
