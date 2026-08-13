from cube.moves import parse_algorithm, parse_move
from cube.pieces import PieceRegistry
from cube.solver.search import restricted_search
from cube.state import Cube

_BASIC_MOVES = [parse_move(f"{f}{s}") for f in "UDLRFB" for s in ("", "2", "'")]


def test_restricted_search_solves_a_single_displaced_edge(solvable_n):
    n = solvable_n
    registry = PieceRegistry(n)
    solved_state_of = {pid: registry.piece_state(Cube(n), pid) for pid in registry.pieces_of_kind("edge")}

    scrambled = Cube(n)
    scrambled.apply_algorithm(parse_algorithm("R U R' U' R U R' U'"))

    displaced = [pid for pid, state in solved_state_of.items() if registry.piece_state(scrambled, pid) != state]
    assert displaced, "expected the scramble to displace at least one edge"
    target = displaced[0]
    target_state = solved_state_of[target]

    def goal_test(cube):
        return registry.piece_state(cube, target) == target_state

    def encode_state(cube):
        return registry.piece_state(cube, target)

    solution = restricted_search(scrambled, goal_test, encode_state, _BASIC_MOVES, max_depth=8)

    assert solution is not None
    check = scrambled.clone()
    check.apply_algorithm(solution)
    assert goal_test(check)


def test_restricted_search_returns_none_when_unreachable_in_depth():
    n = 3
    registry = PieceRegistry(n)
    scrambled = Cube(n)
    scrambled.apply_algorithm(parse_algorithm("R U R' U' R U R' U'"))

    solved_state_of = {pid: registry.piece_state(Cube(n), pid) for pid in registry.pieces_of_kind("edge")}
    displaced = [pid for pid, state in solved_state_of.items() if registry.piece_state(scrambled, pid) != state]
    target = displaced[0]
    target_state = solved_state_of[target]

    def goal_test(cube):
        return registry.piece_state(cube, target) == target_state

    def encode_state(cube):
        return registry.piece_state(cube, target)

    solution = restricted_search(scrambled, goal_test, encode_state, _BASIC_MOVES, max_depth=0)
    assert solution is None


def test_restricted_search_on_already_solved_goal_returns_empty_list():
    n = 3
    registry = PieceRegistry(n)
    cube = Cube(n)
    target = registry.pieces_of_kind("edge")[0]
    target_state = registry.piece_state(cube, target)

    def goal_test(c):
        return registry.piece_state(c, target) == target_state

    def encode_state(c):
        return registry.piece_state(c, target)

    solution = restricted_search(cube, goal_test, encode_state, _BASIC_MOVES, max_depth=5)
    assert solution == []
