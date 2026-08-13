"""Face and color constants shared by the whole engine."""

from enum import Enum


class Face(str, Enum):
    U = "U"
    D = "D"
    F = "F"
    B = "B"
    L = "L"
    R = "R"


# Net layout used everywhere a face needs a fixed reading order.
ALL_FACES = (Face.U, Face.L, Face.F, Face.R, Face.B, Face.D)

# Color ids 0-5. Names follow the standard WCA color scheme.
WHITE, YELLOW, GREEN, BLUE, ORANGE, RED = range(6)

COLOR_NAMES = {
    WHITE: "white",
    YELLOW: "yellow",
    GREEN: "green",
    BLUE: "blue",
    ORANGE: "orange",
    RED: "red",
}

# Physical opposite-color pairs (never change under any move).
OPPOSITE_COLOR = {
    WHITE: YELLOW, YELLOW: WHITE,
    GREEN: BLUE, BLUE: GREEN,
    ORANGE: RED, RED: ORANGE,
}

# Canonical color a solved cube shows on each face. Solver stages target
# this mapping; is_solved() itself does NOT depend on it (see state.py).
SOLVED_COLOR_OF_FACE = {
    Face.U: WHITE,
    Face.D: YELLOW,
    Face.F: GREEN,
    Face.B: BLUE,
    Face.L: ORANGE,
    Face.R: RED,
}
