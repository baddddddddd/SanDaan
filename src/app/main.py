from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton
from kivy_garden.mapview import MapMarker, MapView
from plyer import gps
from urllib import parse


WELCOME_SCREEN = '''
MDScreen:
    name: "welcome"
    
    MDFloatLayout:

        MDFillRoundFlatButton:
            text: "LOG IN"
            pos_hint: {"center_x": .5, "center_y": .20}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                root.manager.transition.direction = "left"
                root.manager.transition.duration = 0.3
                root.manager.current = "login"

        MDRoundFlatButton:
            text: "SIGN UP"
            pos_hint: {"center_x": .5, "center_y": .10}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                root.manager.transition.direction = "left"
                root.manager.transition.duration = 0.3
                root.manager.current = "signup"
'''


LOGIN_SCREEN = '''
MDScreen:
    name: "login"

    MDFloatLayout:
        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"center_y": .95}
            user_font_size: "36 sp"
            on_release:
                root.manager.transition.direction = "right"
                root.manager.current = "welcome"
        
        MDLabel:
            text: "LOG IN"
            font_name: "BPoppins"
            font_size: "26sp"
            pos_hint: {"center_x": .6, "center_y": .85}
            color: "#F1FAEE"

        MDLabel:
            text: "Sign in to continue"
            font_name: "MPoppins"
            font_size: "18sp"
            pos_hint: {"center_x": .6, "center_y": .79}
            color: "#a8dadc"

        MDTextField:
            id: email
            hint_text: "Username or Email"
            font_name: "MPoppins"
            #validator: "email"
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .64}
            font_size: 16

        MDTextField:
            id: password
            hint_text: "Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .52}
            font_size: 16

        MDFillRoundFlatButton:
            text: "LOG IN"
            pos_hint: {"center_x": .5, "center_y": .38}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                app.verify_login(email.text, password.text)
'''

SIGNUP_SCREEN = '''
MDScreen:
    name: "signup"

    MDFloatLayout:
        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"center_y": .95}
            user_font_size: "36 sp"
            on_release:
                root.manager.transition.direction = "right"
                root.manager.current = "welcome"
        
        MDLabel:
            text: "SIGN UP"
            font_name: "BPoppins"
            font_size: "26sp"
            pos_hint: {"center_x": .6, "center_y": .85}
            color: "#F1FAEE"

        MDLabel:
            text: "Create a new account"
            font_name: "MPoppins"
            font_size: "18sp"
            pos_hint: {"center_x": .6, "center_y": .79}
            color: "#a8dadc"

        MDTextField:
            id: email
            hint_text: "Username"
            font_name: "MPoppins"
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .7}
            font_size: 16

        MDTextField:
            id: email
            hint_text: "Email Address"
            font_name: "MPoppins"
            #validator: "email"
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .6}
            font_size: 16

        MDTextField:
            id: password
            hint_text: "Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .5}
            font_size: 16

        MDTextField:
            id: password
            hint_text: "Confirm Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .4}
            font_size: 16

        MDFillRoundFlatButton:
            text: "SIGN UP"
            pos_hint: {"center_x": .5, "center_y": .28}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                root.manager.transition.direction = "left"
                root.manager.transition.duration = 0.3
                root.manager.current = "signup"
'''

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
            pos_hint: {"center_x": 0.875, "center_y": 0.125}
            on_release:
                map.follow_user()

        
            
'''

class InteractiveMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Default location, which is Batangas State University - Alangilan, coordinate if GPS is not available
        self.current_location = [13.78530, 121.07339]
        self.current_location_pin = MapMarker(
            lat=13.78530,
            lon=121.07339,
        )
        self.add_widget(self.current_location_pin)

        self.pinned_location = None
        self.pinned_location_pin = MapMarker()
        self.add_widget(self.pinned_location_pin)

        self.has_initialized_gps = False

        # Request permission for accessing GPS in Android devices
        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            
            gps.configure(on_location=self.update_location)
            gps.start()



    def follow_user(self):
        self.center_on(self.current_location[0], self.current_location[1])
        self.zoom = 15


    def update_location(self, **kwargs):
        if not self.has_initialized_gps:
            self.has_initialized_gps = True
            self.current_location = [kwargs["lat"], kwargs["lon"]]
            self.center_on(kwargs["lat"], kwargs["lon"])
            self.zoom = 15

        self.current_location_pin.lat = kwargs["lat"]
        self.current_location_pin.lon = kwargs["lon"]


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
        self.center_on(latitude, longitude)
        self.zoom = 15


    def failure(self, urlrequest, result):
        print("Failed")
        print(result)


    def error(self, urlrequest, result):
        print("Error")
        print(result)


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_string(WELCOME_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(LOGIN_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(SIGNUP_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(MAPVIEW_SCREEN))

        return self.screen_manager
    

    def verify_login(self, username_or_email, password):
        print(username_or_email, password)
        
        is_logged_in = True

        if is_logged_in:
            self.screen_manager.current = "mapview"


if __name__ == "__main__":
    if __debug__:
        from kivy.core.window import Window
        Window.size = (360, 720)

    LabelBase.register(name="MPoppins", fn_regular=r"fonts/Poppins/Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular=r"fonts/Poppins/Poppins-SemiBold.ttf")

    MainApp().run()
