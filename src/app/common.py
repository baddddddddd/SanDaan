from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivymd.uix.progressbar import MDProgressBar

LOCALHOST = "http://127.0.0.1:5000"
RENDER = "https://sandaan-api.onrender.com"
API_URL = RENDER if platform == "android" else LOCALHOST

HEADERS = {
    "Content-Type": "application/json"
}

COMMON = {
    "id": None
}

TOP_SCREEN_LOADING_BAR = '''
<TopScreenLoadingBar@MDProgressBar>:
    type: "indeterminate"
    pos_hint: {"top": 1}
    back_color: 1, 1, 1, 0
    size_hint_y: None
    height: dp(4)
'''

class TopScreenLoadingBar(MDProgressBar):
    pass


Builder.load_string(TOP_SCREEN_LOADING_BAR)


class SendRequest():
    def __init__(self, url: str, loading_indicator: MDProgressBar, headers=None, body=None, on_success=None, on_failure=None) -> None:
        self.loading_indicator = loading_indicator
        
        self.loading_indicator.start()

        UrlRequest(
            url=url,
            req_headers=HEADERS if headers is None else headers,
            req_body=body,
            on_success=lambda request, result, callback=on_success: self.on_response(request, result, callback),
            on_failure=lambda request, result, callback=on_failure: self.on_response(request, result, callback),
        )


    def on_response(self, request, result, callback):
        self.loading_indicator.stop()

        if callback is not None:
            callback(request, result)
