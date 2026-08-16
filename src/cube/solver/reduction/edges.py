"""Edge pairing (4x4 reduction, stage 2): for each of the 12 edges, place
both of its wing pieces at their correct positions - which, since a wing's
correct position is immediately adjacent to its partner wing with matching
colors, achieves "pairing" and "placement" in the same step, rather than
pairing anywhere and sorting out placement separately (the more common
human technique, which needs extra bookkeeping this project doesn't need
given search already handles exact placement well - see cross/F2L).

Must also protect the centers the previous stage built, which piece-based
tracking alone doesn't cover (same-colored center stickers are
interchangeable, so they're not individually tracked pieces - see
centers.py). Rather than extending solve_pieces_incrementally itself, this
drives bidirectional_search directly with a composite state function:
piece-exact for the wings being placed, color-exact for all 6 centers,
checked together.
"""

from __future__ import annotations

from ...constants import ALL_FACES, Face
from ...moves import Move
from ...pieces import PieceId, PieceRegistry
from ...state import Cube
from ..search import bidirectional_search, combined_piece_state_fn
from ..types import SolveStep
from .centers import ALL_OUTER_AND_INNER_SLICE_MOVES, center_cells


def wing_pairs(registry: PieceRegistry, solved_ref: Cube) -> list[tuple[PieceId, PieceId]]:
    """The 12 (wing_a, wing_b) partner pairs - two wing pieces are partners
    if they touch the same 2 faces in the solved reference, which is
    exactly when they show the same 2-color pattern (color is fixed per
    sticker, so a matching color pattern *is* the pairing condition, not
    just a proxy for it)."""
    groups: dict[frozenset[Face], list[PieceId]] = {}
    for pid in registry.pieces_of_kind("edge"):
        key = frozenset(registry.piece_faces(solved_ref, pid))
        groups.setdefault(key, []).append(pid)
    return [(pids[0], pids[1]) for pids in groups.values()]


def _centers_state_fn(n: int):
    cells = center_cells(n)

    def state_of(cube: Cube) -> tuple:
        return tuple(tuple(int(cube.colors[f][r, c]) for r, c in cells) for f in ALL_FACES)

    return state_of


def edge_pairing_fallback_tiers() -> list[tuple[list[Move], int]]:
    """Same escalating-depth rationale as centers/F2L: with several wings
    (and all 6 centers) already locked in, dedup barely collapses, so a
    too-shallow primary depth just gets slower and slower rather than
    failing outright - only paying for a deeper search when a shallow one
    doesn't land keeps the common case fast.
    """
    return [
        (ALL_OUTER_AND_INNER_SLICE_MOVES, 8),
        (ALL_OUTER_AND_INNER_SLICE_MOVES, 10),
    ]


def solve_edge_pairing(
    cube: Cube,
    registry: PieceRegistry,
    allowed_moves: list[Move] | None = None,
    max_depth: int = 5,
    fallback_tiers: list[tuple[list[Move], int]] | None = None,
) -> list[SolveStep] | None:
    n = cube.n
    if allowed_moves is None:
        allowed_moves = ALL_OUTER_AND_INNER_SLICE_MOVES
    if fallback_tiers is None:
        fallback_tiers = edge_pairing_fallback_tiers()
    solved_ref = Cube(n)
    centers_state = _centers_state_fn(n)

    working = cube.clone()
    steps: list[SolveStep] = []
    locked: list[PieceId] = []
    pairs = wing_pairs(registry, solved_ref)

    for pair_index, (wing_a, wing_b) in enumerate(pairs):
        for piece_id in (wing_a, wing_b):
            locked = locked + [piece_id]
            pieces_state = combined_piece_state_fn(registry, locked)

            def state_of(c: Cube, pieces_state=pieces_state) -> tuple:
                return (centers_state(c), pieces_state(c))

            moves = bidirectional_search(working, solved_ref, state_of, allowed_moves, max_depth)
            if moves is None:
                for tier_moves, tier_depth in fallback_tiers:
                    moves = bidirectional_search(working, solved_ref, state_of, tier_moves, tier_depth)
                    if moves is not None:
                        break
            if moves is None:
                return None
            working.apply_algorithm(moves)
            steps.append(
                SolveStep(
                    stage="Edge Pairing",
                    description=f"pairing edge {pair_index + 1} of {len(pairs)}",
                    moves=moves,
                    pieces=[piece_id],
                )
            )

    return steps
