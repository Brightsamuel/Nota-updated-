from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from utils.db_helper import DatabaseHelper

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseHelper()
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            padding=[40, 20, 40, 20],
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # App title
        title = MDLabel(
            text="Nota",
            halign="center",
            font_style="H4",
            theme_text_color="Primary"
        )
        
        # Subtitle
        subtitle = MDLabel(
            text="Login to continue",
            halign="center",
            theme_text_color="Secondary"
        )
        
        # Email field
        self.email_field = MDTextField(
            hint_text="Email",
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Password field
        self.password_field = MDTextField(
            hint_text="Password",
            password=True,
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Login button
        login_btn = MDRaisedButton(
            text="LOGIN",
            size_hint=(1, None),
            height=50,
            on_release=self.login_user
        )
        
        # Signup link
        signup_link = MDLabel(
          text="[ref=signup]Don't have an account? Sign up[/ref]",
          halign="center",
          theme_text_color="Primary",
          markup=True
        )
        signup_link.bind(on_ref_press=lambda *args: setattr(self.parent, 'current', 'signup'))
        
        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(self.email_field)
        layout.add_widget(self.password_field)
        layout.add_widget(login_btn)
        layout.add_widget(signup_link)
        
        self.add_widget(layout)
    
    def on_touch_down(self, touch):
      # Let text fields handle their own touches first
      for child in self.children:
          if child.collide_point(*touch.pos):
              if hasattr(child, 'on_touch_down'):
                  if child.on_touch_down(touch):
                      return True
      return super().on_touch_down(touch)
    
    def login_user(self, *args):
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()
        
        if not email or not password:
            self.show_error("Please fill all fields")
            return
            
        # In a real app, you would verify credentials against your database
        # For now we'll just check if both fields are filled
        user = self.db.verify_user(email, password)
        if user:
            self.parent.current = 'main'
            self.parent.get_screen('main').load_notes_from_db()
            MDApp.get_running_app().config.set('auth', 'user_id', str(user['id']))
            MDApp.get_running_app().config.set('auth', 'username', user['email'])
            MDApp.get_running_app().config.write()
        else:
            self.show_error("Invalid email or password")
    
    def show_error(self, message):
        self.dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

class SignupScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseHelper()
        self.build_ui()
    
    def build_ui(self):
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            padding=[40, 20, 40, 20],
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # App title
        title = MDLabel(
            text="Nota",
            halign="center",
            font_style="H4",
            theme_text_color="Primary"
        )
        
        # Subtitle
        subtitle = MDLabel(
            text="Create an account",
            halign="center",
            theme_text_color="Secondary"
        )
        
        # Name field
        self.name_field = MDTextField(
            hint_text="Full Name",
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Email field
        self.email_field = MDTextField(
            hint_text="Email",
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Password field
        self.password_field = MDTextField(
            hint_text="Password",
            password=True,
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Confirm Password field
        self.confirm_password_field = MDTextField(
            hint_text="Confirm Password",
            password=True,
            mode="fill",
            size_hint=(1, None),
            height=50
        )
        
        # Signup button
        signup_btn = MDRaisedButton(
            text="SIGN UP",
            size_hint=(1, None),
            height=50,
            on_release=self.signup_user
        )
        
        # Login link
        login_link = MDLabel(
            text="[ref=login]Already have an account? Login[/ref]",
            halign="center",
            theme_text_color="Primary",
            markup=True
          )
        login_link.bind(on_ref_press=lambda *args: setattr(self.parent, 'current', 'login'))
        
        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(self.name_field)
        layout.add_widget(self.email_field)
        layout.add_widget(self.password_field)
        layout.add_widget(self.confirm_password_field)
        layout.add_widget(signup_btn)
        layout.add_widget(login_link)
        
        self.add_widget(layout)

    def on_touch_down(self, touch):
      # Let text fields handle their own touches first
      for child in self.children:
          if child.collide_point(*touch.pos):
              if hasattr(child, 'on_touch_down'):
                  if child.on_touch_down(touch):
                      return True
      return super().on_touch_down(touch)
    
    def signup_user(self, *args):
        name = self.name_field.text.strip()
        email = self.email_field.text.strip()
        password = self.password_field.text.strip()
        confirm_password = self.confirm_password_field.text.strip()
        
        if not all([name, email, password, confirm_password]):
            self.show_error("Please fill all fields")
            return
            
        if password != confirm_password:
            self.show_error("Passwords don't match")
            return
            
        # In a real app, you would add more validation
        
        # Create user in database
        user_id = self.db.create_user(name, email, password)
        if user_id:
            self.parent.current = 'main'
            self.parent.get_screen('main').load_notes_from_db()
            MDApp.get_running_app().config.set('auth', 'user_id', str(user_id))
            MDApp.get_running_app().config.set('auth', 'username', email)
            MDApp.get_running_app().config.write()
        else:
            self.show_error("Error creating account. Email may already exist.")
    
    def show_error(self, message):
        self.dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()