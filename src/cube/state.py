"""Cube state: sticker colors + a permanent sticker identity, and move application."""

from __future__ import annotations

import numpy as np

from .constants import ALL_FACES, Face, SOLVED_COLOR_OF_FACE
from .geometry import face_axis, face_normal_sign, layer_depth, remap_sticker, sticker_xyz
from .moves import Move

# A move's relocation pattern (which (face, r, c) sticker ends up at which
# other (face, r, c)) depends only on (n, axis, depths, quarter_turns), never
# on cube *state* - so it's computed once and cached, rather than re-derived
# via geometry.py on every apply(). This matters a lot: apply() is the
# innermost operation of every BFS search node in solver/search.py, and the
# geometry recomputation (a sticker_xyz call for all n^2 cells on all 6
# faces, plus remap_sticker for every affected one) was the dominant cost
# once searches started tracking more than a couple of pieces at once.
_RELOCATION_CACHE: dict[tuple, list[tuple[Face, int, int, Face, int, int]]] = {}


def _relocations_for(n: int, axis: int, depths: frozenset[int], quarter_turns: int):
    key = (n, axis, depths, quarter_turns)
    cached = _RELOCATION_CACHE.get(key)
    if cached is not None:
        return cached
    relocations = []
    for face in ALL_FACES:
        for r in range(n):
            for c in range(n):
                if sticker_xyz(face, r, c, n)[axis] not in depths:
                    continue
                new_face, new_r, new_c = remap_sticker(face, r, c, n, axis, quarter_turns)
                relocations.append((face, r, c, new_face, new_r, new_c))
    _RELOCATION_CACHE[key] = relocations
    return relocations


class Cube:
    """An NxN cube. `colors` is the actual puzzle state; `sticker_ids` is a
    permanent per-sticker identity assigned once at construction and carried
    along by every move exactly like color is - moves relocate stickers,
    they never change which sticker is where. That second array is what lets
    PieceRegistry (built later) answer "where is this specific piece now"
    without any extra bookkeeping in `apply`.
    """

    def __init__(self, n: int):
        self.n = n
        self.colors: dict[Face, np.ndarray] = {
            face: np.full((n, n), SOLVED_COLOR_OF_FACE[face], dtype=np.uint8) for face in ALL_FACES
        }
        self.sticker_ids: dict[Face, np.ndarray] = {}
        next_id = 0
        for face in ALL_FACES:
            arr = np.empty((n, n), dtype=np.int32)
            for r in range(n):
                for c in range(n):
                    arr[r, c] = next_id
                    next_id += 1
            self.sticker_ids[face] = arr

    def clone(self) -> "Cube":
        other = Cube.__new__(Cube)
        other.n = self.n
        other.colors = {f: arr.copy() for f, arr in self.colors.items()}
        other.sticker_ids = {f: arr.copy() for f, arr in self.sticker_ids.items()}
        return other

    def is_solved(self) -> bool:
        """Every face is monochromatic. NOT compared against a fixed canonical
        array: on an even-N cube there is no fixed center piece, so which
        color ends up on which face is the solver's free choice, not a
        constraint of the puzzle.
        """
        return all(np.all(arr == arr[0, 0]) for arr in self.colors.values())

    def apply(self, move: Move) -> None:
        n = self.n
        axis = face_axis(move.face)
        quarter_turns = (move.turns * face_normal_sign(move.face)) % 4
        if quarter_turns == 0:
            return

        depths = frozenset(range(n)) if move.is_rotation else frozenset(
            layer_depth(move.face, layer_number, n) for layer_number in move.layer_numbers
        )
        relocations = _relocations_for(n, axis, depths, quarter_turns)

        new_colors = {f: arr.copy() for f, arr in self.colors.items()}
        new_ids = {f: arr.copy() for f, arr in self.sticker_ids.items()}
        for src_face, src_r, src_c, dst_face, dst_r, dst_c in relocations:
            new_colors[dst_face][dst_r, dst_c] = self.colors[src_face][src_r, src_c]
            new_ids[dst_face][dst_r, dst_c] = self.sticker_ids[src_face][src_r, src_c]
        self.colors = new_colors
        self.sticker_ids = new_ids

    def apply_algorithm(self, moves: list[Move]) -> None:
        for move in moves:
            self.apply(move)
