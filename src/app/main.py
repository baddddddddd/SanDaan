from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
import json
import re

from common import SendRequest, TopScreenLoadingBar, API_URL, HEADERS, COMMON
from route_finding import MAPVIEW_SCREEN


WELCOME_SCREEN = '''
MDScreen:
    name: "welcome"
    
    MDFloatLayout:
        TopScreenLoadingBar:
            id: loading
            on_parent:
                app.cache_loading = loading

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
        TopScreenLoadingBar:
            id: loading

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
            on_focus:
                self.required = True
            on_text_validate:
                if self.text != "": password.focus = True
            on_text:
                warning.text = ""

        MDTextField:
            id: password
            hint_text: "Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .52}
            font_size: 16
            on_focus:
                self.required = True
            on_text:
                warning.text = ""

        MDFillRoundFlatButton:
            text: "LOG IN"
            pos_hint: {"center_x": .5, "center_y": .38}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                app.login_loading = loading
                app.login_warning = warning
                app.verify_login(email, password)

        MDLabel:
            id: warning
            text: ""
            font_name: "MPoppins"
            font_size: "12sp"
            pos_hint: {"center_x": 0.6, "center_y": .46}
            color: "#FF0000"
'''

SIGNUP_SCREEN = '''
MDScreen:
    name: "signup"

    MDFloatLayout:
        TopScreenLoadingBar:
            id: loading

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
            id: username
            hint_text: "Username"
            font_name: "MPoppins"
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .7}
            font_size: 16
            on_focus:
                self.required = True
            on_text:
                warning.text = ""
            on_text_validate:
                email.focus = True

        MDTextField:
            id: email
            hint_text: "Email Address"
            font_name: "MPoppins"
            #validator: "email"
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .6}
            font_size: 16
            on_focus:
                self.required = True
            on_text:
                warning.text = ""
            on_text_validate:
                password.focus = True

        MDTextField:
            id: password
            hint_text: "Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .5}
            font_size: 16
            on_focus:
                self.required = True
            on_text:
                warning.text = ""
            on_text_validate:
                confirm_password.focus = True

        MDTextField:
            id: confirm_password
            hint_text: "Confirm Password"
            font_name: "MPoppins"
            password: True
            size_hint_x: 0.8
            padding: [24, 14, 24, 14]
            pos_hint: {"center_x": .5, "center_y": .4}
            font_size: 16
            on_focus:
                self.required = True
            on_text:
                warning.text = ""

        MDLabel:
            id: warning
            text: ""
            font_name: "MPoppins"
            font_size: "12sp"
            pos_hint: {"center_x": 0.6, "center_y": .35}
            color: "#FF0000"

        MDFillRoundFlatButton:
            text: "SIGN UP"
            pos_hint: {"center_x": .5, "center_y": .28}
            size_hint_x: .66
            padding: [24, 14, 24, 14]
            font_name: "BPoppins"
            on_release:
                app.signup_loading = loading
                app.signup_warning = warning
                app.create_account(username, email, password, confirm_password)
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
        
        self.login_loading = None
        self.signup_loading = None
        self.login_warning = None
        self.signup_warning = None
        self.cache_loading = None

        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_string(WELCOME_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(LOGIN_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(SIGNUP_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(MAPVIEW_SCREEN))

        self.cache = JsonStore("cache.json")
        Clock.schedule_once(lambda _: self.get_cache())

        return self.screen_manager
    
    
    def get_cache(self):
        if self.cache.exists("authorization"):
            access_token = self.cache.get("authorization").get("access_token", None)
            id = self.cache.get("authorization").get("id", None)

            # Check if token is still valid and user id still exists
            url = f"{API_URL}/verify"
            HEADERS["Authorization"] = f"Bearer {access_token}"
            
            SendRequest(
                url=url,
                on_success=lambda _, result, access_token=access_token, id=id: self.skip_login(access_token, id),
                loading_indicator=self.cache_loading,
            )


    def skip_login(self, access_token, id):
        result = {
                "access_token": access_token,
                "id": id,
            }

        self.show_main_screen(result)


    def create_account(self, username, email, password, confirm_password):
        # Check if any of the fields is empty
        fields = [username, email, password, confirm_password]
        for field in fields:
            if field.text == "":
                field.focus = True
                return
        
        # Check if input username is a valid username
        if len(username.text) < 3:
            self.signup_warning.text = "Username must have at least 3 characters"
            return
        
        if not username.text.isalnum():
            self.signup_warning.text = "Username must not contain symbols and spaces"
            return
        
        # Check if input email is a valid email
        email_pattern = r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$"
        if not re.match(email_pattern, email.text):
            self.signup_warning.text = "Email is not a valid email address"
            return
        
        # Check if input password is a valid password
        if len(password.text) < 8:
            self.signup_warning.text = "Password must have at least 8 characters"
            return
        
        if not password.text.isascii():
            self.signup_warning.text = "Password contains invalid characters"
            return
        
        # Show warning message when passwords do not match
        if password.text != confirm_password.text:
            self.signup_warning.text = "Passwords do not match"
            return
        
        # Create the account through the API
        url = f"{API_URL}/register"
        
        body = json.dumps({
            "username": username.text,
            "email": email.text,
            "password": password.text,
        })

        SendRequest(
            url=url,
            body=body,
            on_success=lambda _, result: self.proceed_to_login(),
            on_failure=lambda _, result: self.show_signup_error(result),
            loading_indicator=self.signup_loading,
        )


    def proceed_to_login(self):
        # Change the current screen to the login screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.transition.duration = 0.3
        self.screen_manager.current = "login"


    def show_signup_error(self, result):
        # Give the user an idea what went wrong
        error_message = result.get("msg", None)
        self.signup_warning.text = error_message if error_message is not None else "Something went wrong"


    def verify_login(self, username, password):
        # Validate input before sending to API
        if username.text == "":
            username.focus = True
            return

        if password.text == "":
            password.focus = True
            return

        # Verify login credentials through the API
        url = f"{API_URL}/login"
        
        body = json.dumps({
            "username": username.text,
            "password": password.text,
        })

        SendRequest(
            url=url,
            body=body,
            on_success=lambda _, result: self.show_main_screen(result),
            on_failure=lambda _, result: self.show_login_error(result),
            loading_indicator=self.login_loading,
        )


    def show_main_screen(self, result):
        access_token = result.get("access_token")
        id = result.get("id")

        # Save authorization details to cache
        self.cache.put(
            key="authorization",
            access_token=access_token,
            id=id,
        )

        # Set authorization header and save user id
        HEADERS["Authorization"] = f"Bearer {access_token}"
        COMMON["id"] = id

        with open("res.txt", "+a") as f:
            f.write(str(HEADERS) + "\n")

        # Change the current screen to the mapview screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.transition.duration = 0.3
        self.screen_manager.current = "mapview"


    def show_login_error(self, result):
        # Give the user an idea what went wrong
        error_message = result.get("msg", None)
        self.login_warning.text = error_message if error_message is not None else "Something went wrong"


if __name__ == "__main__":
    if __debug__:
        from kivy.core.window import Window
        Window.size = (360, 720)

    LabelBase.register(name="MPoppins", fn_regular=r"fonts/Poppins/Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular=r"fonts/Poppins/Poppins-SemiBold.ttf")

    MainApp().run()
