from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.mapview import Coordinate
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.textfield import MDTextField
import datetime
import json

from common import API_URL, SendRequest, TopScreenLoadingBar
from interactive_map import InteractiveMap
from search_view import SearchBar


# Kivy string for the route mapping view tab
ROUTE_MAPPING_TAB = '''
#:import MapView kivy_garden.mapview.MapView

<RouteInformation>:
    orientation: "vertical"
    spacing: "12dp"
    size_hint_y: None
    height: "120dp"


MDBottomNavigationItem:
    name: "route_mapping"
    text: "Contribute"
    icon: "map-plus"

    FloatLayout:
        RouteMapping:
            id: map
            lat: 13.78530
            lon: 121.07339
            zoom: 15
            loading_bar: loading
            confirm_route_button: confirm_route_button

        TopScreenLoadingBar:
            id: loading

        SearchBar:
            map: map

        MDFloatingActionButton:
            id: confirm_route_button
            icon: "check-bold"
            pos_hint: {"center_x": 0.875, "center_y": 0.32}
            disabled: True
            on_release:
                map.confirm_route()

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


# Form for inputting information about the mapped route
class RouteInformation(BoxLayout):
    def __init__(self, confirmation_button):
        super().__init__()
        self.confirmation_button = confirmation_button

        # Create field for the route name
        self.name_field = MDTextField(
            hint_text="Route name",
            max_text_length=50,
        )
        self.name_field.bind(text=lambda *_: self.check_complete())
        self.add_widget(self.name_field)

        # Create field for the route description
        self.desc_field = MDTextField(
            hint_text="Route description",
            multiline=True,
            max_text_length=255,
        )
        self.desc_field.bind(height=self.update_height)
        self.desc_field.bind(text=lambda *_: self.check_complete())
        self.add_widget(self.desc_field)

        # Create a button to show a time picker for setting the starting time of the route based on its schedule
        self.start_time_button = MDRaisedButton(
            text="Pick Start Time",
            pos_hint={'center_x': .5, 'center_y': .5},
            on_release=self.show_start_time_picker,
        )

        # Create a time picker for selecting the starting time
        self.start_time_dialog = MDTimePicker(time=datetime.time.fromisoformat("00:00:00"))
        self.add_widget(self.start_time_button)

        # Create a button to show a time picker for setting the ending time of the route based on its schedule
        self.end_time_button = MDRaisedButton(
            text="Pick End Time",
            pos_hint={'center_x': .5, 'center_y': .5},
            on_release=self.show_end_time_picker,
        )

        # Create a time picker for selecting the ending time
        self.end_time_dialog = MDTimePicker(time=datetime.time.fromisoformat("23:59:59"))
        self.add_widget(self.end_time_button)


    # Called when user clicks the "Pick Start Time" button
    def show_start_time_picker(self, *args):
        self.start_time_dialog.open()

    
    # Called when user clicks the "Pick End Time" button
    def show_end_time_picker(self, *args):
        self.end_time_dialog.open()


    # Called when the user enters a new line in the route description
    # Adjusts the height of the dialog accordingly
    def update_height(self, *args):
        self.height = sum([children.height for children in self.children])


    # Checks if the route name and description is not empty
    # If not, disable the confirmation button
    def check_complete(self):
        self.confirmation_button.disabled = self.name_field.text == "" or self.desc_field.text == ""


# Create a map with functionalities to create or map routes
class RouteMapping(InteractiveMap):
    # Store reference to the "Confirm Route" button
    confirm_route_button = ObjectProperty(None)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Hide the pin that shows the user's current location
        self.remove_widget(self.current_location_pin)
        
        # Store the pins that are used to map the route
        self.pins = []

        # Flag variable to disable functionalities when app is waiting for SanDaan API
        # to return a route
        self.waiting_for_route = False
       
        # Set up and create a dialog for requesting route information from the user
        # before uploading
        self.confirmation_button = MDFlatButton(
            text="OK",
            theme_text_color="Custom",
            on_release=lambda _, index = 0: self.get_route_address(index),
            disabled=True,
        )

        self.route_information = RouteInformation(self.confirmation_button)
        self.confirmation_dialog = MDDialog(
            title="Route Information",
            type="custom",
            content_cls=self.route_information,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    on_release=self.cancel_confirmation,
                ),
                self.confirmation_button,
            ],
        )
        self.route_information.bind(height=self.update_dialog_height)

        self.route_addresses = []
    
        # Create a tutorial message for the route mapping manual
        tutorial_message = '''1. Place pins (double tap) to trace the path that the transport route takes
