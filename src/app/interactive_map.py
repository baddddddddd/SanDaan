from kivy.clock import Clock
from kivy.graphics import Line, Color
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.utils import platform
from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup, Coordinate
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from plyer import gps
from urllib import parse

from common import API_URL, HEADERS, SendRequest


# Main class for implementing an interactive map
class InteractiveMap(MapView):
    # Variable for storing the reference to the loading bar for visual feedback
    loading_bar = ObjectProperty(None)

    # Store the coordinates of the user's current location to be shared by all instances
    # Defaults to the coordinates of BSU Alangilan in cases where GPS is not available
    current_location = Coordinate(13.78530, 121.07339)
    has_initialized_gps = False

    # Store references to all the instances of this class
    instances = []


    # Inner class for placing pains on the map with extra functionality
    class MapPin(MapMarkerPopup):
        def __init__(self, lat, lon, remove_callback):
            super().__init__(lat=lat, lon=lon)

            # Create a remove button to allow removing of the map pins
            self.remove_button = MDIconButton(
                icon="delete",
                icon_size=dp(36),
                theme_icon_color="Custom",
                icon_color="black",
            )
            self.remove_button.bind(on_release= lambda obj: remove_callback(obj))

            self.add_widget(self.remove_button)

            # Disable receiving inputs for this widget until it has finished building
            self.disabled = True
            Clock.schedule_once(lambda *_: self.enable_input(), 0.2)


        # Function to remove the pin from the map
        def remove_pin(self):
            self.parent.parent.remove_marker(self)      


        # Function to start accepting inputs once this widget has finished building
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
            
            # Set the function to call every time the GPS updates
            gps.configure(on_location=lambda **kwargs: InteractiveMap.update_location(kwargs))
            gps.start()

        # Store the coordinates of the graphed route as well as its drawn graphics
        self.graphed_route = []
        self.graph_line = None

        # Create dialog for showing messages to the user
        self.main_dialog = MDDialog()
        
        # Add itself to the list of instances
        InteractiveMap.instances.append(self)

        # Centralize map on the current location if GPS has initialized already
        if InteractiveMap.has_initialized_gps:
            self.centralize_map_on(InteractiveMap.current_location)
            self.zoom = 15


    # Function to call every time the GPS updates
    def update_location(kwargs):
        # Update the user's current location with the provided info by the GPS
        InteractiveMap.current_location = Coordinate(kwargs["lat"], kwargs["lon"])

        # Change the user's location pin to new coordinates for all instances of the map
        for instance in InteractiveMap.instances:
            instance.current_location_pin.lat = kwargs["lat"]
            instance.current_location_pin.lon = kwargs["lon"]

        # Centralize map on the current location of the user once the GPS has initialized
        if not InteractiveMap.has_initialized_gps:
            InteractiveMap.has_initialized_gps = True

            for instance in InteractiveMap.instances:
                instance.centralize_map_on(InteractiveMap.current_location)
                instance.zoom = 15


    # Called when user move's the screen
    def on_touch_move(self, touch):
        # Check if the touch input is directed to the map
        if self.collide_point(*touch.pos):
            # Redraw the graphed route so that the route lines align to the new position of the map
            self.redraw_route()

        # Call the default behaviour
        return super().on_touch_move(touch)
    

    # Called when user zooms in or out the map
    def on_zoom(self, instance, zoom):
        # Redraw the graphed route so that the route lines align to the new size of the map
        self.redraw_route()

        # Call the default behaviour
        return super().on_zoom(instance, zoom)


    # Wrapper function to centralize the map on a specific geological coordinate
    def centralize_map_on(self, coords: Coordinate):
        # Actual function that centralized the map to a coordinate
        self.center_on(coords.lat, coords.lon)

        # Redraw the graphed route so that it aligns with the new position of the map
        self.redraw_route()


    # Centralizes the map to the current location of the user
    def follow_user(self):
        self.centralize_map_on(self.current_location)
        self.zoom = 15


    # Function for redrawing the graphed route
    def redraw_route(self):
        if len(self.graphed_route) > 0 and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.draw_route(self.graphed_route)


    # Function for deleting the graphed route from the screen
    def remove_route(self):
        if len(self.graphed_route) > 0 and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.graphed_route = []


    # Called when user confirms to search a location using the search bar
    def search_location(self, query: str, on_success_callback):
        # Endpoint for geocoding provided by the OpenStreetMap API
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


    # Function for getting the city, state, or country based on geological coordinates
    def get_address_by_location(self, coord: Coordinate, on_success_callback, zoom = 10):
        # Endpoint for reverse geocoding provided by the OpenStreetMap API
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

    
    # Draw routes based on a given list of coordinates
    def draw_route(self, route: list):
        # Remember the graphed route for redrawing purposes
        self.graphed_route = route
        
        # Get the pixel coordinates that correspond with the coordinates on the route
        points = [self.get_window_xy_from(coord[0], coord[1], self.zoom) for coord in route]

        # Draw the route on the canvas
        with self.canvas:
            # Equivalent of rgba(29, 53, 87), which is the primary color of the palette used for UI
            Color(0.27058823529411763, 0.4823529411764706, 0.615686274509804)
            self.graph_line = Line(points=points, width=dp(3), cap="round", joint="round")


    # Helper function to for showing dialog messages to user
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


    # Called when the OK button was clicked on the popup dialog
    def close_popup_dialog(self):
        self.main_dialog.dismiss()
