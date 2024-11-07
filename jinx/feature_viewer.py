from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.message import Message
from textual.reactive import reactive

from rich.segment import Segment
from rich.style import Style

import pandas as pd
import time


class FeatureViewer(ScrollView):
    COMPONENT_CLASSES = {
        "featurevier--label",
        "featurevier--default-feature",
        "featurevier--type-cds",
        "featurevier--type-gene",
        "featurevier--type-mRNA",
        "featurevier--type-sig_peptide",
        "featurevier--type-regulatory",
        "featurevier--type-variation",
    }
    
    nt_per_square = reactive(1)

    def __init__(self, seq_features, genome_length, nt_per_square=1) -> None:
        super().__init__()
        
        self.genome_length = genome_length
        self.seq_features = seq_features.sort_values(["start", "end", "feature_type"])
        self.nt_per_square = nt_per_square # This automatically triggers _initialize_fature_rendering


    def validate_nt_per_square(self, nt_per_square):
        if nt_per_square < 1:
            nt_per_square = 1
        elif nt_per_square > 2**20:
            nt_per_square = 2**20
        
        return nt_per_square


    def watch_nt_per_square(self, new_value):
        # Is called when "nt_per_square" changes
        self._initialize_fature_rendering()


    def change_visible_features(self, seq_features=None, genome_length=None, nt_per_square=None):
        if genome_length is not None:
            self.genome_length = genome_length
        
        if seq_features is not None:
            self.seq_features = seq_features.sort_values(["start", "end", "feature_type"])
        
        if nt_per_square is not None:
            self.nt_per_square = nt_per_square
        else:
            # Since nt_per_square is watched, its change automatically triggers the rendering
            # If we don't change it, we need to trigger it manually
            self._initialize_fature_rendering()


    def _initialize_fature_rendering(self):
        """
        Precompute how the features should be rendered.
        We need to call this whenever a zoom level changes
        """
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
        self.seq_features["screen_start"] = (self.seq_features.start - 1) // int(self.nt_per_square) 
        self.seq_features["screen_end"] = (self.seq_features.end - 1) // int(self.nt_per_square)  + 1 # We add one, because the end is not inclusive
        self.seq_features["screen_feature_width"] = self.seq_features.screen_end - self.seq_features.screen_start
        self.seq_features.loc[self.seq_features.screen_feature_width < 1, "screen_feature_width"] = 1 # Minimal width is always 1
        self.seq_features["label_width"] = self.seq_features.label.str.len()
        self.seq_features["screen_render_width"] = self.seq_features[["screen_feature_width", "label_width"]].max(axis=1)
        self.seq_features["screen_render_end"] = self.seq_features.screen_start  + self.seq_features.screen_render_width

    def _assign_vertical_groups(self):
        vertical_groups = pd.Series(
            [-1] * len(self.seq_features),
            index=self.seq_features.index
        )

        outer_start_time = time.time()
        for group in range(len(self.seq_features)):
            current_max = -1
            for i, row in self.seq_features[vertical_groups == -1].iterrows():
                if row.screen_start > current_max:
                    vertical_groups[i] = group
                    current_max = row.screen_render_end

            if current_max == -1:
                break

        print("--- Positions computed in %s seconds ---" % (time.time() - outer_start_time))
        
        self.seq_features["vertical_group"] = vertical_groups

    

    class Scrolled(Message):
        """Indicates that a scroll has happened"""

        def __init__(self, position, zoom, width) -> None:
            self.position = position
            self.zoom = zoom
            self.width = width
            super().__init__()


    class VisibleFeaturesChanged(Message):
        def __init__(self, visible_features):
            self.visible_features = visible_features
            super().__init__()


    def _get_feature_segment(self, feature_width, segment_class=None, left_overflow=0, right_overflow=0, strand=0):
        try:
            rich_style = self.get_component_rich_style(f"featurevier--{segment_class}")
        except KeyError:
            # Given class is not defined
            rich_style = self.get_component_rich_style("featurevier--default-feature")


        displayed_feature_width = feature_width - left_overflow - right_overflow
        displayed_feature_string = "█" * displayed_feature_width

        if left_overflow > 0:
            displayed_feature_string = "░" + displayed_feature_string[1:]

        if right_overflow > 0:
            displayed_feature_string = displayed_feature_string[:-1] + "░"

        if feature_width == 1:
            if strand == 1:
                displayed_feature_string = "▶"
            elif strand == -1:
                displayed_feature_string = "◀"
            else:
                displayed_feature_string = "●"

        negative_style = Style.chain(rich_style, Style(reverse=True, bold=True, bgcolor="yellow"))

        if displayed_feature_width > 1:
            if strand == 1:
                if right_overflow > 0:
                    segments = [
                        Segment(displayed_feature_string[:-2], rich_style),
                        Segment("→", negative_style),
                        Segment(displayed_feature_string[-1], rich_style),
                    ]
                else:
                    segments = [
                        Segment(displayed_feature_string[:-1], rich_style),
                        Segment("→", negative_style),
                    ]

            elif strand == -1:
                if left_overflow > 0:
                    segments = [
                        Segment(displayed_feature_string[0], rich_style),
                        Segment("←", negative_style),
                        Segment(displayed_feature_string[2:], rich_style),
                    ]
                else:
                    segments = [
                        Segment("←", negative_style),
                        Segment(displayed_feature_string[1:], rich_style),
                    ]
            else:
                segments = [Segment(displayed_feature_string, rich_style)]
        else:
            segments = [Segment(displayed_feature_string, rich_style)]

        return segments


    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        

        scroll_x, scroll_y = self.scroll_offset  # The current scroll position
        y += scroll_y 
        leftmost_position_cell = scroll_x
        # First non-displayed cell; we need to substract the scrollbar width
        rightmost_position_cell = leftmost_position_cell + self.size.width - self.styles.scrollbar_size_vertical 

        label_style = self.get_component_rich_style("featurevier--label")

        features_within_bounds = self.seq_features[
            self.seq_features_interval_index.overlaps(pd.Interval(leftmost_position_cell, rightmost_position_cell, closed='left'))
        ]

        selected_seq_features = features_within_bounds[
            (features_within_bounds.vertical_group == y//3)
        ]

        if y == 0:
            self.post_message(self.Scrolled(self.scroll_offset, self.nt_per_square, self.size.width - self.styles.scrollbar_size_vertical ))
            self.post_message(self.VisibleFeaturesChanged(features_within_bounds))

        if selected_seq_features.empty:
            return Strip.blank(self.size.width)

        if y % 3 == 2:
            # Render features
            segments = []
            current_position = leftmost_position_cell
            
            for _, row in selected_seq_features.iterrows():

                if row.screen_start < leftmost_position_cell:
                    left_overflow = leftmost_position_cell - row.screen_start
                    right_overflow = max(row.screen_end - rightmost_position_cell, 0)

                elif row.screen_end >= rightmost_position_cell:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    left_overflow = 0
                    right_overflow = row.screen_end - rightmost_position_cell
                    
                else:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    left_overflow = right_overflow = 0


                segments.extend(
                    self._get_feature_segment(
                        row.screen_feature_width, 
                        f"type-{row.feature_type.lower()}", 
                        left_overflow=left_overflow,
                        right_overflow=right_overflow,
                        strand=row.strand
                    )
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
                        # We add an empty segment so that the list doesn't stay
                        # empty for the computation of the next position
                        segments.append(
                            Segment("", label_style)
                        )
                    
                else:
                    segments.append(
                        Segment(" " * (row.screen_start - current_position))
                    )
                    segments.append(
                        Segment(row.label, label_style)
                    )

                current_position = max(row.screen_start, current_position) + len(segments[-1].text)


            strip = Strip(segments)
            return strip

            
        else:
            return Strip.blank(self.size.width)


    def go_to_location(self, location_nt, where="left"):
        location_cell = (location_nt-1) // self.nt_per_square

        if where == "left":
            self.scroll_to(
                x=location_cell,
                animate=False
            )
        elif where == "middle":
            self.scroll_to(
                x=location_cell-self.size.width // 2,
                animate=False
            )
            