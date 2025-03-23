from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRectangleFlatIconButton
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivymd.uix.label import MDLabel
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from utils.db_helper import DatabaseHelper


# Create a custom button class for folder selection
class FolderSelectButton(ButtonBehavior, MDBoxLayout):
    folder_id = NumericProperty(0)
    folder_name = StringProperty("")
    is_locked = BooleanProperty(False)
    on_folder_select = ObjectProperty(None)
    on_folder_options = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super(FolderSelectButton, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.spacing = 5
        self.padding = [5, 0, 5, 0]
        
        # Set background color based on lock status
        self.md_bg_color = (0.3, 0.3, 0.3, 1) if not self.is_locked else (0.4, 0.4, 0.5, 1)
        
        # Create lock icon
        self.lock_icon = MDIconButton(
            icon='lock' if self.is_locked else 'folder',
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=None,
            width=30
        )
        
        # Create folder name label
        self.folder_label = MDLabel(
            text=self.folder_name,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_x=0.8
        )
        
        # Create arrow icon for options
        self.arrow_icon = MDIconButton(
            icon="dots-vertical",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=None,
            width=30
        )
        
        # Add widgets to layout
        self.add_widget(self.lock_icon)
        self.add_widget(self.folder_label)
        self.add_widget(self.arrow_icon)
        
        # Bind events
        self.arrow_icon.bind(on_release=self._on_arrow_press)  # Changed to on_release
    
    def on_release(self):  # Changed to on_release for consistency
        # This is called when the main area is pressed
        if self.on_folder_select:
            self.on_folder_select(self.folder_id, self.is_locked)
    
    def _on_arrow_press(self, instance):
        # This is called when the arrow is pressed
        if self.on_folder_options:
            self.on_folder_options(self.folder_name)  # Pass folder name, not label widget
        return True  # Prevent event propagation

# A helper class to handle folder dialogs
class FolderDialog:
    def __init__(self, folder_manager, note_id=None):
        self.folder_manager = folder_manager  # This should be your main app class that has methods like move_to_folder
        self.note_id = note_id  # Store the note_id, can be None when just browsing folders
        self.folder_popup = None
        self.folder_selector_popup = None
        self.db = DatabaseHelper()  # Access the database
        
        # These will be set when creating the dialog
        self.folder_name_input = None
        self.password_input = None
        self.password_layout = None
        self.lock_button = None
        self.is_locked = False
        self.lock_checkbox = None
        self.lock_label = None
    
    def show_folder_selector(self, instance=None):
        """Show a dialog to select from available folders."""
        content, popup = self._create_folder_popup_base("Select Folder")
        
        # Add folder list
        folder_list = self._create_folder_list(include_main=True, for_selection=True)
        content.add_widget(folder_list)
        
        # Add close button
        close_button = MDFlatButton(
            text="Close",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        close_button.bind(on_release=self.dismiss_popup)  # Changed to on_release
        
        buttons_layout = MDBoxLayout(size_hint_y=None, height=40)
        buttons_layout.add_widget(close_button)
        content.add_widget(buttons_layout)
        
        self.folder_selector_popup = popup
        self.folder_selector_popup.open()

    def _create_folder_popup_base(self, title="Select Folder"):
        """Create a base popup for folder selection with common UI elements."""
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_rect, size=self._update_rect)
        
        # Create the popup
        popup = Popup(
            title=title, 
            content=content, 
            size_hint=(0.8, 0.7),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            Rectangle(pos=popup.pos, size=popup.size)
        popup.bind(pos=self._update_rect, size=self._update_rect)
        
        return content, popup

    def _create_folder_list(self, include_main=True, for_selection=True):
        """Create a scrollable list of folders."""
        # Get all folders
        folders = self.db.get_all_folders()
        
        # Create a scrollable view for folders
        scroll_height = 200 if for_selection else 150
        scroll_view = ScrollView(size_hint=(1, None), height=scroll_height)
        folder_layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
        folder_layout.bind(minimum_height=folder_layout.setter('height'))
        
        # Add "Main" option if requested
        if include_main and hasattr(self.folder_manager, 'back_to_main'):
            main_button = MDRectangleFlatIconButton(
                text="Main",
                icon="folder-home",
                size_hint_y=None,
                height=40,
                md_bg_color=(0.3, 0.3, 0.3, 1)
            )
            main_button.bind(on_release=self.folder_manager.back_to_main)  # Changed to on_release
            folder_layout.add_widget(main_button)
        
        # Add folders to the layout
        if for_selection:
            # For folder selection (show_folder_selector style)
            for folder in folders:
                folder_name = folder['name']
                is_locked = folder['is_locked']
                folder_id = folder['id']
                
                # Create a button layout with folder button and options button
                button_layout = MDBoxLayout(size_hint_y=None, height=40, spacing=2)
                
                # Create a button for each folder
                folder_button = MDRectangleFlatIconButton(
                    text=folder_name,
                    icon=('lock' if is_locked else 'folder'),
                    size_hint_x=0.8,
                    height=40,
                    md_bg_color=(0.3, 0.3, 0.3, 1) if not is_locked else (0.4, 0.4, 0.5, 1)
                )
                
                # Using a custom callback to avoid lambda issues
                def create_on_press_callback(fid, fname, flock):
                    def on_folder_selected_callback(btn):
                        self.folder_manager.on_folder_selected(fid, fname, flock)
                    return on_folder_selected_callback

                folder_button.bind(on_release=create_on_press_callback(folder['id'], folder['name'], folder['is_locked']))
                
                # Add options button for each folder
                options_button = MDIconButton(
                    icon="dots-vertical",
                    size_hint_x=0.2,
                    md_bg_color=(0.3, 0.3, 0.3, 1)
                )
                
                # Using a custom callback to avoid lambda issues
                def create_options_callback(fname):
                    def on_options_callback(btn):
                        if hasattr(self.folder_manager, 'show_folder_options'):
                            self.folder_manager.show_folder_options(fname)
                    return on_options_callback
                
                options_button.bind(on_release=create_options_callback(folder_name))
                
                button_layout.add_widget(folder_button)
                button_layout.add_widget(options_button)
                folder_layout.add_widget(button_layout)
        else:
            # For moving notes to folders (show_folder_dialog style)
            for folder in folders:
                folder_button = FolderSelectButton(
                    folder_id=folder['id'],
                    folder_name=folder['name'],
                    is_locked=folder['is_locked'],
                    on_folder_select=self.move_to_folder,  # Use local method that then calls manager
                    on_folder_options=self.show_folder_options  # Use local method
                )
                folder_layout.add_widget(folder_button)
        
        scroll_view.add_widget(folder_layout)
        return scroll_view
    
    def move_to_folder(self, folder_id, is_locked):
        """Local method to pass the call to folder_manager with note_id."""
        if hasattr(self.folder_manager, 'move_to_folder') and self.note_id:
            self.folder_manager.move_to_folder(folder_id, is_locked, self.note_id)
        self.dismiss_popup()
    
    def show_folder_options(self, folder_name):
        """Local method to pass to folder_manager."""
        if hasattr(self.folder_manager, 'show_folder_options'):
            self.folder_manager.show_folder_options(folder_name)

    def show_folder_dialog(self, instance=None):
        """Show dialog to move note to a folder or create a new one."""
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_rect, size=self._update_rect)
        
        # Get all available folders
        folders = self.db.get_all_folders()
        
        # Create a scrollable view for folders
        scroll_view = ScrollView(size_hint=(1, None), height=150)
        folder_layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
        folder_layout.bind(minimum_height=folder_layout.setter('height'))
        
        # Add folders to the layout
        for folder in folders:
            folder_name = folder['name']
            is_locked = folder['is_locked']
            
            # Create a button layout with folder button and options button
            button_layout = MDBoxLayout(size_hint_y=None, height=40, spacing=2)
            
            # Create a button for each folder
            folder_button = MDRectangleFlatIconButton(
                text=folder_name,
                icon=('lock' if is_locked else 'lock-open'),
                size_hint_x=0.8,
                height=40,
                md_bg_color=(0.3, 0.3, 0.3, 1) if not is_locked else (0.4, 0.4, 0.5, 1)
            )
            folder_button.bind(on_press=lambda btn, folder_id=folder['id'], is_locked=is_locked: 
            self.move_to_folder(folder_id, is_locked))
            
            # Add options button for each folder
            options_button = MDIconButton(
                icon="dots-vertical",
                size_hint_x=0.2,
                md_bg_color=(0.3, 0.3, 0.3, 1)
            )
            options_button.bind(on_press=lambda btn, folder_name=folder_name: 
            self.show_folder_options(folder_name))
            
            button_layout.add_widget(folder_button)
            button_layout.add_widget(options_button)
            folder_layout.add_widget(button_layout)
        
        scroll_view.add_widget(folder_layout)
        
        # Create new folder section
        new_folder_layout = MDBoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=120)
        
        new_folder_title = Label(
            text="Create New Folder",
            size_hint_y=None,
            height=30,
            color=(0.9, 0.9, 0.9, 1)
        )
        
        folder_input_layout = MDBoxLayout(size_hint_y=None, height=40, spacing=5)
        self.folder_name_input = TextInput(
            hint_text="Folder Name",
            multiline=False,
            size_hint_x=0.7,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1)
        )
        
        self.lock_checkbox = MDBoxLayout(size_hint_x=0.3, padding=5)
        self.lock_label = Label(text="Lock", size_hint_x=0.5)
        self.is_locked = False
        self.lock_button = MDIconButton(
            icon="lock-open",  # Initially unlocked
            size_hint_x=0.5,
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),  # White lock
            md_bg_color=(0.3, 0.3, 0.3, 1)  # Dark gray background
        )
        self.lock_button.bind(on_press=self.toggle_lock)

        self.lock_checkbox.add_widget(self.lock_label)
        self.lock_checkbox.add_widget(self.lock_button)
        
        folder_input_layout.add_widget(self.folder_name_input)
        folder_input_layout.add_widget(self.lock_checkbox)
        
        # Password input (initially hidden)
        self.password_layout = MDBoxLayout(size_hint_y=None, height=40, opacity=0)
        self.password_input = TextInput(
            hint_text="Enter Password",
            password=True,
            multiline=False,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1)
        )
        self.password_layout.add_widget(self.password_input)
        
        # Buttons
        buttons = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        
        create_folder_button = MDFlatButton(
            text="Create Folder",
            md_bg_color=(0.2, 0.6, 0.8, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        cancel_button = MDFlatButton(
            text="Cancel",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        create_folder_button.bind(on_press=self.create_new_folder)
        cancel_button.bind(on_press=self.dismiss_popup)
        
        buttons.add_widget(create_folder_button)
        buttons.add_widget(cancel_button)
        
        new_folder_layout.add_widget(new_folder_title)
        new_folder_layout.add_widget(folder_input_layout)
        new_folder_layout.add_widget(self.password_layout)
        
        content.add_widget(Label(text="Select Folder", color=(0.9, 0.9, 0.9, 1)))
        content.add_widget(scroll_view)
        content.add_widget(new_folder_layout)
        content.add_widget(buttons)
        
        self.folder_popup = Popup(
            title="Folders", 
            content=content, 
            size_hint=(0.8, 0.7),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.folder_popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            self.popup_rect = Rectangle(pos=self.folder_popup.pos, size=self.folder_popup.size)
        self.folder_popup.bind(pos=self._update_rect, size=self._update_rect)
        
        self.folder_popup.open()
    
    def _update_rect(self, instance, value):
        """Update rectangle position and size for canvas backgrounds."""
        for child in instance.canvas.before.children:
            if isinstance(child, Rectangle):
                child.pos = instance.pos
                child.size = instance.size
    
    def toggle_lock(self, instance):
        """Toggle the lock state for new folder creation."""
        self.is_locked = not self.is_locked
        if self.is_locked:
            instance.icon = "lock"  # KivyMD icon for locked
            instance.md_bg_color = (0.6, 0.4, 0.4, 1)
        else:
            instance.icon = "lock-open"  # KivyMD icon for unlocked
            instance.md_bg_color = (0.3, 0.3, 0.3, 1)

        # Show/hide password input based on lock state
        Animation(opacity=1 if self.is_locked else 0, duration=0.2).start(self.password_layout)
    
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
        
        # Create the folder
        folder_id = self.db.create_folder(folder_name, self.is_locked, password)
        
        # Move the note to the new folder if we have a note_id
        if folder_id and self.note_id:
            self.db.move_note_to_folder(self.note_id, folder_id)
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Success", f"Note moved to folder '{folder_name}'")
            
            # Update the UI
            if hasattr(self.folder_manager, 'refresh_callback') and self.folder_manager.refresh_callback:
                self.folder_manager.refresh_callback()
        elif folder_id:
            if hasattr(self.folder_manager, 'show_notification'):
                self.folder_manager.show_notification("Success", f"Folder '{folder_name}' created")
            
            # Update the UI
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