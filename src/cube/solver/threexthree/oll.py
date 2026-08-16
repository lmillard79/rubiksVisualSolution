"""2-look OLL: orient the last layer's 4 edges, then its 4 corners, so U
shows a single solid color. Permutation (which piece sits in which slot)
isn't fixed here - PLL does that next.

Rather than a large hand-typed case table (full 1-look OLL has 57 cases),
this uses 3 well-known "trigger" algorithms plus `lastlayer.meta_search`
over {U rotations, triggers}: each trigger's safety is verified structurally
at import time (`is_last_layer_only`), and it's a standard, well-established
cubing fact that repeating a single orientation-changing trigger from
different U-angles reaches every case - verified here empirically (see
tests/test_threexthree_stages.py) against real F2L-solved cubes rather than
just assumed.
"""

from __future__ import annotations

from ...constants import Face, SOLVED_COLOR_OF_FACE
from ...moves import Move, parse_algorithm
from ...state import Cube
from .lastlayer import U_CORNER_CELLS, U_EDGE_CELLS, is_last_layer_only, meta_search

EDGE_ORIENT_TRIGGER = parse_algorithm("F R U R' U' F'")
SUNE = parse_algorithm("R U R' U R U2 R'")
ANTI_SUNE = parse_algorithm("R U2 R' U' R U' R'")

for _alg in (EDGE_ORIENT_TRIGGER, SUNE, ANTI_SUNE):
    assert is_last_layer_only(_alg), f"OLL trigger disturbs more than the last layer: {_alg}"

_U, _U2, _UPRIME = parse_algorithm("U"), parse_algorithm("U2"), parse_algorithm("U'")
_EDGE_META_MOVES = [_U, _U2, _UPRIME, EDGE_ORIENT_TRIGGER]
_CORNER_META_MOVES = [_U, _U2, _UPRIME, SUNE, ANTI_SUNE]

_MAX_META_DEPTH = 6


def edges_oriented(cube: Cube) -> bool:
    target = SOLVED_COLOR_OF_FACE[Face.U]
    return all(int(cube.colors[Face.U][r, c]) == target for r, c in U_EDGE_CELLS)


def corners_oriented(cube: Cube) -> bool:
    target = SOLVED_COLOR_OF_FACE[Face.U]
    return all(int(cube.colors[Face.U][r, c]) == target for r, c in U_CORNER_CELLS)


def solve_oll(cube: Cube) -> list[Move] | None:
    """Full moves list to orient the last layer, or None if it couldn't
    (shouldn't happen on a genuine post-F2L cube - see the module tests)."""
    edge_moves = meta_search(cube, edges_oriented, _EDGE_META_MOVES, _MAX_META_DEPTH)
    if edge_moves is None:
        return None

    working = cube.clone()
    working.apply_algorithm(edge_moves)

    corner_moves = meta_search(working, corners_oriented, _CORNER_META_MOVES, _MAX_META_DEPTH)
    if corner_moves is None:
        return None

    return edge_moves + corner_moves
