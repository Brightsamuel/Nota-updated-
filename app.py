from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp
import utils.kivymd_patches  # noqa: F401  (must run before any widget is created)
from ui.screens.CreateNote import NoteEditorScreen
from ui.screens.main_screen import MainScreen
from ui.screens.auth_screens import LoginScreen, SignupScreen


class NotaApp(MDApp):
    def build(self):
        self.title = 'Nota'

        # Initialize config
        self.config.read('notes.ini')

        # App theme (the light/dark choice is remembered between runs)
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = self.config.get('ui', 'theme_style')
        self.theme_cls.theme_style_switch_animation = True

        self.screen_manager = ScreenManager(transition=SlideTransition(duration=0.2))

        # Create auth screens FIRST
        self.login_screen = LoginScreen(name='login')
        self.signup_screen = SignupScreen(name='signup')

        # Create main app screens
        self.main_screen = MainScreen(name='main')
        self.editor_screen = NoteEditorScreen(main_screen=self.main_screen, name='notes')

        # Add screens in order (login first)
        self.screen_manager.add_widget(self.login_screen)
        self.screen_manager.add_widget(self.signup_screen)
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.editor_screen)

        # FORCE login screen first (remove any auto-login logic)
        self.screen_manager.current = 'login'

        Window.bind(on_keyboard=self.on_keyboard)
        return self.screen_manager

    def build_config(self, config):
        config.setdefaults('auth', {
            'user_id': '',
            'username': ''
        })
        config.setdefaults('tagmanager', {
            'consent': ''
        })
        config.setdefaults('ui', {
            'theme_style': 'Dark'
        })

    def toggle_theme(self):
        self.theme_cls.switch_theme()
        self.config.set('ui', 'theme_style', self.theme_cls.theme_style)
        self.config.write()

    def on_keyboard(self, window, key, *args):
        """Handle the Android back button (Escape on desktop)."""
        if key != 27:
            return False
        current = self.screen_manager.current
        if current == 'notes':
            self.editor_screen.go_back()
            return True
        if current == 'signup':
            self.signup_screen.go_to_login()
            return True
        if current == 'main' and self.main_screen.current_folder_id is not None:
            self.main_screen.load_folder(None)
            return True
        return False
