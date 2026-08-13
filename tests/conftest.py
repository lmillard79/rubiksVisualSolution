import numpy as np
import pytest

from cube.constants import ALL_FACES
from cube.state import Cube


@pytest.fixture(params=[2, 3, 4, 5])
def n(request):
    return request.param


@pytest.fixture(params=[3, 4])
def solvable_n(request):
    """Sizes the solver actually targets (see plan: engine is general, solver isn't)."""
    return request.param


def solved_cube(n):
    return Cube(n)


def colors_snapshot(cube):
    return {f: cube.colors[f].copy() for f in ALL_FACES}


def same_colors(a, b):
    return all(np.array_equal(a[f], b[f]) for f in ALL_FACES)
