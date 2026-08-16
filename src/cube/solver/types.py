"""Labeled solve output: not just a move list, but which stage and which
pieces each move belongs to - what lets a step-through visualizer show *why*
a move is happening, not just that it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..moves import Move
from ..pieces import PieceId


@dataclass
class SolveStep:
    stage: str  # e.g. "Cross", "F2L", "OLL", "PLL", "Centers", "Edge Pairing", "Parity"
    description: str  # e.g. "placing edge 3 of 4"
    moves: list[Move]
    pieces: list[PieceId] = field(default_factory=list)  # for highlighting


@dataclass
class Solution:
    steps: list[SolveStep]

    @property
    def moves(self) -> list[Move]:
        """Flattened move list, for single-move stepping."""
        return [move for step in self.steps for move in step.moves]

    @property
    def move_owner(self) -> list[int]:
        """move_owner[i] is the index into `steps` that moves[i] belongs to."""
        owners = []
        for step_index, step in enumerate(self.steps):
            owners.extend([step_index] * len(step.moves))
        return owners
