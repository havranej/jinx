from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import MarkdownViewer

import os


class HelpScreen(ModalScreen):
    BINDINGS = [
        ("escape", "close_screen()", "Exit help"),
        ("q", "close_screen()", "Exit help"),
    ]

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "assets/help.md"), 'r') as f:
            self.help_text = f.read()

        super().__init__()
    
    def compose(self):
        yield MarkdownViewer(self.help_text, id="help-viewer")

    def action_close_screen(self):
        self.dismiss(None)