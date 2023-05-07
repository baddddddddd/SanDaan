from kivy.properties import ObjectProperty
from kivy_garden.mapview import Coordinate
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField


class LocationSearchBar(MDTextField):
    map = ObjectProperty(None)
    search_view = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hint_text = "Search location"
        self.mode = "round"
        self.size_hint_x = 0.9
        self.pos_hint = {
            "center_x": 0.5,
            "top": 0.98,
        }

        self.on_text_validate = lambda: self.map.search_location(self.text, lambda _, result: self.display_results(result))


    def clear_results(self):
        if self.search_view.list is not None:
            self.search_view.list.clear_widgets()


    def display_results(self, result):
        for res in result:
            item = OneLineListItem(
                text=res['display_name'],
                bg_color=(0, 0, 1, 0.6),
                on_release=lambda _, lat=float(res['lat']), lon=float(res['lon']): (self.clear_results(), self.map.centralize_map_on(Coordinate(lat, lon))),
            )
            self.search_view.list.add_widget(item)

    


class SearchView(MDScrollView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.size_hint_x = 0.9
        self.size_hint_y = 0.4
        self.pos_hint = {
            "center_x": 0.5,
            "top": 0.9,
        }

        self.list = MDList(
            md_bg_color=(0, 0, 0, 0)
        )
        self.add_widget(self.list)
            