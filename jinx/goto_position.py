from textual.app import ComposeResult
from textual.widgets import Input, Label
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.validation import Validator, ValidationResult


class GotoValidator(Validator):
    def __init__(self, app):
        self.app = app
        super().__init__()

    def validate(self, value: str) -> ValidationResult:
        try:
            coord = int(value)
        except ValueError:
            return self.failure("Not a valid position")

        if self.is_in_range(coord):
            return self.success()
        else:
            return self.failure("Out of coordinate range for the locus")

    def is_in_range(self, value: int) -> bool:
        return 1 <= value <= self.app.get_current_locus_length()


class GotoPositionScreen(ModalScreen):
    BINDINGS = [
        ("escape", "close_screen()", "Exit goto"),
    ]
    
    def __init__(self):
        self.is_valid = False
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="goto-container"):
            yield Input(
                id="goto-input", 
                placeholder="Go to position",
                valid_empty=False,
                validators=GotoValidator(app=self.app)
            )
            yield Label("[blue]Enter a coordinate", id="goto-message")

    def action_close_screen(self):
        self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        self.is_valid = event.validation_result is None or event.validation_result.is_valid

        if not self.is_valid:  
            self.query_one(Label).update("/".join(event.validation_result.failure_descriptions))
        else:
            self.query_one(Label).update("")

    def on_input_submitted(self):
        if self.is_valid:
            submitted_value = int(self.query_one("#goto-input").value)
            self.dismiss(submitted_value)

        else:
            self.dismiss(None)

    def on_screen_suspend(self):
        self.query_one(Input).clear()
