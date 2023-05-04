from kivy.utils import platform

API_URL = "http://127.0.0.1:5000"

if platform == "android":
    API_URL = "http://192.168.1.42:5000"

HEADERS = {
    "Content-Type": "application/json"
}
    