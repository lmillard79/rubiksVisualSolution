"""Generic restricted breadth-first search, used to drive every solver stage
that has the shape "move a few identifiable pieces into target slots without
disturbing what's already placed" (centers, edge-pairing, cross, F2L).

The key design point: deduplication is keyed on a caller-supplied *compact*
encoding of just the pieces that matter for this search, not on full cube
state. Two different full-cube states that agree on the tracked pieces are
the same node as far as this search cares, which is what keeps the reachable
space small instead of exploding combinatorially with every irrelevant piece
the scramble disturbed.

`solve_pieces_incrementally` is the piece-tracking specialization actually
used by every stage: it takes `PieceId`s directly rather than opaque
GoalTest/EncodeState closures, so that placing the Nth piece while keeping
0..N-1 solved costs one combined position scan per search node instead of N
separate per-piece scans - that constant factor matters a lot once N gets
past a handful (see the design notes on why the naive closure-per-piece
version was too slow to use).
"""

from __future__ import annotations

from collections import deque
from typing import Callable, Hashable

from ..moves import Move
from ..pieces import PieceId, PieceRegistry
from ..state import Cube
from .types import SolveStep

GoalTest = Callable[[Cube], bool]
EncodeState = Callable[[Cube], Hashable]
Target = tuple[GoalTest, EncodeState]


def restricted_search(
    cube: Cube,
    goal_test: GoalTest,
    encode_state: EncodeState,
    allowed_moves: list[Move],
    max_depth: int,
) -> list[Move] | None:
    """Shortest move sequence (using only `allowed_moves`) that makes
    `goal_test` true, up to `max_depth`, or None if none exists within that
    depth. BFS, so any solution found is depth-minimal.
    """
    if goal_test(cube):
        return []

    visited = {encode_state(cube)}
    queue = deque([(cube.clone(), [])])

    while queue:
        current, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for move in allowed_moves:
            candidate = current.clone()
            candidate.apply(move)
            if goal_test(candidate):
                return path + [move]
            key = encode_state(candidate)
            if key in visited:
                continue
            visited.add(key)
            queue.append((candidate, path + [move]))

    return None


def _reconstruct_bidirectional(forward_state: dict, backward_state: dict, meet_key: Hashable) -> list[Move]:
    forward_moves: list[Move] = []
    key = meet_key
    while forward_state[key][0] is not None:
        parent_key, move, _ = forward_state[key]
        forward_moves.append(move)
        key = parent_key
    forward_moves.reverse()

    backward_moves: list[Move] = []
    key = meet_key
    while backward_state[key][0] is not None:
        parent_key, move, _ = backward_state[key]
        backward_moves.append(move)
        key = parent_key

    return forward_moves + backward_moves


