import random

import pytest

from cube.moves import parse_algorithm
from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.state import Cube


@pytest.mark.parametrize("n,expected", [(3, {"corner": 8, "edge": 12, "center": 6}), (4, {"corner": 8, "edge": 24, "center": 24})])
def test_known_piece_kind_counts(n, expected):
    registry = PieceRegistry(n)
    counts = {kind: len(registry.pieces_of_kind(kind)) for kind in expected}
    assert counts == expected


def test_every_sticker_belongs_to_exactly_one_piece(solvable_n):
    registry = PieceRegistry(solvable_n)
    all_sticker_ids = [sid for ids in registry.stickers_of_piece.values() for sid in ids]
    assert len(all_sticker_ids) == len(set(all_sticker_ids))
    assert len(all_sticker_ids) == 6 * solvable_n * solvable_n


def test_piece_positions_on_solved_cube_matches_its_own_stickers(solvable_n):
    registry = PieceRegistry(solvable_n)
    cube = Cube(solvable_n)
    for piece_id, sticker_ids in registry.stickers_of_piece.items():
        positions = registry.piece_positions(cube, piece_id)
        found_ids = {int(cube.sticker_ids[ref.face][ref.row, ref.col]) for ref in positions}
        assert found_ids == set(sticker_ids)


def test_piece_positions_track_a_piece_through_a_scramble(solvable_n):
    registry = PieceRegistry(solvable_n)
    cube = Cube(solvable_n)
    rng_moves = parse_algorithm("R U R' U' R U R' U'")
    cube.apply_algorithm(rng_moves)
    corner_id = registry.pieces_of_kind("corner")[0]
    positions = registry.piece_positions(cube, corner_id)
    # a corner always has exactly 3 stickers, wherever it ends up
    assert len(positions) == 3
    faces = {ref.face for ref in positions}
    assert len(faces) == 3


def test_random_scramble_length_and_no_immediate_repeat(solvable_n):
    scramble = random_scramble(solvable_n, length=50, rng=random.Random(0))
    assert len(scramble) == 50
    for a, b in zip(scramble, scramble[1:]):
        assert a.face != b.face


def test_random_scramble_is_reversible_to_solved(solvable_n):
    scramble = random_scramble(solvable_n, length=30, rng=random.Random(5))
    cube = Cube(solvable_n)
    cube.apply_algorithm(scramble)
    cube.apply_algorithm([m.inverse() for m in reversed(scramble)])
    assert cube.is_solved()
