"""Independent, offline intake for immutable Robo Scan scene-export receipts.

This module intentionally has no producer-package, Git, camera, robot,
simulator, or model dependency.  It validates a selected copied directory and
emits only a local candidate descriptor; global authority remains elsewhere.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Mapping


RECEIPT_SCHEMA = "so101.scene-export-receipt.v1"
MANIFEST_SCHEMA = "so101.layered-scene-manifest.v1"
LOCK_SCHEMA = "scenesmith.robo-scan-export-lock.v1"
CANDIDATE_SCHEMA = "scenesmith.robo-scan-twin-candidate.v1"
RECEIPT_FILE = "export-receipt.json"
MANIFEST_FILE = "layered-scene-manifest.json"
DEFAULT_LOCK_PATH = Path("configurations/robot_lab/robo_scan_export_lock.json")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_-]*$")
_SCENE_SEGMENT = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
_METRIC_EVIDENCE_IDS = (
    "calibration",
    "frame_synchronization",
    "native_depth_capability",
)
_GLOBAL_FIELDS = {
    "authority",
    "physical_qualification_authority",
    "physical_twin_qualified",
    "physical_transfer_ready",
    "promotion_eligible",
    "simulation_training_ready",
    "training_or_promotion_authority",
}


class RoboScanExportError(ValueError):
    """The selected export is not an approved immutable handoff."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _load_canonical(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RoboScanExportError(f"{label} must be one real file")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RoboScanExportError(f"{label} cannot be read") from exc

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RoboScanExportError(f"{label} has a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoboScanExportError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise RoboScanExportError(f"{label} must use canonical JSON serialization")
    return value


def _identifier(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise RoboScanExportError(f"{label} must be a lowercase stable identifier")
    return value


def _sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise RoboScanExportError(f"{label} must be a lowercase SHA-256")
    return value


def _safe_uri(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RoboScanExportError(f"{label} must be a non-empty relative URI")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or "://" in value or any(part in {"", ".", ".."} for part in path.parts):
        raise RoboScanExportError(f"{label} must be a safe relative POSIX URI")
    return value


def _finite(value: Any, *, label: str) -> float:
    if isinstance(value, bool):
        raise RoboScanExportError(f"{label} must be finite")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise RoboScanExportError(f"{label} must be finite") from exc
    if not math.isfinite(number):
        raise RoboScanExportError(f"{label} must be finite")
    return number


def _rigid_transform(value: Any, *, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 4:
        raise RoboScanExportError(f"{label} must be a 4x4 rigid transform")
    matrix = []
    for row in value:
        if not isinstance(row, list) or len(row) != 4:
            raise RoboScanExportError(f"{label} must be a 4x4 rigid transform")
        matrix.append([_finite(item, label=label) for item in row])
    if any(abs(matrix[3][index] - expected) > 1e-9 for index, expected in enumerate((0.0, 0.0, 0.0, 1.0))):
        raise RoboScanExportError(f"{label} must be homogeneous")
    columns = [[matrix[row][column] for row in range(3)] for column in range(3)]
    for column in columns:
        if not math.isclose(sum(item * item for item in column), 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise RoboScanExportError(f"{label} must have unit rotation columns")
    for left in range(3):
        for right in range(left + 1, 3):
            if abs(sum(columns[left][index] * columns[right][index] for index in range(3))) > 1e-6:
                raise RoboScanExportError(f"{label} must have orthogonal rotation columns")
    determinant = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    if not math.isclose(determinant, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise RoboScanExportError(f"{label} must be a proper rigid transform")
    return matrix


def _uncertainty(value: Any, *, metric: bool, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RoboScanExportError(f"{label} must be an object")
    if value.get("state") == "not_provided":
        if set(value) != {"state"} or metric:
            raise RoboScanExportError(f"{label} contradicts metric authority")
        return {"state": "not_provided"}
    required = {"state", "translationStdDevMeters", "rotationStdDevDegrees"}
    if value.get("state") not in {"estimated", "measured"} or set(value) != required:
        raise RoboScanExportError(f"{label} must be unit-explicit")
    return {
        "state": value["state"],
        "translationStdDevMeters": _nonnegative(value["translationStdDevMeters"], label=f"{label}.translationStdDevMeters"),
        "rotationStdDevDegrees": _nonnegative(value["rotationStdDevDegrees"], label=f"{label}.rotationStdDevDegrees"),
    }


def _nonnegative(value: Any, *, label: str) -> float:
    number = _finite(value, label=label)
    if number < 0:
        raise RoboScanExportError(f"{label} must be non-negative")
    return number


def _require_sorted_identifiers(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RoboScanExportError(f"{label} must be a non-empty list")
    result = [_identifier(item, label=f"{label} item") for item in value]
    if result != sorted(result) or len(set(result)) != len(result):
        raise RoboScanExportError(f"{label} must be unique and canonical")
    return result


def _coordinate(value: Any, *, metric: bool, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"units", "upAxis", "forwardAxis", "handedness"}:
        raise RoboScanExportError(f"{label} fields are not exact")
    expected_units = "meters" if metric else "relative"
    if value.get("units") != expected_units or value.get("upAxis") != "+Z" or value.get("forwardAxis") != "+Y" or value.get("handedness") != "right":
        raise RoboScanExportError(f"{label} contradicts authority or convention")
    return dict(value)


def _scene_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("/") or value == "/" or value.endswith("/"):
        raise RoboScanExportError(f"{label} must be an absolute canonical scene path")
    parts = value.split("/")[1:]
    if not parts or parts[0] != "World" or any(_SCENE_SEGMENT.fullmatch(part) is None for part in parts):
        raise RoboScanExportError(f"{label} must be rooted below /World")
    return value


def _parent_path(path: str) -> str | None:
    if path == "/World":
        return None
    parent = str(PurePosixPath(path).parent)
    return parent if parent.startswith("/") else f"/{parent}"


def _validate_asset(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"uri", "sha256", "bytes", "mediaType"}:
        raise RoboScanExportError(f"{label} fields are not exact")
    if not isinstance(value.get("bytes"), int) or isinstance(value["bytes"], bool) or value["bytes"] <= 0:
        raise RoboScanExportError(f"{label}.bytes is invalid")
    if not isinstance(value.get("mediaType"), str) or not value["mediaType"]:
        raise RoboScanExportError(f"{label}.mediaType is invalid")
    return {
        "uri": _safe_uri(value.get("uri"), label=f"{label}.uri"),
        "sha256": _sha256(value.get("sha256"), label=f"{label}.sha256"),
        "bytes": value["bytes"],
        "mediaType": value["mediaType"],
    }


def _manifest_identity(manifest: Mapping[str, Any]) -> str:
    core = deepcopy(dict(manifest))
    core.pop("manifestSha256", None)
    return _sha256_bytes(_canonical_bytes(core))


def _validate_manifest(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    required = {"schemaVersion", "sceneId", "manifestSha256", "metricAuthority", "coordinateSystem", "provenance", "nodes"}
    if not isinstance(payload, Mapping) or set(payload) != required or payload.get("schemaVersion") != MANIFEST_SCHEMA:
        raise RoboScanExportError("manifest schema fields are not exact")
    _identifier(payload.get("sceneId"), label="manifest sceneId")
    if not isinstance(payload.get("metricAuthority"), bool):
        raise RoboScanExportError("manifest metricAuthority must be boolean")
    metric = payload["metricAuthority"]
    _sha256(payload.get("manifestSha256"), label="manifest manifestSha256")
    if payload["manifestSha256"] != _manifest_identity(payload):
        raise RoboScanExportError("manifest identity checksum is invalid")
    coordinate = _coordinate(payload.get("coordinateSystem"), metric=metric, label="manifest coordinateSystem")
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping) or set(provenance) != {"sourceClassification", "sourceArtifactIds", "privacyReview"}:
        raise RoboScanExportError("manifest provenance fields are not exact")
    source = provenance.get("sourceClassification")
    if not isinstance(source, str) or not source:
        raise RoboScanExportError("manifest sourceClassification is invalid")
    if not metric and source not in {"synthetic_fixture", "private_reference_observations"}:
        raise RoboScanExportError("non-metric manifest source classification is invalid")
    if metric and source in {"synthetic_fixture", "private_reference_observations"}:
        raise RoboScanExportError("reference provenance cannot claim metric authority")
    _require_sorted_identifiers(provenance.get("sourceArtifactIds"), label="manifest sourceArtifactIds")
    if provenance.get("privacyReview") != {"rawObservationPublished": False, "sourcePathsPublished": False}:
        raise RoboScanExportError("manifest privacy review is invalid")
    nodes = payload.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise RoboScanExportError("manifest nodes are required")
    assets: dict[str, dict[str, Any]] = {}
    bindings: list[dict[str, Any]] = []
    paths: set[str] = set()
    ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, Mapping):
            raise RoboScanExportError("manifest node must be an object")
        base = {"id", "path", "parentPath", "kind", "authority", "layer", "localTransform", "visible", "viewerDefaultVisible", "provenance"}
        allowed = base | {"asset", "uncertainty"}
        if not set(node).issubset(allowed) or not base.issubset(node):
            raise RoboScanExportError("manifest node fields are not recognized")
        identifier = _identifier(node.get("id"), label="manifest node id")
        if identifier in ids:
            raise RoboScanExportError("manifest node IDs must be unique")
        ids.add(identifier)
        path = _scene_path(node.get("path"), label="manifest node path")
        if path in paths or node.get("parentPath") != _parent_path(path):
            raise RoboScanExportError("manifest node hierarchy is invalid")
        paths.add(path)
        if node.get("authority") not in {"measured", "appearance", "inferred", "reference_only"} or node.get("layer") != node.get("authority"):
            raise RoboScanExportError("manifest node authority/layer is invalid")
        if not isinstance(node.get("kind"), str) or not node["kind"]:
            raise RoboScanExportError("manifest node kind is invalid")
        if not isinstance(node.get("visible"), bool) or not isinstance(node.get("viewerDefaultVisible"), bool):
            raise RoboScanExportError("manifest visibility flags are invalid")
        transform = _rigid_transform(node.get("localTransform"), label="manifest node transform")
        node_provenance = node.get("provenance")
        if not isinstance(node_provenance, Mapping) or set(node_provenance) != {"observationIds"}:
            raise RoboScanExportError("manifest node provenance is invalid")
        observation_ids = _require_sorted_identifiers(node_provenance.get("observationIds"), label="manifest node observationIds")
        uncertainty = _uncertainty(node.get("uncertainty", {"state": "not_provided"}), metric=metric, label="manifest node uncertainty")
        if "asset" in node:
            asset = _validate_asset(node["asset"], label="manifest node asset")
            previous = assets.setdefault(asset["uri"], asset)
            if previous != asset:
                raise RoboScanExportError("manifest asset URI has conflicting bindings")
        elif node["kind"] != "group":
            raise RoboScanExportError("manifest non-group node requires an asset")
        bindings.append({
            "id": identifier,
            "path": path,
            "parentPath": node["parentPath"],
            "authority": node["authority"],
            "localTransform": transform,
            "uncertainty": uncertainty,
            "provenanceObservationIds": observation_ids,
        })
    if any(path != "/World" and _parent_path(path) not in paths for path in paths):
        raise RoboScanExportError("manifest node parent is missing")
    return deepcopy(dict(payload)), [assets[key] for key in sorted(assets)], bindings


def _receipt_checksum(receipt: Mapping[str, Any]) -> str:
    core = deepcopy(dict(receipt))
    core.pop("receiptSha256", None)
    return _sha256_bytes(_canonical_bytes(core))


def _validate_metric_evidence(value: Any, *, metric: bool) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RoboScanExportError("receipt metricEvidence must be an object")
    if not metric:
        if value != {"captureCalibrationVerified": False, "evidence": []}:
            raise RoboScanExportError("non-metric receipt may not carry metric evidence")
        return {"captureCalibrationVerified": False, "evidence": []}
    if value.get("schemaVersion") != "so101.metric-export-evidence.v1" or value.get("captureCalibrationVerified") is not True:
        raise RoboScanExportError("metric receipt requires calibration evidence")
    entries = value.get("evidence")
    if not isinstance(entries, list) or len(entries) != len(_METRIC_EVIDENCE_IDS):
        raise RoboScanExportError("metric evidence entries are incomplete")
    identifiers = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"id", "schemaVersion", "sha256"}:
            raise RoboScanExportError("metric evidence entry fields are not exact")
        identifiers.append(_identifier(entry.get("id"), label="metric evidence id"))
        if not isinstance(entry.get("schemaVersion"), str) or not entry["schemaVersion"]:
            raise RoboScanExportError("metric evidence schema is invalid")
        _sha256(entry.get("sha256"), label="metric evidence sha256")
    if tuple(identifiers) != _METRIC_EVIDENCE_IDS:
        raise RoboScanExportError("metric evidence identities are not canonical")
    return deepcopy(dict(value))


def _validate_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schemaVersion", "exportId", "exportVersion", "scene", "assets", "nodeBindings", "metricEvidence", "disposition", "privacy", "receiptSha256"}
    if not isinstance(payload, Mapping) or set(payload) != required or payload.get("schemaVersion") != RECEIPT_SCHEMA:
        raise RoboScanExportError("receipt schema fields are not exact")
    _identifier(payload.get("exportId"), label="receipt exportId")
    if payload.get("exportVersion") != 1:
        raise RoboScanExportError("receipt exportVersion is unsupported")
    _sha256(payload.get("receiptSha256"), label="receipt checksum")
    if payload["receiptSha256"] != _receipt_checksum(payload):
        raise RoboScanExportError("receipt checksum is invalid")
    scene = payload.get("scene")
    if not isinstance(scene, Mapping) or set(scene) != {"manifest", "manifestSha256", "metricAuthority", "coordinateSystem", "provenance"}:
        raise RoboScanExportError("receipt scene fields are not exact")
    if not isinstance(scene.get("metricAuthority"), bool):
        raise RoboScanExportError("receipt metricAuthority must be boolean")
    manifest = scene.get("manifest")
    if not isinstance(manifest, Mapping) or set(manifest) != {"uri", "sha256", "bytes"} or manifest.get("uri") != MANIFEST_FILE:
        raise RoboScanExportError("receipt manifest binding is invalid")
    _validate_asset({**manifest, "mediaType": "application/json"}, label="receipt manifest")
    _sha256(scene.get("manifestSha256"), label="receipt manifestSha256")
    _coordinate(scene.get("coordinateSystem"), metric=scene["metricAuthority"], label="receipt coordinateSystem")
    if not isinstance(scene.get("provenance"), Mapping):
        raise RoboScanExportError("receipt provenance must be an object")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets or assets != sorted(assets, key=lambda item: item.get("uri", "") if isinstance(item, Mapping) else ""):
        raise RoboScanExportError("receipt assets must be sorted and non-empty")
    normalized_assets = [_validate_asset(asset, label="receipt asset") for asset in assets]
    if len({asset["uri"] for asset in normalized_assets}) != len(normalized_assets):
        raise RoboScanExportError("receipt asset URIs must be unique")
    bindings = payload.get("nodeBindings")
    if not isinstance(bindings, list) or not bindings:
        raise RoboScanExportError("receipt node bindings are required")
    normalized_bindings = []
    for binding in bindings:
        required_binding = {"id", "path", "parentPath", "authority", "localTransform", "uncertainty", "provenanceObservationIds"}
        if not isinstance(binding, Mapping) or set(binding) != required_binding:
            raise RoboScanExportError("receipt node binding fields are not exact")
        path = _scene_path(binding.get("path"), label="receipt node path")
        if binding.get("parentPath") != _parent_path(path):
            raise RoboScanExportError("receipt node hierarchy is invalid")
        if binding.get("authority") not in {"measured", "appearance", "inferred", "reference_only"}:
            raise RoboScanExportError("receipt node authority is invalid")
        normalized_bindings.append({
            "id": _identifier(binding.get("id"), label="receipt node id"),
            "path": path,
            "parentPath": binding["parentPath"],
            "authority": binding["authority"],
            "localTransform": _rigid_transform(binding.get("localTransform"), label="receipt node transform"),
            "uncertainty": _uncertainty(binding.get("uncertainty"), metric=scene["metricAuthority"], label="receipt node uncertainty"),
            "provenanceObservationIds": _require_sorted_identifiers(binding.get("provenanceObservationIds"), label="receipt node provenanceObservationIds"),
        })
    if len({binding["id"] for binding in normalized_bindings}) != len(normalized_bindings) or len({binding["path"] for binding in normalized_bindings}) != len(normalized_bindings):
        raise RoboScanExportError("receipt node identities must be unique")
    _validate_metric_evidence(payload.get("metricEvidence"), metric=scene["metricAuthority"])
    expected_disposition = {"kind": "twin_candidate_only", "physicalTwinQualified": False, "physicalTransferReady": False, "promotionEligible": False, "simulationTrainingReady": False}
    if payload.get("disposition") != expected_disposition:
        raise RoboScanExportError("receipt disposition is not candidate-only")
    if payload.get("privacy") != {"rawObservationPublished": False, "sourcePathsPublished": False}:
        raise RoboScanExportError("receipt privacy is invalid")
    return deepcopy(dict(payload))


def _assert_external_immutable_root(root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise RoboScanExportError("export root must be one real directory")
    resolved = root.resolve(strict=True)
    current = resolved
    while True:
        if (current / ".git").exists() or (current / ".git").is_symlink():
            raise RoboScanExportError("export root must be a copied directory outside a live checkout")
        if current.parent == current:
            break
        current = current.parent
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise RoboScanExportError("immutable export may not contain symlinks")
    return resolved


def _validate_lock(payload: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schemaVersion", "lockId", "producer", "acceptedReceipt", "fixtureFiles", "identitySha256"}
    if not isinstance(payload, Mapping) or set(payload) != required or payload.get("schemaVersion") != LOCK_SCHEMA:
        raise RoboScanExportError("compatibility lock schema fields are not exact")
    _identifier(payload.get("lockId"), label="compatibility lockId")
    producer = payload.get("producer")
    if not isinstance(producer, Mapping) or set(producer) != {"repository", "commit"} or producer.get("repository") != "robo-scan":
        raise RoboScanExportError("compatibility lock producer is invalid")
    if not isinstance(producer.get("commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", producer["commit"]):
        raise RoboScanExportError("compatibility lock producer commit is invalid")
    accepted = payload.get("acceptedReceipt")
    if not isinstance(accepted, Mapping) or set(accepted) != {"schemaVersion", "exportId", "receiptSha256", "manifestSha256", "metricAuthority"}:
        raise RoboScanExportError("compatibility lock receipt binding is invalid")
    if accepted.get("schemaVersion") != RECEIPT_SCHEMA or not isinstance(accepted.get("metricAuthority"), bool):
        raise RoboScanExportError("compatibility lock receipt authority is invalid")
    _identifier(accepted.get("exportId"), label="compatibility lock exportId")
    _sha256(accepted.get("receiptSha256"), label="compatibility lock receiptSha256")
    _sha256(accepted.get("manifestSha256"), label="compatibility lock manifestSha256")
    files = payload.get("fixtureFiles")
    if not isinstance(files, list) or not files or files != sorted(files, key=lambda item: item.get("uri", "") if isinstance(item, Mapping) else ""):
        raise RoboScanExportError("compatibility lock fixture files are invalid")
    normalized = [_validate_asset(item, label="compatibility lock fixture file") for item in files]
    if len({item["uri"] for item in normalized}) != len(normalized):
        raise RoboScanExportError("compatibility lock fixture URIs are not unique")
    _sha256(payload.get("identitySha256"), label="compatibility lock checksum")
    core = deepcopy(dict(payload))
    core.pop("identitySha256")
    if payload["identitySha256"] != _sha256_bytes(_canonical_bytes(core)):
        raise RoboScanExportError("compatibility lock checksum is invalid")
    return deepcopy(dict(payload))


def load_compatibility_lock(path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RoboScanExportError("compatibility lock must be one real file")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoboScanExportError("compatibility lock cannot be read") from exc

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RoboScanExportError("compatibility lock has a duplicate key")
            result[key] = value
        return result

    try:
        payload = json.loads(raw, object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoboScanExportError("compatibility lock is not valid JSON") from exc
    return _validate_lock(payload)


def validate_robo_scan_export(*, export_root: Path, lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    """Independently reopen a selected copied receipt and its declared files."""

    root = _assert_external_immutable_root(export_root)
    lock = load_compatibility_lock(lock_path)
    receipt = _validate_receipt(_load_canonical(root / RECEIPT_FILE, label="export receipt"))
    manifest_path = root / MANIFEST_FILE
    manifest_payload = _load_canonical(manifest_path, label="export manifest")
    manifest_file = {"uri": MANIFEST_FILE, "sha256": _sha256_file(manifest_path), "bytes": manifest_path.stat().st_size, "mediaType": "application/json"}
    bound_manifest = {**receipt["scene"]["manifest"], "mediaType": "application/json"}
    if manifest_file != bound_manifest:
        raise RoboScanExportError("manifest bytes differ from receipt binding")
    manifest, manifest_assets, manifest_bindings = _validate_manifest(manifest_payload)
    if manifest["manifestSha256"] != receipt["scene"]["manifestSha256"] or manifest["metricAuthority"] != receipt["scene"]["metricAuthority"]:
        raise RoboScanExportError("receipt identity/authority differs from manifest")
    if manifest["coordinateSystem"] != receipt["scene"]["coordinateSystem"] or manifest["provenance"] != receipt["scene"]["provenance"]:
        raise RoboScanExportError("receipt provenance/coordinate differs from manifest")
    if manifest_assets != receipt["assets"] or manifest_bindings != receipt["nodeBindings"]:
        raise RoboScanExportError("receipt asset/transform/uncertainty binding differs from manifest")
    expected_files = {RECEIPT_FILE, MANIFEST_FILE, *(item["uri"] for item in receipt["assets"])}
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual_files != expected_files:
        raise RoboScanExportError("export contains an unbound or missing file")
    for asset in receipt["assets"]:
        path = root / asset["uri"]
        if not path.is_file() or path.is_symlink():
            raise RoboScanExportError("receipt-bound asset is missing")
        if path.stat().st_size != asset["bytes"] or _sha256_file(path) != asset["sha256"]:
            raise RoboScanExportError("asset bytes differ from receipt binding")
    accepted = lock["acceptedReceipt"]
    actual = {
        "schemaVersion": receipt["schemaVersion"],
        "exportId": receipt["exportId"],
        "receiptSha256": receipt["receiptSha256"],
        "manifestSha256": receipt["scene"]["manifestSha256"],
        "metricAuthority": receipt["scene"]["metricAuthority"],
    }
    if actual != accepted:
        raise RoboScanExportError("export is not bound by the approved compatibility lock")
    if lock["fixtureFiles"] != [bound_manifest, *receipt["assets"]]:
        raise RoboScanExportError("compatibility lock fixture identity differs from receipt")
    return {"receipt": receipt, "manifest": manifest, "lock": lock}


def build_twin_candidate(*, export_root: Path, lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    """Build metadata only after all independent receipt checks have passed."""

    verified = validate_robo_scan_export(export_root=export_root, lock_path=lock_path)
    receipt = verified["receipt"]
    metric = receipt["scene"]["metricAuthority"]
    candidate = {
        "schemaVersion": CANDIDATE_SCHEMA,
        "candidateId": f"robo_scan_{receipt['exportId']}",
        "candidateClass": "metric_workcell_candidate" if metric else "reference_only_visual_context",
        "producer": deepcopy(verified["lock"]["producer"]),
        "source": {
            "receiptSha256": receipt["receiptSha256"],
            "manifestSha256": receipt["scene"]["manifestSha256"],
            "exportId": receipt["exportId"],
        },
        "coordinateSystem": deepcopy(receipt["scene"]["coordinateSystem"]),
        "provenance": deepcopy(receipt["scene"]["provenance"]),
        "nodeBindings": [
            {
                "id": binding["id"],
                "path": binding["path"],
                "parentPath": binding["parentPath"],
                "sourceLayer": binding["authority"],
                "localTransform": deepcopy(binding["localTransform"]),
                "uncertainty": deepcopy(binding["uncertainty"]),
                "provenanceObservationIds": deepcopy(binding["provenanceObservationIds"]),
            }
            for binding in receipt["nodeBindings"]
        ],
        "assets": deepcopy(receipt["assets"]),
        "simulationAssetCompilation": {
            "eligible": metric,
            "reason": "metric_candidate_requires_separate_compiler_review" if metric else "relative_reference_content_is_visual_context_only",
        },
    }
    _assert_non_authorizing(candidate)
    candidate["identitySha256"] = _sha256_bytes(_canonical_bytes(candidate))
    return candidate


def _assert_non_authorizing(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = set(value) & _GLOBAL_FIELDS
        if forbidden:
            raise RoboScanExportError(f"candidate attempted global authority fields: {sorted(forbidden)}")
        for child in value.values():
            _assert_non_authorizing(child)
    elif isinstance(value, list):
        for child in value:
            _assert_non_authorizing(child)


def write_twin_candidate(*, export_root: Path, output_path: Path, lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, Any]:
    if output_path.exists() or output_path.is_symlink():
        raise RoboScanExportError("candidate output must not already exist")
    candidate = build_twin_candidate(export_root=export_root, lock_path=lock_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_canonical_bytes(candidate))
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independently validate a copied Robo Scan export receipt.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("verify", "candidate"):
        subparser = subparsers.add_parser(action)
        subparser.add_argument("--export-root", required=True, type=Path)
        subparser.add_argument("--lock", type=Path, default=DEFAULT_LOCK_PATH)
        if action == "candidate":
            subparser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "verify":
            result = validate_robo_scan_export(export_root=args.export_root, lock_path=args.lock)
            output = {"exportId": result["receipt"]["exportId"], "manifestSha256": result["receipt"]["scene"]["manifestSha256"], "receiptSha256": result["receipt"]["receiptSha256"], "metricAuthority": result["receipt"]["scene"]["metricAuthority"]}
        elif args.output is None:
            output = build_twin_candidate(export_root=args.export_root, lock_path=args.lock)
        else:
            output = write_twin_candidate(export_root=args.export_root, output_path=args.output, lock_path=args.lock)
    except (OSError, RoboScanExportError) as exc:
        print(f"Robo Scan export rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
