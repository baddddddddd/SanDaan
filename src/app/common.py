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
    "ACCESS_TOKEN": None,
    "REFRESH_TOKEN": None,
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
    def __init__(self, url: str, loading_indicator: MDProgressBar, headers=None, body=None, on_success=None, on_failure=None, auto_refresh=True) -> None:
        self.loading_indicator = loading_indicator
        
        self.loading_indicator.start()

        UrlRequest(
            url=url,
            req_headers=HEADERS if headers is None else headers,
            req_body=body,
            on_success=lambda request, result, callback=on_success: self.on_response(request, result, callback),
            on_failure=lambda request, result, on_failure=on_failure, on_success=on_success: self.on_auto_refresh(request, result, on_failure, on_success) if auto_refresh else self.on_response(request, result, on_failure),
        )


    def on_auto_refresh(self, request, result, on_failure, on_success):
        if request.resp_status == 401:
            url = f"{API_URL}/refresh"

            refresh_token = COMMON["REFRESH_TOKEN"]
            HEADERS["Authorization"] = f"Bearer {refresh_token}"

            SendRequest(
                url=url,
                on_success=lambda request, result, on_success=on_success, on_failure=on_failure, failed_request=request: self.update_access_token(request, result, on_success, on_failure, failed_request),
                on_failure=lambda request, result, callback=on_failure: self.on_response(request, result, callback),
                loading_indicator=self.loading_indicator,
            )
        else:
            self.on_response(request, result, on_failure)


    def update_access_token(self, request, result, on_success, on_failure, failed_request):
        access_token = result.get("access_token")
        HEADERS["Authorization"] = f"Bearer {access_token}"
        COMMON["ACCESS_TOKEN"] = access_token

        SendRequest(
            url=failed_request.url,
            body=failed_request.req_body,
            on_success=on_success,
            on_failure=on_failure,
            loading_indicator=self.loading_indicator,
        )


    def on_response(self, request, result, callback):
        self.loading_indicator.stop()

        if callback is not None:
            callback(request, result)
