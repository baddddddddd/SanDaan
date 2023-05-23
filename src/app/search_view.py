from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy_garden.mapview import Coordinate
from kivymd.uix.list import OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField


# Kivy string for the design of the Search Bar
SEARCH_BAR = '''
<SearchBar@MDTextField>:
    hint_text: "Search location"
    mode: "round"
    size_hint: 0.9, None
    pos_hint: {"center_x": 0.5, "top": 0.98}
    font_size: dp(16)
    icon_left: "magnify"
    on_text_validate: 
        self.map.search_location(self.text, lambda _, result: self.display_results(result))
'''

# Kivy string for the design of the Search Results
SEARCH_RESULTS = '''
<SearchResults@MDScrollView>
    size_hint: 0.9, 0.4
    pos_hint: {"center_x": 0.5, "top": 0.9}
    list: search_list

    MDList:
        id: search_list
        md_bg_color: (0, 0, 0, 0)
'''


# Add behavior to the Search Bar
class SearchBar(MDTextField):
    # Variable for storing the map that the search bar will work with
    map = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.search_view = None


    # Called when search results were successfully fetched
    def display_results(self, result):
        # Add the widget to the screen
        if self.search_view is not None:
            self.clear_results()

        self.search_view = SearchResults()
        self.parent.add_widget(self.search_view)

        # Add the each result to search results
        for res in result:
            # Create a list item that shows each result
            item = OneLineListItem(
                text=res['display_name'],
                bg_color=(0.1, 0.1, 0.1, 1),
                on_release=lambda _, lat=float(res['lat']), lon=float(res['lon']): (
                    self.clear_results(), 
                    self.map.centralize_map_on(Coordinate(lat, lon))
                ),
            )
            self.search_view.list.add_widget(item)
    

    # Called when user selected a result from the search results
    def clear_results(self):
        # Remove the widget from the screen
        self.parent.remove_widget(self.search_view)
        self.search_view = None


# Bring the kivy widget to python
class SearchResults(MDScrollView):
    list = ObjectProperty(None)


# Build the widget from the kivy string
Builder.load_string(SEARCH_BAR)
Builder.load_string(SEARCH_RESULTS)
