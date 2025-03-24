from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty
from kivy.graphics import Rectangle
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivy.uix.popup import Popup
from kivymd.uix.label import MDLabel
from kivy.uix.textinput import TextInput
from utils.db_helper import DatabaseHelper
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp

class FolderSelectButton(MDCard, ButtonBehavior):
    """Custom folder selection button with enhanced responsiveness."""
    folder_id = NumericProperty(0)
    folder_name = StringProperty("")
    is_locked = BooleanProperty(False)
    on_folder_select = ObjectProperty(None)
    on_folder_options = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.ripple_behavior = True
        self.elevation = 2

        self.md_bg_color = (0.3, 0.3, 0.3, 1) if not self.is_locked else (0.4, 0.4, 0.5, 1)

        self.lock_icon = MDIconButton(
            icon='lock' if self.is_locked else 'folder',
            theme_icon_color="Custom",
            icon_color=(1, 0.8, 0.2, 1) if self.is_locked else (0.2, 0.7, 1, 1),
            size_hint_x=None,
            width=dp(40))

        self.folder_label = MDLabel(
            text=self.folder_name,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.8)

        self.arrow_icon = MDIconButton(
            icon="dots-vertical",
            theme_icon_color="Custom",
            icon_color=(0.9, 0.9, 0.9, 1),
            size_hint_x=None,
            width=dp(40),
            ripple_scale=1.5)

        self.add_widget(self.lock_icon)
        self.add_widget(self.folder_label)
        self.add_widget(self.arrow_icon)

        # Changed binding from on_press to on_release for consistency
        self.arrow_icon.bind(on_release=self._on_arrow_press)

    def on_release(self):
        if self.on_folder_select:
            self.on_folder_select(self.folder_id, self.is_locked)

    def _on_arrow_press(self, instance):
        if self.on_folder_options:
            self.on_folder_options(self.folder_id, self.folder_name)


