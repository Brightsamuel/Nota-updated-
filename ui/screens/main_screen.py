from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from models.note import Note
from ui.dialogs import confirm, snackbar
from ui.widgets.folder_manager import FolderManager
from ui.widgets.note_view import NoteCard
from ui.widgets.tag_manager import TagManager
from utils.db_helper import DatabaseHelper

Builder.load_string('''
<MainScreen>:
    md_bg_color: app.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            type: "small"
            theme_bg_color: "Custom"
            md_bg_color: app.theme_cls.backgroundColor

            MDTopAppBarLeadingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "arrow-left" if root.current_folder_id is not None else "folder-multiple-outline"
                    on_release: root.on_leading_button()

            MDTopAppBarTitle:
                text: root.screen_title

            MDTopAppBarTrailingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "folder-multiple-outline"
                    opacity: 1 if root.current_folder_id is not None else 0
                    disabled: root.current_folder_id is None
                    on_release: root.show_folders()
                MDActionTopAppBarButton:
                    icon: "weather-sunny" if app.theme_cls.theme_style == "Dark" else "weather-night"
                    on_release: app.toggle_theme()
                MDActionTopAppBarButton:
                    icon: "logout"
                    on_release: root.logout()

        MDBoxLayout:
            adaptive_height: True
            padding: "16dp", "4dp", "16dp", "8dp"

            MDTextField:
                id: search_input
                mode: "outlined"
                multiline: False
                radius: [dp(28)]
                on_text: root.on_search_text_changed(self, self.text)
                MDTextFieldLeadingIcon:
                    icon: "magnify"
                MDTextFieldHintText:
                    text: "Search notes"

        MDFloatLayout:
            ScrollView:
                do_scroll_x: False
                pos_hint: {"x": 0, "y": 0}

                MDBoxLayout:
                    id: notes_container
                    orientation: "vertical"
                    adaptive_height: True
                    padding: "16dp", "8dp", "16dp", "96dp"
                    spacing: "12dp"

            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "8dp"
                pos_hint: {"center_x": .5, "center_y": .6}
                opacity: 1 if root.is_empty else 0
                padding: "32dp", 0

                MDIcon:
                    icon: root.empty_icon
                    theme_font_size: "Custom"
                    font_size: "64sp"
                    theme_icon_color: "Custom"
                    icon_color: app.theme_cls.outlineColor
                    halign: "center"
                    size_hint: 1, None
                    height: "80dp"

                MDLabel:
                    text: root.empty_text
                    halign: "center"
                    font_style: "Title"
                    role: "medium"
                    adaptive_height: True

                MDLabel:
                    text: root.empty_hint
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.onSurfaceVariantColor
                    adaptive_height: True

            MDExtendedFabButton:
                fab_state: "expand"
                pos: root.width - self.width - dp(20), dp(20)
                on_release: root.go_to_notes_create()

                MDExtendedFabButtonIcon:
                    icon: "plus"

                MDExtendedFabButtonText:
                    text: "New note"
''')


class MainScreen(MDScreen):
    screen_title = StringProperty("All notes")
    current_folder_id = ObjectProperty(None, allownone=True)
    is_empty = BooleanProperty(False)
    empty_icon = StringProperty("note-text-outline")
    empty_text = StringProperty("")
    empty_hint = StringProperty("")

    def __init__(self, **kwargs):
        self.db = DatabaseHelper()
        self.tag_manager = TagManager()
        self.folder_manager = FolderManager(self)
        self.note_list = []
        super().__init__(**kwargs)
        self.load_notes_from_db()

    def on_enter(self):
        self.tag_manager.track_event('screen_view', screen_name='main')

    # ----------------------------------------------------------- navigation
    def on_leading_button(self):
        if self.current_folder_id is not None:
            self.load_folder(None)
        else:
            self.show_folders()

    def show_folders(self):
        self.folder_manager.show_folders()

    def go_to_notes_create(self, *args):
        self.manager.get_screen('notes').open_note(None)

    def open_note(self, note):
        self.manager.get_screen('notes').open_note(note)

    def logout(self):
        def do_logout():
            app = MDApp.get_running_app()
            app.config.set('auth', 'user_id', '')
            app.config.set('auth', 'username', '')
            app.config.write()
            self.manager.transition.direction = 'right'
            self.manager.current = 'login'

        confirm("Log out?", "You'll need to log in again to see your notes.",
                "Log out", do_logout, icon="logout")

    # ------------------------------------------------------------- loading
    def load_folder(self, folder_id, folder_name=None):
        """Show the notes of one folder, or all notes when folder_id is None."""
        self.ids.search_input.text = ""
        self.load_notes_from_db(folder_id)

    def load_notes_from_db(self, folder_id=None):
        self.current_folder_id = folder_id
        if folder_id is None:
            self.screen_title = "All notes"
        else:
            folder = self.db.get_folder(folder_id)
            self.screen_title = folder['name'] if folder else "Folder"
        self.refresh()

    def refresh(self, *args):
        """Reload the notes for the current folder and search text."""
        query = self.ids.search_input.text.strip()
        if query:
            rows = self.db.search_notes(query, self.current_folder_id)
        elif self.current_folder_id is None:
            rows = self.db.get_visible_notes()
        else:
            rows = self.db.get_notes_by_folder(self.current_folder_id)

        self.note_list = [Note.from_db_row(row) for row in rows]
        self.display_notes(query)

    def display_notes(self, query=""):
        container = self.ids.notes_container
        container.clear_widgets()
        for note in self.note_list:
            container.add_widget(NoteCard(note=note, main_screen=self))

        self.is_empty = not self.note_list
        if query:
            self.empty_icon = "text-search"
            self.empty_text = "No matching notes"
            self.empty_hint = f'Nothing found for "{query}"'
        elif self.current_folder_id is not None:
            self.empty_icon = "folder-open-outline"
            self.empty_text = "This folder is empty"
            self.empty_hint = "Tap New note to add one here"
        else:
            self.empty_icon = "note-text-outline"
            self.empty_text = "No notes yet"
            self.empty_hint = "Tap New note to write your first one"

    def on_search_text_changed(self, instance, value):
        self.refresh()

    # ------------------------------------------------------------ changes
    def add_note(self, note):
        note_id = self.db.add_note(note.title, note.content)
        if self.current_folder_id is not None:
            self.db.move_note_to_folder(note_id, self.current_folder_id)
        self.refresh()
        snackbar("Note saved")

    def update_note(self, note, title, content):
        self.db.update_note(note.id, title, content)
        self.refresh()
        snackbar("Note updated")

    def delete_note(self, note):
        if note.id is not None:
            self.db.delete_note(note.id)
        self.refresh()
        snackbar("Note deleted")
