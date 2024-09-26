
from textual.widgets import Static, TabbedContent, Markdown, DataTable, Input, ListView, ListItem, Label, TabPane, ContentSwitcher, Placeholder
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message

class FeatureQualifiers(Horizontal):
    DISPLAYED_COLUMNS = ["feature_type", "start", "end", "strand", "label"]

    current_features = None

    def compose(self):
        yield Horizontal(
            DataTable(cursor_type="row", classes="visible-features-data-table"),
            VerticalScroll(Markdown("I am a Markdown", classes="visible-features-details"))
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
        details_markdown = self.query_one(".visible-features-details")
        
        details_markdown.update(
            self.current_features.formatted_qualifiers.iloc[event.cursor_row]
        )
        

class LocusSwitcher(Static):
    # TODO

    DISPLAYED_COLUMNS = ["locus_id", "name", "sequence_length"]

    current_features = None

    def compose(self):
        yield Horizontal(
            DataTable(cursor_type="row", classes="visible-features-data-table"),
            VerticalScroll(Markdown("I am a Markdown", classes="visible-features-details"))
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
        details_markdown = self.query_one(".visible-features-details")
        
        details_markdown.update(
            "_" + self.current_features.description.iloc[event.cursor_row] + "_\n\n" +
            self.current_features.formatted_annotations.iloc[event.cursor_row]
        )
        


class TextSearch(Static):
    BINDINGS = [
        ("escape", "exit_search()", "Exit search"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self):
        yield Input(id="text-search-input")
        with ContentSwitcher(id="text-search-switcher", initial="no-query"):
            yield Static("No query",id="no-query", classes="text-search-placeholder")
            yield Static("Nothing found",id="nothing-found", classes="text-search-placeholder")
            yield FeatureQualifiers(id="text-search-results")

    def on_input_submitted(self, event):
        query = event.value

        if query == "":
            self.query_one(ContentSwitcher).current = "no-query"
            return

        results_display = self.query_one(FeatureQualifiers)
        current_locus_data = self.app.get_current_locus_data()

        matches = current_locus_data[
            current_locus_data.qualifiers.str.contains(query)
        ]

        if matches.empty:
            self.query_one(ContentSwitcher).current = "nothing-found"
            return
        
        self.query_one(ContentSwitcher).current = "text-search-results"
        results_display.display_features(matches)

        self.app.set_focus(
            self.query_one(DataTable)
        )

    class SearchResultSelected(Message):
        def __init__(self, feature):
            self.feature = feature
            super().__init__()
    
    class ExitSearch(Message):
        def __init__(self):
            super().__init__()


    def on_data_table_row_selected(self, event):
        results_display = self.query_one(FeatureQualifiers)
        selected_feature = results_display.current_features.iloc[event.cursor_row]
        self.post_message(
            self.SearchResultSelected(selected_feature)
        )

    def action_exit_search(self):
        self.post_message(self.ExitSearch())

    

        
class DataViewer(Static):
    def __init__(self):
        super().__init__()
        self.add_class("focus-highlight-border")
        self.border_title = "Visible features"

    def compose(self):
        with ContentSwitcher(id="data-viewer-tabs", initial="visible-features"):
            yield FeatureQualifiers(id="visible-features")
            yield TextSearch(id="text-search")
            yield LocusSwitcher(id="locus-switcher")

    def on_text_search_exit_search(self):
        self.query_one("#text-search-input").clear()
        self.query_one("#data-viewer-tabs").current = "visible-features"
        self.border_title = "Visible features"
        self.app.set_focus(
            self.query_one("#visible-features  .visible-features-data-table")
        )

    def show_locus_switcher(self):
        self.query_one("#data-viewer-tabs").current = "locus-switcher"
        self.border_title = "Current file loci"

        self.query_one(LocusSwitcher).display_features(self.app.locus_data.reset_index())

        self.app.set_focus(
            self.query_one("#locus-switcher  .visible-features-data-table")
        )


        