def bidirectional_search(
    cube: Cube,
    solved_ref: Cube,
    encode_state: EncodeState,
    allowed_moves: list[Move],
    max_depth: int,
) -> list[Move] | None:
    """Like `restricted_search`, but for the specific (and, for this project,
    universal) case where the goal is "encode_state(cube) equals
    encode_state(solved_ref)": explores forward from `cube` AND backward from
    `solved_ref` simultaneously (using each move's inverse on the backward
    side), stopping as soon as both sides reach a common encode_state.

    This is sound, not an approximation, for a fact specific to how cube
    moves work: a move is a permutation of *positions* that doesn't depend on
    what's currently in them. So if a forward path and a backward path both
    reach some state with the same tracked-piece encoding, concatenating
    them is guaranteed to carry the *actual* tracked stickers from `cube` all
    the way to their positions in `solved_ref`, regardless of what either
    path's untracked stickers happened to be doing along the way.

    The payoff is depth, not branching: meeting in the middle for a
    depth-d solution costs roughly 2*b^(d/2) instead of b^d, which is the
    difference between tractable and not once several pieces are locked in
    and dedup on the full combined state barely collapses anything (see the
    module docstring) - i.e. exactly the case that made plain
    `restricted_search` hang on later F2L pieces.
    """
    start_key = encode_state(cube)
    goal_key = encode_state(solved_ref)
    if start_key == goal_key:
        return []

    forward_state: dict[Hashable, tuple] = {start_key: (None, None, cube.clone())}
    backward_state: dict[Hashable, tuple] = {goal_key: (None, None, solved_ref.clone())}
    forward_frontier = [start_key]
    backward_frontier = [goal_key]
    inverse_moves = [(m, m.inverse()) for m in allowed_moves]

    depth_used = 0
    while depth_used < max_depth and forward_frontier and backward_frontier:
        expand_forward = len(forward_frontier) <= len(backward_frontier)
        if expand_forward:
            new_frontier = []
            for key in forward_frontier:
                _, _, base = forward_state[key]
                for move in allowed_moves:
                    candidate = base.clone()
                    candidate.apply(move)
                    ckey = encode_state(candidate)
                    if ckey in forward_state:
                        continue
                    forward_state[ckey] = (key, move, candidate)
                    if ckey in backward_state:
                        return _reconstruct_bidirectional(forward_state, backward_state, ckey)
                    new_frontier.append(ckey)
            forward_frontier = new_frontier
        else:
            new_frontier = []
            for key in backward_frontier:
                _, _, base = backward_state[key]
                for move, inverse in inverse_moves:
                    candidate = base.clone()
                    candidate.apply(inverse)
                    ckey = encode_state(candidate)
                    if ckey in backward_state:
                        continue
                    # `move` (not `inverse`) is what carries ckey's cube
                    # forward to key's cube - that's the direction
                    # reconstruction needs.
                    backward_state[ckey] = (key, move, candidate)
                    if ckey in forward_state:
                        return _reconstruct_bidirectional(forward_state, backward_state, ckey)
                    new_frontier.append(ckey)
            backward_frontier = new_frontier
        depth_used += 1

    return None


def piece_solved_target(registry: PieceRegistry, piece_id: PieceId, solved_ref: Cube) -> Target:
    """A Target for 'this piece is at its solved position and orientation'."""
    target_state = registry.piece_state(solved_ref, piece_id)

    def goal_test(cube: Cube) -> bool:
        return registry.piece_state(cube, piece_id) == target_state

    def encode_state(cube: Cube) -> Hashable:
        return registry.piece_state(cube, piece_id)

    return goal_test, encode_state


def solve_incrementally(
    cube: Cube,
    targets: list[Target],
    allowed_moves: list[Move],
    max_depth: int,
) -> list[Move] | None:
    """Generic version of the incremental pattern, for a caller with its own
    GoalTest/EncodeState closures. Prefer `solve_pieces_incrementally` when
    tracking PieceRegistry pieces (i.e. almost always) - this generic form
    re-scans once per locked target per node, which is fine for a couple of
    targets but not for a long chain.
    """
    solution: list[Move] = []
    working = cube.clone()
    locked: list[Target] = []

    for goal_test, encode_state in targets:
        locked = locked + [(goal_test, encode_state)]

        def combined_goal(c: Cube, locked=locked) -> bool:
            return all(g(c) for g, _ in locked)

        def combined_encode(c: Cube, locked=locked) -> Hashable:
            return tuple(e(c) for _, e in locked)

        step = restricted_search(working, combined_goal, combined_encode, allowed_moves, max_depth)
        if step is None:
            return None
        working.apply_algorithm(step)
        solution.extend(step)

    return solution


class PieceStep:
    """One step of an incremental piece-placement search: place `piece_id`,
    searching with `allowed_moves` up to `max_depth`. A tight, slot-relevant
    `allowed_moves` set (rather than always reaching for every move on the
    cube) is what keeps later steps fast - see the module docstring's note
    on why untargeted move sets blow up once several pieces are locked in.

    `stage`/`label` travel with the step (rather than being passed
    separately to `solve_pieces_incrementally`) specifically so that steps
    from *different* stages - e.g. cross's edges and F2L's corners/edges -
    can be concatenated into one call. That matters for correctness, not
    just labeling: every piece placed in a single call is protected as a
    "must stay solved" constraint for every step after it, so splitting
    cross and F2L into two separate calls would silently stop protecting
    cross while F2L runs.
    """

    __slots__ = ("piece_id", "allowed_moves", "max_depth", "stage", "label")

    def __init__(self, piece_id: PieceId, allowed_moves: list[Move], max_depth: int, stage: str = "", label: str = ""):
        self.piece_id = piece_id
        self.allowed_moves = allowed_moves
        self.max_depth = max_depth
        self.stage = stage
        self.label = label


