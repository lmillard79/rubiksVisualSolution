"""Center building (4x4 reduction, stage 1): group each face's (n-2)^2
center stickers into a solid block matching SOLVED_COLOR_OF_FACE.

Centers of the same color are interchangeable - there's no fixed "true
center" on an even-sized cube, so unlike every other stage this tracks
*color at each center cell*, not piece identity via PieceRegistry. That's
also why it can use `bidirectional_search` directly with a custom
color-reading encode function instead of going through
`solve_pieces_incrementally`.

Placed one *cell* at a time (24 steps: 4 per face x 6 faces), not one face
(4 cells) at a time: tracking 4 cells' colors together as a single search
target has the same failure mode F2L had tracking multiple pieces together
- dedup barely collapses once several cells are already locked in, so
node count tracks branching^depth almost directly, and it stalled for
minutes on just the 3rd face in testing. One cell at a time keeps each
step's target small (6 possible colors) the way F2L's one-piece-at-a-time
kept its target small (a couple dozen states).
"""

from __future__ import annotations

from ...constants import ALL_FACES, Face
from ...moves import Move, parse_move
from ...state import Cube
from ..search import bidirectional_search
from ..types import SolveStep

ALL_OUTER_AND_INNER_SLICE_MOVES = [
    parse_move(f"{prefix}{face.value}{suffix}")
    for face in ALL_FACES
    for prefix in ("", "2")
    for suffix in ("", "2", "'")
]


def center_cells(n: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(1, n - 1) for c in range(1, n - 1)]


def _colors_at(cube: Cube, cells: list[tuple[Face, int, int]]) -> tuple:
    return tuple(int(cube.colors[f][r, c]) for f, r, c in cells)


def centers_fallback_tiers() -> list[tuple[list[Move], int]]:
    return [
        (ALL_OUTER_AND_INNER_SLICE_MOVES, 8),
        (ALL_OUTER_AND_INNER_SLICE_MOVES, 10),
    ]


def solve_centers(
    cube: Cube,
    allowed_moves: list[Move] | None = None,
    max_depth: int = 6,
    fallback_tiers: list[tuple[list[Move], int]] | None = None,
) -> list[SolveStep] | None:
    n = cube.n
    if allowed_moves is None:
        allowed_moves = ALL_OUTER_AND_INNER_SLICE_MOVES
    if fallback_tiers is None:
        fallback_tiers = centers_fallback_tiers()
    cells = center_cells(n)
    solved_ref = Cube(n)

    working = cube.clone()
    steps: list[SolveStep] = []
    locked_cells: list[tuple[Face, int, int]] = []

    for face in ALL_FACES:
        for cell_index, (r, c) in enumerate(cells):
            locked_cells = locked_cells + [(face, r, c)]

            def state_of(cube_: Cube, locked_cells=locked_cells) -> tuple:
                return _colors_at(cube_, locked_cells)

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
                    stage="Centers",
                    description=f"building {face.value} center, sticker {cell_index + 1} of {len(cells)}",
                    moves=moves,
                )
            )

    return steps
