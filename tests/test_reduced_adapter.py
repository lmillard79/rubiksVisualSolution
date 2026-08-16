from cube.moves import parse_algorithm, parse_move
from cube.solver.threexthree.reduced_adapter import translate_algorithm_to_wide, translate_move_to_wide


def test_plain_face_move_becomes_wide():
    wide = translate_move_to_wide(parse_move("R"), width=2)
    assert wide == parse_move("Rw")


def test_turn_count_and_face_preserved():
    for token in ("U2", "F'", "D"):
        move = parse_move(token)
        wide = translate_move_to_wide(move, width=2)
        assert wide.face == move.face
        assert wide.turns == move.turns


def test_rotation_passes_through_unchanged():
    rotation = parse_move("x")
    assert translate_move_to_wide(rotation, width=2) == rotation


def test_algorithm_translates_every_move():
    alg = parse_algorithm("R U R' U'")
    wide = translate_algorithm_to_wide(alg, width=2)
    assert [str(m) for m in wide] == ["Rw", "Uw", "Rw'", "Uw'"]


def test_width_three_for_a_hypothetical_bigger_reduction():
    wide = translate_move_to_wide(parse_move("F"), width=3)
    assert wide == parse_move("3Fw")
