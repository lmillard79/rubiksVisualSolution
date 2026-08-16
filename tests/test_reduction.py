"""4x4 reduction correctness: centers built, then edges paired without
disturbing the centers. Slow (each scramble costs tens of seconds - see
solver/reduction/centers.py and edges.py's notes on why bidirectional
search still isn't fast here the way it is for the 3x3 stages), so this is
deliberately just 3 seeds - enough to catch a real regression, not a
statistical sweep. Run a larger manual sweep before trusting this broadly.
"""

import random

import pytest

from cube.constants import ALL_FACES, SOLVED_COLOR_OF_FACE
from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.solver.reduction.centers import center_cells, solve_centers
from cube.solver.reduction.edges import solve_edge_pairing, wing_pairs
from cube.state import Cube

N = 4
SEEDS = range(3)


@pytest.fixture(scope="module")
def registry():
    return PieceRegistry(N)


@pytest.fixture(scope="module")
def solved_ref():
    return Cube(N)


def _centers_solved(cube):
    cells = center_cells(N)
    return all(
        all(int(cube.colors[f][r, c]) == SOLVED_COLOR_OF_FACE[f] for r, c in cells) for f in ALL_FACES
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_centers_build_to_solid_blocks(seed):
    cube = Cube(N)
    cube.apply_algorithm(random_scramble(N, length=40, rng=random.Random(seed)))

    steps = solve_centers(cube)
    assert steps is not None, f"seed={seed}: center building failed"

    cube.apply_algorithm([move for s in steps for move in s.moves])
    assert _centers_solved(cube)


@pytest.mark.parametrize("seed", SEEDS)
def test_edge_pairing_pairs_all_12_without_disturbing_centers(registry, solved_ref, seed):
    cube = Cube(N)
    cube.apply_algorithm(random_scramble(N, length=40, rng=random.Random(seed)))

    center_steps = solve_centers(cube)
    assert center_steps is not None, f"seed={seed}: center building failed (test setup)"
    cube.apply_algorithm([move for s in center_steps for move in s.moves])

    edge_steps = solve_edge_pairing(cube, registry)
    assert edge_steps is not None, f"seed={seed}: edge pairing failed"
    cube.apply_algorithm([move for s in edge_steps for move in s.moves])

    assert _centers_solved(cube), "edge pairing disturbed the centers"
    for wing_a, wing_b in wing_pairs(registry, solved_ref):
        assert registry.piece_state(cube, wing_a) == registry.piece_state(solved_ref, wing_a)
        assert registry.piece_state(cube, wing_b) == registry.piece_state(solved_ref, wing_b)
