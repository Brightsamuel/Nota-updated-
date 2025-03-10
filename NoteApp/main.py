from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from utils.db_operations import init_db

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
        init_db()
        return AppScreenManager()

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
