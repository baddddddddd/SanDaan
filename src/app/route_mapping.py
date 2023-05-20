from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.mapview import MapMarkerPopup, Coordinate
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.textfield import MDTextField
import datetime
import json

from common import API_URL, SendRequest, TopScreenLoadingBar
from interactive_map import InteractiveMap
from search_view import SearchBar


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

class RouteInformation(BoxLayout):
    def __init__(self, confirmation_button):
        super().__init__()
        self.confirmation_button = confirmation_button

        self.name_field = MDTextField(
            hint_text="Route name",
        )
        self.name_field.bind(text=lambda *_: self.check_complete())
        self.add_widget(self.name_field)

        self.desc_field = MDTextField(
            hint_text="Route description",
            multiline=True,
        )
        self.desc_field.bind(height=self.update_height)
        self.desc_field.bind(text=lambda *_: self.check_complete())
        self.add_widget(self.desc_field)

        self.start_time_button = MDRaisedButton(
            text="Pick Start Time",
            pos_hint={'center_x': .5, 'center_y': .5},
            on_release=self.show_start_time_picker,
        )

        self.start_time_dialog = MDTimePicker(time=datetime.time.fromisoformat("00:00:00"))
        self.add_widget(self.start_time_button)

        self.end_time_button = MDRaisedButton(
            text="Pick End Time",
            pos_hint={'center_x': .5, 'center_y': .5},
            on_release=self.show_end_time_picker,
        )

        self.end_time_dialog = MDTimePicker(time=datetime.time.fromisoformat("00:00:00"))
        self.add_widget(self.end_time_button)


    def show_start_time_picker(self, *args):
        self.start_time_dialog.open()

    
    def show_end_time_picker(self, *args):
        self.end_time_dialog.open()


    def update_height(self, *args):
        self.height = sum([children.height for children in self.children])


    def check_complete(self):
        self.confirmation_button.disabled = self.name_field.text == "" or self.desc_field.text == ""


class RouteMapping(InteractiveMap):
    confirm_route_button = ObjectProperty(None)


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
            self.parent.parent.connect_all_pins()
            self.parent.parent.remove_marker(self)      


        def enable_input(self, *args):
            self.disabled = False


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.remove_widget(self.current_location_pin)
        self.pins = []
        self.graph_line = None
        self.waiting_for_route = False
       
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
    
        self.help_dialog = MDDialog(
            title="Route Mapping Manual",
            type="custom",
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=lambda _: self.help_dialog.dismiss(),
                ),
            ],
        )


    def update_dialog_height(self, *args):
        new_height = sum([children.height for children in self.confirmation_dialog.content_cls.children])
        self.confirmation_dialog.update_height(new_height)
        

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap and not self.waiting_for_route:
                # Place pin on the map
                coord = self.get_latlon_at(touch.x, touch.y, self.zoom)
                self.place_route_pin(coord)

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
        
        pin_coords = [(pin.lat, pin.lon) for pin in self.pins[-2:]]
        body = json.dumps({
            "pins": pin_coords,
        })

        SendRequest(
            url=url,
            body=body,
            loading_indicator=self.loading_bar,
            on_success=lambda _, result: self.connect_route(result),
        )

        self.confirm_route_button.disabled = True
        self.waiting_for_route = True


    def connect_route(self, result):  
        if len(self.pins) == 2:
            self.graphed_route += result["route"]
            self.draw_route(self.graphed_route)
        else:
            self.graphed_route += result["route"][1:]
            self.redraw_route()

        self.confirm_route_button.disabled = len(self.graphed_route) < 2
        self.waiting_for_route = False


    def connect_all_pins(self):
        if len(self.pins) < 2:
            self.confirm_route_button.disabled = True
            return
        
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
        )
        
        self.confirm_route_button.disabled = True
        self.waiting_for_route = True


    def redraw_all(self, result):
        self.remove_route()
        self.draw_directions(result)

        self.confirm_route_button.disabled = len(self.graphed_route) < 2
        self.waiting_for_route = False


    def confirm_route(self):
        self.confirmation_dialog.open()


    def cancel_confirmation(self, *args):
        self.confirmation_dialog.dismiss()


    def get_route_address(self, index):
        # Get location by address all the nodes by using nominatim and the bounding box
        coord = self.graphed_route[index]
        self.get_address_by_location(Coordinate(coord[0], coord[1]), lambda _, result: self.check_bounds(result, index))
        

    def check_bounds(self, result, index):
        result["address"]["city_id"] = result["place_id"]
        self.route_addresses.append(result["address"])

        bounding_box = result["boundingbox"]
        lat_min = float(bounding_box[0])
        lat_max = float(bounding_box[1])
        lon_min = float(bounding_box[2])
        lon_max = float(bounding_box[3])

        for i, coord in enumerate(self.graphed_route[index + 1:]):
            lat = coord[0]
            lon = coord[1]

            # Check if any of the points is outside the bounding box of the place
            if not (lat_min <= lat and lat <= lat_max and lon_min <= lon and lon <= lon_max):
                self.get_route_address(index + i + 1)
                return

        self.upload_route()


    def upload_route(self, *args):
        # Get all the data from the dialog
        route_info = self.confirmation_dialog.content_cls

        name = route_info.name_field.text
        desc = route_info.desc_field.text
        start_time = str(route_info.start_time_dialog.time)
        end_time = str(route_info.end_time_dialog.time)

        # Record all the places the route passes
        cities = []
        states = []
        regions = []

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
            on_success=lambda _, result: self.show_upload_success(result),
        )


    def show_upload_success(self, result):
        # Show dialog that the upload is success
        print(result)
