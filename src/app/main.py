from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivymd.app import MDApp

import json
import re
import os

from common import SendRequest, TopScreenLoadingBar, API_URL, HEADERS, COMMON
from route_finding import MAPVIEW_SCREEN


# Kivy string to build layout and design of the loading screen
LOADING_SCREEN = '''
MDScreen:
    name: "loading"
    
    MDFloatLayout:
        TopScreenLoadingBar:
            id: loading
            on_parent:
                app.cache_loading = loading

        Image:
            source: "assets/logo.png"
            size_hint_x: .85
            pos_hint: {"center_x": .5, "center_y": .6}

        MDLabel:
            text: "For commuters, by commuters"
            font_name: "MPoppins"
            font_size: dp(16)
            size_hint_x: .85
            pos_hint: {"center_x": .5, "center_y": .45}
            halign: "center"
'''

# Kivy string to build layout and design of the welcome screen
WELCOME_SCREEN = '''
MDScreen:
    name: "welcome"
    
    MDFloatLayout:
        Image:
            source: "assets/logo.png"
            size_hint_x: .85
            pos_hint: {"center_x": .5, "center_y": .7}

        MDLabel:
            text: "For commuters, by commuters"
            font_name: "MPoppins"
            font_size: dp(16)
            size_hint_x: .85
            pos_hint: {"center_x": .5, "center_y": .55}
            halign: "center"

        MDFillRoundFlatButton:
            text: "LOG IN"
            pos_hint: {"center_x": .5, "center_y": .20}
            size_hint_x: .66
            padding: [dp(24), dp(14), dp(24), dp(14)]
            font_name: "BPoppins"
            font_size: dp(14)
            on_release:
                root.manager.transition.direction = "left"
                root.manager.transition.duration = 0.3
                root.manager.current = "login"

        MDRoundFlatButton:
            text: "SIGN UP"
            pos_hint: {"center_x": .5, "center_y": .10}
            size_hint_x: .66
            padding: [dp(24), dp(14), dp(24), dp(14)]
            font_name: "BPoppins"
            font_size: dp(14)
            on_release:
                root.manager.transition.direction = "left"
                root.manager.transition.duration = 0.3
                root.manager.current = "signup"
'''

# Kivy string to build layout and design of the login screen
LOGIN_SCREEN = '''
MDScreen:
    name: "login"

    MDFloatLayout:
        TopScreenLoadingBar:
            id: loading

        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"center_y": .95}
            user_font_size: dp(36)
            on_release:
                root.manager.transition.direction = "right"
                root.manager.current = "welcome"
        
        MDLabel:
            text: "LOG IN"
            font_name: "BPoppins"
            font_size: dp(24)
            pos_hint: {"center_x": .6, "center_y": .85}
            color: "#F1FAEE"

        MDLabel:
            text: "Sign in to continue"
            font_name: "MPoppins"
            font_size: dp(16)
            pos_hint: {"center_x": .6, "center_y": .79}
            color: "#a8dadc"

        MDTextField:
            id: email
            hint_text: "Username or Email"
            font_name: "MPoppins"
            #validator: "email"
            size_hint_x: 0.8
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .64}
            font_size: dp(14)
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
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .52}
            font_size: dp(14)
            on_focus:
                self.required = True
            on_text:
                warning.text = ""

        MDFillRoundFlatButton:
            text: "LOG IN"
            pos_hint: {"center_x": .5, "center_y": .38}
            size_hint_x: .66
            padding: [dp(24), dp(14), dp(24), dp(14)]
            font_name: "BPoppins"
            font_size: dp(14)
            on_release:
                app.login_loading = loading
                app.login_warning = warning
                app.verify_login(email, password)

        MDLabel:
            id: warning
            text: ""
            font_name: "MPoppins"
            font_size: dp(12)
            pos_hint: {"center_x": 0.6, "center_y": .46}
            color: "#FF0000"
'''

# Kivy string to build layout and design of the signup screen
SIGNUP_SCREEN = '''
MDScreen:
    name: "signup"

    MDFloatLayout:
        TopScreenLoadingBar:
            id: loading

        MDIconButton:
            icon: "arrow-left"
            pos_hint: {"center_y": .95}
            user_font_size: dp(36)
            on_release:
                root.manager.transition.direction = "right"
                root.manager.current = "welcome"
        
        MDLabel:
            text: "SIGN UP"
            font_name: "BPoppins"
            font_size: dp(24)
            pos_hint: {"center_x": .6, "center_y": .85}
            color: "#F1FAEE"

        MDLabel:
            text: "Create a new account"
            font_name: "MPoppins"
            font_size: dp(16)
            pos_hint: {"center_x": .6, "center_y": .79}
            color: "#a8dadc"

        MDTextField:
            id: username
            hint_text: "Username"
            font_name: "MPoppins"
            size_hint_x: 0.8
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .7}
            font_size: dp(14)
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
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .6}
            font_size: dp(14)
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
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .5}
            font_size: dp(14)
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
            padding: [dp(24), dp(14), dp(24), dp(14)]
            pos_hint: {"center_x": .5, "center_y": .4}
            font_size: dp(14)
            on_focus:
                self.required = True
            on_text:
                warning.text = ""

        MDLabel:
            id: warning
            text: ""
            font_name: "MPoppins"
            font_size: dp(12)
            pos_hint: {"center_x": 0.6, "center_y": .35}
            color: "#FF0000"

        MDFillRoundFlatButton:
            text: "SIGN UP"
            pos_hint: {"center_x": .5, "center_y": .28}
            size_hint_x: .66
            padding: [dp(24), dp(14), dp(24), dp(14)]
            font_name: "BPoppins"
            font_size: dp(14)
            on_release:
                app.signup_loading = loading
                app.signup_warning = warning
                app.create_account(username, email, password, confirm_password)
'''


