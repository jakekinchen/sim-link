"""Append-only content-addressed storage for rendered evidence images."""

from __future__ import annotations

import hashlib

from pathlib import Path
from typing import Any, Iterable

from scenesmith.robot_lab.artifact_contract import (
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)


SCHEMA_VERSION = "scenesmith.evidence_image_manifest.v1"
DEFAULT_MEDIA_TYPE = "image/png"


def store_image_bytes(
    store_root: Path,
    data: bytes,
    *,
    extension: str = ".png",
    media_type: str = DEFAULT_MEDIA_TYPE,
) -> dict[str, Any]:
    """Store bytes under their SHA-256 name without overwriting different bytes."""

    if not isinstance(data, bytes) or not data:
        raise ValueError("Evidence image bytes must be non-empty bytes")
    normalized_extension = _normalize_extension(extension)
    require_nonblank(media_type, label="Evidence image media_type")
    digest = hashlib.sha256(data).hexdigest()
    relative_path = Path(f"{digest}{normalized_extension}")
    store_root = Path(store_root)
    store_root.mkdir(parents=True, exist_ok=True)
    destination = _resolve_relative(store_root, relative_path)
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise ValueError("Evidence image destination is not a regular file")
        if destination.read_bytes() != data:
            raise ValueError("Content-addressed evidence image bytes drifted")
    else:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(destination)
    return {
        "path": relative_path.as_posix(),
        "sha256": digest,
        "size_bytes": len(data),
        "media_type": media_type,
    }


def verify_image_ref(store_root: Path, reference: dict[str, Any]) -> None:
    """Verify one manifest reference and reject path aliases or byte drift."""

    if not isinstance(reference, dict):
        raise ValueError("Evidence image reference must be an object")
    relative_path = require_nonblank(reference.get("path"), label="Evidence image path")
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Evidence image path must stay beneath the store root")
    digest = require_nonblank(reference.get("sha256"), label="Evidence image sha256")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("Evidence image sha256 must be lowercase SHA-256")
    expected_size = reference.get("size_bytes")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0:
        raise ValueError("Evidence image size_bytes must be a positive integer")
    require_nonblank(reference.get("media_type"), label="Evidence image media_type")
    resolved = _resolve_relative(Path(store_root), path)
    if resolved.is_symlink() or not resolved.is_file():
        raise ValueError("Evidence image bytes are missing or aliased")
    data = resolved.read_bytes()
    if len(data) != expected_size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Evidence image bytes do not match their manifest reference")
    if path.stem != digest:
        raise ValueError("Evidence image filename is not content-addressed")


def build_image_manifest(
    store_root: Path,
    references: Iterable[dict[str, Any]],
    *,
    source_identity_sha256: str,
) -> dict[str, Any]:
    """Build a signed, deterministic manifest for stored image bytes."""

    source_identity = require_nonblank(
        source_identity_sha256,
        label="Evidence image source identity_sha256",
    )
    entries = [dict(reference) for reference in references]
    if not entries:
        raise ValueError("Evidence image manifest requires at least one image")
    for reference in entries:
        verify_image_ref(store_root, reference)
    entries.sort(key=lambda reference: reference["path"])
    if len({reference["path"] for reference in entries}) != len(entries):
        raise ValueError("Evidence image manifest contains duplicate paths")
    return sign_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "store_root": str(Path(store_root)),
            "source_identity_sha256": source_identity,
            "image_count": len(entries),
            "images": entries,
            "content_addressed": True,
            "raw_bytes_rewritten": False,
        }
    )


def verify_image_manifest(
    manifest: dict[str, Any],
    store_root: Path,
    *,
    source_identity_sha256: str,
) -> None:
    """Verify a signed image manifest and every referenced byte object."""

    verify_signed_payload(manifest, label="evidence image manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Evidence image manifest schema drifted")
    if manifest.get("store_root") != str(Path(store_root)):
        raise ValueError("Evidence image manifest store root drifted")
    if manifest.get("source_identity_sha256") != source_identity_sha256:
        raise ValueError("Evidence image manifest source identity drifted")
    if manifest.get("content_addressed") is not True or manifest.get("raw_bytes_rewritten") is not False:
        raise ValueError("Evidence image manifest append-only contract drifted")
    images = manifest.get("images")
    if not isinstance(images, list) or manifest.get("image_count") != len(images):
        raise ValueError("Evidence image manifest image count drifted")
    for reference in images:
        verify_image_ref(store_root, reference)


def _normalize_extension(extension: str) -> str:
    if not isinstance(extension, str) or not extension.startswith("."):
        raise ValueError("Evidence image extension must begin with a dot")
    normalized = extension.lower()
    if normalized not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Evidence image extension is unsupported")
    return normalized


def _resolve_relative(root: Path, relative: Path) -> Path:
    root_resolved = Path(root).resolve()
    resolved = (root_resolved / relative).resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError("Evidence image path escapes the store root")
    return resolved
