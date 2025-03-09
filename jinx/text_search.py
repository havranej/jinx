from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Label, ContentSwitcher, DataTable
from qualifier_viewer import QualifierViewer


class TextSearchScreen(ModalScreen):
    BINDINGS = [
        ("escape", "exit_search()", "Exit search"),
    ]

    def __init__(self):
        super().__init__()


    def compose(self) -> ComposeResult:
        with Vertical(id="search-container", classes="large-modal-screen-container"):
            yield Input(id="text-search-input", placeholder="Search qualifiers")
            with ContentSwitcher(id="search-switcher", initial="search-message"):
                yield Label("[blue]Empty query", id="search-message")
                yield TextSearchResults(id="search-results")


    def on_input_submitted(self, event):
        query = event.value

        if query == "":
            self.query_one("#search-message").update("[blue]Empty query")
            self.query_one(ContentSwitcher).current = "search-message"
            return None

        results_display = self.query_one(TextSearchResults)
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
        results_display = self.query_one(TextSearchResults)
        selected_feature = results_display.current_features.iloc[event.cursor_row]
        self.dismiss(selected_feature.name)


    def action_exit_search(self):
        self.dismiss(None)



class TextSearchResults(Horizontal):
    DISPLAYED_COLUMNS = ["feature_type", "start", "end", "strand", "label"]

    current_features = None

    def compose(self):
        yield Horizontal(
            DataTable(cursor_type="row", classes="visible-features-data-table focus-highlight-background"),
            QualifierViewer(classes="focus-highlight-background")
        ) 

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.DISPLAYED_COLUMNS)


    def display_features(self, features):
        table = self.query_one(DataTable)
        table.clear()
        self.current_features = features
        table.add_rows(
            list(features[self.DISPLAYED_COLUMNS].itertuples(index=False, name=None))
        )

    def on_data_table_row_highlighted(self, event):
        details_viewer = self.query_one(QualifierViewer)
        
        details_viewer.view_feature(
            self.current_features.iloc[event.cursor_row]
        )
        