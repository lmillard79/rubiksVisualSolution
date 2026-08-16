"""Scramble a 4x4x4 and run the reduction method (centers -> edge pairing),
then open the interactive step-through viewer. This does NOT yet finish the
solve (the reduced cube isn't solved like a 3x3 yet, and parity isn't
handled) - it shows the reduction stage, which is the 4x4-specific part.

Usage:
    python scripts/demo4x4.py               # random scramble, opens viewer
    python scripts/demo4x4.py --seed 1 --no-show
"""

from __future__ import annotations

import argparse
import random
import time

import matplotlib.pyplot as plt

from cube.pieces import PieceRegistry
from cube.scramble import random_scramble
from cube.solver.reduction.centers import solve_centers
from cube.solver.reduction.edges import solve_edge_pairing
from cube.solver.types import Solution
from cube.state import Cube
from cube.viz.playback import Playback
from cube.viz.render import draw_net


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="scramble RNG seed, for a repeatable scramble")
    parser.add_argument("--no-show", action="store_true", help="save PNGs instead of opening the interactive viewer")
    args = parser.parse_args()

    n = 4
    rng = random.Random(args.seed)

    scrambled = Cube(n)
    scramble = random_scramble(n, rng=rng)
    scrambled.apply_algorithm(scramble)
    print(f"Scrambled {n}x{n}x{n} ({len(scramble)} moves):")
    print(" ".join(str(move) for move in scramble))

    registry = PieceRegistry(n)
    working = scrambled.clone()

    print("\nBuilding centers (usually well under a minute, occasionally longer)...", flush=True)
    t0 = time.time()
    center_steps = solve_centers(working)
    if center_steps is None:
        print("Center building failed - please report this.")
        return
    print(f"  done in {time.time() - t0:.1f}s, {sum(len(s.moves) for s in center_steps)} moves")
    working.apply_algorithm([m for s in center_steps for m in s.moves])

    print("Pairing edges (this is the slow part - can take several minutes, occasionally", flush=True)
    print("well past 10 on an unlucky scramble; it will finish, just be patient)...", flush=True)
    t0 = time.time()
    edge_steps = solve_edge_pairing(working, registry)
    if edge_steps is None:
        print("Edge pairing failed - please report this.")
        return
    print(f"  done in {time.time() - t0:.1f}s, {sum(len(s.moves) for s in edge_steps)} moves")

    solution = Solution(steps=center_steps + edge_steps)
    print(f"\nReduction complete: {len(solution.moves)} total moves.")
    print("(The reduced cube isn't fully solved yet - that needs the 3x3-stage")
    print(" solver run on the reduction plus parity handling, not wired in yet.)")

    if args.no_show:
        draw_net(scrambled, title="Scrambled 4x4x4")
        final = scrambled.clone()
        final.apply_algorithm(solution.moves)
        draw_net(final, title="After reduction (centers + edges)")
        for i, fig_num in enumerate(plt.get_fignums(), start=1):
            plt.figure(fig_num).savefig(f"demo4x4_{i}.png", dpi=150, bbox_inches="tight")
            print(f"Saved demo4x4_{i}.png")
    else:
        print("\nOpening interactive viewer - Right/Left step, Up/Down jump stage, Space play/pause.")
        playback = Playback(scrambled, solution)
        plt.show()


if __name__ == "__main__":
    main()
