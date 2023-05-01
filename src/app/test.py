from kivy.app import App
from kivy.core.text import LabelBase
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivy.utils import platform
from kivy.network.urlrequest import UrlRequest
from kivy_garden.mapview import MapMarker, MapView, Coordinate
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton

FIRST_SCREEN = '''
MDScreen:
    name: "first"
    FloatLayout:
        MDTextField:
            id: first_text
            hint_text: "Enter first text"
            mode: "round"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.98}
        Button:
            id: 1B
            text: "SWITCH"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.78}
            on_release:
                root.manager.current = "second"
'''
SECOND_SCREEN = '''
MDScreen:
    name: "second"
    FloatLayout:
        MDTextField:
            id: second_text
            hint_text: "Enter second text"
            mode: "round"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.98}
            on_text_validate:
                app.addBs()
        Button:
            id: 2B
            text: "SWITCH"
            size_hint_x: 0.9
            pos_hint: {"center_x": 0.5, "top": 0.78}
            on_release:
                root.manager.current = "first"
<addBs>:
    MDScrollView:
        size_hint_x: 0.7
        size_hint_y: 0.5
        pos_hint: {"center_x": 0.5, "top": 0.88}
        MDList:
            id: scroll_list
            Button:
'''
class addBs(FloatLayout):
    def add_buttons(self):
        print("sad")
        for i in range(20):
            self.root.ids.scroll_list.add_widget(MDFlatButton(text = f"BUTTON {i+1}"))

class MainApp(MDApp):
    def build(self):
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(Builder.load_string(FIRST_SCREEN))
        self.screen_manager.add_widget(Builder.load_string(SECOND_SCREEN))
        
        return self.screen_manager

if __name__ == "__main__":
    if __debug__:
        from kivy.core.window import Window
        Window.size = (360, 720)
    MainApp().run()
