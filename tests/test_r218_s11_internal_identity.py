from __future__ import annotations

import ctypes

import numpy as np

from experiments.r218_s11_internal_identity import canonical_sha256


class _Record(ctypes.Structure):
    _fields_ = [("first", ctypes.c_uint32), ("second", ctypes.c_int64)]


def test_canonical_identity_preserves_order_and_float_bits() -> None:
    assert canonical_sha256({"a": 1, "b": 2}) != canonical_sha256(
        {"b": 2, "a": 1}
    )
    assert canonical_sha256(0.0) != canonical_sha256(-0.0)
    assert canonical_sha256([1, 2]) != canonical_sha256((1, 2))


def test_canonical_identity_preserves_numpy_dtype_shape_and_bytes() -> None:
    first = np.asarray([[1.0, -0.0]], dtype="<f8")
    second = first.copy()
    third = first.astype("<f4")
    assert canonical_sha256(first) == canonical_sha256(second)
    assert canonical_sha256(first) != canonical_sha256(third)
    assert canonical_sha256(first) != canonical_sha256(first.reshape(2, 1))


def test_canonical_identity_serializes_ctypes_fields_not_padding() -> None:
    first = _Record(7, -11)
    second = _Record(7, -11)
    changed = _Record(7, -12)
    assert canonical_sha256(first) == canonical_sha256(second)
    assert canonical_sha256(first) != canonical_sha256(changed)
