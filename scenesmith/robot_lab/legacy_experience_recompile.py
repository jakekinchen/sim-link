"""Bounded T17.6 audit and zero-row recompile for legacy canary evidence.

This module is deliberately not a migration path.  It inventories exactly the
three configured legacy descriptors, binds their present bytes, and records why
they cannot be relabelled as T17.1 raw rollout/frame records.  No source bytes
are edited, converted, or copied.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.experience_compiler import (
    compile_projections,
    verify_compilation,
    write_compilation,
)
from scenesmith.robot_lab.experience_records import REPO_ROOT, verify_experience_record_contract
from scenesmith.robot_lab.normalization_bundle import verify_normalization_bundle


SCHEMA_VERSION = "scenesmith.legacy_experience_recompile.v1"
TASK_ID = "T17.6"
DEFAULT_LEGACY_ROOT = REPO_ROOT / "outputs/robot_lab/autolearn/m10-contract-canary"
RECORD_CONTRACT_PATH = REPO_ROOT / "configurations/robot_lab/experience_record_contract.json"
NORMALIZATION_PATH = REPO_ROOT / "configurations/robot_lab/normalization_bundle.json"


@dataclass(frozen=True)
class LegacyCandidateSpec:
    """One fixed legacy descriptor; no recursive discovery is permitted."""

    candidate_id: str
    relative_path: Path
    source_kind: str


CANDIDATE_SPECS = (
    LegacyCandidateSpec(
        "m10_observation_frames",
        Path("collection/randomized-episode-6204/observation_frames.jsonl"),
        "legacy_jsonl_frame_stream",
    ),
    LegacyCandidateSpec(
        "m10_dagger_intervention_sidecar",
        Path("dagger-dataset/scenesmith_intervention_sidecar.jsonl"),
        "legacy_jsonl_intervention_sidecar",
    ),
    LegacyCandidateSpec(
        "m10_training_dataset_metadata",
        Path("training-dataset/meta/info.json"),
        "legacy_training_dataset_metadata",
    ),
)


def build_legacy_inventory_manifest(
    legacy_root: Path = DEFAULT_LEGACY_ROOT,
    *,
    specs: tuple[LegacyCandidateSpec, ...] = CANDIDATE_SPECS,
) -> dict[str, Any]:
    """Return a signed, reasoned audit without modifying legacy source bytes."""

    root = _require_legacy_root(legacy_root)
    if not specs:
        raise ValueError("At least one fixed legacy candidate is required")
    candidate_ids = [spec.candidate_id for spec in specs]
    relative_paths = [spec.relative_path.as_posix() for spec in specs]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Legacy candidate identifiers must be unique")
    if len(relative_paths) != len(set(relative_paths)):
        raise ValueError("Legacy candidate paths must be unique")

    record_contract = load_strict_json(RECORD_CONTRACT_PATH)
    normalization = load_strict_json(NORMALIZATION_PATH)
    verify_experience_record_contract(record_contract, repo_root=REPO_ROOT)
    verify_normalization_bundle(normalization, repo_root=REPO_ROOT)

    candidates = [_inspect_candidate(root, spec) for spec in specs]
    accepted = [candidate for candidate in candidates if candidate["decision"] == "accepted"]
    quarantined = [candidate for candidate in candidates if candidate["decision"] == "quarantined"]
    if accepted:
        raise ValueError("Legacy candidates may not bypass a reviewed raw-record importer")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "inventory_root": _repo_relative(root),
        "inventory_scope": "fixed_named_files_only",
        "source_experience_identity_sha256": record_contract["identity_sha256"],
        "source_normalization_identity_sha256": normalization["identity_sha256"],
        "configured_candidate_count": len(specs),
        "discovered_candidate_count": len(candidates),
        "accepted_candidate_count": len(accepted),
        "quarantined_candidate_count": len(quarantined),
        "accepted_rollout_count": 0,
        "accepted_frame_count": 0,
        "decision": "no_legacy_candidate_qualifies_for_current_raw_record_contract",
        "candidates": candidates,
        "training_eligible": False,
        "simulation_training_ready": False,
        "optimizer_training": False,
        "physical_actuation": False,
        "raw_bytes_rewritten": False,
    }
    return sign_payload(payload)


def verify_legacy_inventory_manifest(
    manifest: dict[str, Any],
    legacy_root: Path = DEFAULT_LEGACY_ROOT,
    *,
    specs: tuple[LegacyCandidateSpec, ...] = CANDIDATE_SPECS,
) -> None:
    """Fail closed if the local inventory, reasons, or authority labels drift."""

    verify_signed_payload(manifest, label="legacy experience inventory")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Legacy inventory schema version drifted")
    if manifest.get("task_id") != TASK_ID:
        raise ValueError("Legacy inventory task identity drifted")
    for field in (
        "training_eligible",
        "simulation_training_ready",
        "optimizer_training",
        "physical_actuation",
        "raw_bytes_rewritten",
    ):
        if manifest.get(field) is not False:
            raise ValueError(f"Legacy inventory authority flag drifted: {field}")
    if manifest.get("accepted_candidate_count") != 0:
        raise ValueError("Legacy inventory unexpectedly accepted a candidate")
    if manifest.get("accepted_rollout_count") != 0 or manifest.get("accepted_frame_count") != 0:
        raise ValueError("Legacy inventory unexpectedly emitted accepted records")
    if manifest.get("decision") != "no_legacy_candidate_qualifies_for_current_raw_record_contract":
        raise ValueError("Legacy inventory decision drifted")
    expected = build_legacy_inventory_manifest(legacy_root, specs=specs)
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected):
        raise ValueError("Legacy inventory manifest drifted from bounded source bytes")


def compile_legacy_inventory(
    manifest: dict[str, Any],
    output_dir: Path,
    *,
    inventory_manifest_sha256: str,
) -> dict[str, Any]:
    """Write the explicit zero-row compiler view bound to the signed audit."""

    _require_sha256(inventory_manifest_sha256, label="legacy inventory manifest hash")
    if manifest.get("accepted_candidate_count") != 0:
        raise ValueError("This bounded legacy audit cannot compile accepted candidates")
    result = compile_projections(
        [],
        source_experience_identity=manifest["source_experience_identity_sha256"],
        source_normalization_identity=manifest["source_normalization_identity_sha256"],
        source_legacy_inventory_manifest_sha256=inventory_manifest_sha256,
    )
    written = write_compilation(result, output_dir)
    verify_compilation(output_dir)
    if written["manifest"]["frame_count"] != 0 or written["manifest"]["segment_count"] != 0:
        raise ValueError("Legacy empty compiler view emitted rows")
    return written


def _inspect_candidate(root: Path, spec: LegacyCandidateSpec) -> dict[str, Any]:
    path = _bound_candidate_path(root, spec.relative_path)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Legacy candidate is absent or not a regular file: {spec.relative_path}")
    if spec.source_kind.startswith("legacy_jsonl_"):
        return _inspect_jsonl_candidate(path, spec)
    if spec.source_kind == "legacy_training_dataset_metadata":
        return _inspect_training_metadata(path, spec)
    raise ValueError(f"Unknown legacy candidate source kind: {spec.source_kind}")


def _inspect_jsonl_candidate(path: Path, spec: LegacyCandidateSpec) -> dict[str, Any]:
    first_record: dict[str, Any] | None = None
    record_count = 0
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Malformed legacy JSONL at {spec.relative_path}:{line_number}"
                ) from error
            if not isinstance(record, dict):
                raise ValueError(
                    f"Legacy JSONL record is not an object at {spec.relative_path}:{line_number}"
                )
            if first_record is None:
                first_record = record
            record_count += 1
    reasons = [
        "not_current_signed_raw_rollout_envelope",
        "missing_current_action_variant_lineage",
        "timestamp_not_integer_nanoseconds",
        "missing_current_frame_provenance",
        "missing_current_hard_boundary_contract",
    ]
    if record_count == 0:
        reasons.insert(0, "empty_legacy_stream")
    elif spec.source_kind == "legacy_jsonl_intervention_sidecar":
        reasons.append("unconfined_legacy_observation_paths")
    return _quarantined_candidate(
        spec,
        path,
        record_count=record_count,
        observed_top_level_keys=sorted(first_record) if first_record is not None else [],
        quarantine_reasons=reasons,
    )


def _inspect_training_metadata(path: Path, spec: LegacyCandidateSpec) -> dict[str, Any]:
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Malformed legacy training metadata: {spec.relative_path}") from error
    if not isinstance(metadata, dict):
        raise ValueError("Legacy training metadata must be an object")
    features = metadata.get("features")
    if not isinstance(features, dict):
        raise ValueError("Legacy training metadata features are required")
    feature_summary = {
        name: {
            key: feature.get(key)
            for key in ("dtype", "shape", "names")
            if key in feature
        }
        for name, feature in sorted(features.items())
        if isinstance(feature, dict)
    }
    return _quarantined_candidate(
        spec,
        path,
        record_count=None,
        observed_top_level_keys=sorted(metadata),
        quarantine_reasons=[
            "legacy_training_dataset_not_current_raw_rollout",
            "missing_current_signed_raw_rollout_envelope",
            "single_legacy_action_field_lacks_variant_lineage",
            "legacy_timestamp_not_integer_nanoseconds",
            "legacy_coordinate_contract_not_current_source_bound_frame_contract",
        ],
        source_facts={
            "declared_episode_count": metadata.get("total_episodes"),
            "declared_frame_count": metadata.get("total_frames"),
            "feature_summary": feature_summary,
        },
    )


def _quarantined_candidate(
    spec: LegacyCandidateSpec,
    path: Path,
    *,
    record_count: int | None,
    observed_top_level_keys: list[str],
    quarantine_reasons: list[str],
    source_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = {
        "candidate_id": spec.candidate_id,
        "path": _repo_relative(path),
        "source_kind": spec.source_kind,
        "file_sha256": _sha256_file(path),
        "byte_count": path.stat().st_size,
        "record_count": record_count,
        "observed_top_level_keys": observed_top_level_keys,
        "decision": "quarantined",
        "quarantine_reason_codes": sorted(set(quarantine_reasons)),
    }
    if source_facts is not None:
        candidate["source_facts"] = source_facts
    return candidate


def _require_legacy_root(legacy_root: Path) -> Path:
    if legacy_root.is_symlink():
        raise ValueError("Configured legacy inventory root may not be a symlink")
    root = legacy_root.resolve()
    if not root.is_dir():
        raise ValueError("Configured legacy inventory root is absent or unsafe")
    return root


def _bound_candidate_path(root: Path, relative_path: Path) -> Path:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Legacy candidate path escapes its configured root")
    configured_path = root / relative_path
    if configured_path.is_symlink():
        raise ValueError("Legacy candidate path may not be a symlink")
    path = configured_path.resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError("Legacy candidate path escapes its configured root") from error
    return path


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("Legacy source must remain inside this checkout") from error


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
    return value
