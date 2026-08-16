"""Building block for letting the 3x3-stage solver (cross/F2L/OLL/PLL,
written purely in terms of a genuine Cube(3) and plain notation) eventually
run on a *reduced* NxN cube: one whose centers are built and whose wing
pieces are all paired, so it behaves like a 3x3 one size up.

NOT YET WIRED IN to solve3.py or anywhere else - reusing the 3x3-stage
solver against a real reduced cube also needs a piece-registry adapter that
groups wing pairs and same-face centers into single logical pieces (so
cross.py/f2l.py's PieceRegistry-based tracking sees 8 corners / 12 edges / 6
centers instead of the reduced cube's real 8 / 24 / 4*6), which isn't built
yet either. This module is just the move-translation half.

The mapping here is direct: on a reduced cube, every logical layer (U, D, L,
R, F, B) is two physical layers thick (the outer face plus its paired-up
neighbor) - so every face letter in a plain-notation algorithm becomes that
face's wide form when applied to the bigger cube. There's no special case
for U: OLL/PLL's top-layer turns would need to carry the paired second layer
with them exactly like every other stage's turns do, or the pairing they
depend on falls apart. (The two 4x4-specific parity fixes, not yet
implemented, are a different thing entirely - they deliberately use a bare
*inner* slice, not a wide move, because desyncing the outer and inner layers
is the whole point of a parity fix.)
"""

from __future__ import annotations

from ...moves import Move


def translate_move_to_wide(move: Move, width: int) -> Move:
    """A plain-notation Move, reinterpreted as covering the outer `width`
    layers together. Whole-cube rotations pass through unchanged - they
    already move every layer."""
    if move.is_rotation:
        return move
    return Move(face=move.face, layer_numbers=tuple(range(1, width + 1)), turns=move.turns)


def translate_algorithm_to_wide(moves: list[Move], width: int) -> list[Move]:
    return [translate_move_to_wide(move, width) for move in moves]
