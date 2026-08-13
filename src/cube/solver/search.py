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
    """

    __slots__ = ("piece_id", "allowed_moves", "max_depth")

    def __init__(self, piece_id: PieceId, allowed_moves: list[Move], max_depth: int):
        self.piece_id = piece_id
        self.allowed_moves = allowed_moves
        self.max_depth = max_depth


def _combined_state_fn(registry: PieceRegistry, piece_ids: list[PieceId]):
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
    fallback_moves: list[Move] | None = None,
    fallback_max_depth: int | None = None,
) -> list[Move] | None:
    """Place each step's piece at its solved_ref position, in order, without
    disturbing previously-placed pieces - the shared shape behind centers,
    edge-pairing, cross, and F2L.

    The goal test always requires *every* locked-in piece to be correct, so
    the result is exact. Deduplication, however, is deliberately keyed on
    just the piece actively being searched for, not the whole locked set:
    keying on everything locked in (the "obviously correct" version) makes
    the BFS frontier grow with the branching factor at every step, because
    almost no two distinct move sequences land on the exact same combination
    of N piece-states - it stopped being usable past a handful of locked
    pieces. Keying on only the new piece caps the frontier at that piece's
    own state space (a couple dozen values for an edge or corner) regardless
    of how many pieces came before, which is what actually keeps this fast.
    The tradeoff is real but narrow: BFS can occasionally discard the one
    path that both reaches a given new-piece state *and* keeps everything
    else intact, in favor of a same-new-piece-state path found first that
    doesn't - so this fast pass isn't provably complete. `fallback_moves`
    (tried first with the same fast dedup, then - only as a last resort -
    with the exact all-locked dedup) is what makes it correct in practice:
    the slow exact search is only ever paid for the rare step the fast pass
    can't handle, not for every step.
    """
    target_state_of = {step.piece_id: registry.piece_state(solved_ref, step.piece_id) for step in steps}

    solution: list[Move] = []
    working = cube.clone()
    locked: list[PieceId] = []

    for step in steps:
        locked = locked + [step.piece_id]
        goal_state = _combined_state_fn(registry, locked)
        target = tuple(target_state_of[pid] for pid in locked)

        def goal_test(c: Cube, goal_state=goal_state, target=target) -> bool:
            return goal_state(c) == target

        fast_encode = _combined_state_fn(registry, [step.piece_id])

        move_step = restricted_search(working, goal_test, fast_encode, step.allowed_moves, step.max_depth)
        if move_step is None and fallback_moves is not None:
            move_step = restricted_search(working, goal_test, fast_encode, fallback_moves, fallback_max_depth)
        if move_step is None and fallback_moves is not None:
            # last resort: exact (slow) dedup on the full locked set
            move_step = restricted_search(working, goal_test, goal_state, fallback_moves, fallback_max_depth)
        if move_step is None:
            return None
        working.apply_algorithm(move_step)
        solution.extend(move_step)

    return solution
