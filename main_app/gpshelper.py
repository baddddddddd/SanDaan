from kivy.app import App
from kivy.utils import platform
from kivymd.uix.dialog import MDDialog

class GpsHelper():
    has_centered_map = False
    def run(self):
        # Get a Reference to GpsBlinker, then call blink()
        gps_blinker = App.get_running_app().root.ids.mapview.ids.blinker
        gps_blinker.blink()
        # Request Permissions on Android
        if platform == 'android':
            from android.permissions import Permissions, request_permissions
            def callback(permission, results):
                if all([res for res in results]):
                    print("Got all Permissions")
                else:
                    print("Did not get all Permissions")

            request_permissions([Permission.ACCESS_COARSE_LOCATION,
                                  Permission.ACCESS_FINE_LOCATION], callback)
        # Configure GPS
        if platform == 'android' or platform == 'ios':
            from plyer import gps
            gps.configure(on_location = self.update_blinker_position,
                          on_status = self.on_auth_status)
            gps.start(minTime=1000, minDistance=0)
    
    def update_blinker_position(self, *args, **kwargs):
        my_lat = kwargs['lat']
        my_lon = kwargs['lon']
        print("GPS POSITION: ", my_lat, my_lon)
        # Update GpsBlinker Position
        gps_blinker = App.get_running_app().root.ids.mapview.ids.blinker
        gps_blinker.lat = my_lat
        gps_blinker.lon = my_lon

        # Center Map on GPS
        if not self.has_centered_map:
            map = App.get_running_app().root.ids.mapview
            map.center_on(my_lat, my_lon)
            self.has_centered_map = True

    def on_auth_status(self, general_status, status_message):
        if general_status == 'provider-enabled':
            pass
        else:
            self.open_gps_access_popup()

    def open_gps_access_popup():
        dialog = MDDialog(title = 'GPS Error', text = "You need to enable GPS access for the app to function properly")
        dialog.size_hint = [0.8, 0.8]
        dialog.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        dialog.open()