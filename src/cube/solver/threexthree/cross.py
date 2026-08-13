"""Cross: place the 4 D-layer edges (D-color facing D, side color matching
the fixed side center). Search-driven, one edge at a time - see search.py's
module docstring for why this shape of problem suits BFS over hand-typed
cases.
"""

from __future__ import annotations

from ...constants import ALL_FACES, Face
from ...moves import parse_move
from ...pieces import PieceRegistry
from ...state import Cube
from ..search import PieceStep

ALL_BASIC_MOVES = [parse_move(f"{f.value}{s}") for f in ALL_FACES for s in ("", "2", "'")]


def cross_steps(registry: PieceRegistry, solved_ref: Cube, max_depth: int = 8) -> list[PieceStep]:
    d_edges = [pid for pid in registry.pieces_of_kind("edge") if Face.D in registry.piece_faces(solved_ref, pid)]
    return [PieceStep(pid, ALL_BASIC_MOVES, max_depth) for pid in d_edges]
