"""Top-level 3x3-stage solve: cross -> F2L -> OLL -> PLL, as a single
labeled Solution a visualizer can step through stage by stage or move by
move.
"""

from __future__ import annotations

from ...pieces import PieceRegistry
from ...state import Cube
from ..search import solve_pieces_incrementally
from ..types import Solution, SolveStep
from .cross import cross_steps
from .f2l import f2l_fallback_tiers, f2l_steps
from .oll import solve_oll
from .pll import solve_pll


def solve_3x3(cube: Cube, registry: PieceRegistry | None = None) -> Solution | None:
    """Solve a genuine 3x3 cube (or a reduced NxN treated as one via plain
    notation - see reduced_adapter.py for how that gets translated back to
    real moves on the bigger cube). Returns None if any stage fails, which
    shouldn't happen on a well-formed input (see the empirical tests)."""
    n = cube.n
    if registry is None:
        registry = PieceRegistry(n)
    solved_ref = Cube(n)

    working = cube.clone()

    # Cross and F2L are placed via ONE call, not two: every piece placed
    # earlier in a `solve_pieces_incrementally` call is protected as a
    # "must stay solved" constraint for every step after it *within that
    # call* - splitting cross and F2L into separate calls would silently
    # stop protecting the cross while F2L runs (this was a real bug here).
    first_two_layers = solve_pieces_incrementally(
        working, registry, solved_ref,
        cross_steps(registry, solved_ref) + f2l_steps(registry, solved_ref),
        fallback_tiers=f2l_fallback_tiers(),
    )
    if first_two_layers is None:
        return None
    steps: list[SolveStep] = list(first_two_layers)
    working.apply_algorithm([move for s in first_two_layers for move in s.moves])

    oll_moves = solve_oll(working)
    if oll_moves is None:
        return None
    steps.append(SolveStep(stage="OLL", description="orienting the last layer", moves=oll_moves))
    working.apply_algorithm(oll_moves)

    pll_moves = solve_pll(working)
    if pll_moves is None:
        return None
    steps.append(SolveStep(stage="PLL", description="permuting the last layer", moves=pll_moves))
    working.apply_algorithm(pll_moves)

    return Solution(steps=steps)
