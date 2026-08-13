"""Random scramble generation."""

from __future__ import annotations

import random

from .constants import Face
from .moves import Move, parse_move

_SUFFIXES = ("", "2", "'")
_OUTER_TOKENS = [f"{face.value}{suffix}" for face in Face for suffix in _SUFFIXES]


def _wide_tokens_for(n: int) -> list[str]:
    if n < 4:
        return []
    return [f"{face.value}w{suffix}" for face in Face for suffix in _SUFFIXES]


def random_scramble(n: int, length: int | None = None, rng: random.Random | None = None) -> list[Move]:
    """A random sequence of outer (and, for n>=4, wide) turns. Filters
    immediate same-face repeats so the scramble doesn't waste moves undoing
    itself. Default lengths are reasonable non-competition sizes, not
    WCA-exact scramble lengths.
    """
    if rng is None:
        rng = random.Random()
    if length is None:
        length = 25 if n == 3 else 40 + 5 * max(0, n - 4)

    pool = _OUTER_TOKENS + _wide_tokens_for(n)
    moves: list[Move] = []
    last_face = None
    while len(moves) < length:
        move = parse_move(rng.choice(pool))
        if move.face == last_face:
            continue
        moves.append(move)
        last_face = move.face
    return moves
