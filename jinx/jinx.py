from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.screen import Screen

from local_viewport import LocalViewport
from feature_viewer import FeatureViewer
from data_viewer import DataViewer
from goto_position import GotoPositionScreen
from parsers import parse_genbank


import pandas as pd
import sys

DATA = pd.DataFrame([
    {"start": 1, "end": 111, "label": "Width"},
    {"start": 20, "end": 144, "label": "Test 1"},
    {"start": 180, "end": 500, "label": "Test 2"},
    {"start": 192, "end": 501, "label": "Test 2.1"},
    {"start": 40, "end": 800, "label": "Test 3"},
    {"start": 80, "end": 800, "label": "Test 4"},
    {"start": 20, "end": 30, "label": "Test 5"},
    {"start": 50, "end": 60, "label": "Test 6"},
    {"start": 40, "end": 80, "label": "Test 7"},
    {"start": 80, "end": 90, "label": "Test 8"},
])


class ViewerScreen(Screen):

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LocalViewport(
            seq_features=self.app.get_current_locus_data(),
            genome_length=self.app.get_current_locus_length(), 
            nt_per_square=64,
        )
        yield DataViewer()
        yield Footer()

    def on_mount(self):
        self.query_one(LocalViewport).border_title = self.app.current_locus

    def on_feature_viewer_visible_features_changed(self, event):
        self.query_one("#visible-features").display_features(event.visible_features)
    
    def on_text_search_search_result_selected(self, event):
        self.query_one(FeatureViewer).go_to_location(
            # Need an explicit conversion to int, because otherwise the animation breaks
            int(event.feature.start),  
            where="middle"
        )

class JinxApp(App):
    CSS_PATH = "style/style.tcss"
    BINDINGS = [
        ("l", "open_locus_selector()", "Loci"),
        ("/", "open_search()", "Search qualifiers"),
        (":", "open_goto()", "Go to position"),
        ("q", "quit()", "Quit"),
    ]

    def __init__(self, path):
        super().__init__()
        self.load_data(path)

    def load_data(self, path):
        feature_data, locus_data = parse_genbank(path)
        feature_data["label"] = feature_data["product"]

        self.feature_data = feature_data.groupby("locus")
        self.locus_data = locus_data
        self.current_locus = self.locus_data.index[0]

    def get_current_locus_data(self):
        return self.feature_data.get_group(self.current_locus)
    
    def get_current_locus_length(self):
        print( self.locus_data.loc[self.current_locus, "sequence_length"] )
        return int(self.locus_data.loc[self.current_locus, "sequence_length"])
    
    
    def on_mount(self) -> None:
        self.install_screen(ViewerScreen(), name="viewer")
        self.install_screen(GotoPositionScreen(), name="goto")
        self.push_screen('viewer')
        self.push_screen('goto')


    def on_locus_switcher_change_current_locus(self, event):
        self.current_locus = self.locus_data.index[event.locus_index]
        print(self.current_locus)

        self.query_one(FeatureViewer).change_visible_features(
            genome_length=self.get_current_locus_length(),
            seq_features=self.get_current_locus_data()
        )

        self.query_one(LocalViewport).border_title = self.app.current_locus


    def action_open_search(self):
        self.query_one("#data-viewer-tabs").current = "text-search"
        self.query_one(DataViewer).border_title = "Search qualifiers"
        self.set_focus(
            self.query_one("#text-search-input")
        )

    def action_open_locus_selector(self):
        self.query_one(DataViewer).show_locus_switcher()

    def evaluate_goto(self, goto_result: int):
        # The result should be validated by the GoTo input itself
        if goto_result is None:
            return

        feature_viewer = self.query_one(FeatureViewer)
        feature_viewer.scroll_to((goto_result-1) // feature_viewer.nt_per_square, duration=0.5)
        
    def action_open_goto(self):
        self.push_screen('goto', self.evaluate_goto)




if __name__ == "__main__":

    app = JinxApp(sys.argv[1])
    app.run()

