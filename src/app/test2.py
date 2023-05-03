MAPVIEW_SCREEN = '''
#:import MapView kivy_garden.mapview.MapView

MDScreen:
    name: "mapview"

    FloatLayout:
        InteractiveMap:
            id: map
            lat: 13.78530
            lon: 121.07339
            zoom: 15
            on_parent:
                self.set_search_list(root.ids.search_list)

        MDTextField:
            id: search_location
            hint_text: "Search location"
            mode: "round"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.98}
            on_text_validate:
                if app.root.get_screen("mapview"): map = app.root.get_screen("mapview").ids.map, map.get_coordinates_by_address(search_location.text), map.add_suggestion(search_location.text)
                #app.root.get_screen("mapview").ids.map.get_coordinates_by_address(search_location.text) if app.root.get_screen("mapview") else None
        MDScrollView:
            size_hint: 0.9, 0.4
            pos_hint: {'center_x': 0.5, 'top': 0.9}
            MDList:
                id: search_list
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

class InteractiveMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_list = None

    #search_list = ObjectProperty()
    def set_search_list(self, search_list):
        self.search_list = search_list
    
    def add_suggestion(self, suggestion):
        if self.search_list is not None:
            for i in range(5):    
                item = TwoLineListItem(text=suggestion, secondary_text="Additional Info")
                item.bind(on_release=lambda x: print("WORKED!"))
                self.search_list.add_widget(item)

    def get_coordinates_by_address(self, address):
        address = parse.quote(address)
        
        # Use a unique user agent
        headers = {'User-Agent': 'SanDaan/1.0'}

        # Used Nominatim for easier Geocoding instead of OSM API because it doesn't have geocoding and reverse geocoding
        url = f'https://nominatim.openstreetmap.org/search?q={address}&format=json&addressdetails=1&limit=1'
        UrlRequest(url, on_success=self.success, on_failure=self.failure, on_error=self.error, req_headers=headers)

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

