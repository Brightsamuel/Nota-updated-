from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from ui.screens.CreateNote import NotesCreate
from ui.screens.main_screen import MainScreen
from ui.screens.auth_screens import LoginScreen, SignupScreen  # New imports

# Set app background color to black
Window.clearcolor = (0, 0, 0, 1)

class NotaApp(MDApp):
    def build(self):
        # App theme
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        
        # Set the window title
        self.title = 'Nota'  
        self.screen_manager = ScreenManager()
        
        # Create auth screens FIRST
        self.login_screen = LoginScreen(name='login')
        self.signup_screen = SignupScreen(name='signup')
        
        # Create main app screens
        self.main_screen = MainScreen(name='main')
        self.CreateNote = NotesCreate(main_screen=self.main_screen, name='notes')
        
        # Add screens in order (login first)
        self.screen_manager.add_widget(self.login_screen)
        self.screen_manager.add_widget(self.signup_screen)
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.CreateNote)
        
        # Initialize config
        self.config.read('notes.ini')

        # FORCE login screen first (remove any auto-login logic)
        self.screen_manager.current = 'login'

        return self.screen_manager
    
    def build_config(self, config):
        config.setdefaults('auth', {
            'user_id': None,
            'username': None
        })
        config.setdefaults('tagmanager', {
            'consent': ''
        })
        
    def on_start(self):
        # Your existing on_start code
        pass