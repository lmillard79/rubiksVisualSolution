"""Shared helpers for the last-layer stages (OLL, PLL).

Once cross + F2L are done, the remaining 8 unsolved pieces (4 edges, 4
corners) are guaranteed to all be sitting somewhere in the U layer: 12 of
the 20 non-center pieces are already correctly placed, each occupying a
distinct position, so by elimination the other 8 must occupy the 8
remaining positions - which are exactly the U layer's. That's what lets
recognition here work directly off U-layer sticker colors rather than
needing PieceRegistry's general piece-tracking machinery.

U's own grid (n=3): row 0 = nearest F, row 2 = nearest B (see geometry.py's
FACE_FRAME derivation); col 0 = nearest L, col 2 = nearest R.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from ...constants import ALL_FACES, Face
from ...moves import Move
from ...state import Cube

U_EDGE_CELLS = [(0, 1), (1, 0), (1, 2), (2, 1)]  # UF, UL, UR, UB
U_CORNER_CELLS = [(0, 0), (0, 2), (2, 0), (2, 2)]  # UFL, UFR, UBL, UBR


def is_last_layer_only(algorithm: list[Move]) -> bool:
    """Structural safety check: applied to a solved cube, does this
    algorithm leave D and the bottom 2 rows of every side face untouched?
    That's the defining property of a valid OLL/PLL algorithm (only the U
    layer + the top row of each side face may change) - checked directly
    rather than trusted, since these algorithms come from memory/references
    that the project's own design notes explicitly distrust until verified.
    """
    before = Cube(3)
    after = Cube(3)
    after.apply_algorithm(algorithm)

    if not np.array_equal(after.colors[Face.D], before.colors[Face.D]):
        return False
    for face in (Face.L, Face.F, Face.R, Face.B):
        if not np.array_equal(after.colors[face][1:, :], before.colors[face][1:, :]):
            return False
    return True


def _colors_key(cube: Cube) -> tuple:
    return tuple(tuple(int(v) for v in cube.colors[f].flat) for f in ALL_FACES)


def meta_search(cube: Cube, goal_test, meta_moves: list[list[Move]], max_meta_depth: int) -> list[Move] | None:
    """BFS where each "move" is a whole (already verified-safe) algorithm,
    not a single quarter turn. Used for OLL/PLL instead of raw-move search:
    a handful of known triggers plus U rotations are enough to reach every
    case by repetition (standard, well-established cubing fact, but this
    project verifies rather than assumes it - see the OLL/PLL modules'
    empirical tests), and searching over whole triggers keeps the space
    tiny (a few meta-moves ^ a handful of meta-depth) regardless of how
    many raw quarter-turns each trigger itself contains. Dedup is keyed on
    full cube color state (cheap here - the search space is tiny by
    construction), not a piece subset, so this never needs to separately
    track that cross/F2L stay intact: `is_last_layer_only` already
    guarantees that structurally for every meta-move used.
    """
    if goal_test(cube):
        return []

    visited = {_colors_key(cube)}
    queue = deque([(cube.clone(), [], 0)])

    while queue:
        current, path, depth = queue.popleft()
        if depth >= max_meta_depth:
            continue
        for meta in meta_moves:
            candidate = current.clone()
            candidate.apply_algorithm(meta)
            new_path = path + meta
            if goal_test(candidate):
                return new_path
            key = _colors_key(candidate)
            if key in visited:
                continue
            visited.add(key)
            queue.append((candidate, new_path, depth + 1))

    return None
