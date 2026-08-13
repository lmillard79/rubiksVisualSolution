"""Color id -> RGB for rendering."""

from __future__ import annotations

from matplotlib.colors import ListedColormap

from ..constants import BLUE, GREEN, ORANGE, RED, WHITE, YELLOW

HEX_BY_COLOR_ID = {
    WHITE: "#FFFFFF",
    YELLOW: "#FFD500",
    GREEN: "#009E60",
    BLUE: "#0051BA",
    ORANGE: "#FF5800",
    RED: "#C41E3A",
}

CUBE_CMAP = ListedColormap([HEX_BY_COLOR_ID[i] for i in range(6)])
STICKER_BORDER_COLOR = "#202020"
HIGHLIGHT_COLOR = "#00E5FF"
LAST_MOVE_COLOR = "#FF00AA"
