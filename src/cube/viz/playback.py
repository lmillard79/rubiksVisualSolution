"""Interactive keyboard-driven stepping through a Solution.

Right/Left: step one move forward/back. Up/Down: jump to the next/previous
stage boundary. Home/End: jump to start/end. Space: play/pause.

Rebuilds the cube from the stored scrambled start and replays moves up to
the current index on every step, rather than caching intermediate states -
deliberately: a single move-apply is well under a millisecond at this scale
(see state.py), so replay-from-scratch is simplest, always correct, and
fast enough, while a snapshot cache would only add invalidation bugs.
"""

from __future__ import annotations

from ..solver.types import Solution
from ..state import Cube
from .render import draw_net, refresh_net


class Playback:
    def __init__(self, scrambled_cube: Cube, solution: Solution, ax=None):
        self.start_cube = scrambled_cube.clone()
        self.solution = solution
        self.moves = solution.moves
        self.move_owner = solution.move_owner
        self.index = 0
        self.playing = False
        self.timer = None

        self.cube = scrambled_cube.clone()
        self.fig, self.ax, self.images = draw_net(self.cube)
        self.ax.set_title(self._status_string())
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)

    def _status_string(self) -> str:
        total = len(self.moves)
        if self.index == 0:
            return f"Scrambled - {total} moves to solve - press -> to start"
        if self.index >= total:
            return "Solved!" if self.cube.is_solved() else "Done (not solved - check solver)"
        step_index = self.move_owner[self.index - 1]
        step = self.solution.steps[step_index]
        move = self.moves[self.index - 1]
        return f"{step.stage}: {step.description}  |  move {self.index}/{total}: {move}"

    def _rebuild(self) -> None:
        self.cube = self.start_cube.clone()
        self.cube.apply_algorithm(self.moves[: self.index])
        refresh_net(self.cube, self.images)
        self.ax.set_title(self._status_string())
        self.fig.canvas.draw_idle()

    def jump_to(self, index: int) -> None:
        index = max(0, min(len(self.moves), index))
        if index == self.index:
            return
        self.index = index
        self._rebuild()

    def step_forward(self) -> None:
        self.jump_to(self.index + 1)

    def step_backward(self) -> None:
        self.jump_to(self.index - 1)

    def jump_to_next_stage(self) -> None:
        total = len(self.moves)
        if self.index >= total:
            return
        current_stage = self.move_owner[self.index]
        i = self.index
        while i < total and self.move_owner[i] == current_stage:
            i += 1
        self.jump_to(i)

    def jump_to_previous_stage(self) -> None:
        if self.index <= 0:
            return
        i = self.index - 1
        current_stage = self.move_owner[i]
        while i > 0 and self.move_owner[i - 1] == current_stage:
            i -= 1
        self.jump_to(i)

    def toggle_play(self) -> None:
        if self.playing:
            self._stop_playing()
            return
        if self.index >= len(self.moves):
            self.jump_to(0)
        self.playing = True
        self.timer = self.fig.canvas.new_timer(interval=350)
        self.timer.add_callback(self._play_tick)
        self.timer.start()

    def _stop_playing(self) -> None:
        self.playing = False
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

    def _play_tick(self) -> None:
        if self.index >= len(self.moves):
            self._stop_playing()
            return
        self.step_forward()

    def on_key(self, event) -> None:
        key = event.key
        if key == "right":
            self.step_forward()
        elif key == "left":
            self.step_backward()
        elif key == "up":
            self.jump_to_next_stage()
        elif key == "down":
            self.jump_to_previous_stage()
        elif key == "home":
            self.jump_to(0)
        elif key == "end":
            self.jump_to(len(self.moves))
        elif key == " ":
            self.toggle_play()
