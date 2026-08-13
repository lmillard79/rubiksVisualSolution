"""Move notation: parsing and representation.

Grammar (defined explicitly rather than reusing community shorthand, which
disagrees across sources about what lowercase/'w' means - see geometry.py's
module docstring and the project plan for why):

    MOVE   := [NUMBER] FACE [w] [SUFFIX]   |   ROTATION [SUFFIX]
    FACE   := U | D | L | R | F | B
    ROTATION := x | y | z                    whole-cube rotation
    SUFFIX := '' (CW quarter) | '2' (half) | ''' (CCW quarter)
    NUMBER + [no w]  -> that ONE inner layer alone, no outer, e.g. 2R
    NUMBER + w       -> outer NUMBER layers together, e.g. 3Rw
    [no NUMBER] + w  -> outer 2 layers together (WCA default wide width), e.g. Rw
    [no NUMBER, no w] -> outer layer only, e.g. R

`M`, `E`, `S` (odd-cube middle slices) are deliberately not supported - there
is no single middle layer on an even-sized cube.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .constants import Face

_ROTATION_FACE = {"x": Face.R, "y": Face.U, "z": Face.F}  # rotation reuses that face's axis/sign
_FACE_TO_ROTATION_LETTER = {face: letter for letter, face in _ROTATION_FACE.items()}
_SUFFIX_TURNS = {"": 1, "2": 2, "'": 3}

_TOKEN_RE = re.compile(r"^(\d*)([UDLRFBxyz])(w?)(2|'?)$")


@dataclass(frozen=True)
class Move:
    face: Face
    layer_numbers: tuple[int, ...]  # 1-indexed, counted inward from `face`; unused for rotations
    turns: int                       # 1 = CW quarter, 2 = half, 3 = CCW quarter
    is_rotation: bool = False

    def inverse(self) -> "Move":
        return Move(self.face, self.layer_numbers, 4 - self.turns, self.is_rotation)

    def __str__(self) -> str:
        suffix = {1: "", 2: "2", 3: "'"}[self.turns]
        if self.is_rotation:
            return f"{_FACE_TO_ROTATION_LETTER[self.face]}{suffix}"
        letter = self.face.value
        n_layers = len(self.layer_numbers)
        if n_layers == 1:
            layer_number = self.layer_numbers[0]
            prefix = "" if layer_number == 1 else str(layer_number)
            return f"{prefix}{letter}{suffix}"
        prefix = "" if n_layers == 2 else str(n_layers)
        return f"{prefix}{letter}w{suffix}"


def parse_move(token: str) -> Move:
    match = _TOKEN_RE.match(token)
    if not match:
        raise ValueError(f"unrecognized move token: {token!r}")
    width_num, letter, wide_flag, suffix = match.groups()
    turns = _SUFFIX_TURNS[suffix]

    if letter in _ROTATION_FACE:
        if width_num or wide_flag:
            raise ValueError(f"whole-cube rotation cannot take a layer width: {token!r}")
        return Move(face=_ROTATION_FACE[letter], layer_numbers=(), turns=turns, is_rotation=True)

    face = Face(letter)
    if width_num and not wide_flag:
        layer_numbers = (int(width_num),)          # bare inner layer, e.g. 2R
    elif wide_flag:
        width = int(width_num) if width_num else 2  # e.g. Rw -> 2, 3Rw -> 3
        layer_numbers = tuple(range(1, width + 1))
    else:
        layer_numbers = (1,)                          # plain outer turn
    return Move(face=face, layer_numbers=layer_numbers, turns=turns)


def parse_algorithm(text: str) -> list[Move]:
    return [parse_move(tok) for tok in text.split()]


def format_algorithm(moves: list[Move]) -> str:
    return " ".join(str(m) for m in moves)
