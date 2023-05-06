from kivy.graphics import Line, Color
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivy_garden.mapview import MapView, MapMarker, Coordinate
from plyer import gps
from urllib import parse
import json

from common import API_URL, HEADERS


class InteractiveMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Default location, which is Batangas State University - Alangilan, coordinate if GPS is not available
        self.current_location = Coordinate(13.78530, 121.07339)
        self.current_location_pin = MapMarker(
            lat=13.78530,
            lon=121.07339,
        )
        self.add_widget(self.current_location_pin)

        self.has_initialized_gps = False

        # Request permission for accessing GPS in Android devices
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            
            gps.configure(on_location=self.update_location)
            gps.start()

            # SanDaan API URL for hosting API on the web server
            # API_URL = "https://sandaan-api.onrender.com"

        self.graphed_route = None
        self.graph_line = None


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


    def update_location(self, **kwargs):
        if not self.has_initialized_gps:
            self.has_initialized_gps = True
            self.current_location = Coordinate(kwargs["lat"], kwargs["lon"])
            self.centralize_map_on(self.current_location)
            self.zoom = 15

        self.current_location_pin.lat = kwargs["lat"]
        self.current_location_pin.lon = kwargs["lon"]


    def redraw_route(self):
        if self.graphed_route is not None and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.draw_route(self.graphed_route)


    def remove_route(self):
        if self.graphed_route is not None and self.graph_line is not None:
            self.canvas.remove(self.graph_line)
            self.graphed_route = []


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

        UrlRequest(url=url, req_headers=headers, on_success=on_success_callback)


    def draw_directions(self, urlrequest, result):
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

