"""Small, deterministic visual-evidence helpers for grasp proof artifacts."""

from __future__ import annotations

import base64
import hashlib
import struct
import zlib

from typing import Any, Mapping

import numpy as np


KEYFRAME_PHASES = (
    "pregrasp",
    "close",
    "grasp_hold",
    "unsupported_lift_hold",
    "retreat",
)
MIN_KEYFRAME_COUNT = 3
MAX_KEYFRAME_COUNT = 5
KEYFRAME_IMAGE_SIZE = 256
IMAGE_ROLES = ("top", "wrist")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def retain_rendered_keyframe(
    store: dict[str, dict[str, Any]],
    frame: Mapping[str, Any],
    images: Mapping[str, np.ndarray],
    *,
    phases: tuple[str, ...] = KEYFRAME_PHASES,
    image_size: int = KEYFRAME_IMAGE_SIZE,
) -> None:
    """Retain the latest rendered frame for each requested grasp phase."""

    phase = frame.get("phase")
    if phase not in phases:
        return
    if not images:
        raise ValueError(f"Rendered keyframe {phase!r} has no images")
    encoded_images: dict[str, dict[str, Any]] = {}
    for role in IMAGE_ROLES:
        if role not in images:
            raise ValueError(f"Rendered keyframe {phase!r} lacks {role!r} image")
        encoded_images[role] = encode_png_image(images[role], image_size=image_size)
    frame_index = frame.get("frame_index")
    if isinstance(frame_index, bool) or not isinstance(frame_index, int):
        raise ValueError("Rendered keyframe frame_index must be an integer")
    store[phase] = {
        "phase": phase,
        "frame_index": frame_index,
        "images": encoded_images,
    }


def finalize_rendered_keyframes(
    store: Mapping[str, dict[str, Any]],
    *,
    phases: tuple[str, ...] = KEYFRAME_PHASES,
) -> list[dict[str, Any]]:
    """Return ordered keyframes and require the standing 3–5-frame range."""

    keyframes = [store[phase] for phase in phases if phase in store]
    if not MIN_KEYFRAME_COUNT <= len(keyframes) <= MAX_KEYFRAME_COUNT:
        raise ValueError(
            "Grasp proof requires 3-5 rendered keyframes; "
            f"captured {len(keyframes)}"
        )
    return keyframes


def validate_rendered_keyframes(
    value: Any, *, phases: tuple[str, ...] = KEYFRAME_PHASES
) -> None:
    """Validate the compact, self-contained PNG evidence in an artifact."""

    if not isinstance(value, list) or not MIN_KEYFRAME_COUNT <= len(value) <= MAX_KEYFRAME_COUNT:
        raise ValueError("Rendered keyframes must contain 3-5 frames")
    phases_seen: list[str] = []
    for keyframe in value:
        if not isinstance(keyframe, dict):
            raise ValueError("Rendered keyframe must be an object")
        phase = keyframe.get("phase")
        if phase not in phases or phase in phases_seen:
            raise ValueError("Rendered keyframe phases must be known and unique")
        phases_seen.append(phase)
        frame_index = keyframe.get("frame_index")
        if isinstance(frame_index, bool) or not isinstance(frame_index, int) or frame_index < 0:
            raise ValueError("Rendered keyframe frame_index is invalid")
        images = keyframe.get("images")
        if not isinstance(images, dict) or set(images) != set(IMAGE_ROLES):
            raise ValueError("Rendered keyframe image roles are incomplete")
        for role in IMAGE_ROLES:
            _validate_png_image(images[role], label=f"{phase}.{role}")


def encode_png_image(image: np.ndarray, *, image_size: int) -> dict[str, Any]:
    """Encode an RGB uint8 image without relying on a mutable image library."""

    pixels = np.asarray(image)
    expected_shape = (image_size, image_size, 3)
    if pixels.shape != expected_shape or pixels.dtype != np.uint8:
        raise ValueError(
            f"Rendered keyframe image must be uint8 {expected_shape}, got "
            f"{pixels.dtype} {pixels.shape}"
        )
    raw_rows = b"".join(b"\x00" + row.tobytes() for row in pixels)
    header = struct.pack(
        ">IIBBBBB", image_size, image_size, 8, 2, 0, 0, 0
    )
    chunks = _png_chunk(b"IHDR", header) + _png_chunk(
        b"IDAT", zlib.compress(raw_rows, level=9)
    ) + _png_chunk(b"IEND", b"")
    png = PNG_SIGNATURE + chunks
    return {
        "encoding": "png",
        "width": image_size,
        "height": image_size,
        "channels": 3,
        "image_sha256": hashlib.sha256(png).hexdigest(),
        "png_base64": base64.b64encode(png).decode("ascii"),
    }


def _validate_png_image(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"Rendered image {label} is not an object")
    if value.get("encoding") != "png" or value.get("channels") != 3:
        raise ValueError(f"Rendered image {label} encoding is invalid")
    if value.get("width") != KEYFRAME_IMAGE_SIZE or value.get("height") != KEYFRAME_IMAGE_SIZE:
        raise ValueError(f"Rendered image {label} dimensions are invalid")
    encoded = value.get("png_base64")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError(f"Rendered image {label} bytes are missing")
    try:
        png = base64.b64decode(encoded, validate=True)
    except Exception as exc:  # pragma: no cover - exact decoder exception varies
        raise ValueError(f"Rendered image {label} is not valid base64") from exc
    if not png.startswith(PNG_SIGNATURE):
        raise ValueError(f"Rendered image {label} is not a PNG")
    if len(png) < 33 or png[12:16] != b"IHDR":
        raise ValueError(f"Rendered image {label} lacks a valid PNG header")
    width, height = struct.unpack(">II", png[16:24])
    if (width, height) != (KEYFRAME_IMAGE_SIZE, KEYFRAME_IMAGE_SIZE):
        raise ValueError(f"Rendered image {label} PNG header dimensions drifted")
    if value.get("image_sha256") != hashlib.sha256(png).hexdigest():
        raise ValueError(f"Rendered image {label} hash drifted")


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )
