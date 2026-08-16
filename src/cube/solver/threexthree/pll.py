"""2-look PLL (well, "last look"): permute the last layer's already-oriented
4 edges and 4 corners into their correct slots. Once this is done the whole
cube is solved, so the goal here is simply `cube.is_solved()`.

Same approach as OLL: a small set of well-known "permutation trigger"
algorithms, each verified structurally safe (`is_last_layer_only`) at import
time, searched over together with U rotations via `lastlayer.meta_search`.
Which combination of named PLL algorithms is actually *sufficient* to reach
every one of the 21 standard PLL cases by repetition/rotation is exactly the
kind of thing this project's design notes say not to trust from memory -
tests/test_threexthree_stages.py checks this empirically against real
F2L+OLL-solved cubes, not just a handful of hand-picked cases.
"""

from __future__ import annotations

from ...moves import Move, parse_algorithm
from ...state import Cube
from .lastlayer import is_last_layer_only, meta_search

T_PERM = parse_algorithm("R U R' U' R' F R2 U' R' U' R U R' F'")
Y_PERM = parse_algorithm("F R U' R' U' R U R' F' R U R' U' R' F R F'")
UA_PERM = parse_algorithm("R U' R U R U R U' R' U' R2")

for _alg in (T_PERM, Y_PERM, UA_PERM):
    assert is_last_layer_only(_alg), f"PLL trigger disturbs more than the last layer: {_alg}"

_U, _U2, _UPRIME = parse_algorithm("U"), parse_algorithm("U2"), parse_algorithm("U'")
_META_MOVES = [_U, _U2, _UPRIME, T_PERM, Y_PERM, UA_PERM]

_MAX_META_DEPTH = 6


def solve_pll(cube: Cube) -> list[Move] | None:
    return meta_search(cube, lambda c: c.is_solved(), _META_MOVES, _MAX_META_DEPTH)
