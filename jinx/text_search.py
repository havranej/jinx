from data_viewer import FeatureQualifiers
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Input, Label, ContentSwitcher, DataTable


class TextSearchScreen(ModalScreen):
    BINDINGS = [
        ("escape", "exit_search()", "Exit search"),
    ]

    def __init__(self):
        super().__init__()


    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Input(id="text-search-input", placeholder="Search qualifiers")
            with ContentSwitcher(id="search-switcher", initial="search-message"):
                yield Label("[blue]Empty query", id="search-message")
                yield FeatureQualifiers(id="search-results")


    def on_input_submitted(self, event):
        query = event.value

        if query == "":
            self.query_one("#search-message").update("[blue]Empty query")
            self.query_one(ContentSwitcher).current = "search-message"
            return None

        results_display = self.query_one(FeatureQualifiers)
        # TODO: Search across all loci
        all_data = self.app.get_current_locus_data()
        
        matches = all_data[
            all_data.qualifiers.str.contains(query)
        ]

        if matches.empty:
            self.query_one("#search-message").update("[red] Nothing found")
            self.query_one(ContentSwitcher).current = "search-message"
            return

        self.query_one(ContentSwitcher).current = "search-results"
        results_display.display_features(matches)

        self.app.set_focus(
            self.query_one(DataTable)
        )


    def on_data_table_row_selected(self, event):
        results_display = self.query_one(FeatureQualifiers)
        selected_feature = results_display.current_features.iloc[event.cursor_row]
        self.dismiss(selected_feature.name)


    def action_exit_search(self):
        self.dismiss(None)
