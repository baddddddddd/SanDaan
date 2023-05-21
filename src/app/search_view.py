from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty
from kivy_garden.mapview import Coordinate
from kivymd.uix.list import OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField


SEARCH_BAR = '''
<SearchBar@MDTextField>:
    hint_text: "Search location"
    mode: "round"
    size_hint: 0.9, None
    pos_hint: {"center_x": 0.5, "top": 0.98}
    icon_left: "magnify"
    on_text_validate: 
        self.map.search_location(self.text, lambda _, result: self.display_results(result))
'''

SEARCH_RESULTS = '''
<SearchResults@MDScrollView>
    size_hint: 0.9, 0.4
    pos_hint: {"center_x": 0.5, "top": 0.9}
    list: search_list

    MDList:
        id: search_list
        md_bg_color: (0, 0, 0, 0)

'''

class SearchBar(MDTextField):
    map = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.search_view = None


    def display_results(self, result):
        self.search_view = SearchResults()
        self.parent.add_widget(self.search_view)

        for res in result:
            item = OneLineListItem(
                text=res['display_name'],
                bg_color=(0, 0, 1, 0.6),
                on_release=lambda _, lat=float(res['lat']), lon=float(res['lon']): (
                    self.clear_results(), 
                    self.map.centralize_map_on(Coordinate(lat, lon))
                ),
            )
            self.search_view.list.add_widget(item)
    

    def clear_results(self):
        self.parent.remove_widget(self.search_view)
        self.search_view = None


class SearchResults(MDScrollView):
    list = ObjectProperty(None)


Builder.load_string(SEARCH_BAR)
Builder.load_string(SEARCH_RESULTS)
