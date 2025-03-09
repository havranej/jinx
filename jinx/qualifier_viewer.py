
from textual.widgets import RichLog

class QualifierViewer(RichLog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wrap=True
        self.min_width=20
        self.markup=True
        self.auto_scroll=False

    def view_feature(self, feature):
        self.clear()
        
        if feature.strand == 1:
            strand = "+"
        elif feature.strand == -1:
            strand = "-"
        elif feature.strand == 0:
            strand = "."
        else:
            strand = "?"

        self.write(f"[underline]{feature.feature_type} at {feature.locus}:{feature.start}-{feature.end} ({strand})[/underline]\n")
        self.write(feature.formatted_qualifiers)
