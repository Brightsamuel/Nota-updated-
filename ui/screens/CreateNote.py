from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup
from kivymd.uix.button import MDFloatingActionButton
from models.note import Note
from utils.graphics import create_gradient_texture
from utils.db_helper import DatabaseHelper

class NotesCreate(Screen):
    main_screen = ObjectProperty(None)
    
    def __init__(self, main_screen=None, **kwargs):
        super(NotesCreate, self).__init__(**kwargs)
        self.main_screen = main_screen
        self.db = DatabaseHelper()

        self.root = MDBoxLayout(orientation='vertical', padding=[15, 15], spacing=10)
        
        with self.root.canvas.before:
            Color(1, 1, 1, 1)
            self.gradient_texture = create_gradient_texture((0, 0, 0, 1), (0.2, 0.2, 0.2, 1), width=Window.width, height=Window.height)
            self.rect = Rectangle(size=self.root.size, pos=self.root.pos, texture=self.gradient_texture)
        self.root.bind(size=self._update_rect, pos=self._update_rect)
        
        header_layout = MDBoxLayout(size_hint_y=0.1, spacing=40)

        self.back_button = MDFloatingActionButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(50, 50),
            md_bg_color=(0, 0, 0, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            pos_hint={'center_y': 0.5}
        )
        self.back_button.bind(on_press=self.go_back)

        self.app_title = Label(
            text='Nota',
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
            font_size='24sp',
            halign='left'
        )
        header_layout.add_widget(self.back_button)
        header_layout.add_widget(self.app_title)
        self.root.add_widget(header_layout)
        
        self.title_input = TextInput(
            hint_text="Title",
            size_hint_y=0.1,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            padding=[10, 10, 0, 0],
            font_size='16sp',
            multiline=False
        )
        
        self.content_input = TextInput(
            hint_text="Note something down...",
            size_hint_y=0.7,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            padding=[10, 10, 0, 0],
            font_size='16sp'
        )
        
        self.save_button = MDRectangleFlatButton(
            text="save",
            size_hint=(None, None),
            size=(100, 50),
            md_bg_color=(0, 0, 0, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            pos_hint={'right': 0.95, 'center_y': 0.5}
        )

        self.root.add_widget(self.title_input)
        self.root.add_widget(self.content_input)
        self.root.add_widget(self.save_button)

        self.save_button.bind(on_press=self.save_note)
        self.add_widget(self.root)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.gradient_texture = create_gradient_texture((0, 0, 0, 1), (0.2, 0.2, 0.2, 1), width=instance.width, height=instance.height)
        self.rect.texture = self.gradient_texture

    def save_note(self, instance):
        title = self.title_input.text.strip()
        content = self.content_input.text.strip()

        if not title or not content:
            self.show_error_popup("Please enter a title and some content before saving.")
            return

        note = Note(title, content)
        
        if self.main_screen:
            self.main_screen.add_note(note)
        
        self.clear_input_fields()
        
        if self.manager:
            self.manager.current = "main"
            self.manager.transition.direction = 'right'

    def clear_input_fields(self):
        self.title_input.text = ""
        self.content_input.text = ""
            
    def go_back(self, instance):
        if self.manager:
            self.manager.current = "main"
            self.manager.transition.direction = 'right'

    def show_error_popup(self, message):
        content = MDBoxLayout(orientation='vertical', spacing=5, padding=[10, 5])
        
        error_label = Label(
            text=message,
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        
        ok_button = MDFlatButton(
            text="OK",
            size_hint_y=None,
            height=40,
            text_color=(0, 0, 0, 1),
            md_bg_color=(0, 0, 0, 1)
        )
        
        ok_button.bind(on_press=lambda instance: popup.dismiss())
        
        content.add_widget(error_label)
        content.add_widget(ok_button)
        
        popup = Popup(
            title="Error",
            content=content,
            size_hint=(0.8, 0.4),
            title_color=(1, 1, 1, 1),
            separator_color=(0.05, 0.05, 0.05, 1)
        )
        
        popup.open()