"""Correctness tests for the search-driven early stages (cross, F2L). Uses a
modest number of scrambles rather than the plan's full "hundreds" sweep -
each solve costs a few seconds (see solver/search.py's bidirectional_search
notes), so this is deliberately scoped to stay fast for routine runs; a
larger sweep is worth running manually before a release, not on every
`pytest`.
"""

import random

import pytest

from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.solver.search import solve_pieces_incrementally
from cube.solver.threexthree.cross import cross_steps
from cube.solver.threexthree.f2l import f2l_fallback_tiers, f2l_steps
from cube.state import Cube

N = 3
SEEDS = range(15)


@pytest.fixture(scope="module")
def registry():
    return PieceRegistry(N)


@pytest.fixture(scope="module")
def solved_ref():
    return Cube(N)


def _scrambled(seed):
    cube = Cube(N)
    cube.apply_algorithm(random_scramble(N, length=25, rng=random.Random(seed)))
    return cube


@pytest.mark.parametrize("seed", SEEDS)
def test_cross_solves_all_four_d_edges(registry, solved_ref, seed):
    cube = _scrambled(seed)
    steps = cross_steps(registry, solved_ref)
    solve_steps = solve_pieces_incrementally(cube, registry, solved_ref, steps)
    assert solve_steps is not None
    assert len(solve_steps) == len(steps)

    cube.apply_algorithm([move for s in solve_steps for move in s.moves])
    for step in steps:
        assert registry.piece_state(cube, step.piece_id) == registry.piece_state(solved_ref, step.piece_id)


@pytest.mark.parametrize("seed", SEEDS)
def test_cross_then_f2l_solves_first_two_layers(registry, solved_ref, seed):
    cube = _scrambled(seed)
    steps = cross_steps(registry, solved_ref) + f2l_steps(registry, solved_ref)
    solve_steps = solve_pieces_incrementally(cube, registry, solved_ref, steps, fallback_tiers=f2l_fallback_tiers())
    assert solve_steps is not None, f"seed={seed} failed to solve cross+F2L"

    cube.apply_algorithm([move for s in solve_steps for move in s.moves])

    # Every cross/F2L target piece must be exactly at its solved position -
    # i.e. the first two layers are done, even though is_solved() would
    # still be False (last layer isn't touched by this stage).
    for step in steps:
        assert registry.piece_state(cube, step.piece_id) == registry.piece_state(solved_ref, step.piece_id)
