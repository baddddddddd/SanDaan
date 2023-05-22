from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivymd.uix.progressbar import MDProgressBar

# Dynamically set the api url to send requests to depending on the development environment
LOCALHOST = "http://127.0.0.1:5000"
RENDER = "https://sandaan-api.onrender.com"
API_URL = RENDER if platform == "android" else LOCALHOST

# Set the headers to be used for communicating with the SanDaan API
HEADERS = {
    "Content-Type": "application/json"
}

# Store the tokens in a global dictionary so that it can be accessed anywhere in the program
COMMON = {
    "ACCESS_TOKEN": None,
    "REFRESH_TOKEN": None,
}

# Kivy string for loading bars
TOP_SCREEN_LOADING_BAR = '''
<TopScreenLoadingBar@MDProgressBar>:
    type: "indeterminate"
    pos_hint: {"top": 1}
    back_color: 1, 1, 1, 0
    size_hint_y: None
    height: dp(4)
'''


# Bring the widget that will be built in the kivy string to python itself
class TopScreenLoadingBar(MDProgressBar):
    pass


# Build the widget from the kivy string
Builder.load_string(TOP_SCREEN_LOADING_BAR)


# Helper class to manage and send HTTP Requests with more control and reduce code repetition
class SendRequest():
    def __init__(self, url: str, loading_indicator: MDProgressBar, headers=None, body=None, on_success=None, on_failure=None, auto_refresh=True) -> None:
        # Set and start the loading indicator as a visual feedback for users that the app
        # is waiting for an http request to be finished
        self.loading_indicator = loading_indicator
        self.loading_indicator.start()

        # Sends a non-blocking HTTP request with the provided info/data
        UrlRequest(
            url=url,
            req_headers=HEADERS if headers is None else headers,
            req_body=body,
            on_success=lambda request, result, callback=on_success: self.on_response(request, result, callback),
            on_failure=lambda request, result, on_failure=on_failure, on_success=on_success: self.on_auto_refresh(request, result, on_failure, on_success) if auto_refresh else self.on_response(request, result, on_failure),
        )


    # Called when HTTP request failed due to access token being expired. 
    # Automatically gets a new access token then resends the failed http request.
    def on_auto_refresh(self, request, result, on_failure, on_success):
        # Checks for 401 Unauthorized HTTP status, which means the access token is invalid
        if request.resp_status == 401:
            url = f"{API_URL}/refresh"

            # Use the refresh token to get new access token
            refresh_token = COMMON["REFRESH_TOKEN"]
            HEADERS["Authorization"] = f"Bearer {refresh_token}"

            SendRequest(
                url=url,
                on_success=lambda request, result, on_success=on_success, on_failure=on_failure, failed_request=request: self.update_access_token(request, result, on_success, on_failure, failed_request),
                on_failure=lambda request, result, callback=on_failure: self.on_response(request, result, callback),
                loading_indicator=self.loading_indicator,
            )
        # Handle cases where the HTTP Request failed for reasons other than invalid tokens
        else:
            self.on_response(request, result, on_failure)


    # Called when a new access token was successfully created
    # Updates the headers and token dictionary accordingly
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


    # Called when the HTTP Request was successful.
    # Stops the loading indicator for the HTTP request.
    def on_response(self, request, result, callback):
        self.loading_indicator.stop()

        if callback is not None:
            callback(request, result)
