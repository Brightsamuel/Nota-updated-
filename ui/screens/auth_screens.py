from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from ui.dialogs import show_field_error
from utils.db_helper import DatabaseHelper

Builder.load_string('''
<AuthField@MDTextField>:
    mode: "outlined"
    multiline: False

<ThemeToggleButton@MDIconButton>:
    icon: "weather-sunny" if app.theme_cls.theme_style == "Dark" else "weather-night"
    on_release: app.toggle_theme()


<AuthHeader@MDBoxLayout>:
    subtitle: ""
    orientation: "vertical"
    adaptive_height: True
    spacing: "4dp"
    padding: 0, 0, 0, "16dp"

    MDIcon:
        icon: "notebook-edit-outline"
        theme_font_size: "Custom"
        font_size: "56sp"
        theme_icon_color: "Custom"
        icon_color: app.theme_cls.primaryColor
        halign: "center"
        size_hint: 1, None
        height: "72dp"

    MDLabel:
        text: "Nota"
        halign: "center"
        font_style: "Display"
        role: "small"
        bold: True
        adaptive_height: True

    MDLabel:
        text: root.subtitle
        halign: "center"
        theme_text_color: "Custom"
        text_color: app.theme_cls.onSurfaceVariantColor
        adaptive_height: True


<LoginScreen>:
    md_bg_color: app.theme_cls.backgroundColor

    MDAnchorLayout:
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            size_hint_x: None
            width: min(dp(400), root.width - dp(48))
            # Room below each field for its red error message
            spacing: "26dp"

            AuthHeader:
                subtitle: "Log in to continue"

            AuthField:
                id: email_field
                on_text_validate: password_field.focus = True
                MDTextFieldLeadingIcon:
                    icon: "email-outline"
                MDTextFieldHintText:
                    text: "Email"
                MDTextFieldHelperText:
                    id: email_helper
                    mode: "on_error"

            AuthField:
                id: password_field
                password: True
                on_text_validate: root.login_user()
                MDTextFieldLeadingIcon:
                    icon: "lock-outline"
                MDTextFieldHintText:
                    text: "Password"
                MDTextFieldHelperText:
                    id: password_helper
                    mode: "on_error"

            MDButton:
                style: "filled"
                theme_width: "Custom"
                size_hint_x: 1
                height: "48dp"
                on_release: root.login_user()
                MDButtonText:
                    text: "Log in"
                    pos_hint: {"center_x": .5, "center_y": .5}

            MDButton:
                style: "text"
                pos_hint: {"center_x": .5}
                on_release: root.go_to_signup()
                MDButtonText:
                    text: "Don't have an account? Sign up"

    ThemeToggleButton:
        pos_hint: {"right": .98, "top": .98}


<SignupScreen>:
    md_bg_color: app.theme_cls.backgroundColor

    MDAnchorLayout:
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            size_hint_x: None
            width: min(dp(400), root.width - dp(48))
            # Room below each field for its red error message
            spacing: "26dp"

            AuthHeader:
                subtitle: "Create an account"

            AuthField:
                id: name_field
                on_text_validate: email_field.focus = True
                MDTextFieldLeadingIcon:
                    icon: "account-outline"
                MDTextFieldHintText:
                    text: "Full name"
                MDTextFieldHelperText:
                    mode: "on_error"

            AuthField:
                id: email_field
                on_text_validate: password_field.focus = True
                MDTextFieldLeadingIcon:
                    icon: "email-outline"
                MDTextFieldHintText:
                    text: "Email"
                MDTextFieldHelperText:
                    mode: "on_error"

            AuthField:
                id: password_field
                password: True
                on_text_validate: confirm_password_field.focus = True
                MDTextFieldLeadingIcon:
                    icon: "lock-outline"
                MDTextFieldHintText:
                    text: "Password"
                MDTextFieldHelperText:
                    mode: "on_error"

            AuthField:
                id: confirm_password_field
                password: True
                on_text_validate: root.signup_user()
                MDTextFieldLeadingIcon:
                    icon: "lock-check-outline"
                MDTextFieldHintText:
                    text: "Confirm password"
                MDTextFieldHelperText:
                    mode: "on_error"

            MDButton:
                style: "filled"
                theme_width: "Custom"
                size_hint_x: 1
                height: "48dp"
                on_release: root.signup_user()
                MDButtonText:
                    text: "Sign up"
                    pos_hint: {"center_x": .5, "center_y": .5}

            MDButton:
                style: "text"
                pos_hint: {"center_x": .5}
                on_release: root.go_to_login()
                MDButtonText:
                    text: "Already have an account? Log in"

    ThemeToggleButton:
        pos_hint: {"right": .98, "top": .98}
''')


_error = show_field_error


def _clear_errors(*fields):
    for field in fields:
        field.error = False


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseHelper()

    def on_pre_enter(self, *args):
        _clear_errors(self.ids.email_field, self.ids.password_field)

    def go_to_signup(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'signup'

    def login_user(self, *args):
        email_field = self.ids.email_field
        password_field = self.ids.password_field
        _clear_errors(email_field, password_field)

        email = email_field.text.strip()
        password = password_field.text.strip()

        if not email:
            _error(email_field, "Enter your email")
            return
        if not password:
            _error(password_field, "Enter your password")
            return

        user = self.db.verify_user(email, password)
        if not user:
            _error(password_field, "Incorrect email or password")
            return

        app = MDApp.get_running_app()
        app.config.set('auth', 'user_id', str(user['id']))
        app.config.set('auth', 'username', user['email'])
        app.config.write()

        password_field.text = ""
        self.manager.transition.direction = 'left'
        self.manager.current = 'main'
        self.manager.get_screen('main').load_notes_from_db()


class SignupScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseHelper()

    def on_pre_enter(self, *args):
        ids = self.ids
        _clear_errors(ids.name_field, ids.email_field, ids.password_field,
                      ids.confirm_password_field)

    def go_to_login(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'

    def signup_user(self, *args):
        ids = self.ids
        fields = (ids.name_field, ids.email_field, ids.password_field,
                  ids.confirm_password_field)
        _clear_errors(*fields)

        name, email, password, confirm_password = (f.text.strip() for f in fields)

        for field, value, label in zip(fields, (name, email, password, confirm_password),
                                       ("your name", "your email", "a password",
                                        "the password again")):
            if not value:
                _error(field, f"Enter {label}")
                return

        if password != confirm_password:
            _error(ids.confirm_password_field, "Passwords don't match")
            return

        user_id = self.db.create_user(name, email, password)
        if not user_id:
            _error(ids.email_field, "An account with this email already exists")
            return

        app = MDApp.get_running_app()
        app.config.set('auth', 'user_id', str(user_id))
        app.config.set('auth', 'username', email)
        app.config.write()

        for field in fields:
            field.text = ""
        self.manager.transition.direction = 'left'
        self.manager.current = 'main'
        self.manager.get_screen('main').load_notes_from_db()