def combined_piece_state_fn(registry: PieceRegistry, piece_ids: list[PieceId]):
    """A hashable encode/goal function reading exactly where each of
    `piece_ids` currently sits (position + orientation). Public because
    reduction stages that need to combine piece-exact tracking with other
    conditions (e.g. edge-pairing also protecting the centers stage's
    color-exact result) drive `bidirectional_search` directly with a
    composite of this and their own state function, rather than going
    through `solve_pieces_incrementally`.
    """
    sticker_order = [sid for pid in piece_ids for sid in registry.stickers_of_piece[pid]]

    def state_of(cube: Cube) -> tuple:
        located = registry.sticker_locations(cube, sticker_order)
        offset = 0
        state = []
        for pid in piece_ids:
            k = len(registry.stickers_of_piece[pid])
            state.append(tuple(located[sid] for sid in sticker_order[offset:offset + k]))
            offset += k
        return tuple(state)

    return state_of


def solve_pieces_incrementally(
    cube: Cube,
    registry: PieceRegistry,
    solved_ref: Cube,
    steps: list[PieceStep],
    fallback_tiers: list[tuple[list[Move], int]] | None = None,
) -> list[SolveStep] | None:
    """Place each step's piece at its solved_ref position, in order, without
    disturbing previously-placed pieces - the shared shape behind centers,
    edge-pairing, cross, and F2L. Returns one labeled `SolveStep` per piece
    placed (using that PieceStep's own `stage`/`label`), so a visualizer can
    show which piece and why, or None if any step fails.

    Steps from more than one logical stage (e.g. cross's edges followed by
    F2L's corners/edges) can and should be concatenated into a single
    `steps` list/call when later stages must not disturb earlier ones -
    every piece placed becomes a "stay solved" constraint for every step
    after it *within this call*, so splitting them into separate calls
    silently drops that protection across the split (this was a real bug
    here, not a hypothetical one - solve3.py originally called this once
    for cross and once for F2L, so F2L was free to disturb the cross).

    Both the meeting condition and the dedup key require *every* locked-in
    piece to be correct, so this is exact: no solution is ever missed
    because of an overly-coarse dedup key (see `bidirectional_search` for
    why that's sound here specifically, not just an optimization). That used
    to be too slow once more than a handful of pieces were locked in, for
    two compounding reasons, both now fixed: `Cube.apply`/
    `PieceRegistry.sticker_locations` were re-deriving sticker positions
    from scratch on every BFS node (fixed by the incremental
    `Cube.position_of` index and the cached move-relocation table in
    state.py), and plain one-directional BFS pays for the *full* solution
    depth in branching^depth (fixed by searching from both ends at once -
    see `bidirectional_search`). A step's own tight `allowed_moves` (e.g.
    U + 2 slot faces for F2L) still matters - smaller branching is always
    cheaper - and `fallback_tiers` is a small escalating ladder tried only
    if that tight set isn't enough (the piece is buried somewhere those
    moves can't reach), widening before it deepens.
    """
    solve_steps: list[SolveStep] = []
    working = cube.clone()
    locked: list[PieceId] = []

    for step in steps:
        locked = locked + [step.piece_id]
        goal_state = combined_piece_state_fn(registry, locked)

        move_step = bidirectional_search(working, solved_ref, goal_state, step.allowed_moves, step.max_depth)
        if move_step is None and fallback_tiers:
            for tier_moves, tier_depth in fallback_tiers:
                move_step = bidirectional_search(working, solved_ref, goal_state, tier_moves, tier_depth)
                if move_step is not None:
                    break
        if move_step is None:
            return None
        working.apply_algorithm(move_step)
        solve_steps.append(SolveStep(stage=step.stage, description=step.label, moves=move_step, pieces=[step.piece_id]))

    return solve_steps
