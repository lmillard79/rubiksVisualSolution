"""Algebraic sanity checks on the move engine. These are the gate the plan
calls out: geometry.py must pass all of these, for every size, before
anything else is built on top of it.
"""

import random

import numpy as np
import pytest

from cube.constants import ALL_FACES, Face, GREEN
from cube.moves import parse_algorithm, parse_move
from cube.state import Cube
from tests.conftest import colors_snapshot, same_colors

FACE_LETTERS = "UDLRFB"


@pytest.mark.parametrize("face", FACE_LETTERS)
def test_quarter_turn_order_four(n, face):
    cube = Cube(n)
    start = colors_snapshot(cube)
    for _ in range(4):
        cube.apply(parse_move(face))
    assert same_colors(colors_snapshot(cube), start)


@pytest.mark.parametrize("face", FACE_LETTERS)
def test_wide_turn_order_four(n, face):
    cube = Cube(n)
    start = colors_snapshot(cube)
    for _ in range(4):
        cube.apply(parse_move(f"{face}w"))
    assert same_colors(colors_snapshot(cube), start)


@pytest.mark.parametrize("face", FACE_LETTERS)
def test_bare_inner_layer_order_four(face):
    # only meaningful once there's a genuine inner layer distinct from both caps
    for n in (3, 4, 5):
        cube = Cube(n)
        start = colors_snapshot(cube)
        for _ in range(4):
            cube.apply(parse_move(f"2{face}"))
        assert same_colors(colors_snapshot(cube), start), f"n={n} face={face}"


@pytest.mark.parametrize("face", FACE_LETTERS)
def test_half_turn_is_two_quarters(n, face):
    a = Cube(n)
    a.apply(parse_move(f"{face}2"))
    b = Cube(n)
    b.apply(parse_move(face))
    b.apply(parse_move(face))
    assert same_colors(colors_snapshot(a), colors_snapshot(b))


@pytest.mark.parametrize("face", FACE_LETTERS)
def test_prime_is_inverse_of_cw(n, face):
    cube = Cube(n)
    start = colors_snapshot(cube)
    cube.apply(parse_move(face))
    cube.apply(parse_move(f"{face}'"))
    assert same_colors(colors_snapshot(cube), start)


def test_sledgehammer_order_six(n):
    cube = Cube(n)
    start = colors_snapshot(cube)
    alg = parse_algorithm("R U R' U'")
    for _ in range(6):
        cube.apply_algorithm(alg)
    assert same_colors(colors_snapshot(cube), start)


def test_opposite_faces_commute(n):
    a = Cube(n)
    a.apply_algorithm(parse_algorithm("U D"))
    b = Cube(n)
    b.apply_algorithm(parse_algorithm("D U"))
    assert same_colors(colors_snapshot(a), colors_snapshot(b))


def test_random_algorithm_composed_with_its_inverse_is_identity(n):
    rng = random.Random(1234 + n)
    pool = []
    for f in FACE_LETTERS:
        pool += [f, f + "2", f + "'"]
        pool += [f + "w", f + "w2", f + "w'"]
    alg = [parse_move(rng.choice(pool)) for _ in range(30)]
    inverse = [m.inverse() for m in reversed(alg)]

    cube = Cube(n)
    start = colors_snapshot(cube)
    cube.apply_algorithm(alg)
    cube.apply_algorithm(inverse)
    assert same_colors(colors_snapshot(cube), start)


def test_sticker_multiset_invariant_under_random_moves(n):
    rng = random.Random(99 + n)
    pool = []
    for f in FACE_LETTERS:
        pool += [f, f + "2", f + "'", f + "w", f + "w2", f + "w'"]
    cube = Cube(n)
    for _ in range(80):
        cube.apply(parse_move(rng.choice(pool)))
    all_colors = np.concatenate([cube.colors[f].ravel() for f in ALL_FACES])
    values, counts = np.unique(all_colors, return_counts=True)
    assert len(values) == 6
    assert all(count == n * n for count in counts)


def test_no_duplicate_or_lost_sticker_ids_under_random_moves(n):
    rng = random.Random(7 + n)
    pool = []
    for f in FACE_LETTERS:
        pool += [f, f + "2", f + "'", f + "w"]
    cube = Cube(n)
    all_ids_before = sorted(np.concatenate([cube.sticker_ids[f].ravel() for f in ALL_FACES]).tolist())
    for _ in range(80):
        cube.apply(parse_move(rng.choice(pool)))
    all_ids_after = sorted(np.concatenate([cube.sticker_ids[f].ravel() for f in ALL_FACES]).tolist())
    assert all_ids_before == all_ids_after


def test_r_sends_front_strip_to_up(n):
    """Ground-truth check, verified by hand during design: R (clockwise viewed
    from outside R) sends the F-colored strip to U, not the other way around."""
    cube = Cube(n)
    cube.apply(parse_move("R"))
    assert all(color == GREEN for color in cube.colors[Face.U][:, n - 1])


def test_u_sends_front_strip_to_left(n):
    """Second independent ground-truth check: U sends F -> L, so the GREEN
    (F's color) strip should land on L, not L's own original ORANGE."""
    cube = Cube(n)
    cube.apply(parse_move("U"))
    assert all(color == GREEN for color in cube.colors[Face.L][0, :])


@pytest.mark.parametrize("axis_letter", ["x", "y", "z"])
def test_whole_cube_rotation_order_four_and_stays_solved(n, axis_letter):
    cube = Cube(n)
    for _ in range(4):
        cube.apply(parse_move(axis_letter))
        assert cube.is_solved()
    assert same_colors(colors_snapshot(cube), colors_snapshot(Cube(n)))


def test_is_solved_true_only_when_every_face_monochromatic(n):
    cube = Cube(n)
    assert cube.is_solved()
    cube.apply(parse_move("R"))
    if n >= 2:
        assert not cube.is_solved()


def test_move_str_roundtrips_through_parser():
    tokens = ["R", "R2", "R'", "Rw", "Rw2", "Rw'", "3Rw", "2R", "3R", "x", "y2", "z'"]
    for token in tokens:
        move = parse_move(token)
        assert parse_move(str(move)) == move, f"{token} -> {move} -> {move!s} round-trip failed"
