"""OLL/PLL correctness, verified against real cross+F2L-solved cubes rather
than hand-picked cases - see solver/threexthree/lastlayer.py and oll.py/
pll.py's module docstrings for why that matters here (sourced algorithms,
not derived).
"""

import functools
import random

import numpy as np
import pytest

from cube.constants import Face
from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.solver.search import solve_pieces_incrementally
from cube.solver.threexthree.cross import cross_steps
from cube.solver.threexthree.f2l import f2l_fallback_tiers, f2l_steps
from cube.solver.threexthree.lastlayer import is_last_layer_only
from cube.solver.threexthree.oll import ANTI_SUNE, EDGE_ORIENT_TRIGGER, SUNE, corners_oriented, edges_oriented, solve_oll
from cube.solver.threexthree.pll import T_PERM, UA_PERM, Y_PERM, solve_pll
from cube.solver.threexthree.solve3 import solve_3x3
from cube.state import Cube

N = 3
SEEDS = range(10)


@pytest.fixture(scope="module")
def registry():
    return PieceRegistry(N)


@pytest.fixture(scope="module")
def solved_ref():
    return Cube(N)


@functools.lru_cache(maxsize=None)
def _f2l_solved_cube_cached(seed):
    # Module-scope fixtures aren't visible to an lru_cache'd free function,
    # so this rebuilds its own (cheap - PieceRegistry/Cube construction is
    # not what's slow here). Caching is purely to avoid re-running F2L's
    # multi-second search 3x per seed across this file's test functions.
    registry = PieceRegistry(N)
    solved_ref = Cube(N)
    cube = Cube(N)
    cube.apply_algorithm(random_scramble(N, length=25, rng=random.Random(seed)))
    steps = cross_steps(registry, solved_ref) + f2l_steps(registry, solved_ref)
    solve_steps = solve_pieces_incrementally(cube, registry, solved_ref, steps, fallback_tiers=f2l_fallback_tiers())
    assert solve_steps is not None, f"seed={seed}: F2L failed (test setup, not the thing under test)"
    cube.apply_algorithm([move for s in solve_steps for move in s.moves])
    return cube


def _f2l_solved_cube(registry, solved_ref, seed):
    return _f2l_solved_cube_cached(seed).clone()


@pytest.mark.parametrize("alg", [EDGE_ORIENT_TRIGGER, SUNE, ANTI_SUNE, T_PERM, Y_PERM, UA_PERM])
def test_last_layer_triggers_are_structurally_safe(alg):
    """Every OLL/PLL trigger must only touch the last layer. This is also
    asserted at import time in oll.py/pll.py; re-checking here makes the
    property visible as an ordinary test result, not just an import-time
    assertion someone could miss."""
    assert is_last_layer_only(alg)


@pytest.mark.parametrize("seed", SEEDS)
def test_oll_orients_last_layer_without_disturbing_f2l(registry, solved_ref, seed):
    cube = _f2l_solved_cube(registry, solved_ref, seed)
    before_d = cube.colors[Face.D].copy()
    before_sides = {f: cube.colors[f][1:, :].copy() for f in (Face.L, Face.F, Face.R, Face.B)}

    oll_moves = solve_oll(cube)
    assert oll_moves is not None, f"seed={seed}: OLL search failed"
    cube.apply_algorithm(oll_moves)

    assert edges_oriented(cube)
    assert corners_oriented(cube)
    assert np.array_equal(cube.colors[Face.D], before_d)
    for face, before in before_sides.items():
        assert np.array_equal(cube.colors[face][1:, :], before)


@pytest.mark.parametrize("seed", SEEDS)
def test_pll_after_oll_solves_the_cube(registry, solved_ref, seed):
    cube = _f2l_solved_cube(registry, solved_ref, seed)
    oll_moves = solve_oll(cube)
    assert oll_moves is not None
    cube.apply_algorithm(oll_moves)

    pll_moves = solve_pll(cube)
    assert pll_moves is not None, f"seed={seed}: PLL search failed"
    cube.apply_algorithm(pll_moves)
    assert cube.is_solved()


@pytest.mark.parametrize("seed", SEEDS)
def test_solve_3x3_end_to_end(registry, solved_ref, seed):
    cube = Cube(N)
    cube.apply_algorithm(random_scramble(N, length=25, rng=random.Random(seed)))

    solution = solve_3x3(cube, registry)
    assert solution is not None, f"seed={seed}: full solve failed"

    check = cube.clone()
    check.apply_algorithm(solution.moves)
    assert check.is_solved()

    # Solution bookkeeping (moves/move_owner) must stay internally consistent.
    # Note: a step can legitimately contribute zero moves (a piece that was
    # already correctly placed by an earlier step's side effect needs none
    # to "place" it), so not every step index need appear in move_owner.
    assert len(solution.moves) == len(solution.move_owner)
    assert solution.move_owner == sorted(solution.move_owner)
    assert set(solution.move_owner) <= set(range(len(solution.steps)))
