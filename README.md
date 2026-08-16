# RubikSolver

An NxN Rubik's cube engine, a from-scratch reduction-method solver, and a
step-through visualizer that renders the cube as an unfolded net - built to
develop intuition for *how* a cube gets solved, not just to produce an
answer.

## What works today

- **Cube engine** (`src/cube/`): move application, geometry, piece/orbit
  tracking, scrambling - generalized over cube size, verified for 3x3x3 and
  4x4x4.
- **Unfolded-net visualizer**: renders the cube as a flattened cross (U
  above F; L, F, R, B in a row; D below F), the same layout most cube tools
  use.
- **Full 3x3x3 solver** (cross -> F2L -> OLL -> PLL): reliably solves any
  scramble in a couple of seconds. Interactive step-through viewer included.
- **4x4x4 reduction** (center building + edge pairing): works and is
  verified correct, but is slow - a full reduction can take several minutes
  (see "Performance notes" below).

## Not done yet

- Finishing a reduced 4x4x4 like a 3x3x3 (the solver stages above are
  written for a genuine 3x3x3 - reusing them on a reduced 4x4x4 needs a
  translation layer that isn't wired up yet).
- The two 4x4-specific parity fixes (OLL parity, PLL parity).
- A CLI with size/scramble-string flags - each `scripts/*.py` is currently
  its own small entry point instead.

## Setup

```bash
pip install -e ".[dev]"
```

Needs Python 3.11+, numpy, and matplotlib (TkAgg backend recommended - it's
what ships with the standard python.org Windows installer).

## Usage

**Solve and step through a 3x3x3:**

```bash
python scripts/demo.py
```

Opens an interactive window. Controls:

| Key | Action |
|---|---|
| `->` / `<-` | step one move forward / back |
| `up` / `down` | jump to the next / previous stage (Cross, F2L, OLL, PLL) |
| `home` / `end` | jump to the very start / end |
| `space` | play / pause an auto-advancing run |

Use `--seed N` for a repeatable scramble, `--no-show` to save PNGs instead
of opening a window (useful when running headless).

**Run the 4x4x4 reduction:**

```bash
python scripts/demo4x4.py
```

Same controls, but stops after center-building and edge-pairing (see "Not
done yet" above) - you'll see the reduction happen, not a fully solved
cube. **This can take several minutes** - the reduction search is
correctness-verified but not yet fast (see below).

**Run the tests:**

```bash
python -m pytest tests/                        # fast suite (~a few minutes)
python -m pytest tests/test_reduction.py -v     # slow: 4x4 reduction, minutes per seed
```

## Performance notes

The solver is a generic search (`solver/search.py`) that places pieces one
at a time while protecting everything already placed, meeting in the middle
via `bidirectional_search` rather than a one-directional BFS - the
difference between roughly `2 * branching^(depth/2)` and `branching^depth`
in nodes explored, which is what makes the 3x3 stages fast (seconds) despite
using no hand-typed case tables beyond OLL/PLL's named triggers.

4x4 reduction (centers, edge pairing) uses the same machinery but is
slower, and - unlike F2L - the slowness *worsens* as more pieces get locked
in rather than leveling off: more pieces need protecting (24 wing stickers
+ 4 centers per face vs. F2L's 8 last-layer pieces), and the move set is
wider (36 moves, including bare inner-slice turns, vs. F2L's 9-18). In
testing, individual pieces late in edge-pairing took up to ~3 minutes each
in the worst case, which means a full reduction can run well past 10
minutes on an unlucky scramble. It's correct and it terminates (bounded by
the search's max-depth cutoff, never an infinite loop), just not fast - the
clearest next target if this project continues, likely needing either a
smarter admissible-heuristic search (IDA*) or hand-sourced setup algorithms
for edge pairing the way OLL/PLL use named triggers instead of blind search.

## Project layout

```
src/cube/
├── constants.py, geometry.py, state.py, moves.py   # engine core
├── pieces.py                                         # piece/orbit tracking
├── scramble.py
├── solver/
│   ├── search.py                                     # restricted_search, bidirectional_search
│   ├── types.py                                      # SolveStep, Solution
│   ├── threexthree/                                   # cross, F2L, OLL, PLL
│   └── reduction/                                     # centers, edge pairing
└── viz/
    ├── render.py                                      # static unfolded-net rendering
    └── playback.py                                    # interactive step-through viewer
scripts/
├── demo.py            # 3x3x3: scramble, solve, step through
└── demo4x4.py          # 4x4x4: scramble, reduce, step through
tests/
```
