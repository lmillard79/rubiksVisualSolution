"""Scramble a 3x3x3, solve it (cross -> F2L -> OLL -> PLL), then open the
interactive step-through viewer.

Controls in the viewer window:
    Right / Left   step one move forward / back
    Up / Down      jump to the next / previous stage
    Home / End     jump to the very start / end
    Space          play / pause an auto-advancing run through the solve

Usage:
    python scripts/demo.py               # random scramble, opens the viewer
    python scripts/demo.py --seed 1 --no-show
"""

from __future__ import annotations

import argparse
import random
import time

import matplotlib.pyplot as plt

from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.solver.threexthree.solve3 import solve_3x3
from cube.state import Cube
from cube.viz.playback import Playback
from cube.viz.render import draw_net


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="scramble RNG seed, for a repeatable scramble")
    parser.add_argument("--no-show", action="store_true", help="save PNGs instead of opening the interactive viewer")
    args = parser.parse_args()

    n = 3
    rng = random.Random(args.seed)

    scrambled = Cube(n)
    scramble = random_scramble(n, rng=rng)
    scrambled.apply_algorithm(scramble)
    print(f"Scrambled {n}x{n}x{n} ({len(scramble)} moves):")
    print(" ".join(str(move) for move in scramble))

    registry = PieceRegistry(n)
    t0 = time.time()
    solution = solve_3x3(scrambled, registry)
    elapsed = time.time() - t0

    if solution is None:
        print(f"\nSolve failed after {elapsed:.1f}s - please report this.")
        draw_net(scrambled, title=f"Scrambled {n}x{n}x{n} (solve failed)")
        plt.show()
        return

    print(f"\nSolved in {len(solution.moves)} moves ({elapsed:.1f}s):")
    by_stage: dict[str, int] = {}
    for step in solution.steps:
        by_stage[step.stage] = by_stage.get(step.stage, 0) + len(step.moves)
    for stage, count in by_stage.items():
        print(f"  {stage}: {count} moves")

    if args.no_show:
        draw_net(scrambled, title=f"Scrambled {n}x{n}x{n}")
        solved = scrambled.clone()
        solved.apply_algorithm(solution.moves)
        draw_net(solved, title=f"Solved - {n}x{n}x{n}")
        for i, fig_num in enumerate(plt.get_fignums(), start=1):
            plt.figure(fig_num).savefig(f"demo_{i}.png", dpi=150, bbox_inches="tight")
            print(f"Saved demo_{i}.png")
    else:
        print("\nOpening interactive viewer - Right/Left step, Up/Down jump stage, Space play/pause.")
        playback = Playback(scrambled, solution)
        plt.show()


if __name__ == "__main__":
    main()
