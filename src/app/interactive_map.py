from kivy.clock import Clock
from kivy.graphics import Line, Color
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.utils import platform
from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup, Coordinate
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from plyer import gps
from urllib import parse

from common import API_URL, HEADERS, SendRequest


class InteractiveMap(MapView):
    loading_bar = ObjectProperty(None)
    current_location = Coordinate(13.78530, 121.07339)
    has_initialized_gps = False

    instances = []


    class MapPin(MapMarkerPopup):
        def __init__(self, lat, lon, remove_callback):
            super().__init__(lat=lat, lon=lon)
            self.remove_button = MDIconButton(
                icon="delete",
                icon_size=dp(36),
                theme_icon_color="Custom",
                icon_color="black",
            )
            self.remove_button.bind(on_release= lambda obj: remove_callback(obj))

            self.add_widget(self.remove_button)

            self.disabled = True
            Clock.schedule_once(lambda *_: self.enable_input(), 0.2)


        def remove_pin(self):
            self.parent.parent.remove_marker(self)      


        def enable_input(self):
            self.disabled = False


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Default location, which is Batangas State University - Alangilan, coordinate if GPS is not available
        self.current_location_pin = MapMarker(
            lat=13.78530,
            lon=121.07339,
        )
        self.add_widget(self.current_location_pin)

        # Request permission for accessing GPS in Android devices
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            
            gps.configure(on_location=lambda **kwargs: InteractiveMap.update_location(kwargs))
            gps.start()

        self.graphed_route = []
        self.graph_line = None

        self.main_dialog = MDDialog()
        
        InteractiveMap.instances.append(self)


    # Function to call every time the GPS updates
    def update_location(kwargs):
        # Update the user's current location with the provided info by the GPS
        InteractiveMap.current_location = Coordinate(kwargs["lat"], kwargs["lon"])

        # Change the user's location pin to new coordinates for all instances of the map
        for instance in InteractiveMap.instances:
            instance.current_location_pin.lat = kwargs["lat"]
            instance.current_location_pin.lon = kwargs["lon"]

        # Centralize map on the current location of the user once the GPS has initialized
        if not InteractiveMap.has_initialized_gps and len(InteractiveMap.instances) == 2:
            InteractiveMap.has_initialized_gps = True

            for instance in InteractiveMap.instances:
                instance.centralize_map_on(InteractiveMap.current_location)
                instance.zoom = 15


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.redraw_route()

        return super().on_touch_move(touch)
    

    def on_zoom(self, instance, zoom):
        self.redraw_route()
        return super().on_zoom(instance, zoom)


    def centralize_map_on(self, coords: Coordinate):
        self.center_on(coords.lat, coords.lon)
        self.redraw_route()


    def follow_user(self):
        self.centralize_map_on(self.current_location)
        self.zoom = 15


    def redraw_route(self):
        if len(self.graphed_route) > 0 and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.draw_route(self.graphed_route)


    def remove_route(self):
        if len(self.graphed_route) > 0 and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.graphed_route = []


    def search_location(self, query: str, on_success_callback):
        url = "https://nominatim.openstreetmap.org/search?"

        params = {
            "q": query,
            "limit": 10,
            "format": "json",
            "addressdetails": 1,
        }

        url_params = parse.urlencode(params)
        url += url_params

        # Use a unique user agent
        headers = {'User-Agent': 'SanDaan/1.0'}

        SendRequest(
            url=url, 
            headers=headers,
            loading_indicator=self.loading_bar,
            on_success=on_success_callback,
            auto_refresh=False,
        )


    def get_address_by_location(self, coord: Coordinate, on_success_callback, zoom = 10):
        url = "https://nominatim.openstreetmap.org/reverse?"

        params = {
            "lat": coord.lat,
            "lon": coord.lon,
            "format": "json",
            "addressdetails": 1,
            "zoom": zoom,
        }

        url_params = parse.urlencode(params)
        url += url_params

        # Use a unique user agent
        headers = {'User-Agent': 'SanDaan/1.0'}

        SendRequest(
            url=url,
            headers=headers,
            loading_indicator=self.loading_bar,
            on_success=on_success_callback,
            auto_refresh=False,
        )


    def draw_directions(self, result):
        route = result["route"]
        self.graphed_route = route

        self.draw_route(self.graphed_route)

    
    def draw_route(self, route: list):
        # Remeber the graphed route for redrawing purposes
        self.graphed_route = route
        
        # Get the pixel coordinates that correspond with the coordinates on the route
        points = [self.get_window_xy_from(coord[0], coord[1], self.zoom) for coord in route]

        with self.canvas:
            # Equivalent of rgba(29, 53, 87), which is the primary color of the palette used for UI
            Color(0.27058823529411763, 0.4823529411764706, 0.615686274509804)
            self.graph_line = Line(points=points, width=3, cap="round", joint="round")


    def show_popup_dialog(self, title: str, content=None):
        self.main_dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=lambda _: self.close_popup_dialog(),
                ),
            ],
        )
        self.main_dialog.open()


    def close_popup_dialog(self):
        self.main_dialog.dismiss()
