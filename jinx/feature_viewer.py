from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.message import Message
from textual.reactive import reactive

from rich.segment import Segment
from rich.style import Style

from collections import namedtuple

import pandas as pd
import time
import math

LabelTuple = namedtuple("LabelTuple", ["above", "below"])


class FeatureViewer(ScrollView):
    COMPONENT_CLASSES = {
        "featurevier--label",
        "featurevier--default-feature",
        "featurevier--type-cds",
        "featurevier--type-gene",
        "featurevier--type-mrna",
        "featurevier--type-rrna",
        "featurevier--type-trna",
        "featurevier--type-rep_origin",
        "featurevier--type-regulatory",
        "featurevier--type-sig_peptide",
        "featurevier--type-regulatory",
        "featurevier--type-variation",
    }
    
    nt_per_square = reactive(1)

    def __init__(self, seq_features, genome_length, nt_per_square=1, min_height=10) -> None:
        super().__init__()

        self.min_height = min_height
        self.genome_length = genome_length
        self.seq_features = seq_features.sort_values(["start", "end", "feature_type"])
        self.nt_per_square = nt_per_square # This automatically triggers _initialize_fature_rendering
        self.features_within_bounds = pd.DataFrame()
        self.labels_within_bounds = pd.DataFrame()
        

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

        # The virtual_size determines the scrollbar range
        self.virtual_size = Size(self.genome_length//self.nt_per_square+1, max(self.min_height, self.size.height))
    
    def on_resize(self):
        self._initialize_fature_rendering()


    def _compute_screen_positions(self):
        self.seq_features["screen_start"] = (self.seq_features.start) // int(self.nt_per_square) 
        self.seq_features["screen_end"] = (self.seq_features.end - 1 ) // int(self.nt_per_square) + 1 # We add one, because the end is not inclusive
        self.seq_features["screen_feature_width"] = self.seq_features.screen_end - self.seq_features.screen_start
        self.seq_features.loc[self.seq_features.screen_feature_width < 1, "screen_feature_width"] = 1 # Minimal width is always 1
        self.seq_features["label_width"] = self.seq_features.label.str.len()
        self.seq_features["screen_render_width"] = self.seq_features.screen_feature_width
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
                if row.screen_start >= current_max:
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
        displayed_feature_string = "━" * displayed_feature_width

        if left_overflow > 0:
            displayed_feature_string = "┅" + displayed_feature_string[1:]

        if right_overflow > 0:
            displayed_feature_string = displayed_feature_string[:-1] + "┅"

        if feature_width == 1:
            if strand == 1:
                displayed_feature_string = "▶"
            elif strand == -1:
                displayed_feature_string = "◀"
            else:
                displayed_feature_string = "●"
        else:
            if strand == 1 and left_overflow == 0:
                displayed_feature_string = "╺" + displayed_feature_string[1:]
            elif strand == -1 and right_overflow == 0:
                displayed_feature_string = displayed_feature_string[1:] + "╸"


        if displayed_feature_width > 1:
            if strand == 1:
                if right_overflow > 0:
                    segments = [
                        Segment(displayed_feature_string[:-2], rich_style),
                        Segment("▶", rich_style),
                        Segment(displayed_feature_string[-1], rich_style),
                    ]
                else:
                    segments = [
                        Segment(displayed_feature_string[:-1], rich_style),
                        Segment("▶", rich_style),
                    ]

            elif strand == -1:
                if left_overflow > 0:
                    segments = [
                        Segment(displayed_feature_string[0], rich_style),
                        Segment("◀", rich_style),
                        Segment(displayed_feature_string[2:], rich_style),
                    ]
                else:
                    segments = [
                        Segment("◀", rich_style),
                        Segment(displayed_feature_string[1:], rich_style),
                    ]
            else:
                segments = [Segment(displayed_feature_string, rich_style)]
        else:
            segments = [Segment(displayed_feature_string, rich_style)]

        return segments
    

    def _find_free_x_coordinate(self, feature, blocking_features, left_screen_bound, right_screen_bound):
        candidate_x = max(feature.screen_start, left_screen_bound)

        while candidate_x < min(feature.screen_end, right_screen_bound):
            for _, feature_above in blocking_features.iterrows():
                if feature_above.screen_start <= candidate_x < feature_above.screen_end:
                    # One of the features is blocking this x coordinate
                    candidate_x = feature_above.screen_end
                    break 
            else:
                return candidate_x
        
        return -1

    def _assign_vertical_label_groups(self, label_df):
        vertical_groups = pd.Series(
            [-1] * len(label_df),
            index=label_df.index
        )

        # We are trying to center the features -> we have an equal number of rows above and below them
        available_label_space = (self.virtual_size.height - self.features_within_bounds.vertical_group.max()) // 2 - 1

        # List of first available position in each row
        y_maxima = []

        for i, row in label_df.iterrows():
            feature_width = row.x_coord + row.label_width + 1

            if not y_maxima:
                # The first label to be placed
                vertical_groups[i] = 0
                y_maxima.append(feature_width)
                continue

            # We look at the rows from the reverse order (from the features out)
            for y, maximum in enumerate(y_maxima[::-1]):
                # And find one that we cannot place our label in
                # We terminate the search at the first failure, because we need to draw not only the label, but also the stem
                if row.x_coord < maximum:
                    break
            else:
                y += 1
            
            if y == 0 and len(y_maxima) >= available_label_space:
                # We run of available vertical space
                continue

            vertical_groups[i] = len(y_maxima) - y

            if y == 0:
                # If we failed at the bottommost row, we need to create a new row    
                y_maxima.append(feature_width)
            else:
                # Otherwise we just update the fist available position in the row that the label fits
                y_maxima[-(y)] = feature_width

        label_df["vertical_group"] = vertical_groups
        return label_df
    
    def _safely_postprocess_label_list(self, label_list):
        if label_list:
            labels_df = self._assign_vertical_label_groups(pd.DataFrame(label_list).sort_values("x_coord"))
        else:
            # No sroting can be done
            labels_df = self._assign_vertical_label_groups(pd.DataFrame([]))
        
        # Drop labels that couldn't fit vertically
        labels_df = labels_df[labels_df.vertical_group != -1]
        return labels_df
    
    
    def _compute_current_labels(self, left_screen_bound, right_screen_bound):
        labels_above = []
        labels_below = []

        for _, feature in self.features_within_bounds.iterrows():
            overlapping_features = self.features_within_bounds[
                ~(
                    (self.features_within_bounds.screen_start >= feature.screen_end) |
                    (self.features_within_bounds.screen_end < feature.screen_start)
                )
            ]

            features_above = overlapping_features[
                (overlapping_features.vertical_group < feature.vertical_group)
            ]
            features_below = overlapping_features[
                (overlapping_features.vertical_group > feature.vertical_group) 
            ]

            x_coord_above = self._find_free_x_coordinate(feature, features_above, left_screen_bound, right_screen_bound)
            x_coord_below = self._find_free_x_coordinate(feature, features_below, left_screen_bound, right_screen_bound)

            # Decide if the label should go above or below
            if x_coord_above == -1:
                if x_coord_below == -1:
                    # No position found
                    continue
                else:
                    labels_below.append({"x_coord":x_coord_below, "label":feature.label, "label_width":feature.label_width})
            else:
                if x_coord_below == -1:
                    labels_above.append({"x_coord":x_coord_above, "label":feature.label, "label_width":feature.label_width})
                else:
                    # Leftmost available position
                    if x_coord_above <= x_coord_below:
                        labels_above.append({"x_coord":x_coord_above, "label":feature.label, "label_width":feature.label_width})
                    else:
                        labels_below.append({"x_coord":x_coord_below, "label":feature.label, "label_width":feature.label_width})
        
        labels_above_df = self._safely_postprocess_label_list(labels_above)
        labels_below_df = self._safely_postprocess_label_list(labels_below)

        return LabelTuple(labels_above_df, labels_below_df)
    

    def _render_feature_strip(self, features_to_render, leftmost_position_cell, rightmost_position_cell):
        if features_to_render.empty:
            return Strip.blank(self.size.width)

        segments = []
        current_position = leftmost_position_cell
        
        for _, row in features_to_render.iterrows():

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


    def _render_label_strip(self, labels_to_render, stems_to_render, leftmost_position_cell, rightmost_position_cell):
        if labels_to_render.empty and stems_to_render.empty:
            return Strip.blank(self.size.width)

        segments = []
        current_position = leftmost_position_cell
        label_style = self.get_component_rich_style("featurevier--label")

        # We make stems look like labels and mix them in with the other labels
        stems_df = pd.DataFrame({
            "x_coord": stems_to_render.x_coord,
            "label": "│",
            "label_width": 1
        })

        mixed_df = pd.concat([
            labels_to_render,
            stems_df
        ]).sort_values("x_coord", ascending=True)

        for _, row in mixed_df.iterrows():
            segments.append(
                Segment(" " * (row.x_coord - current_position))
            )

            if row.x_coord + row.label_width >= rightmost_position_cell:
                # Label goes out of screen -> we truncate it
                segments.append(
                    Segment(row.label[:rightmost_position_cell-(row.x_coord+row.label_width)-1] + "…", label_style)
                )
            else:
                segments.append(
                    Segment(row.label, label_style)
                )
            current_position = row.x_coord + row.label_width


        strip = Strip(segments)
        return strip



    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        
        scroll_x, scroll_y = self.scroll_offset  # The current scroll position
        y += scroll_y 
        leftmost_position_cell = scroll_x
        # First non-displayed cell; we need to substract the scrollbar width
        rightmost_position_cell = leftmost_position_cell + self.size.width - self.styles.scrollbar_size_vertical 

        if y == scroll_y:
            # Update which features are visible on the x axis
            self.features_within_bounds = self.seq_features[
                self.seq_features_interval_index.overlaps(pd.Interval(leftmost_position_cell, rightmost_position_cell, closed='left'))
            ]
            # Update which labels are visible
            self.labels_within_bounds = self._compute_current_labels(leftmost_position_cell, rightmost_position_cell)

            # Signal the chagnge to other components
            self.post_message(self.Scrolled(self.scroll_offset, self.nt_per_square, self.size.width - self.styles.scrollbar_size_vertical ))
            self.post_message(self.VisibleFeaturesChanged(self.features_within_bounds))

            print("CURRENT FEATURES")
            print(self.features_within_bounds)

        # # Adding constants to create spacing between features and labels
        # last_label_above_row = self.labels_within_bounds.above.vertical_group.max() + 1
        # last_feature_row = self.features_within_bounds.vertical_group.max() + last_label_above_row + 1
        # last_label_below_row = self.labels_within_bounds.below.vertical_group.max() + last_feature_row + 1

        last_label_above_row = (self.virtual_size.height - self.features_within_bounds.vertical_group.max()) // 2 - 1
        first_label_above_row = max(last_label_above_row - self.labels_within_bounds.above.vertical_group.max() - 1, 0)

        last_feature_row = self.features_within_bounds.vertical_group.max() + last_label_above_row + 1
        last_label_below_row = self.labels_within_bounds.below.vertical_group.max() + last_feature_row + 1

        if y <= last_label_above_row:
            # We are rendering labels above
            labels_to_render = self.labels_within_bounds.above[y == self.labels_within_bounds.above.vertical_group + first_label_above_row]
            stems_to_render = self.labels_within_bounds.above[y > self.labels_within_bounds.above.vertical_group + first_label_above_row]
            strip = self._render_label_strip(labels_to_render, stems_to_render, leftmost_position_cell, rightmost_position_cell)
        
        elif y <= last_feature_row:
            # We are rendering features
            features_to_render = self.features_within_bounds[
                (y == self.features_within_bounds.vertical_group + last_label_above_row + 1)
            ]
            strip = self._render_feature_strip(features_to_render, leftmost_position_cell, rightmost_position_cell)
        else:
            # We are rendering labels below
            labels_to_render = self.labels_within_bounds.below[y == last_label_below_row - self.labels_within_bounds.below.vertical_group + 1]
            stems_to_render = self.labels_within_bounds.below[y < (last_label_below_row - self.labels_within_bounds.below.vertical_group + 1)]
            strip = self._render_label_strip(labels_to_render, stems_to_render, leftmost_position_cell, rightmost_position_cell)
        
        return strip


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
            