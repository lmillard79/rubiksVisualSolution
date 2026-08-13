"""Direct unit coverage of the pure coordinate math, underneath the
higher-level move-algebra checks in test_moves_algebra.py."""

import pytest

from cube.constants import ALL_FACES
from cube.geometry import face_axis, face_normal_sign, sticker_xyz, xyz_on_face


@pytest.mark.parametrize("face", ALL_FACES)
def test_xyz_on_face_inverts_sticker_xyz(n, face):
    for r in range(n):
        for c in range(n):
            xyz = sticker_xyz(face, r, c, n)
            assert xyz_on_face(face, xyz, n) == (r, c)


@pytest.mark.parametrize("face", ALL_FACES)
def test_sticker_xyz_is_bijective_within_a_face(n, face):
    seen = set()
    for r in range(n):
        for c in range(n):
            xyz = sticker_xyz(face, r, c, n)
            assert xyz not in seen, f"duplicate xyz {xyz} on face {face} at n={n}"
            seen.add(xyz)


@pytest.mark.parametrize("face", ALL_FACES)
def test_every_sticker_has_normal_axis_at_its_depth(n, face):
    axis = face_axis(face)
    sign = face_normal_sign(face)
    expected_depth = (n - 1) if sign == 1 else 0
    for r in range(n):
        for c in range(n):
            assert sticker_xyz(face, r, c, n)[axis] == expected_depth
