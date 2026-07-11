"""Strict numeric, identity, and reference rules for robot-lab artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import sys

from pathlib import Path
from typing import Any, Iterable


JACOBI_MAX_ITERATIONS = 128
_MACHINE_EPSILON = sys.float_info.epsilon


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


def validate_inertia_tensor(
    values: Any,
    *,
    label: str,
    tolerance: float = 1e-10,
) -> list[list[float]]:
    """Validate a physical 3x3 inertia tensor with scale-relative tolerances.

    ``tolerance`` is a dimensionless relative tolerance, retained under the
    legacy keyword for API compatibility.
    """

    matrix = _finite_3x3_matrix(values, label=label)
    relative_tolerance = _relative_tolerance(tolerance)
    scale = _matrix_scale(matrix)
    comparison_tolerance = _scaled_tolerance(scale, relative_tolerance)
    _validate_symmetry(
        matrix,
        label=label,
        comparison_tolerance=comparison_tolerance,
    )
    eigenvalues = _symmetric_eigenvalues(
        _symmetric_part(matrix),
        relative_tolerance=relative_tolerance,
        label=label,
    )
    if min(eigenvalues) < -comparison_tolerance:
        raise ValueError(f"{label} must be positive semidefinite")
    principal = sorted(
        0.0 if abs(value) <= comparison_tolerance else value for value in eigenvalues
    )
    if principal[2] > principal[0] + principal[1] + comparison_tolerance:
        raise ValueError(f"{label} principal moments violate rigid-body triangle inequality")
    return matrix


def symmetric_eigenvalues(
    values: Any,
    *,
    label: str,
    tolerance: float = 1e-10,
) -> list[float]:
    """Return deterministic symmetric 3x3 eigenvalues after residual checks."""

    matrix = _finite_3x3_matrix(values, label=label)
    relative_tolerance = _relative_tolerance(tolerance)
    scale = _matrix_scale(matrix)
    _validate_symmetry(
        matrix,
        label=label,
        comparison_tolerance=_scaled_tolerance(scale, relative_tolerance),
    )
    return _symmetric_eigenvalues(
        _symmetric_part(matrix),
        relative_tolerance=relative_tolerance,
        label=label,
    )


def _finite_3x3_matrix(values: Any, *, label: str) -> list[list[float]]:
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{label} must be a 3x3 finite matrix")
    matrix: list[list[float]] = []
    for row in values:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"{label} must be a 3x3 finite matrix")
        matrix.append([require_finite_number(value, label=label) for value in row])
    return matrix


def _validate_symmetry(
    matrix: list[list[float]],
    *,
    label: str,
    comparison_tolerance: float,
) -> None:
    if any(
        abs(matrix[row][column] - matrix[column][row]) > comparison_tolerance
        for row in range(3)
        for column in range(row + 1, 3)
    ):
        raise ValueError(f"{label} must be symmetric")


def _symmetric_part(matrix: list[list[float]]) -> list[list[float]]:
    symmetric = [row[:] for row in matrix]
    for row in range(3):
        for column in range(row + 1, 3):
            average = 0.5 * matrix[row][column] + 0.5 * matrix[column][row]
            symmetric[row][column] = average
            symmetric[column][row] = average
    return symmetric


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


def _symmetric_eigenvalues(
    matrix: list[list[float]],
    *,
    relative_tolerance: float,
    label: str,
) -> list[float]:
    """Return scale-safe symmetric eigenvalues using deterministic Jacobi rotations."""

    scale = _matrix_scale(matrix)
    if scale == 0.0:
        return [0.0, 0.0, 0.0]
    normalized = [[value / scale for value in row] for row in matrix]
    _reject_non_finite_tree(normalized, label=f"{label} normalized eigensystem")
    convergence_tolerance = max(
        64.0 * _MACHINE_EPSILON,
        min(relative_tolerance * 0.01, 1e-13),
    )
    eigenvalues, eigenvectors = _jacobi_eigendecomposition(
        normalized,
        convergence_tolerance=convergence_tolerance,
        label=label,
    )
    residual_tolerance = max(
        1024.0 * _MACHINE_EPSILON,
        relative_tolerance * 0.01,
    )
    _validate_eigenpairs(
        normalized,
        eigenvalues=eigenvalues,
        eigenvectors=eigenvectors,
        residual_tolerance=residual_tolerance,
        label=label,
    )
    scaled = [value * scale for value in eigenvalues]
    if not all(math.isfinite(value) for value in scaled):
        raise ValueError(f"{label} eigensolver produced non-finite eigenvalues")
    return sorted(0.0 if value == 0.0 else value for value in scaled)


def _jacobi_eigendecomposition(
    matrix: list[list[float]],
    *,
    convergence_tolerance: float,
    label: str,
) -> tuple[list[float], list[list[float]]]:
    work = [row[:] for row in matrix]
    eigenvectors = [[1.0 if row == column else 0.0 for column in range(3)] for row in range(3)]
    pivot_pairs = ((0, 1), (0, 2), (1, 2))
    converged = False
    for iteration in range(JACOBI_MAX_ITERATIONS + 1):
        row, column = max(
            pivot_pairs,
            key=lambda pair: abs(work[pair[0]][pair[1]]),
        )
        off_diagonal = work[row][column]
        if abs(off_diagonal) <= convergence_tolerance:
            converged = True
            break
        if iteration == JACOBI_MAX_ITERATIONS:
            break
        diagonal_row = work[row][row]
        diagonal_column = work[column][column]
        angle = 0.5 * math.atan2(
            2.0 * off_diagonal,
            diagonal_column - diagonal_row,
        )
        cosine = math.cos(angle)
        sine = math.sin(angle)
        for index in range(3):
            if index in {row, column}:
                continue
            value_row = work[index][row]
            value_column = work[index][column]
            rotated_row = cosine * value_row - sine * value_column
            rotated_column = sine * value_row + cosine * value_column
            work[index][row] = rotated_row
            work[row][index] = rotated_row
            work[index][column] = rotated_column
            work[column][index] = rotated_column
        work[row][row] = (
            cosine * cosine * diagonal_row
            - 2.0 * sine * cosine * off_diagonal
            + sine * sine * diagonal_column
        )
        work[column][column] = (
            sine * sine * diagonal_row
            + 2.0 * sine * cosine * off_diagonal
            + cosine * cosine * diagonal_column
        )
        work[row][column] = 0.0
        work[column][row] = 0.0
        for index in range(3):
            vector_row = eigenvectors[index][row]
            vector_column = eigenvectors[index][column]
            eigenvectors[index][row] = cosine * vector_row - sine * vector_column
            eigenvectors[index][column] = sine * vector_row + cosine * vector_column
        _reject_non_finite_tree(work, label=f"{label} Jacobi iterate")
        _reject_non_finite_tree(eigenvectors, label=f"{label} Jacobi eigenvectors")
    if not converged:
        raise ValueError(
            f"{label} eigensolver did not converge within {JACOBI_MAX_ITERATIONS} iterations"
        )
    return [work[index][index] for index in range(3)], eigenvectors


def _validate_eigenpairs(
    matrix: list[list[float]],
    *,
    eigenvalues: list[float],
    eigenvectors: list[list[float]],
    residual_tolerance: float,
    label: str,
) -> None:
    for column, eigenvalue in enumerate(eigenvalues):
        vector = [eigenvectors[row][column] for row in range(3)]
        vector_norm = math.sqrt(sum(value * value for value in vector))
        if not math.isfinite(vector_norm) or vector_norm <= 0.0:
            raise ValueError(f"{label} eigensolver produced an invalid eigenvector")
        residual = []
        for row in range(3):
            projected = sum(matrix[row][index] * vector[index] for index in range(3))
            residual.append(projected - eigenvalue * vector[row])
        residual_norm = math.sqrt(sum(value * value for value in residual)) / vector_norm
        if not math.isfinite(residual_norm) or residual_norm > residual_tolerance:
            raise ValueError(
                f"{label} eigensolver residual exceeded tolerance: {residual_norm}"
            )
    for left in range(3):
        for right in range(left, 3):
            dot = sum(
                eigenvectors[row][left] * eigenvectors[row][right] for row in range(3)
            )
            expected = 1.0 if left == right else 0.0
            if not math.isfinite(dot) or abs(dot - expected) > residual_tolerance:
                raise ValueError(f"{label} eigensolver eigenvectors lost orthogonality")


def _matrix_scale(matrix: list[list[float]]) -> float:
    return max(abs(value) for row in matrix for value in row)


def _relative_tolerance(value: Any) -> float:
    tolerance = require_finite_number(value, label="inertia relative tolerance", positive=True)
    if tolerance >= 1.0:
        raise ValueError("inertia relative tolerance must be less than one")
    return tolerance


def _scaled_tolerance(scale: float, relative_tolerance: float) -> float:
    if scale == 0.0:
        return 0.0
    scaled = scale * relative_tolerance
    if not math.isfinite(scaled):
        raise ValueError("inertia tolerance scaling produced a non-finite value")
    return max(scaled, 8.0 * math.ulp(scale))
