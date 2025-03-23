from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatButton
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.textinput import TextInput
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon
import webbrowser
from kivy.core.clipboard import Clipboard
from utils.event_tracker import track_event
# Import for Google Drive functionality
try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    google_drive_available = True
except ImportError:
    google_drive_available = False

# Try to import share from plyer
try:
    from plyer import share
    share_available = True
except (ImportError, ModuleNotFoundError):
    share_available = False

from utils.db_helper import DatabaseHelper
from models.note import Note
from ui.widgets.folder_manager import FolderManager  # Import the folder manager

class NoteView(MDBoxLayout):
    def __init__(self, note, delete_callback, refresh_callback=None, **kwargs):
        super(NoteView, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        #self.height = 100
        Window.bind(on_resize=self.on_window_resize)
        
        self.padding = [10, 5]
        self.spacing = 5
        
        self.delete_callback = delete_callback
        self.refresh_callback = refresh_callback
        self.note = note
        self.db = DatabaseHelper()
        self.folder_manager = FolderManager(self)
        
        # Background for each note
        with self.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for notes
            self.rect = Rectangle(size=self.size, pos=self.pos)
            #Add a border
            Color(0.15, 0.15, 0.15, 1)  # Slightly lighter gray for border
            self.border = Line(Rectangle=(self.x, self.y, self.width, self.height), width=1)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # Get the first sentence for preview
        content_preview = note.content.split('.')[0]
        if len(content_preview) > 100:  # Limit length if first sentence is too long
            content_preview = content_preview[:100] + "..."
        elif content_preview == note.content and not content_preview.endswith('.'):
            content_preview += "..."
       
        # Create title label
        self.title_label = Label(
        text=note.title, 
        size_hint=(0.7, None),  
        height=30,
        color=(0.8, 0.8, 0.8, 1),  
        font_size='16sp',
        halign='left',
        valign='middle',
        text_size=(self.width, None)  # Ensure text wraps properly
    )

        #Proper way to bind size to text_size
        self.title_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
        
        # Pin indicator using an icon instead of emoji
        self.pin_indicator = MDIcon(
            icon="pin",
            theme_text_color="Custom",
            text_color=(1, 0.8, 0, 1),  # Gold color for pin
            font_size="16sp",
            opacity=1 if note.is_pinned else 0  # Hide if not pinned
            # if note.is_pinned else "",
            # size_hint_x=0.1,
            # color=(1, 0.8, 0, 1),  # Gold color for pin
            # font_size='16sp'
        )
        
        # Create a layout for the title row with pin indicator
        title_row = MDBoxLayout(size_hint_y=None, height=30, spacing=5)
        title_row.add_widget(self.pin_indicator)  # Add pin indicator to title row
                
        # Create content label
        self.content_label = Label(
        text=content_preview, 
        size_hint_y=None, 
        height=70,
        color=(0.6, 0.6, 0.6, 1),
        font_size='12sp',
        halign='left',
        valign='top',
        text_size=(self.width, None)
    )

        self.content_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))

        # Prepare timestamp text
        timestamp_text = "No date available"
        if hasattr(note, 'updated_at') and note.updated_at:
            try:
                if isinstance(note.updated_at, str):
                    # Try to parse the string directly
                    from datetime import datetime
                    try:
                        parsed_time = datetime.strptime(note.updated_at, '%Y-%m-%d %H:%M:%S')
                        timestamp_text = parsed_time.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        timestamp_text = note.updated_at  # Use the string as is
                elif hasattr(note.updated_at, 'strftime'):
                    # If it's already a datetime object
                    timestamp_text = note.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # Last resort, convert to string
                    timestamp_text = str(note.updated_at)
            except Exception as e:
                print(f"Error formatting timestamp: {e}")
                timestamp_text = str(note.updated_at)
        
        self.timestamp_label = Label(
            text=timestamp_text,
            size_hint_x=0.3,  # Take 30% of the width
            color=(0.6, 0.6, 0.6, 1),  # Slightly dimmer than title
            font_size='12sp',
            halign='right',
            valign='middle'
        )
        self.timestamp_label.bind(size=self.timestamp_label.setter('text_size'))
                
        # Add widgets to title row
        title_row.add_widget(self.title_label)
        title_row.add_widget(self.timestamp_label)
        
        # Add the title row and content label to main layout
        self.add_widget(title_row)  # Add only once
        self.add_widget(self.content_label)

        # Tags row
        self.tags_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        if note.tags:
            tags_label = Label(
                text=f"Tags: {note.tags}",
                size_hint_x=1,
                color=(0.5, 0.7, 0.9, 1),  # Blue-ish color for tags
                font_size='12sp',
                halign='left',
                valign='middle'
            )
            tags_label.bind(size=tags_label.setter('text_size'))
            self.tags_row.add_widget(tags_label)
        
        # Add tags row to main layout
        self.add_widget(self.tags_row)
        
        # Add lock icon if note is in a locked folder
        if note.is_locked:
            lock_row = MDBoxLayout(size_hint_y=None, height=20, spacing=5)
            lock_icon = Label(
                text="🔒",
                size_hint_x=0.1,
                color=(1, 1, 1, 1)
            )
            lock_row.add_widget(lock_icon)
            self.add_widget(lock_row)
        self.height = self.title_label.height + self.content_label.height + self.tags_row.height + 20        
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.border.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            track_event('note_selected', note_id=self.note.id, note_title=self.note.title)
            self.show_options_popup()
            return True
        return super(NoteView, self).on_touch_down(touch)

    def show_options_popup(self):
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_content_rect, size=self._update_content_rect)
        
        # Buttons for actions
         
        # Create two rows of buttons
        buttons_row1 = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        buttons_row2 = MDBoxLayout(size_hint_y=None, height=50, spacing=10, padding=[0, 10, 0, 0])


        edit_button = MDFillRoundFlatButton(
            text="Edit",
            md_bg_color=(0.2, 0.6, 0.8, 1),  # Blue MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        delete_button = MDFillRoundFlatButton(
            text="Delete",
            md_bg_color=(0.8, 0.2, 0.2, 1),  # Red MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        # Pin/Unpin MDFlatButton
        pin_button = MDFillRoundFlatButton(
            text="Unmark" if self.note.is_pinned else "Mark",
            md_bg_color=(0.8, 0.7, 0.2, 1),  # Gold MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        # Share MDFlatButton
        share_button = MDFillRoundFlatButton(
            text="Share",
            md_bg_color=(0.2, 0.8, 0.2, 1),  # Green MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        # Google Drive MDFlatButton
        drive_button = MDFillRoundFlatButton(
            text="Upload to Drive",
            md_bg_color=(0.4, 0.4, 0.8, 1),  # Blue MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        # Tags MDFlatButton
        tags_button = MDFillRoundFlatButton(
            text="Manage Tags",
            md_bg_color=(0.5, 0.7, 0.9, 1),  # Light blue MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        # Move to folder MDFlatButton
        folder_button = MDFillRoundFlatButton(
            text="Move to Folder",
            md_bg_color=(0.6, 0.4, 0.8, 1),  # Purple MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        cancel_button = MDFillRoundFlatButton(
            text="Cancel",
            md_bg_color=(0.3, 0.3, 0.3, 1),  # Gray MDFlatButton
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )

        edit_button.bind(on_press=self.edit_note)
        delete_button.bind(on_press=self.show_delete_dialog)
        pin_button.bind(on_press=self.toggle_pin)
        share_button.bind(on_press=self.show_share_options)
        drive_button.bind(on_press=self.upload_to_drive)
        tags_button.bind(on_press=self.show_tags_dialog)
        folder_button.bind(on_press=self.folder_manager.show_folder_dialog)
        cancel_button.bind(on_press=self.dismiss_popup)

        # Add buttons to first row
        buttons_row1.add_widget(edit_button)
        buttons_row1.add_widget(delete_button)
        buttons_row1.add_widget(pin_button)
        buttons_row1.add_widget(share_button)
        
        # Add buttons to second row
        buttons_row2.add_widget(drive_button)
        buttons_row2.add_widget(tags_button)
        buttons_row2.add_widget(folder_button)
        buttons_row2.add_widget(cancel_button)
        
        content.add_widget(Label(text="Note Options", color=(1, 1, 1, 1)))
        # content.add_widget(buttons)
        content.add_widget(buttons_row1)
        content.add_widget(buttons_row2)

        self.popup = Popup(
            title=self.note.title, 
            content=content, 
            size_hint=(0.8, 0.3),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            self.popup_rect = Rectangle(pos=self.popup.pos, size=self.popup.size)
        self.popup.bind(pos=self._update_popup_rect, size=self._update_popup_rect)
        
        self.popup.open()
    
    def update_ui(self):
        """Method to update UI after folder operations"""
        if self.refresh_callback:
            self.refresh_callback()
        
    def toggle_pin(self, instance):
        """Toggle the pinned status of the note."""
        
        pin_status = "unpinned" if self.note.is_pinned else "pinned"
        track_event('note_pin_toggled', note_id=self.note.id, new_status=pin_status)

        if self.note.is_pinned:
            self.db.unpin_note(self.note.id)
            self.note.is_pinned = 0
            self.pin_indicator.opacity = 0  # Hide the pin icon
        else:
            self.db.pin_note(self.note.id)
            self.note.is_pinned = 1
            self.pin_indicator.opacity = 1  # Show the pin icon

        self.popup.dismiss()
        
        # Call the refresh callback to update the main screen
        if self.refresh_callback:
            self.refresh_callback()
    
    def show_share_options(self, instance):
        """Show sharing options."""
        self.popup.dismiss()
        
        content = MDBoxLayout(
            orientation="vertical",
            padding=[20, 10],  # Padding around the whole popup
            spacing=10,
            # size_hint=(1, None) # Adjust height based on content
        )
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_content_rect, size=self._update_content_rect)
        
        # Sharing options
        buttons_grid = MDGridLayout(cols=2, size_hint_y=0.1, height=100, padding=[0, 10, 0, 0], spacing=10)
        # buttons_grid.bind(minimum_height=buttons_grid.setter("height"))
        
        #Various sharing options
        copy_button = MDFillRoundFlatButton(
            text="Copy to Clipboard",
            md_bg_color=(0.3, 0.6, 0.7, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        email_button = MDFillRoundFlatButton(
            text="Email",
            md_bg_color=(0.7, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        twitter_button = MDFillRoundFlatButton(
            text="Twitter/X",
            md_bg_color=(0.0, 0.6, 0.9, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        facebook_button = MDFillRoundFlatButton(
            text="Facebook",
            md_bg_color=(0.2, 0.4, 0.8, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        whatsapp_button = MDFillRoundFlatButton(
            text="WhatsApp",
            md_bg_color=(0.1, 0.8, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        native_share_button = MDFillRoundFlatButton(
            text="Native Share",
            md_bg_color=(0.5, 0.5, 0.5, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        cancel_button = MDFillRoundFlatButton(
            text="Cancel",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        copy_button.bind(on_press=self.copy_to_clipboard)
        email_button.bind(on_press=self.share_via_email)
        twitter_button.bind(on_press=lambda x: self.share_via_social("twitter"))
        facebook_button.bind(on_press=lambda x: self.share_via_social("facebook"))
        whatsapp_button.bind(on_press=lambda x: self.share_via_social("whatsapp"))
        native_share_button.bind(on_press=self.native_share)
        cancel_button.bind(on_press=self.dismiss_popup)
        
        buttons_grid.add_widget(copy_button)
        buttons_grid.add_widget(email_button)
        buttons_grid.add_widget(twitter_button)
        buttons_grid.add_widget(facebook_button)
        buttons_grid.add_widget(whatsapp_button)
        buttons_grid.add_widget(native_share_button)
        buttons_grid.add_widget(cancel_button)
        
        # content.add_widget(Label(text="Share Note", color=(0.9, 0.9, 0.9, 1)))
        content.add_widget(buttons_grid)
        
            # Create popup with fixed size
        self.share_popup = Popup(
            title="Share Options", 
            content=content, 
            size_hint=(None, None),  # Fixed size instead of percentage
            size=(450, 300),  # Match size with share_popup for consistency
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        # Customizing popup background
        with self.share_popup.canvas.before:
            Color(0.01, 0.01, 0.01, 1)  
            self.share_popup_rect = Rectangle(pos=self.share_popup.pos, size=self.share_popup.size)
        self.share_popup.bind(pos=self._update_share_popup_rect, size=self._update_share_popup_rect)
        
        self.share_popup.open()
        
    def _update_share_popup_rect(self, instance, value):
        self.share_popup_rect.pos = instance.pos
        self.share_popup_rect.size = instance.size
    
    def copy_to_clipboard(self, instance):
        """Copy the note content to clipboard."""
        try:
            Clipboard.copy(f"{self.note.title}\n\n{self.note.content}")
            self.show_notification("Copied to Clipboard", "Note content has been copied to clipboard")
        except Exception as e:
            self.show_notification("Error", f"Failed to copy to clipboard: {str(e)}")
        finally:
            if hasattr(self, 'share_popup'):
                self.share_popup.dismiss()
    
    def share_via_email(self, instance):
        """Share note via email."""
        try:
            subject = self.note.title
            body = self.note.content
            mailto_link = f"mailto:?subject={subject}&body={body}"
            webbrowser.open(mailto_link)
        except Exception as e:
            self.show_notification("Error", f"Failed to open email client: {str(e)}")
        finally:
            if hasattr(self, 'share_popup'):
                self.share_popup.dismiss()
                
    def on_window_resize(self, window, width, height):
        """Handle window resize and adjust layout accordingly."""
        self.popup.size_hint = (0.8, 0.5)  # Adjust size hint based on window size
        # You can also adjust other elements in the layout based on new width and height if needed

    
    def share_via_social(self, platform):
        """Share note via a social platform."""
        import urllib.parse
        content = f"{self.note.title}\n\n{self.note.content}"
        
        try:
            if platform == "twitter":
                url = f"https://twitter.com/intent/tweet?text={content}"
                webbrowser.open(url)
            elif platform == "facebook":
                url = f"https://www.facebook.com/sharer/sharer.php?u=https://example.com&quote={content}"
                webbrowser.open(url)
            elif platform == "whatsapp":
                url = f"https://wa.me/?text={content}"
                webbrowser.open(url)
        except Exception as e:
            self.show_notification("Error", f"Failed to share via {platform}: {str(e)}")
        finally:
            if hasattr(self, 'share_popup'):
                self.share_popup.dismiss()
    
    def native_share(self, instance):
        """Use the native sharing mechanism if available."""
        if share_available:
            try:
                share.share(
                    title="Share Note",
                    text=f"{self.note.title}\n\n{self.note.content}",
                    chooser=True
                )
            except Exception as e:
                self.show_notification("Error", f"Native sharing failed: {str(e)}")
        else:
            self.show_notification("Not Available", "Native sharing is not available on this platform")
        
        if hasattr(self, 'share_popup'):
            self.share_popup.dismiss()
    
    def upload_to_drive(self, instance):
        """Upload the note to Google Drive and retrieve the file URL."""
        self.popup.dismiss()
        
        try:
            # Try to import required packages
            from pydrive.auth import GoogleAuth
            from pydrive.drive import GoogleDrive
            from utils.drive_helper import DriveHelper
            import webbrowser
            google_drive_available = True
        except ImportError:
            google_drive_available = False
        
        if not google_drive_available:
            self.show_notification("Not Available", "Google Drive integration is not available. Please install pydrive2.")
            return
                
        print(f"Uploading Note: ID={getattr(self.note, 'id', None)} Title={self.note.title}")
        
        # Check if note exists
        if not hasattr(self.note, 'id') or not self.note.id:
            self.show_notification("Error", "Please save the note first before uploading.")
            return
        
        # Get the current note content
        note_id = self.note.id
        title = self.note.title
        content = self.note.content
        
        # Show uploading notification
        self.show_notification("Uploading", "Authenticating with Google Drive...")
        
        # Initialize DriveHelper if not already done
        if not hasattr(self, 'drive_helper'):
            self.drive_helper = DriveHelper()
        
        # Direct upload approach - skip the nested callbacks for simplicity
        def direct_upload_callback(success, message):
            if success:
                # Extract the URL from the success message
                try:
                    url_start_index = message.find("URL: ") + 5
                    file_url = message[url_start_index:].strip()
                    
                    # Show success message
                    self.show_notification("Success", "Note uploaded successfully")
                    
                    # Debug print
                    print(f"Opening URL: {file_url}")
                    
                    # Open the URL directly
                    webbrowser.open(file_url)
                except Exception as e:
                    print(f"Error processing URL: {str(e)}")
                    self.show_notification("Success", message)
            else:
                print(f"Upload error: {message}")
                self.show_notification("Error", message)
        
        # Simplified approach - authenticate and then upload in a single flow
        def auth_callback(success, message):
            if success:
                # Now that we're authenticated, upload the note
                self.show_notification("Uploading", "Uploading note to Google Drive...")
                self.drive_helper.upload_note(
                    note_id=note_id,
                    title=title,
                    content=content,
                    callback=direct_upload_callback
                )
            else:
                self.show_notification("Error", message)
        
        # First authenticate, then proceed to upload
        self.drive_helper.authenticate(callback=auth_callback)
        
    def show_tags_dialog(self, instance):
        """Show dialog to manage tags."""
        self.popup.dismiss()
        
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_content_rect, size=self._update_content_rect)
        
        # Current tags header
        current_tags_label = Label(
            text="Current tags:",
            size_hint_y=None,
            height=30,
            color=(0.9, 0.9, 0.9, 1)
        )
        
        # Tags container - scrollable for many tags
        tags_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=60, spacing=5)
        scroll_view = ScrollView(size_hint=(1, None), height=60)
        scroll_view.add_widget(tags_container)
        
        # Create tag chips
        tag_list = self.note.get_tag_list() if hasattr(self.note, 'get_tag_list') else []
        if not tag_list and self.note.tags:
            tag_list = [tag.strip() for tag in self.note.tags.split(',')]
            
        if tag_list:
            for tag in tag_list:
                tag_row = MDBoxLayout(size_hint_y=None, height=30, spacing=5)
                
                tag_label = Label(
                    text=tag,
                    size_hint_x=0.8,
                    color=(0.5, 0.7, 0.9, 1)
                )
                
                remove_button = MDFlatButton(
                    text="×",
                    size_hint_x=0.2,
                    md_bg_color=(0.8, 0.2, 0.2, 1),
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                )
                # Important: store the tag as an attribute of the button
                remove_button.tag = tag
                remove_button.bind(on_press=self.remove_tag)
                
                tag_row.add_widget(tag_label)
                tag_row.add_widget(remove_button)
                tags_container.add_widget(tag_row)
        else:
            no_tags_label = Label(
                text="No tags added yet",
                color=(0.7, 0.7, 0.7, 1)
            )
            tags_container.add_widget(no_tags_label)
        
        # New tag input
        self.tag_input = TextInput(
            hint_text="Enter tag (e.g., work, personal, @john)",
            size_hint_y=None,
            height=40,
            background_color=(1, 1, 1, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            multiline=False
        )
        
        # Buttons
        buttons = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        
        add_tag_button = MDFlatButton(
            text="Add Tag",
            md_bg_color=(0.2, 0.6, 0.8, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        remove_tag_button = MDFlatButton(
            text="Remove Tag",
            md_bg_color=(0.8, 0.2, 0.2, 1),
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            size_hint=(None, None),
            size=("30dp", "30dp")
        )

        # Missing: remove_tag_button.tag = tag
        
        done_button = MDFlatButton(
            text="Done",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        add_tag_button.bind(on_press=self.add_tag)
        done_button.bind(on_press=self.dismiss_popup)
        
        buttons.add_widget(add_tag_button)
        buttons.add_widget(done_button)
        
        content.add_widget(current_tags_label)
        content.add_widget(scroll_view)
        content.add_widget(self.tag_input)
        content.add_widget(buttons)
        
        self.tags_popup = Popup(
            title="Manage Tags", 
            content=content, 
            size_hint=(0.8, 0.5),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.tags_popup.canvas.before:
            Color(0.01, 0.01, 0.01, 1)  # Dark gray background for popup
            self.tags_popup_rect = Rectangle(pos=self.tags_popup.pos, size=self.tags_popup.size)
        self.tags_popup.bind(pos=self._update_tags_popup_rect, size=self._update_tags_popup_rect)        
        self.tags_popup.open()
        
    def _update_tags_popup_rect(self, instance, value):
        self.tags_popup_rect.pos = instance.pos
        self.tags_popup_rect.size = instance.size

    # Fix the add_tag method
    def add_tag(self, instance):
        """Add a new tag to the note."""
        new_tag = self.tag_input.text.strip()
        if new_tag:
            # Use the Note class method
            if hasattr(self.note, 'add_tag'):
                self.note.add_tag(new_tag)
                
                try:
                    # Update database
                    self.db.update_note_tags(self.note.id, self.note.tags)
                    
                    # Update UI
                    self.update_tags_display()
                    
                    # Clear input
                    self.tag_input.text = ""
                    
                    # Show success notification
                    self.show_notification("Success", f"Tag '{new_tag}' added")
                    
                    # Refresh tags display
                    if self.refresh_callback:
                        self.refresh_callback()
                        
                except Exception as e:
                    self.show_notification("Error", f"Failed to save tag: {str(e)}")
                    return
                    
                finally:
                    # Properly close dialogs
                    if hasattr(self, 'tags_popup'):
                        self.tags_popup.dismiss()

    def remove_tag(self, instance):
        """Remove a tag from the note."""
        if hasattr(instance, 'tag'):
            tag_to_remove = instance.tag
            
            # Use the Note class method
            if hasattr(self.note, 'remove_tag'):
                self.note.remove_tag(tag_to_remove)
                
                try:
                    # Update database
                    self.db.update_note_tags(self.note.id, self.note.tags)
                    
                    # Update UI
                    self.update_tags_display()
                    
                    # Show success notification  
                    self.show_notification("Success", f"Tag '{tag_to_remove}' removed")
                    
                    # Refresh main screen
                    if self.refresh_callback:
                        self.refresh_callback()
                        
                except Exception as e:
                    self.show_notification("Error", f"Failed to remove tag: {str(e)}")
                    return
                    
                finally:
                    # Properly close dialogs
                    if hasattr(self, 'tags_popup'):
                        self.tags_popup.dismiss()

    def update_tags_display(self):
        """Update the tags displayed in the note view."""
        try:
            # Clear current tags
            self.tags_row.clear_widgets()
            
            # Add new tags display if tags exist
            if self.note.tags:
                tags_label = Label(
                    text=f"Tags: {self.note.tags}",
                    size_hint_x=1,
                    color=(0.5, 0.7, 0.9, 1),
                    font_size='12sp',
                    halign='left',
                    valign='middle'
                )
                tags_label.bind(size=tags_label.setter('text_size'))
                self.tags_row.add_widget(tags_label)
                
        except Exception as e:
            self.show_notification("Error", f"Failed to update tags display: {str(e)}")

    def edit_note(self, instance):
        track_event('note_edit_started', note_id=self.note.id)
        self.popup.dismiss()
        self.show_edit_popup()
    
    def show_edit_popup(self):
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_content_rect, size=self._update_content_rect)
        
        # Title input
        self.edit_title_input = TextInput(
            text=self.note.title,
            hint_text="Title",
            size_hint_y=None, 
            height=40,
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            font_size='16sp',
            multiline=False
        )
        
        # Content input
        self.edit_content_input = TextInput(
            text=self.note.content,
            hint_text="Content",
            background_color=(0, 0, 0, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            font_size='14sp',
            size_hint_y=None,
            height=150
        )
        
        # Buttons
        buttons = MDBoxLayout(size_hint_y=None, height=50, spacing=10)
        
        save_button = MDFlatButton(
            text="Save",
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
        
        save_button.bind(on_press=self.save_edited_note)
        cancel_button.bind(on_press=self.dismiss_popup)
        
        buttons.add_widget(save_button)
        buttons.add_widget(cancel_button)
        
        content.add_widget(self.edit_title_input)
        content.add_widget(self.edit_content_input)
        content.add_widget(buttons)
        
        self.edit_popup = Popup(
            title="Edit Note", 
            content=content, 
            size_hint=(0.9, 0.7),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.edit_popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            self.edit_popup_rect = Rectangle(pos=self.edit_popup.pos, size=self.edit_popup.size)
        self.edit_popup.bind(pos=self._update_edit_popup_rect, size=self._update_edit_popup_rect)
        
        self.edit_popup.open()
        
    def save_edited_note(self, instance):
        # Update the note with new values
        self.note.title = self.edit_title_input.text.strip()
        self.note.content = self.edit_content_input.text.strip()
        
        # Update note in database
        from utils.db_helper import DatabaseHelper
        db = DatabaseHelper()
        db.update_note(self.note.id, self.note.title, self.note.content)
        
        # Reload the note to get the updated timestamp
        updated_note = db.get_note_by_id(self.note.id)
        if updated_note:
            self.note.updated_at = Note.from_db_row(updated_note).updated_at
        
        # Update UI
        content_preview = self.note.content.split('.')[0]
        if len(content_preview) > 100:
            content_preview = content_preview[:100] + "..."
        elif content_preview == self.note.content and not content_preview.endswith('.'):
            content_preview += "..."
            
        self.title_label.text = self.note.title
        self.content_label.text = content_preview
        
        # Update timestamp label
        if self.note.updated_at:
            self.timestamp_label.text = self.note.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.timestamp_label.text = "No date available"
        
        self.edit_popup.dismiss()
        
        # Update note in database
        from utils.db_helper import DatabaseHelper
        db = DatabaseHelper()
        db.update_note(self.note.id, self.note.title, self.note.content)
        
        track_event('note_edited', note_id=self.note.id)
        self.edit_popup.dismiss()
    
    def _update_edit_popup_rect(self, instance, value):
        self.edit_popup_rect.pos = instance.pos
        self.edit_popup_rect.size = instance.size

    def show_delete_dialog(self, instance=None):
        self.popup.dismiss()  # Dismiss the options popup
        
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=[20, 10])
        
        # Adding background to the content
        with content.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark background for popup
            Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=self._update_content_rect, size=self._update_content_rect)
        
        message = Label(
            text="Are you sure you want to delete this note?",
            color=(0.9, 0.9, 0.9, 1)
        )
        buttons = MDBoxLayout(size_hint_y=None, height=50, spacing=10)

        yes_button = MDFlatButton(
            text="Delete",
            md_bg_color=(0.8, 0.2, 0.2, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        no_button = MDFlatButton(
            text="Cancel",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )

        yes_button.bind(on_press=self.delete_note)
        no_button.bind(on_press=self.dismiss_popup)

        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)

        content.add_widget(message)
        content.add_widget(buttons)

        self.delete_popup = Popup(
            title="Delete Note", 
            content=content, 
            size_hint=(0.8, 0.4),
            title_color=(0.9, 0.9, 0.9, 1),
            separator_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Customizing popup background
        with self.delete_popup.canvas.before:
            Color(0.05, 0.05, 0.05, 1)  # Dark gray background for popup
            self.delete_popup_rect = Rectangle(pos=self.delete_popup.pos, size=self.delete_popup.size)
        self.delete_popup.bind(pos=self._update_delete_popup_rect, size=self._update_delete_popup_rect)
        
        self.delete_popup.open()
    
    def _update_content_rect(self, instance, value):
        for child in instance.canvas.before.children:
            if isinstance(child, Rectangle):
                child.pos = instance.pos
                child.size = instance.size
                
    def _update_popup_rect(self, instance, value):
        self.popup_rect.pos = instance.pos
        self.popup_rect.size = instance.size
        
    def _update_delete_popup_rect(self, instance, value):
        self.delete_popup_rect.pos = instance.pos
        self.delete_popup_rect.size = instance.size

    def delete_note(self, instance):
        track_event('note_deleted', note_id=self.note.id)
        self.delete_callback(self.note)
        if hasattr(self, 'delete_popup'):
            self.delete_popup.dismiss()

    def dismiss_popup(self, instance):
        """Dismiss all popups and refresh the main screen."""
        # Close any open popups
        if hasattr(self, 'popup'):
            self.popup.dismiss()
        if hasattr(self, 'tags_popup'):
            self.tags_popup.dismiss()
        if hasattr(self, 'share_popup'):
            self.share_popup.dismiss()
            
        # Refresh the main screen if callback exists
        if self.refresh_callback:
            self.refresh_callback()
            
    def _update_password_popup_rect(self, instance, value):
        self.password_popup_rect.pos = instance.pos
        self.password_popup_rect.size = instance.size

    def verify_folder_password(self, folder_id):
        """Verify the folder password and move the note if correct."""
        password = self.folder_password_input.text.strip()
        if self.db.check_folder_password(folder_id, password):
            # Move the note
            self.db.move_note_to_folder(self.note.id, folder_id)
            self.show_notification("Success", "Note moved to locked folder")
            
            # Update the UI
            if self.refresh_callback:
                self.refresh_callback()
            
            self.password_popup.dismiss()
        else:
            self.show_notification("Error", "Incorrect password")

    def dismiss_popup(self, instance=None):
        """Dismiss any active popup."""
        for popup_name in ['folder_popup', 'password_popup', 'options_dialog', 'confirm_dialog', 'password_dialog']:
            popup = getattr(self, popup_name, None)
            if popup:
                popup.dismiss()
                setattr(self, popup_name, None)  # Ensure it's set to None after dismissal


    def dismiss_folder_popup(self, instance):
        """Dismiss the folder popup."""
        if hasattr(self, 'folder_popup') and self.folder_popup:
            self.folder_popup.dismiss()

    def show_notification(self, title, message):
        """Show a notification popup."""
        content = MDBoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        
        close_button = MDFlatButton(
            text="OK",
            md_bg_color=(0.3, 0.3, 0.3, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        content.add_widget(close_button)
        
        notification = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.3),
            title_color=(0.9, 0.9, 0.9, 1)
        )
        
        close_button.bind(on_press=notification.dismiss)
        notification.open()            