# Class to define the application root and building instructions
class MainApp(MDApp):
    # Called when the app starts running
    def build(self):
        # Set the theme of the app
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        
        # Variables to store the loading bars of the app
        self.login_loading = None
        self.signup_loading = None
        self.login_warning = None
        self.signup_warning = None
        self.cache_loading = None

        # Use a screen manager from kivy to allow changing screens
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_string(LOADING_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(WELCOME_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(LOGIN_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(SIGNUP_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(MAPVIEW_SCREEN))
        
        # Request permission to use storage for android devices to be used for caching
        if platform == "android":
            from android.permissions import request_permissions, Permission
            from android.storage import app_storage_path

            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            
            cache_dir = app_storage_path()
        else:
            cache_dir = "."

        # Get the cache once the app has finished building
        cache_file = os.path.join(cache_dir, "cache.json")
        self.cache = JsonStore(cache_file)
        Clock.schedule_once(lambda _: self.get_cache())

        return self.screen_manager
    
    
    # Gets the authorization tokens from the cache file so that user does not have to
    # log in to the app every time
    def get_cache(self):
        if self.cache.exists("authorization"):
            access_token = self.cache.get("authorization").get("access_token", None)
            refresh_token = self.cache.get("authorization").get("refresh_token", None)
            COMMON["ACCESS_TOKEN"] = access_token
            COMMON["REFRESH_TOKEN"] = refresh_token

            # Check if token is still valid and user id still exists
            url = f"{API_URL}/verify"
            HEADERS["Authorization"] = f"Bearer {access_token}"
            
            SendRequest(
                url=url,
                on_success=lambda _, result: self.skip_login(),
                on_failure=lambda _, result: self.proceed_to_welcome(),
                loading_indicator=self.cache_loading,
            )
        else:
            self.proceed_to_welcome()


    # Called when the tokens from cache are still valid, letting the user skip the login screen
    def skip_login(self):
        result = {
            "access_token": COMMON["ACCESS_TOKEN"],
            "refresh_token": COMMON["REFRESH_TOKEN"],
        }

        self.show_main_screen(result)


    # Called when there is no cache or token is no longer valid
    def proceed_to_welcome(self):
        # Change the current screen to the welcome screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.transition.duration = 0.3
        self.screen_manager.current = "welcome"


    # Called when user submits their information for signing up through the sign up screen
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
            auto_refresh=False,
        )


    # Called when account was successfully created
    def proceed_to_login(self):
        # Change the current screen to the login screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.transition.duration = 0.3
        self.screen_manager.current = "login"


    # Called when account creation failed. Shows the user what went wrong
    def show_signup_error(self, result):
        # Change the label text in the UI to contain the error message
        error_message = result.get("msg", None)
        self.signup_warning.text = error_message if error_message is not None else "Something went wrong"


    # Called when user submits their login credentials through the login screen
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
            auto_refresh=False,
        )


    # Called when login was successful. Shows the main screen of the app
    def show_main_screen(self, result):
        # Obtain the authorization tokens from the cache or from the server
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")

        # Save authorization details to cache
        self.cache.put(
            key="authorization",
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # Set authorization header and save the tokens to the app
        HEADERS["Authorization"] = f"Bearer {access_token}"
        COMMON["ACCESS_TOKEN"] = access_token
        COMMON["REFRESH_TOKEN"] = refresh_token

        # Change the current screen to the mapview screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.transition.duration = 0.3
        self.screen_manager.current = "mapview"


    # Called when login failed and shows the user what went wrong
    def show_login_error(self, result):
        # Change the label text that shows errors to contain the error message
        error_message = result.get("msg", None)
        self.login_warning.text = error_message if error_message is not None else "Something went wrong"


if __name__ == "__main__":
    # Set a specific window size for non-android devices for development purposes
    if platform != "android":
        from kivy.core.window import Window
        Window.size = (360, 720)

    # Register fonts to kivy so that it can be used for design
    LabelBase.register(name="MPoppins", fn_regular=r"fonts/Poppins/Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular=r"fonts/Poppins/Poppins-SemiBold.ttf")

    # Runs the app
    MainApp().run()
