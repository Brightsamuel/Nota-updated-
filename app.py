from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from ui.screens.CreateNote import NotesCreate
from ui.screens.main_screen import MainScreen

# Set app background color to black
Window.clearcolor = (0, 0, 0, 1)

class NotaApp(MDApp):
    def build(self):
        #apptheme
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # Set the window title
        self.title = 'Nota'  
        self.screen_manager = ScreenManager()
        
        # Create the MainScreen instance first
        self.main_screen = MainScreen(name='main')
        
         # Pass the MainScreen instance to NotesCreate
        self.CreateNote = NotesCreate(main_screen=self.main_screen, name='notes')
        

        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.CreateNote)
        
        # Initialize and configure the config
        self.config.read('notes.ini')

        return self.screen_manager
    
    def build_config(self, config):
        config.setdefaults('tagmanager', {
            'consent': ''
        })
        
    def on_start(self):
        # Your existing on_start code
        pass