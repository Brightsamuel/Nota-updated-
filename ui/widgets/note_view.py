import urllib.parse
import webbrowser
from datetime import datetime
from threading import Thread

from kivy.clock import mainthread
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.stacklayout import StackLayout
from kivy.utils import platform
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.chip import MDChip, MDChipText, MDChipTrailingIcon
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemLeadingIcon
from kivymd.uix.menu import MDDropdownMenu
from ui.dialogs import alert, confirm, scrolling_list, show_dialog, snackbar, text_field
from utils.event_tracker import track_event

# Try to import share from plyer
try:
    from plyer import share
    share_available = True
except (ImportError, ModuleNotFoundError):
    share_available = False

Builder.load_string('''
<NoteCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: "16dp", "6dp", "4dp", "14dp"
    spacing: "2dp"
    radius: [dp(16)]
    md_bg_color:
        app.theme_cls.surfaceContainerHighestColor if self.state == "down" \
        else app.theme_cls.surfaceContainerHighColor
    on_release: root.open_note()

    MDBoxLayout:
        adaptive_height: True
        spacing: "6dp"

        MDLabel:
            text: root.title_text
            font_style: "Title"
            role: "medium"
            bold: True
            shorten: True
            shorten_from: "right"
            adaptive_height: True
            pos_hint: {"center_y": .5}

        MDIcon:
            icon: "pin"
            theme_icon_color: "Custom"
            icon_color: app.theme_cls.primaryColor
            opacity: 1 if root.pinned else 0
            pos_hint: {"center_y": .5}

        MDIconButton:
            icon: "dots-vertical"
            pos_hint: {"center_y": .5}
            on_release: root.open_menu(self)

    MDLabel:
        text: root.preview_text
        font_style: "Body"
        role: "medium"
        theme_text_color: "Custom"
        text_color: app.theme_cls.onSurfaceVariantColor
        adaptive_height: True
        padding: 0, 0, "12dp", 0

    MDLabel:
        text: root.tags_text
        font_style: "Label"
        role: "large"
        theme_text_color: "Custom"
        text_color: app.theme_cls.primaryColor
        size_hint_y: None
        height: self.texture_size[1] + dp(6) if self.text else 0
        valign: "bottom"
        opacity: 1 if self.text else 0

    MDLabel:
        text: root.date_text
        font_style: "Label"
        role: "medium"
        theme_text_color: "Custom"
        text_color: app.theme_cls.onSurfaceVariantColor
        size_hint_y: None
        height: self.texture_size[1] + dp(6)
        valign: "bottom"
''')


def _format_date(value):
    if not value:
        return ""
    if value.date() == datetime.now().date():
        return "Today, " + value.strftime('%H:%M')
    return value.strftime('%d %b %Y')


