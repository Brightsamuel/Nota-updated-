"""Shared dialog and snackbar helpers so every popup in the app looks the same."""
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogIcon,
    MDDialogSupportingText,
)
from kivymd.uix.list import MDList
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldHelperText,
    MDTextFieldHintText,
    MDTextFieldLeadingIcon,
)


def show_dialog(title, text="", content=None, buttons=(("OK", None),), icon=None):
    """Open a dialog and return it.

    buttons is a list of (label, callback) or (label, callback, style) tuples,
    where style is "text" (default), "filled" or "danger". The dialog closes
    after the callback runs, unless the callback returns False.
    """
    parts = []
    if icon:
        parts.append(MDDialogIcon(icon=icon))
    parts.append(MDDialogHeadlineText(text=title))
    if text:
        parts.append(MDDialogSupportingText(text=text))
    if content is not None:
        parts.append(MDDialogContentContainer(content, orientation="vertical"))
    dialog = MDDialog(*parts)

    button_row = MDDialogButtonContainer(Widget(), spacing=dp(8))
    for spec in buttons:
        label, callback = spec[0], spec[1]
        style = spec[2] if len(spec) > 2 else "text"
        button_row.add_widget(_dialog_button(dialog, label, callback, style))
    dialog.add_widget(button_row)
    dialog.open()
    return dialog


def _dialog_button(dialog, label, callback, style):
    theme = MDApp.get_running_app().theme_cls
    if style == "danger":
        button = MDButton(
            MDButtonText(
                text=label,
                theme_text_color="Custom",
                text_color=theme.onErrorColor,
            ),
            style="filled",
            theme_bg_color="Custom",
            md_bg_color=theme.errorColor,
        )
    else:
        button = MDButton(MDButtonText(text=label), style=style)

    def on_release(*_):
        if (callback is None or callback() is not False) and dialog._is_open:
            dialog.dismiss()

    button.bind(on_release=on_release)
    return button


def alert(title, text):
    return show_dialog(title, text)


def confirm(title, text, confirm_label, on_confirm, danger=False, icon=None):
    return show_dialog(
        title,
        text,
        icon=icon,
        buttons=[
            ("Cancel", None),
            (confirm_label, on_confirm, "danger" if danger else "filled"),
        ],
    )


def text_field(hint, text="", password=False, icon=None):
    """An outlined text field with a hint and an (initially hidden) error line."""
    parts = []
    if icon:
        parts.append(MDTextFieldLeadingIcon(icon=icon))
    parts.append(MDTextFieldHintText(text=hint))
    parts.append(MDTextFieldHelperText(text="", mode="on_error"))
    return MDTextField(*parts, mode="outlined", text=text, password=password,
                       multiline=False)


def show_field_error(field, message):
    """Show message in red under a text field that has an MDTextFieldHelperText."""
    helper = field._helper_text_label
    if helper is not None:
        helper.text = message
        # KivyMD copies the helper's texture before re-rendering it, so render
        # the new text first or the old (empty) text is drawn.
        helper.texture_update()
    # Toggle so the field redraws even if it was already showing an error
    field.error = False
    field.error = True


def prompt(title, hint, on_submit, text="", password=False, confirm_label="OK",
           supporting="", icon=None):
    """Ask for one line of text.

    on_submit(value) may return an error message to keep the dialog open and
    show the message under the field.
    """
    field = text_field(hint, text=text, password=password)

    def submit():
        error = on_submit(field.text.strip())
        if error:
            show_field_error(field, error)
            return False
        return True

    dialog = show_dialog(
        title,
        supporting,
        content=field,
        icon=icon,
        buttons=[("Cancel", None), (confirm_label, submit, "filled")],
    )
    field.bind(on_text_validate=lambda *_: submit() and dialog._is_open and dialog.dismiss())
    Clock.schedule_once(lambda dt: setattr(field, "focus", True), 0.2)
    return dialog


def scrolling_list(rows, max_height=dp(320)):
    """Wrap list rows in a ScrollView that grows with its content up to max_height."""
    md_list = MDList(spacing=dp(2))
    for row in rows:
        md_list.add_widget(row)
    scroll = ScrollView(size_hint_y=None, do_scroll_x=False)
    scroll.add_widget(md_list)
    md_list.bind(
        height=lambda inst, h: setattr(scroll, "height", min(h, max_height))
    )
    return scroll


def snackbar(text):
    MDSnackbar(
        MDSnackbarText(text=text),
        y=dp(24),
        pos_hint={"center_x": 0.5},
        size_hint_x=None,
        width=min(dp(420), Window.width - dp(32)),
    ).open()
