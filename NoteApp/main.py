from kivy.uix.settings import text_type
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from utils.db_operations import init_db
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput

# Load KV file for UI design
Builder.load_file('kv/app_design.kv')

# Define screens
class HomeScreen(Screen):
    pass

class NoteEditorScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

# Manage screen transitions
class AppScreenManager(ScreenManager):
    pass

class NotesApp(App):
    def build(self):
        # initialise database
        self.dropdown = self.create_dropdown()
        init_db()
        return AppScreenManager()



        ''''create dropdown functionality'''
    def create_dropdown(self):
        dropdown = DropDown()

       # Dropdown Items
        create_note_btn = Button(text='Create Note', size_hint_y=None, height=44)
        create_note_btn.bind(on_release=lambda btn: self.select_action('create_note'))

        settings_btn = Button(text='Settings', size_hint_y=None, height=44)
        settings_btn.bind(on_release=lambda btn: self.select_action('settings'))

        exit_btn = Button(text='Exit', size_hint_y=None, height=44)
        exit_btn.bind(on_release=lambda btn: self.select_action('exit'))

        # Add buttons to dropdown
        dropdown.add_widget(create_note_btn)
        dropdown.add_widget(settings_btn)
        dropdown.add_widget(exit_btn)

        return dropdown
    
    def open_dropdown(self, button):
        self.dropdown.open(button)

    def select_action(self, action):
        if action == 'create_note':
            self.root.current = 'note_editor'
        elif action == 'settings':
            self.root.current = 'settings'
        elif action == 'exit':
            self.stop()
    
if __name__ == '__main__':
    NotesApp().run()

# theme
import json

def save_theme(theme):
    with open('config.json', 'w') as file:
        json.dump({'theme': theme}, file)

def load_theme():
    try:
        with open('config.json', 'r') as file:
            return json.load(file).get('theme', 'light')
    except FileNotFoundError:
        return 'light'