def _preview(content, limit=160):
    text = " ".join(content.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


class NoteCard(ButtonBehavior, MDBoxLayout):
    """A note in the list. A plain rounded box rather than an MDCard: MDCard's
    shadow and ripple make each card slow to create, which adds up in long lists."""

    title_text = StringProperty()
    preview_text = StringProperty()
    tags_text = StringProperty()
    date_text = StringProperty()
    pinned = BooleanProperty(False)

    def __init__(self, note, main_screen, **kwargs):
        self.note = note
        self.main_screen = main_screen
        self.db = main_screen.db
        self.menu = None
        super().__init__(**kwargs)
        self.update_from_note()

    def update_from_note(self):
        note = self.note
        self.title_text = note.title
        self.preview_text = _preview(note.content)
        self.tags_text = "   ".join(f"#{tag}" for tag in note.get_tag_list())
        self.date_text = _format_date(note.updated_at)
        self.pinned = bool(note.is_pinned)

    def open_note(self):
        track_event('note_selected', note_id=self.note.id, note_title=self.note.title)
        self.main_screen.open_note(self.note)

    def open_menu(self, caller):
        actions = [
            ("Unpin" if self.note.is_pinned else "Pin",
             "pin-off-outline" if self.note.is_pinned else "pin-outline", self.toggle_pin),
            ("Share", "share-variant-outline", self.show_share_options),
            ("Tags", "tag-outline", self.show_tags_dialog),
            ("Move to folder", "folder-move-outline", self.move_to_folder),
            ("Upload to Drive", "google-drive", self.upload_to_drive),
            ("Delete", "delete-outline", self.show_delete_dialog),
        ]

        def run(action):
            self.menu.dismiss()
            action()

        self.menu = MDDropdownMenu(
            caller=caller,
            items=[{"text": text, "leading_icon": icon,
                    "on_release": lambda a=action: run(a)}
                   for text, icon, action in actions],
        )
        self.menu.open()

    # ---------------------------------------------------------------- pin
    def toggle_pin(self):
        """Toggle the pinned status of the note."""
        pin_status = "unpinned" if self.note.is_pinned else "pinned"
        track_event('note_pin_toggled', note_id=self.note.id, new_status=pin_status)

        if self.note.is_pinned:
            self.db.unpin_note(self.note.id)
        else:
            self.db.pin_note(self.note.id)
        self.main_screen.refresh()
        snackbar("Note unpinned" if pin_status == "unpinned" else "Note pinned to the top")

    # -------------------------------------------------------------- delete
    def show_delete_dialog(self):
        def delete():
            track_event('note_deleted', note_id=self.note.id)
            self.main_screen.delete_note(self.note)

        confirm("Delete note?", f"\"{self.note.title}\" will be permanently deleted.",
                "Delete", delete, danger=True, icon="delete-outline")

    # -------------------------------------------------------------- folder
    def move_to_folder(self):
        self.main_screen.folder_manager.choose_folder_for_note(self.note)

    # --------------------------------------------------------------- share
    def _share_text(self):
        return f"{self.note.title}\n\n{self.note.content}"

    def show_share_options(self):
        """Show sharing options."""
        options = [
            ("content-copy", "Copy to clipboard", self.copy_to_clipboard),
            ("email-outline", "Email", self.share_via_email),
            ("alpha-x-box-outline", "X (Twitter)", lambda: self.share_via_social("twitter")),
            ("facebook", "Facebook", lambda: self.share_via_social("facebook")),
            ("whatsapp", "WhatsApp", lambda: self.share_via_social("whatsapp")),
        ]
        if share_available and platform == 'android':
            options.append(("share-variant-outline", "More apps...", self.native_share))

        dialog = None

        def pick(action):
            dialog.dismiss()
            action()

        rows = []
        for icon, text, action in options:
            item = MDListItem(
                MDListItemLeadingIcon(icon=icon),
                MDListItemHeadlineText(text=text),
                theme_bg_color="Custom",
                md_bg_color=(0, 0, 0, 0),
            )
            item.bind(on_release=lambda _i, a=action: pick(a))
            rows.append(item)

        dialog = show_dialog("Share note", content=scrolling_list(rows),
                             buttons=[("Cancel", None)])

    def copy_to_clipboard(self):
        """Copy the note content to clipboard."""
        Clipboard.copy(self._share_text())
        snackbar("Note copied to clipboard")

    def share_via_email(self):
        """Share note via email."""
        query = urllib.parse.urlencode(
            {"subject": self.note.title, "body": self.note.content},
            quote_via=urllib.parse.quote,
        )
        webbrowser.open(f"mailto:?{query}")

    def share_via_social(self, platform_name):
        """Share note via a social platform."""
        text = urllib.parse.quote(self._share_text())
        urls = {
            "twitter": f"https://twitter.com/intent/tweet?text={text}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u=https://example.com&quote={text}",
            "whatsapp": f"https://wa.me/?text={text}",
        }
        webbrowser.open(urls[platform_name])

    def native_share(self):
        """Use the native sharing mechanism if available."""
        try:
            share.share(title="Share Note", text=self._share_text(), chooser=True)
        except Exception as e:
            alert("Sharing failed", str(e))

    # ---------------------------------------------------------------- tags
    def show_tags_dialog(self):
        """Show dialog to add and remove tags."""
        chips = StackLayout(size_hint_y=None, spacing=dp(8))
        chips.bind(minimum_height=chips.setter('height'))
        empty_label = MDLabel(text="No tags yet", adaptive_height=True,
                              theme_text_color="Custom",
                              text_color=self.theme_cls.onSurfaceVariantColor)

        def save_tags():
            self.db.update_note_tags(self.note.id, self.note.tags)
            self.update_from_note()

        def remove(tag):
            self.note.remove_tag(tag)
            save_tags()
            rebuild()

        def rebuild():
            chips.clear_widgets()
            for tag in self.note.get_tag_list():
                chip = MDChip(
                    MDChipText(text=tag),
                    MDChipTrailingIcon(icon="close"),
                    type="input",
                )
                chip.bind(on_release=lambda _c, t=tag: remove(t))
                chips.add_widget(chip)
            if not chips.children:
                chips.add_widget(empty_label)

        field = text_field("Add a tag (e.g. work, @john)", icon="tag-plus-outline")

        def add(*_):
            new_tag = field.text.strip().lstrip('#')
            if new_tag:
                self.note.add_tag(new_tag)
                save_tags()
                rebuild()
            field.text = ""
            field.focus = True

        field.bind(on_text_validate=add)
        rebuild()

        content = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(16))
        content.add_widget(chips)
        content.add_widget(field)

        def done():
            self.main_screen.refresh()

        show_dialog("Tags", "Tap a tag to remove it.", content=content,
                    buttons=[("Add", lambda: add() or False), ("Done", done, "filled")])

    # --------------------------------------------------------------- drive
    def upload_to_drive(self):
        """Upload the note to Google Drive and open the uploaded file."""
        try:
            from utils.drive_helper import DriveHelper
        except ImportError:
            alert("Not available", "Google Drive upload needs the pydrive2 package.")
            return

        if not getattr(self.note, 'id', None):
            alert("Save first", "Please save the note before uploading it.")
            return

        note_id, title, content = self.note.id, self.note.title, self.note.content
        if not hasattr(self, 'drive_helper'):
            self.drive_helper = DriveHelper()

        @mainthread
        def upload_done(success, message):
            if success:
                snackbar("Note uploaded to Google Drive")
                url_start = message.find("URL: ")
                if url_start != -1:
                    webbrowser.open(message[url_start + 5:].strip())
            else:
                alert("Upload failed", message)

        @mainthread
        def auth_done(success, message):
            if not success:
                alert("Google Drive", message)
                return
            snackbar("Uploading note...")
            Thread(target=self.drive_helper.upload_note, daemon=True,
                   kwargs=dict(note_id=note_id, title=title, content=content,
                               callback=upload_done)).start()

        snackbar("Connecting to Google Drive...")
        self.drive_helper.authenticate(callback=auth_done)