class FolderDialog:
    """Folder selection and management dialog."""
    
    def __init__(self, folder_manager, note_id=None):
        self.folder_manager = folder_manager
        self.note_id = note_id
        self.folder_popup = None
        self.db = DatabaseHelper()
        self.dropdown_menu = None

    def show_folder_selector(self):
        """Display the folder selection popup."""
        content, popup = self._create_folder_popup("Select Folder")
        folder_list = self._create_folder_list(for_selection=True)
        content.add_widget(folder_list)

        close_button = MDRaisedButton(text="Close", on_release=self.dismiss_popup)
        close_button.md_bg_color = (0.3, 0.6, 0.8, 1)
        close_button.text_color = (1, 1, 1, 1)

        content.add_widget(close_button)
        self.folder_popup = popup
        self.folder_popup.open()

    def _create_folder_popup(self, title="Select Folder"):
        """Creates a base popup layout with proper sizing."""
        content = MDBoxLayout(
            orientation='vertical', 
            spacing=dp(8), 
            padding=dp(15),
            size_hint_y=None)
        
        content.bind(minimum_height=content.setter('height'))
        
        popup = Popup(
            title=title, 
            content=content, 
            size_hint=(0.85, 0.9),
            auto_dismiss=True)
        
        content.do_scroll_y = True
        
        return content, popup

    def _create_folder_list(self, for_selection=True):
        """Creates a scrollable list of folders with proper height constraints."""
        folders = self.db.get_all_folders()
        folder_count = len(folders)

        min_height = dp(100)
        max_height = dp(250)
        
        item_height = dp(56)
        spacing = dp(8)
        desired_height = (item_height + spacing) * folder_count
        scroll_height = min(max_height, max(min_height, desired_height))

        scroll_view = ScrollView(
            size_hint=(1, None), 
            height=scroll_height,
            bar_width=dp(4),
            scroll_type=['bars', 'content'],
            bar_color=(0.7, 0.7, 0.7, 0.9),
            bar_inactive_color=(0.5, 0.5, 0.5, 0.2),
            do_scroll_x=False,
            do_scroll_y=True)
        
        folder_layout = GridLayout(
            cols=1, 
            spacing=dp(8), 
            size_hint_y=None,
            padding=[dp(5), dp(5)])
        folder_layout.bind(minimum_height=folder_layout.setter('height'))

        for folder in folders:
            folder_button = FolderSelectButton(
                folder_id=folder['id'],
                folder_name=folder['name'],
                is_locked=folder['is_locked'],
                on_folder_select=self._on_folder_selected if for_selection else self.move_to_folder,
                on_folder_options=self._show_folder_options)
            folder_layout.add_widget(folder_button)

        scroll_view.add_widget(folder_layout)
        return scroll_view

    def _on_folder_selected(self, folder_id, is_locked):
        """Handles folder selection."""
        folder_name = self.db.get_folder_name(folder_id)
        self.folder_manager.on_folder_selected(folder_id, folder_name, is_locked)
        self.dismiss_popup()

    def move_to_folder(self, folder_id, is_locked):
        """Moves a note to the selected folder."""
        if self.note_id:
            self.folder_manager.move_to_folder(folder_id, is_locked, self.note_id)
        self.dismiss_popup()

    def _show_folder_options(self, folder_id, folder_name):
        """Shows a simple dialog for folder options."""
        options_layout = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        
        rename_button = MDFlatButton(
            text="Rename Folder",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=1)
        delete_button = MDFlatButton(
            text="Delete Folder",
            theme_text_color="Custom", 
            text_color=(1, 0.5, 0.5, 1),
            size_hint_x=1)
        password_button = MDFlatButton(
            text="Change Password",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=1)
        
        rename_button.bind(on_release=lambda x: self._rename_folder(folder_id, folder_name))
        delete_button.bind(on_release=lambda x: self._delete_folder(folder_id))
        password_button.bind(on_release=lambda x: self._change_folder_password(folder_id))
        
        options_layout.add_widget(rename_button)
        options_layout.add_widget(delete_button)
        options_layout.add_widget(password_button)
        
        close_button = MDRaisedButton(
            text="Close",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            md_bg_color=(0.3, 0.3, 0.3, 1),
            size_hint_x=1)
        close_button.bind(on_release=lambda x: self.dismiss_options_popup())
        
        options_layout.add_widget(close_button)
        
        self.options_popup = Popup(
            title=f"Folder Options: {folder_name}",
            content=options_layout,
            size_hint=(0.8, 0.5))
        self.options_popup.open()
    
    def dismiss_options_popup(self):
        if hasattr(self, 'options_popup') and self.options_popup:
            self.options_popup.dismiss()

    def _rename_folder(self, folder_id, folder_name):
        """Show dialog to rename folder"""
        if hasattr(self, 'options_popup') and self.options_popup:
            self.options_popup.dismiss()
        self.folder_manager.rename_folder(folder_id, folder_name)

    def _delete_folder(self, folder_id):
        """Delete folder after confirmation"""
        if hasattr(self, 'options_popup') and self.options_popup:
            self.options_popup.dismiss()
        self.folder_manager.delete_folder(folder_id)

    def _change_folder_password(self, folder_id):
        """Change folder password"""
        if hasattr(self, 'options_popup') and self.options_popup:
            self.options_popup.dismiss()
        self.folder_manager.change_folder_password(folder_id)

    def show_folder_dialog(self, instance=None):
        print("Show folder dialog called")
        
        if hasattr(self, 'note_id'):
            print(f"Note ID: {self.note_id}")
        else:
            print("No note_id attribute found")
            self.note_id = None
        
        if not hasattr(self, 'folder_manager'):
            print("No folder_manager attribute - this will cause issues")
            self.folder_manager = self

        content, popup = self._create_folder_popup("")
        
        folders = self.db.get_all_folders()
        
        title_label = MDLabel(
            text="Select Folder", 
            theme_text_color="Custom",
            text_color=(0.3, 0.6, 0.9, 1),
            font_style="H6",
            size_hint_y=None,
            height=30)
        content.add_widget(title_label)
        
        scroll_view = self._create_folder_list(for_selection=False)
        content.add_widget(scroll_view)
        
        new_folder_layout = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=140)
        
        new_folder_title = MDLabel(
            text="Create New Folder",
            theme_text_color="Custom",
            text_color=(0.3, 0.6, 0.9, 1),
            font_style="Subtitle1",
            size_hint_y=None,
            height=30)
        
        folder_input_layout = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        self.folder_name_input = TextInput(
            hint_text="Folder Name",
            multiline=False,
            size_hint_x=0.7,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.3, 0.6, 0.9, 1),
            padding=(10, 12, 10, 10))
        
        self.lock_checkbox = MDBoxLayout(size_hint_x=0.3, padding=5)
        self.lock_label = MDLabel(
            text="Lock", 
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1))
        self.is_locked = False
        self.lock_button = MDIconButton(
            icon="lock-open",
            size_hint_x=0.5,
            theme_icon_color="Custom",
            icon_color=(0.9, 0.9, 0.9, 1),
            md_bg_color=(0.3, 0.3, 0.3, 1))
        self.lock_button.bind(on_release=self.toggle_lock)

        self.lock_checkbox.add_widget(self.lock_label)
        self.lock_checkbox.add_widget(self.lock_button)
        
        folder_input_layout.add_widget(self.folder_name_input)
        folder_input_layout.add_widget(self.lock_checkbox)
        
        self.password_layout = MDBoxLayout(
            size_hint_y=None, 
            height=0,
            opacity=0)
        self.password_input = TextInput(
            hint_text="Enter Password",
            password=True,
            multiline=False,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.3, 0.6, 0.9, 1),
            padding=(10, 12, 10, 10))
        self.password_layout.add_widget(self.password_input)
        
        buttons = MDBoxLayout(size_hint_y=None, height=60, spacing=15, padding=[0, 10, 0, 0])
        
        create_folder_button = MDRaisedButton(
            text="Create Folder",
            md_bg_color=(0.2, 0.6, 0.8, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1))
        
        cancel_button = MDRaisedButton(
            text="Cancel",
            md_bg_color=(0.5, 0.5, 0.5, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1))
        
        # Changed from on_release to on_press for more immediate response
        create_folder_button.bind(on_press=self.create_new_folder)
        cancel_button.bind(on_press=self.dismiss_popup)
        
        buttons.add_widget(create_folder_button)
        buttons.add_widget(cancel_button)
        
        new_folder_layout.add_widget(new_folder_title)
        new_folder_layout.add_widget(folder_input_layout)
        new_folder_layout.add_widget(self.password_layout)
        
        content.add_widget(new_folder_layout)
        content.add_widget(buttons)
        
        self.initial_popup_height = popup.height
        
        self.folder_popup = popup
        self.folder_popup.open()

    def toggle_lock(self, instance):
        """Toggle the lock state with simplified approach."""
        self.is_locked = not self.is_locked
        
        if self.is_locked:
            instance.icon = "lock"
            instance.md_bg_color = (0.8, 0.4, 0.2, 1)
            instance.icon_color = (1, 0.8, 0.2, 1)
            
            self.password_layout.height = dp(40)
            self.password_layout.opacity = 1
            self.password_input.opacity = 1
            self.password_input.disabled = False
        else:
            instance.icon = "lock-open"
            instance.md_bg_color = (0.3, 0.3, 0.3, 1)
            instance.icon_color = (0.9, 0.9, 0.9, 1)
            
            self.password_input.disabled = True
            self.password_layout.height = 0
            self.password_layout.opacity = 0
            self.password_input.text = ""

    def _update_rect(self, instance, value):
            """Update rectangle position and size for canvas backgrounds."""
            for child in instance.canvas.before.children:
                if isinstance(child, Rectangle):
                    child.pos = instance.pos
                    child.size = instance.size

    def create_new_folder(self, instance):
        """Create a new folder and move the note to it."""
        folder_name = self.folder_name_input.text.strip()
        if not folder_name:
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Error", "Please enter a folder name")
            return
        
        password = None
        if self.is_locked:
            password = self.password_input.text.strip()
            if not password:
                if hasattr(self.folder_manager, 'show_notification'):
                    self.folder_manager.show_notification("Error", "Please enter a password for the locked folder")
                return
        
        folder_id = self.db.create_folder(folder_name, self.is_locked, password)
        
        if folder_id and self.note_id:
            self.db.move_note_to_folder(self.note_id, folder_id)
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Success", f"Note moved to folder '{folder_name}'")
            
            if hasattr(self.folder_manager, 'refresh_callback') and self.folder_manager.refresh_callback:
                self.folder_manager.refresh_callback()
        elif folder_id:
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Success", f"Folder '{folder_name}' created")
            
            if hasattr(self.folder_manager, 'refresh_callback') and self.folder_manager.refresh_callback:
                self.folder_manager.refresh_callback()
        else:
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Error", "Failed to create folder")
        
        self.dismiss_popup()

    def dismiss_popup(self, instance=None):
        """Dismiss the currently open popup."""
        if hasattr(self, 'folder_popup') and self.folder_popup:
            self.folder_popup.dismiss()
        if hasattr(self, 'folder_selector_popup') and self.folder_selector_popup:
            self.folder_selector_popup.dismiss()
        if hasattr(self, 'options_popup') and self.options_popup:
            self.options_popup.dismiss()