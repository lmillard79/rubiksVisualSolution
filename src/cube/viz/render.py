"""Static unfolded-net rendering of a Cube."""

from __future__ import annotations

import matplotlib.pyplot as plt

from ..constants import ALL_FACES
from ..state import Cube
from .colors import CUBE_CMAP, STICKER_BORDER_COLOR
from .layout import NET_TILE_COLS, NET_TILE_ROWS, face_extent


def draw_net(cube: Cube, ax=None, title: str | None = None):
    """Render `cube` as an unfolded net onto `ax` (a new figure/axes if None).
    Returns (fig, ax, images) - `images` maps Face -> the AxesImage for that
    face, so a caller doing interactive stepping can update with
    image.set_data(...) instead of redrawing from scratch.
    """
    n = cube.n
    if ax is None:
        fig, ax = plt.subplots(figsize=(NET_TILE_COLS * 1.3, NET_TILE_ROWS * 1.3))
    else:
        fig = ax.figure

    images = {}
    for face in ALL_FACES:
        left, right, bottom, top = face_extent(face, n)
        image = ax.imshow(
            cube.colors[face],
            cmap=CUBE_CMAP,
            vmin=0,
            vmax=5,
            extent=(left, right, bottom, top),
            origin="upper",
        )
        images[face] = image
        for i in range(n + 1):
            line_width = 2.0 if i in (0, n) else 0.6
            ax.plot([left, right], [top - i, top - i], color=STICKER_BORDER_COLOR, linewidth=line_width)
            ax.plot([left + i, left + i], [bottom, top], color=STICKER_BORDER_COLOR, linewidth=line_width)

    ax.set_xlim(0, NET_TILE_COLS * n)
    ax.set_ylim(-NET_TILE_ROWS * n, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    if title:
        ax.set_title(title)
    return fig, ax, images


def refresh_net(cube: Cube, images: dict) -> None:
    """Update an existing render in place (no re-draw of borders/axes)."""
    for face, image in images.items():
        image.set_data(cube.colors[face])
