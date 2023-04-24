from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy_garden.mapview import MapMarker, MapView
from kivymd.app import MDApp
from kivymd.uix.button import MDRoundFlatIconButton, MDIconButton
from kivymd.uix.screen import MDScreen
from plyer import gps
import bcrypt

from android.permissions import request_permissions, Permission


class InteractiveMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_location = [13.78669, 121.07459]
        self.current_location_pin = MapMarker(
            lat=self.current_location[0],
            lon=self.current_location[1],
        )

        self.target_location = None
        self.target_location_pin = MapMarker()
        
        self.add_widget(self.current_location_pin)
        self.add_widget(self.target_location_pin)


        self.touch_event = None


    def on_touch_down(self, touch):
        self.touch_hold = True

        self.target_location = None
        self.remove_widget(self.target_location_pin)

        self.touch_event = Clock.schedule_once(lambda dt: self.check_long_press(touch), 1.0)
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        self.touch_hold = False

        if self.touch_event is not None:
            self.touch_event.cancel()

        return super().on_touch_up(touch)
    
    def on_touch_move(self, touch):
        self.touch_hold = False

        if self.touch_event is not None:
            self.touch_event.cancel()

        return super().on_touch_move(touch)
    
    def check_long_press(self, touch):
        if self.touch_hold:
            self.touch_hold = False
            print(self.get_latlon_at(touch.x, touch.y))

            self.target_location = self.get_latlon_at(touch.x, touch.y)
            self.target_location_pin.lat = self.target_location.lat
            self.target_location_pin.lon = self.target_location.lon

            self.add_widget(self.target_location_pin)
            
        

class MapViewScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

        request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
        gps.configure(on_location=self.update_location)
        gps.start()

        self.has_initialized_gps = False

        self.current_location = [0, 0]
        self.mapview = InteractiveMap()
        self.add_widget(self.mapview)

        self.directions_button = MDIconButton()

        self.directions_button.pos_hint = {
            "center_x": 0.9,
            "center_y": 0.1,
        }

        self.directions_button.icon = "car-arrow-right"
        self.directions_button.user_font_size = "40sp"
        self.directions_button.theme_text_color = "Custom"
        self.directions_button.text_color = [26, 24, 58, 255]

        self.add_widget(self.directions_button)


    def update_location(self, **kwargs):
        if not self.has_initialized_gps:
            self.has_initialized_gps = True
            self.current_location = [kwargs["lat"], kwargs["lon"]]
            self.mapview.lat = kwargs["lat"]
            self.mapview.lon = kwargs["lon"]
            self.mapview.zoom = 15

        self.mapview.current_location_pin.lat = kwargs["lat"]
        self.mapview.current_location_pin.lon = kwargs["lon"]


class MainApp(MDApp):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MapViewScreen())
        screen_manager.add_widget(Builder.load_file("screens/welcome.kv"))
        screen_manager.add_widget(Builder.load_file("screens/login.kv"))
        screen_manager.add_widget(Builder.load_file("screens/signup.kv"))

        return screen_manager
    
    
    

if __name__ == "__main__":
    if __debug__:
        from kivy.core.window import Window
        Window.size = (360, 720)

    LabelBase.register(name="MPoppins", fn_regular=r"fonts/Poppins/Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular=r"fonts/Poppins/Poppins-SemiBold.ttf")

    MainApp().run()
