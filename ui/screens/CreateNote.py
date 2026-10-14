from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen
from models.note import Note
from ui.dialogs import confirm, snackbar
from utils.event_tracker import track_event

Builder.load_string('''
<EditorInput@TextInput>:
    background_normal: ""
    background_active: ""
    background_color: 0, 0, 0, 0
    foreground_color: app.theme_cls.onSurfaceColor
    hint_text_color: app.theme_cls.onSurfaceVariantColor
    cursor_color: app.theme_cls.primaryColor
    selection_color: app.theme_cls.primaryColor[:3] + [.3]
    padding: 0, "8dp"


<NoteEditorScreen>:
    md_bg_color: app.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            type: "small"
            theme_bg_color: "Custom"
            md_bg_color: app.theme_cls.backgroundColor

            MDTopAppBarLeadingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "arrow-left"
                    on_release: root.go_back()

            MDTopAppBarTitle:
                text: root.heading

            MDTopAppBarTrailingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "check"
                    on_release: root.save_note()

        MDBoxLayout:
            orientation: "vertical"
            padding: "20dp", "4dp", "20dp", "16dp"
            spacing: "4dp"

            EditorInput:
                id: title_input
                hint_text: "Title"
                multiline: False
                font_size: "22sp"
                size_hint_y: None
                height: self.minimum_height
                on_text_validate: content_input.focus = True

            MDLabel:
                text: root.timestamp
                font_style: "Label"
                role: "medium"
                theme_text_color: "Custom"
                text_color: app.theme_cls.onSurfaceVariantColor
                adaptive_height: True

            MDDivider:

            EditorInput:
                id: content_input
                hint_text: "Start writing..."
                font_size: "16sp"
''')


class NoteEditorScreen(MDScreen):
    main_screen = ObjectProperty(None)
    note = ObjectProperty(None, allownone=True)
    heading = StringProperty("New note")
    timestamp = StringProperty("")

    def __init__(self, main_screen=None, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        self._original = ("", "")

    def open_note(self, note=None):
        """Show the editor for an existing note, or an empty one when note is None."""
        self.note = note
        self.ids.title_input.text = note.title if note else ""
        self.ids.content_input.text = note.content if note else ""
        self._original = self._values()

        self.heading = "Edit note" if note else "New note"
        if note and note.updated_at:
            self.timestamp = "Edited " + note.updated_at.strftime('%d %b %Y, %H:%M')
        else:
            self.timestamp = ""

        if note:
            track_event('note_edit_started', note_id=note.id)
        self.manager.transition.direction = 'left'
        self.manager.current = self.name

    def on_enter(self, *args):
        field = self.ids.content_input if self.note else self.ids.title_input
        Clock.schedule_once(lambda dt: setattr(field, 'focus', True), 0.1)

    def _values(self):
        return (self.ids.title_input.text.strip(), self.ids.content_input.text.strip())

    def save_note(self, *args):
        title, content = self._values()

        if not title and not content:
            snackbar("Write something before saving")
            return
        if not title:
            title = content.splitlines()[0][:40]

        if self.note:
            self.main_screen.update_note(self.note, title, content)
            track_event('note_edited', note_id=self.note.id)
        else:
            self.main_screen.add_note(Note(title, content))
        self.close()

    def go_back(self, *args):
        if self._values() != self._original:
            confirm("Discard changes?", "Your changes to this note will be lost.",
                    "Discard", self.close, danger=True)
        else:
            self.close()

    def close(self):
        self.ids.title_input.focus = False
        self.ids.content_input.focus = False
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = "main"
