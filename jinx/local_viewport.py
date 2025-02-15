
from textual.widgets import Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from feature_viewer import FeatureViewer

from textual.reactive import reactive


class PositionBar(Static):

    def compose(self):
        with Horizontal():
            yield Static(id="left")
            yield Static(id="middle")
            yield Static(id="right")

    def render_view_info(self, position, zoom, width):

        leftmost_position_nt = position.x * zoom + 1
        middle_position_nt = (position.x + width//2) * zoom 
        rightmost_position_nt = (position.x + width) * zoom


        self.query_one("#left").update(f"{leftmost_position_nt} \n|")
        self.query_one("#middle").update(f"{middle_position_nt} \n|")
        self.query_one("#right").update(f"{rightmost_position_nt} \n|")


class ZoomDetailsBar(Static):

    def compose(self):
        with Horizontal():
            yield Static(id="left")
            yield Static(id="right")

    def render_view_info(self, zoom, width):

        viewport_width = width * zoom


        self.query_one("#left").update(f"[b]±[/b] 1:{zoom} \n|")
        self.query_one("#right").update(f"[b]↔[/b] {viewport_width} nt\n|")


class LocalViewport(Static):

    ALLOW_MAXIMIZE = True

    BINDINGS = [
        Binding("+", "zoom_in", "Zoom in"),
        Binding("-", "zoom_out", "Zoom out"),
        Binding("shift+right", "fast_scroll_by(10)", "Scroll right by 10 cells", show=False),
        Binding("shift+left", "fast_scroll_by(-10)", "Scroll left by 10 cells", show=False),
        Binding("pagedown", "fast_scroll_by(100)", "Scroll right by 100 cells", show=False, priority=True),
        Binding("pageup", "fast_scroll_by(-100)", "Scroll left by 100 cells", show=False, priority=True),
        Binding("home", "fast_scroll_to('home')", "Scroll to beginning", show=False, priority=True),
        Binding("end", "fast_scroll_to('end')", "Scroll to end", show=False, priority=True),
        Binding("n", "select_feature('next')", "Next feature", show=False, priority=True ),
        Binding("p", "select_feature('previous')", "Previous feature", show=False, priority=True ),
        Binding("q", "close_feature_details", "Close feature details", show=False, priority=True ),
        Binding("escape", "close_feature_details", "Close feature details", show=False, priority=True ),
    ]

    def __init__(self, **kwargs):
        super().__init__()
        self.add_class("focus-highlight-border")
        self.feature_viewer_kwargs = kwargs
        

    def compose(self):
        yield Vertical(
            PositionBar(),
            FeatureViewer(**self.feature_viewer_kwargs),
            ZoomDetailsBar(),
        )
        yield Static("Sidebar", id="feature-details")


    def on_feature_viewer_scrolled(self, event):
        self.query_one(PositionBar).render_view_info(event.position, event.zoom, event.width)
        self.query_one(ZoomDetailsBar).render_view_info(event.zoom, event.width)

    def action_zoom_in(self):
        feature_viewer = self.query_one(FeatureViewer)
        feature_viewer.nt_per_square = feature_viewer.nt_per_square // 2
        # Viewer scroll position stayed the same in screen coordinates
        # but changed in nucleotide coordinates
        # We change the screen coordinates in order to stay in the same 
        # nucleotide coordinates
        feature_viewer.scroll_to(
            x=feature_viewer.scroll_offset.x * 2,
            animate=False
        )
    
    def action_zoom_out(self):
        feature_viewer = self.query_one(FeatureViewer)
        feature_viewer.nt_per_square = feature_viewer.nt_per_square * 2
        feature_viewer.scroll_to(
            x=feature_viewer.scroll_offset.x // 2,
            animate=False
        )

    def action_fast_scroll_by(self, scroll_by=0):
        feature_viewer = self.query_one(FeatureViewer)
        if scroll_by != 0:
            feature_viewer.scroll_relative(scroll_by, duration=0.2)

    def action_fast_scroll_to(self, scroll_to=None):
        feature_viewer = self.query_one(FeatureViewer)

        if scroll_to is not None:
            if scroll_to == "home":
                feature_viewer.scroll_to(0, duration=0.5)
            if scroll_to == "end":
                feature_viewer.scroll_to(feature_viewer.genome_length // feature_viewer.nt_per_square, duration=0.5)



    def action_select_feature(self, direction):
        feature_viewer = self.query_one(FeatureViewer)
        details_sidebar = self.query_one("#feature-details")

        if feature_viewer.features_within_bounds.empty:
            # TODO Add a message: no feature in the view
            details_sidebar.styles.display = "none"
            return


        details_sidebar.styles.display = "block"
        
        if direction=="next":
            feature_viewer.select_next_feature()
        elif direction == "previous":
            feature_viewer.select_previous_feature()

        details_sidebar.update(feature_viewer.seq_features.loc[feature_viewer.selected_feature].formatted_qualifiers)


    def action_close_feature_details(self):
        feature_viewer = self.query_one(FeatureViewer)
        feature_viewer.unselect_feature()

        details_sidebar = self.query_one("#feature-details")
        details_sidebar.styles.display = "none"
    