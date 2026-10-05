from kivy.app import App
from kivy.uix.label import Label


class AccountingApp(App):

    def build(self):
        return Label(
            text="نرم افزار حسابداری من",
            font_size=30
        )


AccountingApp().run()