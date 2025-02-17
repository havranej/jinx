#!/usr/bin/env python3

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.screen import Screen

from local_viewport import LocalViewport
from feature_viewer import FeatureViewer
from data_viewer import DataViewer
from goto_position import GotoPositionScreen
from text_search import TextSearchScreen
from help_screen import HelpScreen

from parsers import parse_genbank

import sys


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
        # yield DataViewer()
        yield Footer()

    def on_mount(self):
        self.query_one(LocalViewport).border_title = self.app.current_locus

    # def on_feature_viewer_visible_features_changed(self, event):
    #     self.query_one("#visible-features").display_features(event.visible_features)
    
    def on_text_search_search_result_selected(self, event):
        self.query_one(FeatureViewer).go_to_location(
            # Need an explicit conversion to int, because otherwise the animation breaks
            int(event.feature.start),  
            where="middle"
        )

class JinxApp(App):
    TITLE = "Jinx"
    CSS_PATH = "style/style.tcss"
    BINDINGS = [
        ("l", "open_locus_selector()", "Loci"),
        ("/", "open_search()", "Search qualifiers"),
        (":", "open_goto()", "Go to position"),
        ("?", "open_help()", "Help"),
    ]

    def __init__(self, path):
        super().__init__()
        self.load_data(path)

    def determine_labels(self, feature_data):
        current_labels = feature_data.label.copy()
        current_labels.loc[current_labels == "no_label"] = feature_data.gene.loc[current_labels == "no_label"]
        current_labels.loc[current_labels == "no_gene_name"] = feature_data["product"].loc[current_labels == "no_gene_name"]
        current_labels.loc[current_labels == "no_product"] = feature_data.locus_tag.loc[current_labels == "no_product"]
        current_labels.loc[current_labels == "no_tag"] = feature_data.feature_type.loc[current_labels == "no_tag"] + " <no label>"
        return current_labels

    def load_data(self, path):
        feature_data, locus_data = parse_genbank(path)
        feature_data["label"] = self.determine_labels(feature_data)

        self.feature_data = feature_data
        self.locus_data = locus_data
        self.current_locus = self.locus_data.index[0]

    def get_current_locus_data(self):
        return self.feature_data[self.feature_data.locus == self.current_locus]
    
    def get_current_locus_length(self):
        print( self.locus_data.loc[self.current_locus, "sequence_length"] )
        return int(self.locus_data.loc[self.current_locus, "sequence_length"])
    
    
    def on_mount(self) -> None:
        self.install_screen(ViewerScreen(), name="viewer")
        self.install_screen(GotoPositionScreen(), name="goto")
        self.install_screen(TextSearchScreen(), name="text_search")
        self.install_screen(HelpScreen(), name="help")
        self.push_screen('viewer')


    def switch_locus(self, locus_id):
        self.current_locus = locus_id

        self.query_one(FeatureViewer).change_visible_features(
            genome_length=self.get_current_locus_length(),
            seq_features=self.get_current_locus_data()
        )

        self.query_one(LocalViewport).border_title = self.app.current_locus


    def on_locus_switcher_change_current_locus(self, event):
        self.switch_locus(
            self.locus_data.index[event.locus_index]
        )
        
        
    def evaluate_text_search(self, search_result):
        if search_result is None:
            return

        local_viewport = self.query_one(LocalViewport)
        local_viewport.select_specific_feature(search_result)

    def action_open_search(self):
        self.push_screen('text_search', self.evaluate_text_search)

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

    def action_open_help(self):
        self.push_screen('help')


if __name__ == "__main__":

    app = JinxApp(sys.argv[1])
    app.run()

