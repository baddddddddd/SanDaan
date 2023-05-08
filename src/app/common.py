from kivy.utils import platform

LOCALHOST = "http://127.0.0.1:5000"
RENDER = "https://sandaan-api.onrender.com"
API_URL = RENDER if platform == "android" else LOCALHOST

HEADERS = {
    "Content-Type": "application/json"
}

COMMON = {
    "id": None
}
    