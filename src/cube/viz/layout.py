"""2D unfolded-net layout: where each face's tile sits in the picture.

Uses the same face-adjacency convention geometry.py's FACE_FRAME was derived
from (U above F; L, F, R, B left-to-right; D below F), and reuses each
face's own (row, col) indices directly - they were already defined with
row 0 = top, col 0 = left when geometry.py's sticker_xyz formulas were built,
so no separate derivation is needed here to get the picture right-side up.
"""

from __future__ import annotations

from ..constants import Face

NET_ORIGIN: dict[Face, tuple[int, int]] = {
    Face.U: (1, 0),
    Face.L: (0, 1),
    Face.F: (1, 1),
    Face.R: (2, 1),
    Face.B: (3, 1),
    Face.D: (1, 2),
}

NET_TILE_COLS = 4
NET_TILE_ROWS = 3


def face_extent(face: Face, n: int) -> tuple[float, float, float, float]:
    """(left, right, bottom, top) for imshow(extent=...), consistent with
    origin='upper' so row 0 is drawn at the top of the tile."""
    tile_col, tile_row = NET_ORIGIN[face]
    left = tile_col * n
    right = left + n
    top = -(tile_row * n)
    bottom = top - n
    return left, right, bottom, top


def sticker_center(face: Face, r: int, c: int, n: int) -> tuple[float, float]:
    """Screen-space center of a single sticker cell, for placing highlight overlays."""
    tile_col, tile_row = NET_ORIGIN[face]
    x = tile_col * n + c + 0.5
    y = -(tile_row * n) - r - 0.5
    return x, y


def sticker_cell_bounds(face: Face, r: int, c: int, n: int) -> tuple[float, float, float, float]:
    """(x, y, width, height) of one sticker cell's bottom-left corner + size, for Rectangle patches."""
    cx, cy = sticker_center(face, r, c, n)
    return cx - 0.5, cy - 0.5, 1.0, 1.0
