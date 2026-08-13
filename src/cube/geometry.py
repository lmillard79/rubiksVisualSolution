"""Pure coordinate geometry for an NxN cube: sticker <-> 3D position, and the
rotation math used to apply a layer turn.

Coordinate system: integer grid indices 0..n-1 along each of x (left->right),
y (down->up), z (back->front); axis order (x, y, z) = (0, 1, 2).

Every face is defined by an outward-pointing unit normal plus `right` and
`down` unit vectors giving the direction increasing column/row moves in
space. Values were derived by unfolding the cube into the net (U above F;
L, F, R, B left-to-right; D below F) via hinge matching against F's own
natural orientation - not guessed. This table is the single hand-derived
source of geometric truth: every other piece of move logic (which stickers
cycle, in which direction) is computed from it programmatically rather than
hand-typed per face, to avoid sign/reversal mistakes that are easy to make
and easy to miss by eye if each face's adjacency is transcribed separately.

Rotation direction convention (verified, not assumed): a positive-normal
face (R, U, F) turning clockwise as viewed from outside that face is a
single application of `_quarter_rotate_position`/`_quarter_rotate_direction`.
This was checked against two independently-derived ground truths - R turn
sends the F-colored strip to U, and U turn sends F->L->B->R->F - both of
which hold under this formula. A negative-normal face (L, D, B) turning
clockwise from its own outside is the *inverse* of that same formula (three
quarter-turns), since viewing from the opposite side of an axis reverses
the apparent rotation sense; `face_normal_sign` plus the `% 4` turn count in
`Cube.apply` is what selects that inverse automatically rather than needing
a second hand-derived formula.
"""

from __future__ import annotations

from .constants import Face

Vec3 = tuple[int, int, int]

FACE_FRAME: dict[Face, dict[str, Vec3]] = {
    Face.F: dict(normal=(0, 0, 1), right=(1, 0, 0), down=(0, -1, 0)),
    Face.B: dict(normal=(0, 0, -1), right=(-1, 0, 0), down=(0, -1, 0)),
    Face.U: dict(normal=(0, 1, 0), right=(1, 0, 0), down=(0, 0, -1)),
    Face.D: dict(normal=(0, -1, 0), right=(1, 0, 0), down=(0, 0, -1)),
    Face.R: dict(normal=(1, 0, 0), right=(0, 0, -1), down=(0, -1, 0)),
    Face.L: dict(normal=(-1, 0, 0), right=(0, 0, 1), down=(0, -1, 0)),
}

_NORMAL_TO_FACE: dict[Vec3, Face] = {frame["normal"]: face for face, frame in FACE_FRAME.items()}


def _axis_of(vec: Vec3) -> int:
    for axis, component in enumerate(vec):
        if component != 0:
            return axis
    raise ValueError(f"zero vector has no axis: {vec}")


def _sign_of(vec: Vec3) -> int:
    return 1 if vec[_axis_of(vec)] > 0 else -1


def face_axis(face: Face) -> int:
    """Which global axis (0=x, 1=y, 2=z) this face's normal lies along."""
    return _axis_of(FACE_FRAME[face]["normal"])


def face_normal_sign(face: Face) -> int:
    """+1 if the face sits on the positive side of its axis (R/U/F), else -1 (L/D/B)."""
    return _sign_of(FACE_FRAME[face]["normal"])


def _grid_index(component: int, local_index: int, n: int) -> int:
    return local_index if component == 1 else (n - 1 - local_index)


def sticker_xyz(face: Face, r: int, c: int, n: int) -> Vec3:
    """3D grid position (each coordinate in 0..n-1) of the sticker at (row r, col c) on `face`."""
    frame = FACE_FRAME[face]
    coord = [0, 0, 0]
    normal, right, down = frame["normal"], frame["right"], frame["down"]
    na = _axis_of(normal)
    coord[na] = (n - 1) if normal[na] == 1 else 0
    ra = _axis_of(right)
    coord[ra] = _grid_index(right[ra], c, n)
    da = _axis_of(down)
    coord[da] = _grid_index(down[da], r, n)
    return (coord[0], coord[1], coord[2])


def xyz_on_face(face: Face, xyz: Vec3, n: int) -> tuple[int, int]:
    """Inverse of sticker_xyz: recover (row, col) on `face` for a position already on it."""
    frame = FACE_FRAME[face]
    right, down = frame["right"], frame["down"]
    ra = _axis_of(right)
    c = xyz[ra] if right[ra] == 1 else (n - 1 - xyz[ra])
    da = _axis_of(down)
    r = xyz[da] if down[da] == 1 else (n - 1 - xyz[da])
    return (r, c)


def layer_depth(face: Face, layer_number: int, n: int) -> int:
    """Grid coordinate (along this face's axis) of the layer `layer_number`
    deep counting inward from `face` (1 = the face's own outer layer)."""
    sign = face_normal_sign(face)
    return (n - layer_number) if sign == 1 else (layer_number - 1)


def _quarter_rotate_position(xyz: Vec3, axis: int, n: int) -> Vec3:
    j, k = (axis + 1) % 3, (axis + 2) % 3
    coord = list(xyz)
    old_j, old_k = coord[j], coord[k]
    coord[j] = old_k
    coord[k] = (n - 1) - old_j
    return (coord[0], coord[1], coord[2])


def _quarter_rotate_direction(vec: Vec3, axis: int) -> Vec3:
    j, k = (axis + 1) % 3, (axis + 2) % 3
    coord = list(vec)
    old_j, old_k = coord[j], coord[k]
    coord[j] = old_k
    coord[k] = -old_j
    return (coord[0], coord[1], coord[2])


def rotate_position(xyz: Vec3, axis: int, quarter_turns: int, n: int) -> Vec3:
    for _ in range(quarter_turns % 4):
        xyz = _quarter_rotate_position(xyz, axis, n)
    return xyz


def rotate_direction(vec: Vec3, axis: int, quarter_turns: int) -> Vec3:
    for _ in range(quarter_turns % 4):
        vec = _quarter_rotate_direction(vec, axis)
    return vec


def new_face_for(face: Face, axis: int, quarter_turns: int) -> Face:
    normal = FACE_FRAME[face]["normal"]
    return _NORMAL_TO_FACE[rotate_direction(normal, axis, quarter_turns)]


def remap_sticker(face: Face, r: int, c: int, n: int, axis: int, quarter_turns: int) -> tuple[Face, int, int]:
    """Where does the sticker at (face, r, c) end up after `quarter_turns`
    positive-normal-convention quarter turns about `axis`?

    Face identity and grid position are computed independently (rotating the
    face's normal direction, and rotating the sticker's grid position) and
    then recombined, rather than searching for "which face does this xyz
    land on" - at shared edges/corners multiple faces' stickers can occupy
    the same (x, y, z), so identity has to come from the normal, not the
    position.
    """
    new_face = new_face_for(face, axis, quarter_turns)
    xyz = sticker_xyz(face, r, c, n)
    new_xyz = rotate_position(xyz, axis, quarter_turns, n)
    new_r, new_c = xyz_on_face(new_face, new_xyz, n)
    return new_face, new_r, new_c
