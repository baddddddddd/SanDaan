from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.button import MDFloatingActionButton, MDIconButton
from kivymd.uix.floatlayout import FloatLayout
from kivymd.uix.screen import MDScreen
from kivy_garden.mapview import MapMarker, MapView
from plyer import gps
import bcrypt


class InteractiveMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_location_pin = MapMarker()

        self.target_location = None
        self.target_location_pin = MapMarker()
        
        self.add_widget(self.current_location_pin)
        self.add_widget(self.target_location_pin)

    ################## Experimenting
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
    ##############################        


class MainScreenLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.has_initialized_gps = False

        self.current_location = [0, 0]
        self.mapview = InteractiveMap()
        self.add_widget(self.mapview)

        if platform == "android":
            from android.permissions import request_permissions, Permission

            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            
            gps.configure(on_location=self.update_location)
            gps.start()
            
        else:
            self.has_initialized_gps = True

            self.current_location = [13.78530, 121.07339]
            self.mapview.lat = self.current_location[0]
            self.mapview.lon = self.current_location[1]
            self.mapview.zoom = 15

            self.mapview.current_location_pin.lat = self.current_location[0]
            self.mapview.current_location_pin.lon = self.current_location[1]

        ################### Experimenting
        self.show_directions_button = MDFloatingActionButton(
            icon="pencil",
            #type="standard",
            #theme_icon_color="Custom",
            #md_bg_color="#fefbff",
            #icon_color="#6851a5",
            pos_hint={
                "center_x": 0.875,
                "center_y": 0.125,
            },
        )

        self.add_widget(self.show_directions_button)

        self.show_directions_button.bind(on_release=self.centralize_map)
        ####################################


    def centralize_map(self, instance):
        self.mapview.center_on(self.current_location[0], self.current_location[1])
        self.mapview.zoom = 15


    def update_location(self, **kwargs):
        if not self.has_initialized_gps:
            self.has_initialized_gps = True
            self.current_location = [kwargs["lat"], kwargs["lon"]]
            self.mapview.center_on(kwargs["lat"], kwargs["lon"])
            self.mapview.zoom = 15

        self.mapview.current_location_pin.lat = kwargs["lat"]
        self.mapview.current_location_pin.lon = kwargs["lon"]


class MapViewScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.layout = MainScreenLayout()
        self.add_widget(self.layout)


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"
    
        screen_manager = ScreenManager()
        #screen_manager.add_widget(MapViewScreen())
        screen_manager.add_widget(Builder.load_file("screens/welcome.kv"))
        screen_manager.add_widget(Builder.load_file("screens/login.kv"))
        screen_manager.add_widget(Builder.load_file("screens/signup.kv"))

        return screen_manager
    

if __name__ == "__main__":
    if __debug__:
        from kivy.core.window import Window
        Window.size = (360, 720)

    LabelBase.register(name="Poppins_Medium", fn_regular=r"fonts/Poppins/Poppins-Medium.ttf")
    LabelBase.register(name="Poppins_SemiBold", fn_regular=r"fonts/Poppins/Poppins-SemiBold.ttf")

    MainApp().run()
