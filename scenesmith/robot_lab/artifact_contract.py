"""Strict numeric, identity, and reference rules for robot-lab artifacts."""

from __future__ import annotations

import hashlib
import json
import math

from pathlib import Path
from typing import Any, Iterable


def load_strict_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    _reject_non_finite_tree(payload, label=str(path))
    return payload


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def dump_canonical_json(path: Path, payload: dict[str, Any]) -> None:
    _reject_non_finite_tree(payload, label=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def require_finite_number(value: Any, *, label: str, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    if positive and number <= 0.0:
        raise ValueError(f"{label} must be positive")
    return number


def require_nonblank(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value.strip()


def validate_unique_ids(items: Iterable[dict[str, Any]], *, field: str, label: str) -> set[str]:
    seen: set[str] = set()
    for item in items:
        identifier = require_nonblank(item.get(field), label=f"{label} {field}")
        if identifier in seen:
            raise ValueError(f"Duplicate {label} {field}: {identifier}")
        seen.add(identifier)
    return seen


def sign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = dict(payload)
    unsigned = {key: value for key, value in signed.items() if key != "identity_sha256"}
    signed["identity_sha256"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    return signed


def verify_signed_payload(payload: dict[str, Any], *, label: str) -> None:
    expected = sign_payload(payload)["identity_sha256"]
    if payload.get("identity_sha256") != expected:
        raise ValueError(f"{label} identity hash is invalid")


def artifact_ref(*, path: Path, payload: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    identity = require_nonblank(payload.get("identity_sha256"), label="artifact identity_sha256")
    schema = require_nonblank(payload.get("schema_version"), label="artifact schema_version")
    resolved = path if path.is_absolute() else repo_root / path
    return {
        "path": str(path),
        "schema_version": schema,
        "identity_sha256": identity,
        "file_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def verify_artifact_ref(
    reference: dict[str, Any] | None,
    expected: dict[str, Any],
    *,
    label: str,
) -> None:
    if not isinstance(reference, dict):
        raise ValueError(f"{label} linkage is missing")
    for key in ("path", "schema_version", "identity_sha256", "file_sha256"):
        require_nonblank(reference.get(key), label=f"{label} {key}")
        if reference.get(key) != expected.get(key):
            raise ValueError(f"{label} linkage drifted for {key}")


def validate_inertia_tensor(values: Any, *, label: str, tolerance: float = 1e-10) -> list[list[float]]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{label} must be a 3x3 finite matrix")
    matrix: list[list[float]] = []
    for row in values:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"{label} must be a 3x3 finite matrix")
        matrix.append([require_finite_number(value, label=label) for value in row])
    if any(abs(matrix[row][column] - matrix[column][row]) > tolerance for row in range(3) for column in range(3)):
        raise ValueError(f"{label} must be symmetric")
    eigenvalues = _symmetric_eigenvalues(matrix, tolerance=tolerance)
    if min(eigenvalues) < -tolerance:
        raise ValueError(f"{label} must be positive semidefinite")
    principal = sorted(eigenvalues)
    if principal[2] > principal[0] + principal[1] + tolerance:
        raise ValueError(f"{label} principal moments violate rigid-body triangle inequality")
    return matrix


def validate_content_addressed_evidence(items: Any, *, label: str) -> set[tuple[str, str, str]]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} evidence is required")
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{label} evidence entries must be objects")
        kind = require_nonblank(item.get("kind"), label=f"{label} evidence kind")
        ref = require_nonblank(item.get("ref"), label=f"{label} evidence ref")
        digest = require_nonblank(item.get("sha256"), label=f"{label} evidence sha256")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"{label} evidence sha256 must be lowercase SHA-256")
        key = (kind, ref, digest)
        if key in seen:
            raise ValueError(f"Duplicate {label} evidence: {ref}")
        seen.add(key)
    return seen


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def _reject_non_finite_tree(value: Any, *, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} contains a non-finite number")
    if isinstance(value, dict):
        for child in value.values():
            _reject_non_finite_tree(child, label=label)
    elif isinstance(value, list):
        for child in value:
            _reject_non_finite_tree(child, label=label)


def _symmetric_eigenvalues(matrix: list[list[float]], *, tolerance: float) -> list[float]:
    """Return symmetric 3x3 eigenvalues using deterministic Jacobi rotations."""

    work = [row[:] for row in matrix]
    for _ in range(64):
        row, column = max(
            ((0, 1), (0, 2), (1, 2)),
            key=lambda pair: abs(work[pair[0]][pair[1]]),
        )
        off_diagonal = work[row][column]
        if abs(off_diagonal) <= tolerance:
            break
        angle = 0.5 * math.atan2(
            2.0 * off_diagonal,
            work[column][column] - work[row][row],
        )
        cosine = math.cos(angle)
        sine = math.sin(angle)
        left = [line[:] for line in work]
        for index in range(3):
            left[index][row] = cosine * work[index][row] - sine * work[index][column]
            left[index][column] = sine * work[index][row] + cosine * work[index][column]
        rotated = [line[:] for line in left]
        for index in range(3):
            rotated[row][index] = cosine * left[row][index] - sine * left[column][index]
            rotated[column][index] = sine * left[row][index] + cosine * left[column][index]
        work = rotated
    return [work[index][index] for index in range(3)]
