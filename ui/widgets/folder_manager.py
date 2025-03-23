from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRoundFlatButton
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from utils.db_helper import DatabaseHelper
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatIconButton
from ui.widgets.folder_select import FolderSelectButton, FolderDialog

class FolderManager:
    def __init__(self, note_view, floatlayout=None):
        self.note_view = note_view
        self.floatlayout = floatlayout
        self.db = DatabaseHelper()
        self.is_locked = False
        self.current_folder_id = None
        self.current_folder_name = None
        self.folder_id_map = {}
        
        # Only set up folder navigation if floatlayout is provided
        if floatlayout:
            self.setup_folder_navigation()  

    def show_folder_dialog(self, note_id, instance=None):
        """Show dialog to select or create a folder."""
        if self.note_view.note:
            note_id = self.note_view.note.id
        else:
            return  # Handle properly or show an error
        folder_dialog = FolderDialog(self, note_id)
        folder_dialog.show_folder_dialog()
            
    def create_folder(self, folder_name, is_locked, password=None):
        """Create a new folder in the database."""
        # Your implementation to create a folder in the database
        folder_id = self.db.create_folder(folder_name, is_locked, password)      

    def move_to_folder(self, folder_id, is_locked):
        """Move the note to the selected folder."""
        if is_locked:
            # Show password prompt
            self.dismiss_popup(None)
            self.show_password_prompt(folder_id)
        else:
            # Move directly
            self.db.move_note_to_folder(self.note_view.note.id, folder_id)
            self.note_view.show_notification("Success", "Note moved to folder")
            
            # Update the UI
            if self.note_view.refresh_callback:
                self.note_view.refresh_callback()
            
            self.dismiss_popup(None)

    def show_password_prompt(self, folder_id):
        """Show prompt to enter folder password."""
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # # Adding background to the content
        # with content.canvas.before:
        #     Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
        #     Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_rect, size=self._update_rect)
        
        message = Label(
            text="This folder is locked. Please enter the password:",
            color=(0.9, 0.9, 0.9, 1)
        )
        
        self.folder_password_input = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=40,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1)
        )
        
        buttons = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        
        unlock_button = MDFlatButton(
            text="Unlock",
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
        
        unlock_button.bind(on_press=lambda x: self.verify_folder_password(folder_id))
        cancel_button.bind(on_press=self.dismiss_popup)
        
        buttons.add_widget(unlock_button)
        buttons.add_widget(cancel_button)
        
        content.add_widget(message)
        content.add_widget(self.folder_password_input)
        content.add_widget(buttons)
        
        self.password_popup = Popup(
            title="Locked Folder", 
            content=content, 
            size_hint=(0.8, 0.4),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.password_popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            self.popup_rect = Rectangle(pos=self.password_popup.pos, size=self.password_popup.size)
        self.password_popup.bind(pos=self._update_rect, size=self._update_rect)
        
        self.password_popup.open()

    def _update_rect(self, instance, value):
        self.popup_rect.pos = instance.pos
        self.popup_rect.size = instance.size

    def verify_folder_password(self, folder_id):
        """Verify the folder password and move the note if correct."""
        password = self.folder_password_input.text.strip()
        if self.db.check_folder_password(folder_id, password):
            # Move the note
            self.db.move_note_to_folder(self.note_view.note.id, folder_id)
            self.note_view.show_notification("Success", "Note moved to locked folder")
            
            # Update the UI
            if self.note_view.refresh_callback:
                self.note_view.refresh_callback()
            
            self.dismiss_popup(None)
        else:
            self.note_view.show_notification("Error", "Incorrect password")
            
    def check_folder_password(self, folder_id, folder_name):
        """Check if password is correct and open folder if it is"""
        password = self.password_field.text
        
        if self.db.check_folder_password(folder_id, password):
            # Close dialog and open folder
            self.dismiss_popup(None)
            self.open_folder(folder_id, folder_name)
        else:
            # Show error
            self.password_field.helper_text = "Incorrect password"
            self.password_field.error = True

    def dismiss_popup(self, instance):
        """Dismiss any active popup."""
        popups = ['folder_popup', 'password_popup', 'options_dialog', 'confirm_dialog', 'password_dialog']
        for popup_name in popups:
            if hasattr(self, popup_name) and getattr(self, popup_name):
                getattr(self, popup_name).dismiss()
        
    def setup_folder_navigation(self):
        """Set up the folder navigation buttons."""
        if not self.floatlayout:
            print("No floatlayout provided to FolderManager")
            return
            
        self.folder_button = MDFloatingActionButton(
            icon="folder",
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'left': 0.05, 'bottom': 0.02},
            md_bg_color=(0, 0, 0, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1)
        )
        self.folder_button.bind(on_press=self.show_folder_selector)
        self.floatlayout.add_widget(self.folder_button)

            # Access the folder button from note_view if it exists
        if hasattr(self.note_view, 'folder_button'):
            self.folder_button = self.note_view.folder_button        
        # Add back button (initially hidden)
        self.back_button = MDFloatingActionButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'left': 0.05, 'bottom': 0.02},
            md_bg_color=(0.5, 0.5, 0.5, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            opacity=0
        )
        self.back_button.bind(on_press=self.back_to_main)
        self.floatlayout.add_widget(self.back_button)
        
        # Update folder list
        self.update_folder_list()
        
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
        close_button.bind(on_press=self.dismiss_popup)
        
        buttons_layout = MDBoxLayout(size_hint_y=None, height=40)
        buttons_layout.add_widget(close_button)
        content.add_widget(buttons_layout)
        
        self.folder_selector_popup = popup
        self.folder_selector_popup.open()
        
    def show_folder_options(self, folder_name):
        """Show options for a folder (delete, rename, etc.)"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
        
        # Get folder ID
        folder_id = self.folder_id_map.get(folder_name)
        if folder_id is None:
            # Try to find the folder name without the icon
            clean_name = folder_name.strip()
            found = False
            for name in self.folder_id_map:
                if name in clean_name:
                    folder_name = name
                    folder_id = self.folder_id_map[name]
                    found = True
                    break
            
            if not found:
                print(f"Error: Cannot find folder name in '{folder_name}'")
                return
            
        # Create list items for options
        delete_item = OneLineIconListItem(
            text="Delete Folder",
            on_release=lambda x: self.confirm_delete_folder(folder_name, folder_id)
        )
        delete_icon = IconLeftWidget(icon="delete")
        delete_item.add_widget(delete_icon)
        
        # Create and show the dialog
        self.options_dialog = MDDialog(
            title=f"Folder Options: {folder_name}",
            type="simple",
            items=[delete_item],
            buttons=[
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: self.dismiss_popup(None)
                )
            ],
        )
        self.options_dialog.open()

    def confirm_delete_folder(self, folder_name, folder_id):
        """Confirm deletion of a folder"""
        # Close the options dialog
        self.dismiss_popup(None)
            
        self.confirm_dialog = MDDialog(
            title="Delete Folder",
            text=f"Are you sure you want to delete '{folder_name}'? All notes will be moved to the main area.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.dismiss_popup(None)
                ),
                MDFlatButton(
                    text="DELETE",
                    text_color="red",
                    on_release=lambda x: self.delete_folder(folder_id, folder_name)
                ),
            ],
        )
        self.confirm_dialog.open()

    def delete_folder(self, folder_id, folder_name):
        """Delete a folder and move its notes to the main area"""
        # Close the confirmation dialog
        self.dismiss_popup(None)
        
        # Delete the folder using DatabaseHelper
        success = self.db.delete_folder(folder_id)
        
        if success:
            # Show success message
            if hasattr(self.note_view, 'show_notification'):
                self.note_view.show_notification("Success", f"Folder '{folder_name}' has been deleted")
            else:
                print(f"Folder '{folder_name}' deleted successfully")
            
            # Remove from folder_id_map
            if folder_name in self.folder_id_map:
                del self.folder_id_map[folder_name]
            
            # Update the folder list
            self.update_folder_list()
            
            # If we were in the deleted folder, go back to main
            if hasattr(self.note_view, 'current_folder_id') and self.note_view.current_folder_id == folder_id:
                self.back_to_main(None)
        else:
            # Show error message
            if hasattr(self.note_view, 'show_notification'):
                self.note_view.show_notification("Error", f"Failed to delete folder '{folder_name}'")
            else:
                print(f"Error deleting folder '{folder_name}'")
        
    def update_folder_list(self):
        """Update the folder list mapping"""
        folders = self.db.get_all_folders()
        
        # Reset folder_id_map
        self.folder_id_map = {}
        
        # Add all folders from the database
        for folder in folders:
            # Skip the default folder if you want
            if folder['id'] == 1 and folder['name'] == 'Default':
                continue
                
            # Store the folder ID in the dictionary for lookup
            self.folder_id_map[folder['name']] = folder['id']
    
    def on_folder_selected(self, folder_id, folder_name, is_locked):
        """Handle folder selection"""
        print(f"Folder selected: {folder_name} (ID: {folder_id})")  # Debug print
        # Close the folder selector popup
        self.dismiss_popup(None)
        
        # Check if folder is locked
        if is_locked:
            # Show password dialog
            self.show_folder_password_dialog(folder_id, folder_name)
        else:
            # Open the folder directly
            self.open_folder(folder_id, folder_name)
            
    def back_to_main(self, instance):
        """Return to main view"""
        # Reset current folder
        if hasattr(self.note_view, 'current_folder_id'):
            self.note_view.current_folder_id = None
        
        # Update screen title if possible
        if hasattr(self.note_view, 'update_screen_title'):
            self.note_view.update_screen_title("Notes")
        elif hasattr(self.note_view, 'app_title'):
            self.note_view.app_title.text = "Notes"
        
        # Load notes (without folder filter)
        if hasattr(self.note_view, 'load_notes_from_db'):
            self.note_view.load_notes_from_db()
        
        # Hide back button if it exists
        if hasattr(self, 'back_button'):
            self.back_button.opacity = 0
        
        # Show folder button if it exists
        if hasattr(self, 'folder_button'):
            self.folder_button.opacity = 1
    
    def show_folder_password_dialog(self, folder_id, folder_name):
        """Show dialog to input password for locked folder using the desired layout"""
        # Create the content layout
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Add a label for the password prompt
        label = Label(
            text="This folder is locked. Please enter the password:",
            size_hint_y=None,
            height=30,
            color=(0.9, 0.9, 0.9, 1)  # Light gray text color
        )
        
        # Add the password input field
        self.password_field = MDTextField(
            hint_text="Password",
            password=True,
            size_hint_y=None,
            height=40,
            mode="rectangle"  # Use a rectangular input field
        )
        
        # Add buttons for unlock and cancel
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=10
        )
        
        unlock_button = MDFlatButton(
            text="Unlock",
            md_bg_color=(0.2, 0.6, 0.8, 1),  # Blue background
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)  # White text
        )
        
        cancel_button = MDFlatButton(
            text="Cancel",
            md_bg_color=(0.3, 0.3, 0.3, 1),  # Gray background
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)  # White text
        )
        
        # Bind buttons to their respective functions
        unlock_button.bind(on_release=lambda x: self.check_folder_password(folder_id, folder_name))
        cancel_button.bind(on_release=lambda x: self.dismiss_popup(None))
        
        # Add widgets to the layout
        buttons_layout.add_widget(unlock_button)
        buttons_layout.add_widget(cancel_button)
        
        content.add_widget(label)
        content.add_widget(self.password_field)
        content.add_widget(buttons_layout)
        
        # Create and show the dialog
        self.password_dialog = MDDialog(
            title=f"Folder Locked: {folder_name}",
            type="custom",
            content_cls=content,
            size_hint=(0.8, 0.4),  # Adjust size as needed
            buttons=[]  # Buttons are already added to the content layout
        )
        
        # Open the dialog
        self.password_dialog.open()
        
    def open_folder(self, folder_id, folder_name):
        print(f"Opening folder: {folder_name} (ID: {folder_id})")  # Debug print
        """Open a folder and display its notes"""
        try:
            print(f"Opening folder: {folder_name} (ID: {folder_id})")
            
            # Update current folder ID
            self.note_view.current_folder_id = folder_id
            
            # Update screen title directly (without calling update_screen_title)
            if hasattr(self.note_view, 'app_title'):
                self.note_view.app_title.text = f"Folder: {folder_name}"
            
            # Load notes from the folder
            if hasattr(self.note_view, 'load_notes_from_db'):
                self.note_view.load_notes_from_db(folder_id)
                print(f"Loaded notes for folder: {folder_id}")
            else:
                print("note_view doesn't have load_notes_from_db method")
            
            # Show the back button
            if hasattr(self, 'back_button'):
                self.back_button.opacity = 1
            
            # Hide the folder button when viewing a specific folder
            if hasattr(self, 'folder_button'):
                self.folder_button.opacity = 0
            
            return True
        except Exception as e:
            print(f"Error opening folder: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def show_folder_selector(self, instance):
        print("Fetching folders from database...")  # Debug print
        folders = self.db.get_all_folders()
        print(f"Folders fetched: {folders}")  # Debug print
        # Rest of the method...
        