2. To remove a pin, tap on the pin and click the delete icon
3. Please wait for the route to be processed every time you place or remove a pin (indicated by a loading bar on the top of your screen)
4. If done mapping, press the Check button to confirm the route.
5. For the route name, enter the "cards" that commuters would see in jeepneys or buses (such as "North Bayan" or "Alangilan" or "G. terminal")
6. For the route description, enter any additional information that would help the commuters (such as fees or warnings)
7. (Optional) For the start time and end time, pick the time range that the transport route is available (example 4:00 AM to 7:00 PM)
8. After reviewing that the information you put is correct, press OK then wait
'''

        # Inner function to disable editing of the route mapping manual
        def disable_focus():
            content_cls.focus = False

        # Display the tutorial message using a textfield
        content_cls = MDTextField(
            text=tutorial_message,
            multiline=True,
            text_color_normal="white",
        )
        content_cls.bind(focus=lambda *_: disable_focus())

        # Create a dialog for the route mapping manual
        self.help_dialog = MDDialog(
            title="Route Mapping Manual",
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


    # Update the dialog height depending on the height of its children so that it all fits inside
    def update_dialog_height(self, *args):
        new_height = sum([children.height for children in self.confirmation_dialog.content_cls.children])
        self.confirmation_dialog.update_height(new_height)
        

    # Wrapper function for removing pins
    def remove_pin(self, pin_button):
        # Disable this feature if the app is waiting for the SanDaan API to respond
        if self.waiting_for_route:
            return

        # Get the map pin that the button corresponds to
        pin = pin_button.parent.parent

        # Remember pin to be removed for undoing purposes
        self.removed_pin = pin
        self.removed_pin_index = self.pins.index(pin)
        self.pins.remove(pin)

        # Reconnect all the pins based on the remaining pins
        self.connect_all_pins()

        # Remove the pin from the map
        self.remove_marker(pin)


    # Called when user touches the screen
    def on_touch_down(self, touch):
        # Check if the touch was directed to the map
        if self.collide_point(*touch.pos):
            # Check if the touch is a double tap, if yes, add a pin to where the touch happened
            # Disabled when app is waiting for the SanDaan API to respond
            if touch.is_double_tap and not self.waiting_for_route:
                # Place pin on the map
                coord = self.get_latlon_at(touch.x, touch.y, self.zoom)
                self.place_route_pin(coord)

        return super().on_touch_down(touch)


    # Place pin on the map and connect to the previous pin
    def place_route_pin(self, coord: Coordinate):
        # Places the pin on the map
        route_pin = self.MapPin(
            lat=coord.lat,
            lon=coord.lon,
            remove_callback=self.remove_pin,
        )

        self.pins.append(route_pin)                
        self.add_widget(route_pin)

        if len(self.pins) <= 1:
            return
        
        # Endpoint for requesting the shortest path between a list of coordinates
        # through the SanDaan API
        url = f"{API_URL}/route"
        
        # Convert the coordinates into tuples
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins[-2:]]
        body = json.dumps({
            "pins": pin_coords,
        })

        SendRequest(
            url=url,
            body=body,
            loading_indicator=self.loading_bar,
            on_success=lambda _, result: self.connect_route(result),
            on_failure=lambda _, result: self.remove_last_pin(result),
        )

        # Disable the "Confirm Route" button and set the flag variable
        self.confirm_route_button.disabled = True
        self.waiting_for_route = True


    # Called when the HTTP request for getting the shortest path between a list of coordinates failed
    # Removes the last pin, which caused the error, from the map
    def remove_last_pin(self, result):
        unknown_error_message = "An unknown error occured."
        error_message = result.get("msg", unknown_error_message) if isinstance(result, dict) else unknown_error_message
        self.show_popup_dialog(
            "Failed to connect pins",
            MDLabel(
                text=error_message,
            ),
        )

        self.remove_marker(self.pins.pop())
        self.waiting_for_route = False


    # Called when the HTTP request for getting the shortest path between a list of coordinates succeeded
    # Connects the last pin from the previous pin
    def connect_route(self, result):  
        # Check if the number of pins is exactly two, if yes, draw the route from scratch
        # If no, connect the new route to the existing graphed route
        if len(self.pins) == 2:
            self.graphed_route += result["route"]
            self.draw_route(self.graphed_route)
        else:
            self.graphed_route += result["route"][1:]
            self.redraw_route()

        # Re-enable the "Confirm Route" button if there is a graphed route
        self.confirm_route_button.disabled = len(self.graphed_route) < 2
        self.waiting_for_route = False


    # Called when a pin was deleted
    # Connects all the remaining pins in a shortest path possible
    def connect_all_pins(self):
        # Check if the number of remaining pins is less than two
        # If yes, remove the graphed route from the screen and disable the "Confirm Route" button
        if len(self.pins) < 2:
            self.remove_route()
            self.confirm_route_button.disabled = True
            return
        
        # Endpoint for finding the shortest path between a list of coordinates through the SanDaan API
        url = f"{API_URL}/route"
        
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins]
        body = json.dumps({
            "pins": pin_coords,
        })

        SendRequest(
            url=url,
            body=body,
            loading_indicator=self.loading_bar,
            on_success=lambda _, result: self.redraw_all(result),
            on_failure=lambda _, result: self.undo_pin_remove(),
        )
        
        # Disable the "Confirm Route" button and set the flag that the app is waiting for response
        self.confirm_route_button.disabled = True
        self.waiting_for_route = True


    # Redraws the new route from the remaining pins
    def redraw_all(self, result):
        self.remove_route()
        self.draw_route(result["route"])

        # Re-enable the "Confirm Route" button if there is a graphed route
        self.confirm_route_button.disabled = len(self.graphed_route) < 2
        self.waiting_for_route = False


    # Called when a route cannot be constructed from the remaining pins
    # Undos the pin removal, and show the user what went wrong
    def undo_pin_remove(self, result):
        # Display a dialog that shows what went wrong
        unknown_error_message = "An unknown error occured."
        error_message = result.get("msg", unknown_error_message) if isinstance(result, dict) else unknown_error_message
        
        self.show_popup_dialog(
            "Failed to connect pins",
            MDLabel(
                text=error_message,
            ),
        )
        
        # Re-add the pin that was removed to the list of pins and to the map
        self.pins.insert(self.removed_pin_index, self.removed_pin)
        self.add_widget(self.removed_pin)

        # Re-enable the "Confirm Route" button if there is a graphed route
        self.confirm_route_button.disabled = len(self.graphed_route) < 2
        self.waiting_for_route = False


    # Called when the user clicks the "Confirm Route" button
    def confirm_route(self):
        self.confirmation_dialog.open()


    # Called when the user clicks the "Cancel" button in the route confirmation dialog
    def cancel_confirmation(self, *args):
        self.confirmation_dialog.dismiss()


    # Get the vicinity or area that covers the whole route
    def get_route_address(self, index):
        # Disable the "OK" button to avoid sending multiple duplicate requests
        self.confirmation_button.disabled = True

        # Get location by address all the nodes by using nominatim and the bounding box
        coord = self.graphed_route[index]
        self.get_address_by_location(Coordinate(coord[0], coord[1]), lambda _, result: self.check_bounds(result, index))
        

    # Check if the route crosses out the current vicinity of the route
    # If it does, increase the vicinity or area of the route
    def check_bounds(self, result, index):
        result["address"]["city_id"] = result["place_id"]
        self.route_addresses.append(result["address"])

        # Define the bounding box of the current vicinity of the route
        bounding_box = result["boundingbox"]
        lat_min = float(bounding_box[0])
        lat_max = float(bounding_box[1])
        lon_min = float(bounding_box[2])
        lon_max = float(bounding_box[3])

        # Iterate each coordinate of the route
        for i, coord in enumerate(self.graphed_route[index + 1:]):
            lat = coord[0]
            lon = coord[1]

            # Check if any of the points is outside the bounding box of the place
            if not (lat_min <= lat and lat <= lat_max and lon_min <= lon and lon <= lon_max):
                self.get_route_address(index + i + 1)
                return

        self.upload_route()


    # Called when all the route information has been processed and ready for uploading
    def upload_route(self, *args):
        # Get all the data from the dialog
        route_info = self.confirmation_dialog.content_cls

        name = route_info.name_field.text
        desc = route_info.desc_field.text
        start_time = str(route_info.start_time_dialog.time)
        end_time = str(route_info.end_time_dialog.time)

        # Record all the places that the route passes
        cities = []
        states = []
        regions = []

        # Get how many cities, states, or regions the route crosses
        for address in self.route_addresses:
            city_id = address["city_id"]
            state = address["state"]
            region = address["region"]

            if city_id not in cities:
                cities.append(city_id)
            
            if state not in states:
                states.append(state)

            if region not in regions:
                regions.append(region)

        # Check if route crosses cities, states, or regions
        route_region = regions[0] if len(regions) == 1 else None
        route_state = states[0] if len(states) == 1 else None
        route_city = cities[0] if len(cities) == 1 else None

        # Upload the route using the API
        url = f"{API_URL}/contribute"
                
        body = json.dumps({
            "name": name,
            "description": desc,
            "start_time": start_time,
            "end_time": end_time,
            "coords": self.graphed_route,
            "region": route_region,
            "state": route_state,
            "city_id": route_city,
        })

        SendRequest(
            url=url,
            body=body,
            loading_indicator=self.loading_bar,
            on_success=lambda _, result: self.handle_upload_success(result),
            on_failure=lambda _, result: self.handle_upload_failure(result),
        )


    # Called when uploading the route succeeded
    def handle_upload_success(self, result):
        # Show dialog that the upload is success
        self.confirmation_dialog.dismiss()
        success_message = result.get("msg", "")
        content_cls = MDLabel(text=success_message)
        self.show_popup_dialog("Route upload success", content_cls)   
           
        # Clear all pins and graphs
        for pin in self.pins:
            self.remove_marker(pin)

        self.pins = []
        self.remove_route()

        # Clear route information
        self.route_information = RouteInformation(self.confirmation_button)
        self.confirm_route_button.disabled = True


    # Called when uploading the route failed
    def handle_upload_failure(self, result):
        # Show dialog that the upload failed and why it failed
        unknown_error_message = "An unknown error occured."
        error_message = result.get("msg", unknown_error_message) if isinstance(result, dict) else unknown_error_message
        content_cls = MDLabel(text=error_message)
        self.show_popup_dialog("Route upload failed", content_cls)

        # Re-enable the "OK" button to allow reuploading the route
        self.confirmation_button.disabled = False
        