from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input
from textual.screen import Screen


from widgets import LocalViewport
from feature_viewer import FeatureViewer
from data_viewer import DataViewer, VisibleFeaturesTab, TextSearch
from parsers import parse_genbank

from textual._animator import AnimationError

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

    def __init__(self, data, locus_sequences, current_locus):
        self.data = data
        self.locus_sequences = locus_sequences
        self.current_locus = current_locus
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LocalViewport(
            seq_features=self.data, 
            genome_length=len(self.locus_sequences[self.current_locus]), 
            nt_per_square=64
        )
        yield DataViewer(
            seq_features=self.data
        )
        yield Footer()

    def on_feature_viewer_visible_features_changed(self, event):
        self.query_one(VisibleFeaturesTab).display_visible_features(event.visible_features)
    
    def on_text_search_search_result_selected(self, event):
        # TODO: Make feature viewer go to location
        self.query_one(FeatureViewer).go_to_location(
            # Need an explicit conversion to int, because otherwise the animation breaks
            int(event.feature.start),  
            where="middle"
        )


class JinxApp(App):
    CSS_PATH = "style/style.tcss"
    BINDINGS = [
        ("/", "open_search()", "Search"),
        ("q", "quit()", "Quit"),
    ]


    data, locus_sequences = parse_genbank(sys.argv[1])
    data["label"] = data.gene
    # TODO: Display according to current locus + inter-locus switching
    current_locus = list(locus_sequences.keys())[0]

    
    def on_mount(self) -> None:
        self.install_screen(ViewerScreen(self.data, self.locus_sequences, self.current_locus), name="viewer")
        self.push_screen('viewer')

    def action_open_search(self):
        self.query_one("#data-viewer-tabs").active = "text-search"
        self.set_focus(
            self.query_one("#text-search-input")
        )


if __name__ == "__main__":

    app = JinxApp()
    app.run()

