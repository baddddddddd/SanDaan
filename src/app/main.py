from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from route_mapping import MAP_ROUTING_SCREEN
from main_mapview import MAPVIEW_SCREEN


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

# Finding jeepney routes algorithm
# 1. Find nearest node of initial location
# 2. Find shortest path to nearest jeepney stop from initial location node
# 3. Find nearest node of target location
# 4. Find shortest path to nearest jeepney stop from target location node
# 5. Determine the vicinity of two location nodes
# 6. Fetch all the routes that is inside the vicinity
# 7. Find routes that contain both the nodes of jeepney stops

class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_string(MAP_ROUTING_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(MAPVIEW_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(WELCOME_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(LOGIN_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(SIGNUP_SCREEN))

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
