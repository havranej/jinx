
from textual.widgets import Static, TabbedContent, Markdown, DataTable, Input, ListView, ListItem, Label, TabPane
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message

class VisibleFeaturesTab(Horizontal):
    DISPLAYED_COLUMNS = ["feature_type", "start", "end", "strand", "label"]

    currently_visible_features = None

    def compose(self):
        yield Horizontal(
            DataTable(cursor_type="row", classes="visible-features-data-table"),
            VerticalScroll(Markdown("I am a Markdown", classes="visible-features-details"))
        ) 

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.DISPLAYED_COLUMNS)


    def display_visible_features(self, visible_features):
        table = self.query_one(DataTable)
        table.clear()
        self.currently_visible_features = visible_features
        table.add_rows(
            list(visible_features[self.DISPLAYED_COLUMNS].itertuples(index=False, name=None))
        )

    def on_data_table_row_highlighted(self, event):
        details_markdown = self.query_one(".visible-features-details")
        
        details_markdown.update(
            self.currently_visible_features.formatted_qualifiers.iloc[event.cursor_row]
        )
        
        
class TextSearch(Static):

    def __init__(self, seq_features):
        self.seq_features = seq_features
        super().__init__()

    def compose(self):
        yield Input(id="text-search-input")
        yield ListView(
            ListItem(Label("Type above to start searching...")),
        )

    def on_input_submitted(self, event):
        query = event.value
        results = self.query_one(ListView)
        matches = self.seq_features[
            self.seq_features.qualifiers.str.contains(query)
        ]
        
        results.clear()

        new_result_list = [
            ListItem(Label(
                f"{row.locus}:{row.start}-{row.end} [b]{row.label}[/b]"
            ), name="feature-"+str(idx)) \
            for idx, row in matches.iterrows()
        ]
        results.extend(new_result_list)
        
        self.app.set_focus(
            results
        )

        

    class SearchResultSelected(Message):
        def __init__(self, feature):
            self.feature = feature
            super().__init__()

    def on_list_view_highlighted(self, event):
        if event.item is not None and event.item.name is not None:
            event.stop()
            row_id = int(event.item.name.split("-")[-1])
            self.post_message(
                self.SearchResultSelected(
                    self.seq_features.loc[row_id]
                )
            )



        
class DataViewer(Static):
    def __init__(self, seq_features):
        super().__init__()
        self.seq_features = seq_features
        self.border_title = "Visible features"

    def compose(self):
        with TabbedContent(id="data-viewer-tabs"):
            with TabPane("Visible features", id="visible-features"):
                yield VisibleFeaturesTab()
            with TabPane("Search", id="text-search"):
                yield TextSearch(self.seq_features)
        
