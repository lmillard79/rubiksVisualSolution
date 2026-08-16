"""Piece (cubie) identity and orbit tracking, built once from a solved cube.

A "piece" is the set of stickers that physically sit on the same cubie.
Since every sticker's xyz *is* that cubie's grid coordinate (sticker_xyz in
geometry.py already places it there), pieces fall straight out of grouping
stickers by shared xyz on a solved cube - no separate hand-derived adjacency
needed. A cubie with 3 coordinates at an extreme (0 or n-1) is a corner (3
stickers), 2 extreme coordinates is an edge (2 stickers; called "wings" on
4x4+ once they need pairing, but structurally the same kind here), and 1
extreme coordinate is a center (1 sticker - on a 4x4 there's no fixed "true"
center, so each of the (n-2)^2 center stickers per face is its own piece).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .constants import ALL_FACES, Face
from .geometry import sticker_xyz
from .state import Cube

PieceId = int

_KIND_BY_STICKER_COUNT = {1: "center", 2: "edge", 3: "corner"}


@dataclass(frozen=True)
class StickerRef:
    face: Face
    row: int
    col: int


class PieceRegistry:
    def __init__(self, n: int):
        self.n = n
        solved = Cube(n)

        groups: dict[tuple[int, int, int], list[StickerRef]] = defaultdict(list)
        for face in ALL_FACES:
            for r in range(n):
                for c in range(n):
                    groups[sticker_xyz(face, r, c, n)].append(StickerRef(face, r, c))

        self.stickers_of_piece: dict[PieceId, list[int]] = {}
        self.kind_of_piece: dict[PieceId, str] = {}
        self.piece_of_sticker: dict[int, PieceId] = {}

        for piece_id, refs in enumerate(groups.values()):
            sticker_ids = [int(solved.sticker_ids[ref.face][ref.row, ref.col]) for ref in refs]
            self.stickers_of_piece[piece_id] = sticker_ids
            self.kind_of_piece[piece_id] = _KIND_BY_STICKER_COUNT[len(refs)]
            for sid in sticker_ids:
                self.piece_of_sticker[sid] = piece_id
        self.num_pieces = len(groups)

    def pieces_of_kind(self, kind: str) -> list[PieceId]:
        return [pid for pid, k in self.kind_of_piece.items() if k == kind]

    def piece_positions(self, cube: Cube, piece_id: PieceId) -> list[StickerRef]:
        """Where this piece's stickers currently are on `cube` (which may be
        scrambled). O(1) per sticker via `cube.position_of`, the reverse
        index Cube maintains incrementally - this is on the solver search's
        hot path (called on every BFS node), so it matters that this isn't a
        per-call O(n^2) re-scan.
        """
        return [StickerRef(*cube.position_of[sid]) for sid in self.stickers_of_piece[piece_id]]

    def sticker_locations(self, cube: Cube, sticker_ids) -> dict[int, StickerRef]:
        """Current location of each requested sticker id."""
        return {sid: StickerRef(*cube.position_of[sid]) for sid in sticker_ids}

    def piece_faces(self, cube: Cube, piece_id: PieceId) -> set[Face]:
        """Which faces this piece's stickers currently sit on (ignores exact
        row/col) - handy for identifying a piece by which faces it touches,
        e.g. "the edge between F and R", independent of orientation."""
        return {ref.face for ref in self.piece_positions(cube, piece_id)}

    def piece_state(self, cube: Cube, piece_id: PieceId) -> tuple[StickerRef, ...]:
        """Where each of this piece's stickers currently is, in the piece's own
        canonical sticker order - so this doubles as an orientation-aware,
        hashable encoding: two states are equal only if every one of the
        piece's stickers is in exactly the same place (not just the same set
        of cells, which would ignore twisted-in-place orientation).
        """
        sticker_ids = self.stickers_of_piece[piece_id]
        located = self.sticker_locations(cube, sticker_ids)
        return tuple(located[sid] for sid in sticker_ids)
