from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemLeadingIcon,
    MDListItemSupportingText,
)
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDSwitch
from ui.dialogs import (
    confirm,
    prompt,
    scrolling_list,
    show_dialog,
    show_field_error,
    snackbar,
    text_field,
)


def _count_text(count):
    return "1 note" if count == 1 else f"{count} notes"


def _list_item(icon, title, subtitle, on_release):
    item = MDListItem(
        MDListItemLeadingIcon(icon=icon),
        MDListItemHeadlineText(text=title),
        MDListItemSupportingText(text=subtitle),
        theme_bg_color="Custom",
        md_bg_color=(0, 0, 0, 0),
    )
    item.bind(on_release=lambda *_: on_release())
    return item


class FolderManager:
    """Dialogs for browsing, creating, unlocking and managing folders."""

    def __init__(self, main_screen):
        self.main_screen = main_screen
        self.db = main_screen.db
        self.dialog = None
        self.menu = None

    def _close_dialog(self):
        if self.dialog and self.dialog._is_open:
            self.dialog.dismiss()
        self.dialog = None

    # ------------------------------------------------------------ browsing
    def show_folders(self):
        """List all folders; tapping one shows its notes."""
        folders = self.db.get_all_folders()
        all_count = len(self.db.get_visible_notes())

        rows = [_list_item("note-multiple-outline", "All notes", _count_text(all_count),
                           lambda: self._open(None))]
        for folder in folders:
            rows.append(self._folder_row(folder))

        self.dialog = show_dialog(
            "Folders",
            content=scrolling_list(rows),
            buttons=[("New folder", lambda: self.show_create_folder()),
                     ("Close", None)],
        )

    def _folder_row(self, folder):
        icon = "folder-lock-outline" if folder['is_locked'] else "folder-outline"
        subtitle = "Locked" if folder['is_locked'] else _count_text(folder['note_count'])
        item = _list_item(icon, folder['name'], subtitle, lambda: self._open(folder))

        row = MDBoxLayout(adaptive_height=True)
        row.add_widget(item)
        options = MDIconButton(icon="dots-vertical", pos_hint={"center_y": 0.5})
        options.bind(on_release=lambda btn: self._show_folder_options(folder, btn))
        row.add_widget(options)
        return row

    def _open(self, folder):
        self._close_dialog()
        if folder is None:
            self.main_screen.load_folder(None)
        elif folder['is_locked']:
            self._unlock(folder, lambda: self.main_screen.load_folder(folder['id'], folder['name']))
        else:
            self.main_screen.load_folder(folder['id'], folder['name'])

    def _unlock(self, folder, on_success):
        def check(password):
            if not self.db.check_folder_password(folder['id'], password):
                return "Incorrect password"
            on_success()

        prompt(f"{folder['name']} is locked", "Password", check, password=True,
               confirm_label="Unlock", icon="lock-outline",
               supporting="Enter the folder password to continue.")

    # ------------------------------------------------------------- options
    def _show_folder_options(self, folder, caller):
        def pick(action):
            self.menu.dismiss()
            self._close_dialog()
            if folder['is_locked']:
                self._unlock(folder, lambda: action(folder))
            else:
                action(folder)

        self.menu = MDDropdownMenu(
            caller=caller,
            items=[
                {"text": "Rename", "leading_icon": "pencil-outline",
                 "on_release": lambda: pick(self._rename_folder)},
                {"text": "Delete", "leading_icon": "delete-outline",
                 "on_release": lambda: pick(self._delete_folder)},
            ],
        )
        self.menu.open()

    def _rename_folder(self, folder):
        def rename(name):
            if not name:
                return "Enter a folder name"
            self.db.rename_folder(folder['id'], name)
            if self.main_screen.current_folder_id == folder['id']:
                self.main_screen.screen_title = name
            snackbar(f"Folder renamed to {name}")

        prompt("Rename folder", "Folder name", rename, text=folder['name'],
               confirm_label="Rename")

    def _delete_folder(self, folder):
        def delete():
            self.db.delete_folder(folder['id'])
            if self.main_screen.current_folder_id == folder['id']:
                self.main_screen.load_folder(None)
            else:
                self.main_screen.refresh()
            snackbar(f"Folder {folder['name']} deleted")

        confirm("Delete folder?",
                f"\"{folder['name']}\" will be deleted. Its notes will be kept "
                "and moved out of the folder.",
                "Delete", delete, danger=True, icon="delete-outline")

    # ------------------------------------------------------------ creating
    def show_create_folder(self, on_created=None):
        """Ask for a new folder's name and optional password.

        on_created(folder_id) runs after the folder is created.
        """
        name_field = text_field("Folder name", icon="folder-outline")
        password_field = text_field("Password", password=True, icon="lock-outline")

        lock_row = MDBoxLayout(adaptive_height=True, padding=(dp(4), dp(8), 0, dp(4)))
        lock_row.add_widget(MDLabel(text="Lock with a password", adaptive_height=True,
                                    pos_hint={"center_y": 0.5}))
        lock_switch = MDSwitch(pos_hint={"center_y": 0.5})
        lock_row.add_widget(lock_switch)

        content = MDBoxLayout(orientation="vertical", adaptive_height=True,
                              spacing=dp(8))
        content.add_widget(name_field)
        content.add_widget(lock_row)

        def on_lock(switch, active):
            if active:
                content.add_widget(password_field)
            elif password_field.parent:
                content.remove_widget(password_field)

        lock_switch.bind(active=on_lock)

        def create():
            name = name_field.text.strip()
            if not name:
                show_field_error(name_field, "Enter a folder name")
                return False
            password = password_field.text.strip() if lock_switch.active else None
            if lock_switch.active and not password:
                show_field_error(password_field, "Enter a password")
                return False
            folder_id = self.db.create_folder(name, 1 if lock_switch.active else 0, password)
            snackbar(f"Folder {name} created")
            if on_created:
                on_created(folder_id)

        show_dialog("New folder", content=content,
                    buttons=[("Cancel", None), ("Create", create, "filled")])

    # -------------------------------------------------------------- moving
    def choose_folder_for_note(self, note):
        """Let the user pick the folder a note should live in."""
        def move(folder):
            self._close_dialog()
            if folder is not None and folder['is_locked']:
                self._unlock(folder, lambda: self._move(note, folder))
            else:
                self._move(note, folder)

        rows = [_list_item("note-multiple-outline", "No folder",
                           "Keep the note outside folders", lambda: move(None))]
        for folder in self.db.get_all_folders():
            if folder['id'] == note.folder_id:
                continue
            icon = "folder-lock-outline" if folder['is_locked'] else "folder-outline"
            subtitle = "Locked" if folder['is_locked'] else _count_text(folder['note_count'])
            rows.append(_list_item(icon, folder['name'], subtitle,
                                   lambda f=folder: move(f)))

        def new_folder():
            self.show_create_folder(
                on_created=lambda folder_id: self._move(note, self.db.get_folder(folder_id))
            )

        self.dialog = show_dialog(
            "Move to folder",
            content=scrolling_list(rows),
            buttons=[("New folder", new_folder), ("Cancel", None)],
        )

    def _move(self, note, folder):
        self.db.move_note_to_folder(note.id, folder['id'] if folder else None)
        self.main_screen.refresh()
        snackbar(f"Moved to {folder['name']}" if folder else "Removed from folder")
