from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.uix.button import Button
import webbrowser
from kivy.utils import platform
from kivymd.uix.button import MDFloatingActionButton, MDFlatButton, MDIconButton  # Add these imports
from ui.widgets.folder_manager import FolderManager
from kivy.core.clipboard import Clipboard
from ui.widgets.tag_manager import TagManager
import os
import traceback
from kivy.properties import ObjectProperty
try:
    from plyer import share
    share_available = True
except (ImportError, ModuleNotFoundError):
    share_available = False
from kivy.lang import Builder
from models.note import Note
from ui.widgets.note_view import NoteView
from utils.graphics import create_gradient_texture
from utils.db_helper import DatabaseHelper

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
kv_file = os.path.join(project_root, 'tagmanager.kv')

try:
    Builder.load_file(kv_file)
    print(f"Successfully loaded KV file from: {kv_file}")
except Exception as e:
    print(f"Error loading KV file: {e}")
    print(f"Attempted to load from path: {kv_file}")

class MainScreen(Screen):
    tag_manager = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.is_loading_notes = False  # Add a flag to track note loading
        self.db = DatabaseHelper()
        self.note_list = []
        self.tag_manager = TagManager()
        self.folder_manager = FolderManager(note_view=self)
        self.password_dialog = None
        self.folder_popup = None
        self.current_folder_id = None
        self.current_folder_id = None
        self.folder_id_map = {}
        
        self.add_widget(self.tag_manager)
        
        self.root = MDBoxLayout(orientation='vertical', padding=[20, 20], spacing=10)
        self.float_layout = FloatLayout(size_hint=(1, 0.1))
        
        # Initialize folder manager with both self and float_layout
        self.folder_manager = FolderManager(self, self.float_layout)
        
        # Add folder button specifically for main screen
        self.folder_button = MDFloatingActionButton(
            icon="folder",
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'left': 0.05, 'bottom': 0.02},
            md_bg_color=(0, 0, 0, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1)
        )
        self.folder_button.bind(on_press=self.show_folders)  # Bind to local method
        self.float_layout.add_widget(self.folder_button)
        
        with self.root.canvas.before:
            Color(1, 1, 1, 1)
            self.gradient_texture = create_gradient_texture((0, 0, 0, 1), (0.2, 0.2, 0.2, 1), 
                                                            width=Window.width, height=Window.height)
            self.rect = Rectangle(size=self.root.size, pos=self.root.pos, texture=self.gradient_texture)
        self.root.bind(size=self._update_rect, pos=self._update_rect)

        self.app_title = Label(
            text='Nota',
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
            font_size='24sp',
            halign='left'
        )
        self.app_title.bind(size=self.app_title.setter('text_size'))
        
        self.search_input = TextInput(
            hint_text="Search",
            size_hint_y=None,
            height=50,
            background_color=(0, 0, 0, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            font_size='16sp',
            multiline=False
        )
        
        self.search_input.bind(text=self.on_search_text_changed)

        self.notes_container = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=[10, 10])
        self.notes_container.bind(minimum_height=self.notes_container.setter('height'))

        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.scroll_view.add_widget(self.notes_container)

        self.content_layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[15, 15])
        self.content_layout.add_widget(self.scroll_view)

        self.root.add_widget(self.app_title)
        self.root.add_widget(self.search_input)
        self.root.add_widget(self.content_layout)
        
        self.add_note_button = MDFloatingActionButton(
            icon="plus",
            size_hint=(None, None),
            size=(60, 60),
            md_bg_color=(0, 0, 0, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            pos_hint={'right': 1, 'bottom': 15}
        )
        self.add_note_button.bind(on_press=self.go_to_notes_create)
        self.float_layout.add_widget(self.add_note_button)

        self.root.add_widget(self.float_layout)

        self.load_notes_from_db()
        self.display_notes()

        self.add_widget(self.root)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def on_enter(self):
        self.tag_manager.track_event('screen_view', screen_name='main')
        
    def go_to_notes_create(self, instance):
        self.manager.current = "notes"
        self.manager.transition.direction = 'left'
        
    def update_screen_title(self, title):
        """Update the screen title without causing circular calls"""
        if hasattr(self, 'app_title'):
            self.app_title.text = title
            
            # Only update folder manager state without triggering another load
            if self.folder_manager and "Folder:" in title:
                # Extract the folder name from the title
                folder_name = title.replace("Folder:", "").strip()
                
                # Update folder manager's internal state
                if hasattr(self.folder_manager, 'current_folder_name'):
                    self.folder_manager.current_folder_name = folder_name
                    
                # Instead of calling open_folder, just update UI state if needed
                if hasattr(self.folder_manager, 'update_folder_buttons'):
                    self.folder_manager.update_folder_buttons(is_in_folder=True)
                
                # You can still track the current folder ID if needed
                folder_id = self.folder_manager.folder_id_map.get(folder_name)
                if folder_id is not None:
                    self.folder_manager.current_folder_id = folder_id
                    
    def add_note(self, note):
        if self.current_folder_id:
            note_id = self.db.add_note(note.title, note.content)
            self.db.move_note_to_folder(note_id, self.current_folder_id)
        else:
            note_id = self.db.add_note(note.title, note.content)
        
        fresh_note_data = self.db.get_note_by_id(note_id)
        fresh_note = Note.from_db_row(fresh_note_data)
        
        self.note_list.append(fresh_note)
        self.display_notes()
            
    def display_notes(self):
        self.notes_container.clear_widgets()
        for note in self.note_list:
            note_view = NoteView(note, self.delete_note_and_refresh)
            self.notes_container.add_widget(note_view)

    def load_notes_from_db(self, folder_id=None):
        if self.is_loading_notes:
            return  # Exit if notes are already being loaded        
        self.is_loading_notes = True  # Set the flag to True
        print(f"Loaded notes for folder: {folder_id}")  # Debug print
        print(f"Called from: {traceback.format_stack()}")  # Print the call stack
      
        """Load notes with proper folder filtering"""
        try:
            self.note_list = []
            if folder_id is None:
                db_notes = self.db.get_all_notes()
                # Update UI for main view
                self.update_screen_title("Notes")
            else:
                db_notes = self.db.get_notes_by_folder(folder_id)
                # Get folder name and update UI
                folder = self.db.get_folder(folder_id)
                if folder:
                    self.update_screen_title(f"Folder: {folder['name']}")
            
            for row in db_notes:
                note = Note.from_db_row(row)
                self.note_list.append(note)
                
            self.display_notes()
            self.current_folder_id = folder_id
        except Exception as e:
            print(f"Error loading notes: {e}")
        finally:
            self.is_loading_notes = False  # Reset the flag

    def delete_note_and_refresh(self, note):
        if note.id is not None:
            self.db.delete_note(note.id)
        self.note_list.remove(note)
        self.refresh_note_views()

    def refresh_note_views(self):
        self.notes_container.clear_widgets()
        self.display_notes()

    def on_search_text_changed(self, instance, value):
        if value.strip():
            self.note_list = []
            results = self.db.search_notes(value.strip())
            for row in results:
                note = Note.from_db_row(row)
                self.note_list.append(note)
        else:
            self.load_notes_from_db()
        
        self.display_notes()
    
    def show_popup(self, title, message):
        popup = Popup(
            title=title, 
            content=Label(text=message), 
            size_hint=(0.8, 0.3)
        )
        popup.open()
    
    def share_note(self, note):
        if share_available and platform == 'android':
            try:
                share.share(
                    title="Share Note",
                    text=f"{note.title}\n\n{note.content}",
                    chooser=True
                )
                return
            except Exception as e:
                print(f"Plyer share failed: {str(e)}")
        
        try:
            Clipboard.copy(f"{note.title}\n\n{note.content}")
            self.show_popup("Copied to Clipboard", 
                           "Note has been copied to clipboard since direct sharing is not available")
            return
        except Exception as e:
            print(f"Clipboard copy failed: {str(e)}")
        
        try:
            subject = note.title
            body = note.content
            mailto_link = f"mailto:?subject={subject}&body={body}"
            webbrowser.open(mailto_link)
            return
        except Exception as e:
            print(f"Email share failed: {str(e)}")
            self.show_popup("Sharing Failed", 
               "Unable to share note. No sharing method is available on this platform.")
    
    def show_folders(self, instance):
        """Display folders and their contents in a popup"""
        try:
            folders = self.db.get_all_folders()
            
            # Create popup content
            content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
            
            # Create scrollable container for folders
            scroll = ScrollView(size_hint=(1, None), height=400)
            grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[10, 10])
            grid.bind(minimum_height=grid.setter('height'))
            
            # Add "All Notes" option at the top
            notes_count = len(self.db.get_all_notes())
            main_btn = MDFlatButton(
                text=f"All Notes ({notes_count} notes)",
                size_hint_y=None,
                height=50,
                md_bg_color=(0.2, 0.2, 0.2, 1),
                text_color=(1, 1, 1, 1)
            )
            main_btn.bind(on_press=lambda x: self.load_folder(None, "All Notes"))
            grid.add_widget(main_btn)
            
            # Add each folder with its notes count
            for folder in folders:
                folder_id = folder['id']
                folder_name = folder['name']
                is_locked = folder['is_locked']
                notes_count = folder['note_count']
                
                folder_layout = MDBoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    height=50,
                    spacing=5
                )
                
                # Create folder button
                btn = MDFlatButton(
                    text=f"{folder_name} ({notes_count} notes)",
                    size_hint=(0.8, 1),
                    md_bg_color=(0.2, 0.2, 0.2, 1),
                    text_color=(1, 1, 1, 1)
                )
                
                # Correctly bind the folder selection function
                # Use lambda with default arguments to capture the current values
                btn.bind(on_press=lambda x, fid=folder_id, locked=is_locked, fname=folder_name: 
                        self.handle_folder_selection(fid, locked, fname))
                
                # Add lock icon if folder is locked
                if is_locked:
                    lock_icon = MDIconButton(
                        icon="lock", 
                        theme_text_color="Custom", 
                        text_color=(1, 0.8, 0, 1)
                    )
                    folder_layout.add_widget(lock_icon)
                
                folder_layout.add_widget(btn)
                grid.add_widget(folder_layout)
            
            scroll.add_widget(grid)
            content.add_widget(scroll)
            
            # Add close button at the bottom
            close_btn = MDFlatButton(
                text="Close",
                size_hint_y=None,
                height=40,
                md_bg_color=(0.3, 0.3, 0.3, 1),
                text_color=(1, 1, 1, 1)
            )
            
            # Use an instance variable to track the popup
            self.folder_popup = Popup(
                title='Available Folders',
                content=content,
                size_hint=(0.9, 0.9)
            )
            
            close_btn.bind(on_press=lambda x: self.folder_popup.dismiss())
            content.add_widget(close_btn)
            
            self.folder_popup.open()
        
        except Exception as e:
            print(f"Error showing folders: {e}")
            self.show_popup("Error", "Failed to load folders")

    def show_folder_password_dialog(self, folder_id, folder_name):
        """Show dialog to input password for locked folder"""
        # Use the FolderManager's method to show the password dialog
        self.folder_manager.show_folder_password_dialog(folder_id, folder_name)
    
    def handle_folder_selection(self, folder_id, is_locked, folder_name):
        """Handle folder selection based on lock status"""
        if is_locked:
            self.show_folder_password_dialog(folder_id, folder_name)
        else:
            self.load_folder(folder_id, folder_name)

    def check_folder_password(self, folder_id, folder_name):
        """Check if the entered password is correct and load the folder if it is"""
        # Use the FolderManager's method to check the password
        self.folder_manager.check_folder_password(folder_id, folder_name)

    def dismiss_popup(self, instance):
        """Dismiss the password dialog"""
        if self.password_dialog:
            self.password_dialog.dismiss()

    def load_folder(self, folder_id, folder_name=None):
        """Load notes from selected folder"""
        try:
            self.current_folder_id = folder_id
            
            if folder_id is None:
                self.update_screen_title("All Notes")
                self.load_notes_from_db()
            else:
                self.update_screen_title(f"Folder: {folder_name}")
                self.load_notes_from_db(folder_id)
            
            # Close any open popups
            if hasattr(self, 'folder_popup') and self.folder_popup:
                self.folder_popup.dismiss()
                
        except Exception as e:
            print(f"Error loading folder: {e}")
            self.show_popup("Error", "Failed to load folder contents")

    # def show_password_prompt(self, folder_id, folder_name):
    #     """Show password prompt for locked folders using MDDialog layout"""
    #     self.password_field = MDTextField(
    #         hint_text="Enter password", 
    #         password=True, 
    #         size_hint_y=None, 
    #         height=40
    #     )
        
    #     self.password_dialog = MDDialog(
    #         title=f"Folder Locked: {folder_name}",
    #         type="custom",
    #         content_cls=self.password_field,
    #         buttons=[
    #             MDFlatButton(
    #                 text="CANCEL", 
    #                 on_release=lambda x: self.dismiss_popup(None)
    #             ),
    #             MDFlatButton(
    #                 text="UNLOCK", 
    #                 on_release=lambda x: self.check_folder_password(folder_id, folder_name)
    #             ),
    #         ],
    #     )
    #     self.password_dialog.open()

    # def check_folder_password(self, folder_id, folder_name):
    #     entered_password = self.password_field.text
    #     correct_password = self.db.get_folder_password(folder_id)
    #     if entered_password == correct_password:
    #         self.dismiss_popup(None)
    #         self.load_folder(folder_id, folder_name)
    #         if self.folder_popup:
    #             self.folder_popup.dismiss()
    #     else:
    #         self.password_field.error = True
    #         self.password_field.helper_text = "Incorrect password, try again!"

    def dismiss_popup(self, instance):
        if self.password_dialog:
            self.password_dialog.dismiss()

