from textual.app import App, ComposeResult
from textual.geometry import Size
from textual.scrollbar import ScrollRight
from textual.strip import Strip
from textual.scroll_view import ScrollView
from textual.widgets import Header, Footer, Static
from textual.message import Message
from textual.containers import Horizontal, Vertical

from rich.segment import Segment

import pandas as pd


class FeatureViewer(ScrollView):
    COMPONENT_CLASSES = {
        "featurevier--label",
        "featurevier--cds",
    }

    def __init__(self, seq_features, genome_length, nt_per_square=1) -> None:
        super().__init__()
        self.show_vertical = True

        self.genome_length = genome_length
        self.nt_per_square = nt_per_square

        self.seq_features = seq_features.sort_values("start")
        self._compute_screen_positions()
        self._assign_vertical_groups()
        self.seq_features_interval_index = pd.IntervalIndex.from_arrays(
            self.seq_features.screen_start, 
            self.seq_features.screen_end,
            closed="left"
        )

        self.n_virtual_groups = self.seq_features["vertical_group"].max()+1

        self.virtual_size = Size(self.genome_length//self.nt_per_square+1, self.n_virtual_groups*3)

    def _compute_screen_positions(self):
        # Convert from 1-based to 0-based coords
        self.seq_features["screen_start"] = (self.seq_features.start - 1) // self.nt_per_square 
        self.seq_features["screen_end"] = (self.seq_features.end - 1) // self.nt_per_square  + 1 # We add one, because the end is not inclusive
        self.seq_features["screen_feature_width"] = self.seq_features.screen_end - self.seq_features.screen_start
        self.seq_features.loc[self.seq_features.screen_feature_width < 1, "screen_feature_width"] = 1 # Minimal width is always 1
        self.seq_features["label_width"] = self.seq_features.label.str.len()
        self.seq_features["screen_render_width"] = self.seq_features[["screen_feature_width", "label_width"]].max(axis=1)
        self.seq_features["screen_render_end"] = self.seq_features.screen_start  + self.seq_features.screen_render_width

    def _assign_vertical_groups(self):
        vertical_groups = [-1] * len(self.seq_features)

        for group in range(len(self.seq_features)):
            current_max = -1
            for i, (_, row) in enumerate(self.seq_features.iterrows()):
                if vertical_groups[i] == -1 and row.screen_start > current_max:
                    vertical_groups[i] = group
                    current_max = row.screen_render_end

            if current_max == 0:
                break
        
        self.seq_features["vertical_group"] = vertical_groups

    

    class Scrolled(Message):
        """Color selected message."""

        def __init__(self, position, zoom, width) -> None:
            self.position = position
            self.zoom = zoom
            self.width = width
            super().__init__()



    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        

        scroll_x, scroll_y = self.scroll_offset  # The current scroll position
        y += scroll_y 
        leftmost_position_cell = scroll_x
        # First non-displayed cell; we need to substract the scrollbar width
        rightmost_position_cell = leftmost_position_cell + self.size.width - self.styles.scrollbar_size_vertical 

        if y == 0:
            self.post_message(self.Scrolled(self.scroll_offset, self.nt_per_square, self.size.width - self.styles.scrollbar_size_vertical ))


        label_style = self.get_component_rich_style("featurevier--label")
        cds_style = self.get_component_rich_style("featurevier--cds")

        selected_seq_features = self.seq_features[
            self.seq_features_interval_index.overlaps(pd.Interval(leftmost_position_cell, rightmost_position_cell, closed='left')) &
            (self.seq_features.vertical_group == y//3)
        ]


        if selected_seq_features.empty:
            return Strip.blank(self.size.width)

        if y % 3 == 2:
            # Render features
            segments = []
            current_position = leftmost_position_cell
            
            for _, row in selected_seq_features.iterrows():


                if row.screen_start < leftmost_position_cell:
                    segments.append(
                        Segment(" " * (row.screen_end - leftmost_position_cell), cds_style)
                    )

                elif row.screen_end >= rightmost_position_cell:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    segments.append(
                        Segment(" " * (row.screen_feature_width), cds_style)
                    )
                    
                else:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    segments.append(
                        Segment(" " * row.screen_feature_width, cds_style)
                    )
                    
                current_position = row.screen_end


            strip = Strip(segments)
            return strip
        
        if y % 3 == 1:
            # Render labels
            segments = []
            current_position = leftmost_position_cell
        
            for _, row in selected_seq_features.iterrows():


                if row.screen_start < leftmost_position_cell:
                    if row.label_width <= (row.screen_end - leftmost_position_cell):
                        segments.append(
                            Segment(row.label, label_style)
                        )
                    else:
                        segments.append(
                            Segment(" " * (row.screen_end - leftmost_position_cell))
                        )

                elif (row.screen_start + row.label_width) > rightmost_position_cell:
                    if row.label_width < (rightmost_position_cell - row.screen_start):
                        segments.append(
                            Segment(" " * (row.screen_start - current_position))
                        )
                        segments.append(
                            Segment(row.label, label_style)
                        )
                    
                else:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    segments.append(
                        Segment(row.label, label_style)
                    )
                    

                current_position = max(row.screen_start, current_position) + row.label_width


            strip = Strip(segments)
            return strip

            
        else:
            return Strip.blank(self.size.width)




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


class LocalViewport(Static):

    def __init__(self, **kwargs):
        super().__init__()
        self.feature_viewer_kwargs = kwargs

    def compose(self):
        yield PositionBar()
        yield FeatureViewer(**self.feature_viewer_kwargs)

    def on_feature_viewer_scrolled(self, event):
        self.query_one(PositionBar).render_view_info(event.position, event.zoom, event.width)
        



# DATA = pd.DataFrame([
#     {"start": 2, "end": 13, "label": "Test 1"},
#     {"start": 15, "end": 50, "label": "Test 2"},
# ])
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


class GeneBankerApp(App):
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield LocalViewport(seq_features=DATA, genome_length=900, nt_per_square=1)
        yield Footer()


if __name__ == "__main__":

    app = GeneBankerApp()
    app.run()

