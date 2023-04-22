from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.textfield import MDTextField
from kivymd.theming import ThemeManager

class SearchPopupMenu(MDDialog):
    dialog = None
    theme_cls = ThemeManager()
    def __init__(self, **kwargs):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        return (
            MDFloatLayout(
                MDFlatButton(
                    text="ALERT DIALOG",
                    pos_hint={'center_x': 0.5, 'center_y': 0.5},
                    on_release=self.show_confirmation_dialog,
                )
            )
        )


    def show_confirmation_dialog(self, *args):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Address:",
                type="custom",
                content_cls=MDBoxLayout(
                    MDTextField(
                        hint_text="City",
                    ),
                    MDTextField(
                        hint_text="Street",
                    ),
                    orientation="vertical",
                    spacing="12dp",
                    size_hint_y=None,
                    height="120dp",
                ),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                    ),
                    MDFlatButton(
                        text="OK",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                    ),
                ],
            )
        self.dialog.open()



