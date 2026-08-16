"""F2L (first two layers): for each D-layer corner, place the corner and its
adjacent second-layer edge. Search-driven, slot by slot, restricted to U plus
the slot's own 2 side faces - matching standard human F2L practice (D is
never used, and algorithms essentially always stay within the current slot's
2 faces plus U), which keeps branching small enough to stay fast even with
many pieces already locked in (see search.py's module docstring on why an
untargeted move set blows up combinatorially instead). The full move set is
kept as a fallback for the rare case that genuinely needs another face.
"""

from __future__ import annotations

from ...constants import Face
from ...moves import Move, parse_move
from ...pieces import PieceId, PieceRegistry
from ...state import Cube
from ..search import PieceStep
from .cross import ALL_BASIC_MOVES

_U_MOVES = [parse_move(f"U{s}") for s in ("", "2", "'")]


def _moves_for_faces(faces: set[Face]) -> list[Move]:
    return [parse_move(f"{f.value}{s}") for f in faces for s in ("", "2", "'")]


def _second_layer_edge_between(registry: PieceRegistry, solved_ref: Cube, faces: set[Face]) -> PieceId:
    for pid in registry.pieces_of_kind("edge"):
        if registry.piece_faces(solved_ref, pid) == faces:
            return pid
    raise ValueError(f"no second-layer edge found between {faces}")


def f2l_steps(registry: PieceRegistry, solved_ref: Cube, max_depth: int = 8) -> list[PieceStep]:
    d_corners = [pid for pid in registry.pieces_of_kind("corner") if Face.D in registry.piece_faces(solved_ref, pid)]
    total = len(d_corners)
    steps: list[PieceStep] = []
    for slot_index, corner_pid in enumerate(d_corners):
        side_faces = registry.piece_faces(solved_ref, corner_pid) - {Face.D}
        slot_moves = _U_MOVES + _moves_for_faces(side_faces)
        edge_pid = _second_layer_edge_between(registry, solved_ref, side_faces)
        steps.append(PieceStep(corner_pid, slot_moves, max_depth, stage="F2L",
                                label=f"inserting corner {slot_index + 1} of {total}"))
        steps.append(PieceStep(edge_pid, slot_moves, max_depth, stage="F2L",
                                label=f"inserting edge {slot_index + 1} of {total}"))
    return steps


def f2l_fallback_tiers() -> list[tuple[list[Move], int]]:
    """An escalating ladder tried only when a slot's own 2 faces aren't
    enough (the piece is buried in a not-yet-relevant slot). Widens the move
    set before it deepens - more likely to actually unstick a buried piece -
    and depth grows generously here: with `bidirectional_search` (see
    search.py), a depth-d search costs roughly 2*branching^(d/2), not
    branching^d, so doubling the depth budget is cheap in a way it never was
    for one-directional BFS. The failure mode this is guarding against is
    depth, not branching: a too-shallow cap can't be searched around no
    matter how fast each node is, it just always returns "no solution".
    """
    all_but_d = _moves_for_faces({Face.U, Face.L, Face.F, Face.R, Face.B})
    return [
        (all_but_d, 10),
        (all_but_d, 12),
        (ALL_BASIC_MOVES, 10),
        (ALL_BASIC_MOVES, 12),
    ]
