"""
Position manager for spectrum, lyrics, logo, and CTA elements.
Handles auto-avoid overlap and safe area constraints.
"""
import logging

logger = logging.getLogger(__name__)


class ElementRect:
    """Rectangle representing an element's position and size."""
    def __init__(self, x, y, width, height, name=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    def intersects(self, other):
        return not (self.right < other.left or self.left > other.right or
                    self.bottom < other.top or self.top > other.bottom)

    def __repr__(self):
        return f"Rect({self.name}: x={self.x}, y={self.y}, w={self.width}, h={self.height})"


class PositionManager:
    """Manage positions of all visual elements."""

    POSITION_MAP = {
        "bottom": (0.5, 0.9),
        "top": (0.5, 0.1),
        "left": (0.1, 0.5),
        "right": (0.9, 0.5),
        "center": (0.5, 0.5),
        "above_spectrum": (0.5, 0.7),
    }

    def __init__(self, video_width, video_height):
        self.video_width = video_width
        self.video_height = video_height
        self.safe_area_margin = 0.05
        self.auto_avoid_overlap = True
        self.elements = {}
        self.margins = {"top": 20, "bottom": 20, "left": 20, "right": 20}

    def set_safe_area(self, margin_ratio=0.05):
        self.safe_area_margin = margin_ratio

    def resolve_position(self, position_name):
        """Convert named position to (x_ratio, y_ratio)."""
        if isinstance(position_name, dict):
            return position_name.get("x", 0.5), position_name.get("y", 0.5)
        return self.POSITION_MAP.get(position_name, (0.5, 0.5))

    def register_element(self, name, x_ratio, y_ratio, width, height):
        """Register an element's position."""
        x = int(x_ratio * self.video_width - width / 2)
        y = int(y_ratio * self.video_height - height / 2)
        rect = ElementRect(x, y, width, height, name)
        self.elements[name] = rect
        return rect

    def apply_margins(self, rect):
        """Ensure element is within margins."""
        min_x = self.margins["left"]
        max_x = self.video_width - self.margins["right"] - rect.width
        min_y = self.margins["top"]
        max_y = self.video_height - self.margins["bottom"] - rect.height

        rect.x = max(min_x, min(rect.x, max_x))
        rect.y = max(min_y, min(rect.y, max_y))
        return rect

    def apply_safe_area(self, rect):
        """Ensure element is within safe area."""
        margin = self.safe_area_margin
        min_x = int(self.video_width * margin)
        max_x = int(self.video_width * (1 - margin)) - rect.width
        min_y = int(self.video_height * margin)
        max_y = int(self.video_height * (1 - margin)) - rect.height

        rect.x = max(min_x, min(rect.x, max_x))
        rect.y = max(min_y, min(rect.y, max_y))
        return rect

    def avoid_overlap(self, element_name, fixed_elements=None):
        """Adjust element position to avoid overlapping with other elements."""
        if not self.auto_avoid_overlap:
            return

        if element_name not in self.elements:
            return

        rect = self.elements[element_name]
        others = fixed_elements or [n for n in self.elements if n != element_name]

        for other_name in others:
            if other_name not in self.elements:
                continue
            other = self.elements[other_name]
            if rect.intersects(other):
                overlap_y = min(rect.bottom, other.bottom) - max(rect.top, other.top)
                if rect.y < other.y:
                    rect.y = other.top - rect.height - 10
                else:
                    rect.y = other.bottom + 10

        self.apply_margins(rect)
        self.apply_safe_area(rect)

    def get_position(self, element_name):
        """Get element's current position as (x, y)."""
        if element_name in self.elements:
            rect = self.elements[element_name]
            return rect.x, rect.y
        return 0, 0

    def get_position_ratio(self, element_name):
        """Get position as ratio (0-1)."""
        if element_name in self.elements:
            rect = self.elements[element_name]
            return {
                "x": (rect.x + rect.width / 2) / self.video_width,
                "y": (rect.y + rect.height / 2) / self.video_height,
            }
        return {"x": 0.5, "y": 0.5}

    def calculate_spectrum_rect(self, settings, position):
        """Calculate spectrum bounding rect."""
        bar_count = settings.get("bar_count", 64)
        bar_width = settings.get("bar_width", 8)
        bar_spacing = settings.get("bar_spacing", 3)
        max_height = settings.get("max_height", 200)

        total_w = bar_count * (bar_width + bar_spacing) - bar_spacing
        x_ratio, y_ratio = self.resolve_position(position)

        return self.register_element("spectrum", x_ratio, y_ratio, total_w, max_height)

    def calculate_lyrics_rect(self, font_size, text_width, position):
        """Calculate lyrics bounding rect."""
        height = int(font_size * 3)
        x_ratio, y_ratio = self.resolve_position(position)
        return self.register_element("lyrics", x_ratio, y_ratio, text_width, height)

    def calculate_logo_rect(self, logo_width, logo_height, position):
        """Calculate logo bounding rect."""
        x_ratio, y_ratio = self.resolve_position(position)
        return self.register_element("logo", x_ratio, y_ratio, logo_width, logo_height)

    def calculate_cta_rect(self, cta_width, cta_height, position):
        """Calculate CTA bounding rect."""
        x_ratio, y_ratio = self.resolve_position(position)
        return self.register_element("cta", x_ratio, y_ratio, cta_width, cta_height)

    def auto_layout(self):
        """Auto-arrange all elements to avoid overlaps."""
        priority = ["spectrum", "lyrics", "logo", "cta"]
        for name in priority:
            if name in self.elements:
                fixed = [n for n in priority if n != name and n in self.elements]
                self.avoid_overlap(name, fixed)
