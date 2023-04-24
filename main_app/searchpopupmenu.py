from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import Button
from kivymd.uix.textfield import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.network.urlrequest import UrlRequest
from kivy.uix.label import Label
from urllib import parse
from kivy.app import App
import time

class SearchPopupMenu(MDDialog):
    title = 'Search by Address'
    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5}, auto_dismiss = False)
        self.build()

    def build(self):
        layout = FloatLayout(size = self.size)
        self.textF = TextInput(
            size_hint = [0.6, None],
            height = 50,
            pos_hint={'center_x': 0.5, 'center_y': 0.45}
        )
        layout.add_widget(self.textF)
        self.search_button = Button(
            text='Search',
            size_hint=(0.1, None),
            height=30,
            pos_hint={'center_x': 0.9, 'center_y': 0.45},
            background_color=(0, 0, 1, 1)
            )
        self.search_button.bind(on_release = self.callback)
        layout.add_widget(self.search_button)

        self.add_widget(layout)

    def callback(self, *args):
        address = self.textF.text
        self.geocode_get_lat_lon(address)
        print(address)

    def geocode_get_lat_lon(self, address):
        address = parse.quote(address)
        # Use a unique user agent
        headers = {'User-Agent': 'SanDaan/1.0'}
        # Apply a slight delay between each request
        time.sleep(1)
        # Used Nominatim for easier Geocoding instead of OSM API because it doesn't have geocoding and reverse geocoding
        url = f'https://nominatim.openstreetmap.org/search?q={address}&format=json&addressdetails=1&limit=1'
        UrlRequest(url, on_success=self.success, on_failure=self.failure, on_error=self.error, req_headers=headers)

    def success(self, urlrequest, result):
        print("Success")
        latitude = float(result[0]['lat'])
        longitude = float(result[0]['lon'])
        app = App.get_running_app()
        mapview = app.root.ids.mapview
        mapview.center_on(latitude, longitude)
        self.dismiss()

    def failure(self, urlrequest, result):
        print("Failed")
        print(result)

    def error(self, urlrequest, result):
        print("Error")
        print(result)