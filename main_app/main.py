from kivymd.app import MDApp
from batsmapview import BatsMapView
from searchpopupmenu import SearchPopupMenu
from gpshelper import GpsHelper

class MainApp(MDApp):
    search_menu = None
    # def on_start(self):
    #     marker = MapMarkerPopup(lat = 13.7565, lon = 121.0583, source = "me_ico.png")
    #     marker.add_widget(Button(text = "Test Button"))
    #     self.root.add_widget(marker)

    def on_start(self):
        # Initialize GPS
        GpsHelper().run()
        # Connect to Database

        # Instantiate Seach PopupMenu
        self.search_menu = SearchPopupMenu()
        pass

    
MainApp().run()