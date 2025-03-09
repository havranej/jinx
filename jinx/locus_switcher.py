from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import RichLog, DataTable, Label


class LocusSwitcherScreen(ModalScreen):
    DISPLAYED_COLUMNS = ["locus_id", "name", "sequence_length"]
    BINDINGS = [
        ("escape", "exit_switcher()", "Exit locus switcher"),
    ]

    def __init__(self, locus_data):
        super().__init__()
        self.locus_data = locus_data.reset_index()

    def compose(self):
        with Vertical(id="locus-switcher-container", classes="large-modal-screen-container"):
            yield Label("Loci in current file:")
            yield Horizontal(
                DataTable(cursor_type="row", classes="features-data-table focus-highlight-background"),
                RichLog(classes="features-details focus-highlight-background", wrap=True, min_width=20, markup=True, auto_scroll=False)
            )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*self.DISPLAYED_COLUMNS)
        table.clear() 
        table.add_rows(
            list(self.locus_data[self.DISPLAYED_COLUMNS].itertuples(index=False, name=None))
        )
    
    def on_data_table_row_highlighted(self, event):
        details_richlog = self.query_one(RichLog)
        
        details_richlog.clear()
        details_richlog.write("[underline]" + self.locus_data.description.iloc[event.cursor_row] + "[/underline]\n")
        details_richlog.write(self.locus_data.formatted_annotations.iloc[event.cursor_row])
    
    def on_data_table_row_selected(self, event):    
        self.dismiss(event.cursor_row)

    def action_exit_switcher(self):
        self.dismiss(None)
