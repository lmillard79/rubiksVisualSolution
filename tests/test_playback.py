"""Headless test of Playback's stepping/navigation logic - forces Agg so
this never tries to open a window, and drives the same methods a real key
press would call rather than simulating actual GUI events."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from cube.moves import parse_algorithm
from cube.solver.types import SolveStep, Solution
from cube.state import Cube
from cube.viz.playback import Playback


def _sample_solution():
    steps = [
        SolveStep(stage="Cross", description="edge 1 of 4", moves=parse_algorithm("R U")),
        SolveStep(stage="Cross", description="edge 2 of 4", moves=parse_algorithm("F")),
        SolveStep(stage="F2L", description="corner 1 of 4", moves=parse_algorithm("U R U'")),
    ]
    return Solution(steps=steps)


@pytest.fixture
def playback():
    cube = Cube(3)
    cube.apply_algorithm(parse_algorithm("R U F' L2"))
    pb = Playback(cube, _sample_solution())
    yield pb
    plt.close(pb.fig)


def test_starts_at_zero_showing_scrambled_state(playback):
    assert playback.index == 0
    assert playback.cube.colors.keys() == playback.start_cube.colors.keys()


def test_step_forward_and_backward(playback):
    playback.step_forward()
    assert playback.index == 1
    playback.step_forward()
    assert playback.index == 2
    playback.step_backward()
    assert playback.index == 1


def test_step_forward_past_end_is_clamped(playback):
    for _ in range(20):
        playback.step_forward()
    assert playback.index == len(playback.moves)
    playback.step_forward()
    assert playback.index == len(playback.moves)


def test_step_backward_past_start_is_clamped(playback):
    playback.step_backward()
    assert playback.index == 0


def test_jump_to_replays_correctly(playback):
    playback.jump_to(3)
    check = playback.start_cube.clone()
    check.apply_algorithm(playback.moves[:3])
    for face in check.colors:
        assert (playback.cube.colors[face] == check.colors[face]).all()


def test_jump_to_next_and_previous_stage(playback):
    # moves = [R, U | F | U, R, U'] -> owners = [0,0, 1, 2,2,2]
    assert playback.move_owner == [0, 0, 1, 2, 2, 2]

    playback.jump_to_next_stage()
    assert playback.index == 2  # end of stage 0
    playback.jump_to_next_stage()
    assert playback.index == 3  # end of stage 1
    playback.jump_to_next_stage()
    assert playback.index == 6  # end of stage 2 (all moves)

    playback.jump_to_previous_stage()
    assert playback.index == 3
    playback.jump_to_previous_stage()
    assert playback.index == 2
    playback.jump_to_previous_stage()
    assert playback.index == 0


def test_home_and_end_keys(playback):
    playback.on_key(type("Event", (), {"key": "end"})())
    assert playback.index == len(playback.moves)
    playback.on_key(type("Event", (), {"key": "home"})())
    assert playback.index == 0


def test_arrow_keys(playback):
    playback.on_key(type("Event", (), {"key": "right"})())
    assert playback.index == 1
    playback.on_key(type("Event", (), {"key": "left"})())
    assert playback.index == 0


def test_status_string_reflects_current_step(playback):
    assert "Scrambled" in playback._status_string()
    playback.step_forward()
    assert "Cross" in playback._status_string()
    playback.jump_to(len(playback.moves))
    assert "Solved" in playback._status_string() or "Done" in playback._status_string()


def test_toggle_play_starts_and_stops_without_error(playback):
    playback.toggle_play()
    assert playback.playing is True
    playback.toggle_play()
    assert playback.playing is False
