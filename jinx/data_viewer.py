
from textual.widgets import Static, TabbedContent, Markdown, MarkdownViewer, DataTable
from textual.containers import Horizontal, VerticalScroll

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
        
        print("Hi")
        print(event.cursor_row)
        
        
class DataViewer(Static):
    def __init__(self, seq_features):
        super().__init__()
        self.seq_features = seq_features

    def compose(self):
        with TabbedContent("Visible features", "Locus"):
            yield VisibleFeaturesTab()
            yield MarkdownViewer("Oh no")
            yield Markdown("_Jessica_ tab")
        
