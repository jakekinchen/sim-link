"""Deterministic structural diff between the active SO-101 runtime and Menagerie."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.robotics_dependency_lock import (
    MENAGERIE_VENDORED_ROOT,
    verify_robotics_dependency_lock,
)
from scenesmith.robot_lab.twin_contract import DEFAULT_DEPENDENCY_LOCK_PATH


STRUCTURAL_TWIN_DIFF_SCHEMA_VERSION = "scenesmith.structural_twin_diff.v1"
DEFAULT_STRUCTURAL_TWIN_DIFF_PATH = Path(
    "configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json"
)
REQUIRED_CATEGORIES = (
    "inertials",
    "joint_frames",
    "joint_limits",
    "actuators",
    "arm_collisions",
    "gripper_collisions",
    "cameras",
    "solver_settings",
    "friction",
    "backlash",
    "named_sites",
)
DIFF_DECISIONS = {"adopt", "adapt", "retain"}


def build_structural_twin_diff(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    dependency_lock = _load_dependency_lock(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    runtime_source = dependency_lock["payload"]["runtime_contract"]["source_mjcf"]
    menagerie_source = _menagerie_so101_source(dependency_lock["payload"])

    runtime_path = repo_root / runtime_source["path"]
    menagerie_path = repo_root / menagerie_source["path"]
    _verify_source_evidence(
        runtime_source,
        actual_path=runtime_path,
        expected_rel_path=runtime_source["path"],
        hash_error="Runtime source hash drifted",
    )
    _verify_source_evidence(
        menagerie_source,
        actual_path=menagerie_path,
        expected_rel_path=menagerie_source["path"],
        hash_error="Menagerie source hash drifted",
    )

    runtime_model = _extract_model(runtime_path)
    menagerie_model = _extract_model(menagerie_path)

    payload = {
        "schema_version": STRUCTURAL_TWIN_DIFF_SCHEMA_VERSION,
        "artifact_name": "pi05_structural_twin_diff_simulation_only",
        "dependency_lock_ref": dependency_lock["ref"],
        "sources": {
            "runtime": _artifact_source_record(runtime_source),
            "menagerie": _artifact_source_record(menagerie_source),
        },
        "categories": {
            category_name: _compare_category(
                category_name,
                runtime_model["categories"][category_name],
                menagerie_model["categories"][category_name],
            )
            for category_name in REQUIRED_CATEGORIES
        },
    }
    payload["summary"] = _build_summary(payload["categories"])
    payload["identity_sha256"] = _sign(payload)
    return payload


def verify_structural_twin_diff(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> None:
    repo_root = repo_root.resolve()
    if payload.get("schema_version") != STRUCTURAL_TWIN_DIFF_SCHEMA_VERSION:
        raise ValueError("Unsupported structural twin diff schema")
    _verify_identity(payload)
    missing_categories = set(REQUIRED_CATEGORIES) - set(payload.get("categories", {}))
    if missing_categories:
        raise ValueError(
            "Missing structural diff categories: " + ", ".join(sorted(missing_categories))
        )
    for category_name in REQUIRED_CATEGORIES:
        category = payload["categories"][category_name]
        if set(category) != {"matched", "mismatched", "missing", "extra", "unknown"}:
            raise ValueError(f"Structural diff category buckets drifted: {category_name}")
        for bucket_name in ("mismatched", "missing", "extra"):
            for record in category[bucket_name]:
                if record.get("decision") not in DIFF_DECISIONS:
                    raise ValueError(f"Structural diff record missing decision: {category_name}")

    dependency_lock = _load_dependency_lock(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    if payload["dependency_lock_ref"] != dependency_lock["ref"]:
        raise ValueError("Structural diff dependency lock reference drifted")

    runtime_source = dependency_lock["payload"]["runtime_contract"]["source_mjcf"]
    menagerie_source = _menagerie_so101_source(dependency_lock["payload"])
    _verify_payload_source_record(
        payload["sources"]["runtime"],
        expected=runtime_source,
        hash_error="Runtime source hash drifted",
    )
    _verify_payload_source_record(
        payload["sources"]["menagerie"],
        expected=menagerie_source,
        hash_error="Menagerie source hash drifted",
    )

    _verify_source_evidence(
        runtime_source,
        actual_path=repo_root / runtime_source["path"],
        expected_rel_path=runtime_source["path"],
        hash_error="Runtime source hash drifted",
    )
    _verify_source_evidence(
        menagerie_source,
        actual_path=repo_root / menagerie_source["path"],
        expected_rel_path=menagerie_source["path"],
        hash_error="Menagerie source hash drifted",
    )

    expected = build_structural_twin_diff(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    if payload != expected:
        raise ValueError("Structural twin diff artifact drifted from repo state")


def write_structural_twin_diff(
    *,
    repo_root: Path,
    output_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
) -> dict[str, Any]:
    payload = build_structural_twin_diff(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
    )
    artifact_path = output_path if output_path.is_absolute() else repo_root / output_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _load_dependency_lock(*, repo_root: Path, dependency_lock_path: Path) -> dict[str, Any]:
    resolved = dependency_lock_path if dependency_lock_path.is_absolute() else repo_root / dependency_lock_path
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    verify_robotics_dependency_lock(payload, repo_root=repo_root)
    return {
        "payload": payload,
        "ref": {
            "path": str(Path(payload_path := str(dependency_lock_path)).as_posix()),
            "identity_sha256": payload["identity_sha256"],
        },
    }


def _artifact_source_record(source_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": source_evidence["path"],
        "sha256": source_evidence["sha256"],
        "size_bytes": source_evidence["size_bytes"],
    }


def _menagerie_so101_source(dependency_lock: dict[str, Any]) -> dict[str, Any]:
    vendored_files = dependency_lock["dependencies"]["menagerie_robotstudio_so101"]["vendored_files"]
    for evidence in vendored_files:
        if evidence.get("upstream_path") == "robotstudio_so101/so101.xml":
            return {
                "path": evidence["path"],
                "sha256": evidence["sha256"],
                "size_bytes": evidence["size_bytes"],
            }
    raise ValueError("Menagerie so101.xml vendored evidence is missing")


def _extract_model(xml_path: Path) -> dict[str, Any]:
    root = ET.parse(xml_path).getroot()
    defaults = _collect_defaults(root)
    categories = {
        "inertials": _extract_inertials(root),
        "joint_frames": _extract_joint_frames(root),
        "joint_limits": _extract_joint_limits(root),
        "actuators": _extract_actuators(root, defaults),
        "arm_collisions": _extract_collision_geoms(root, defaults, gripper_only=False),
        "gripper_collisions": _extract_collision_geoms(root, defaults, gripper_only=True),
        "cameras": _extract_cameras(root),
        "solver_settings": _extract_solver_settings(root),
        "friction": _extract_friction(root, defaults),
        "backlash": _extract_backlash(root, defaults),
        "named_sites": _extract_named_sites(root),
    }
    return {"categories": categories}


def _collect_defaults(root: ET.Element) -> dict[str, dict[str, dict[str, Any]]]:
    classes: dict[str, dict[str, dict[str, Any]]] = {}
    for default_root in root.findall("./default"):
        _walk_default(default_root, inherited={}, classes=classes)
    return classes


def _walk_default(
    element: ET.Element,
    *,
    inherited: dict[str, dict[str, Any]],
    classes: dict[str, dict[str, dict[str, Any]]],
) -> None:
    current = {tag: dict(attrs) for tag, attrs in inherited.items()}
    for child in element:
        if child.tag in {"joint", "position", "geom"}:
            current.setdefault(child.tag, {}).update(_normalize_attrs(child.attrib))
    class_name = element.attrib.get("class")
    if class_name:
        classes[class_name] = {
            tag: dict(attrs)
            for tag, attrs in current.items()
        }
    for child in element.findall("./default"):
        _walk_default(child, inherited=current, classes=classes)


def _extract_inertials(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        inertial = body.find("./inertial")
        if inertial is None:
            continue
        records[f"body:{body_path}"] = _normalize_attrs(inertial.attrib)
    return records


def _extract_joint_frames(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        if body.find("./joint") is None:
            continue
        records[f"body:{body_path}"] = {
            "name": body.attrib.get("name", body_path.split("/")[-1]),
            "pos": _normalize_vector(body.attrib.get("pos")),
            "quat": _normalize_vector(body.attrib.get("quat")),
        }
    return records


def _extract_joint_limits(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        for joint in body.findall("./joint"):
            name = joint.attrib.get("name")
            if not name:
                continue
            records[f"joint:{name}"] = {
                "parent_body": body_path,
                **_normalize_attrs(joint.attrib),
            }
    return records


def _extract_actuators(root: ET.Element, defaults: dict[str, dict[str, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for actuator in root.findall("./actuator/position"):
        name = actuator.attrib.get("name")
        if not name:
            continue
        attrs = _normalize_attrs(actuator.attrib)
        class_name = actuator.attrib.get("class")
        effective = _resolved_default_attrs(class_name, "position", defaults)
        effective.update(attrs)
        records[f"actuator:{name}"] = effective
    return records


def _extract_collision_geoms(
    root: ET.Element,
    defaults: dict[str, dict[str, dict[str, Any]]],
    *,
    gripper_only: bool,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        in_gripper = body_path == "base/shoulder/upper_arm/lower_arm/wrist/gripper" or body_path.startswith(
            "base/shoulder/upper_arm/lower_arm/wrist/gripper/"
        )
        if in_gripper != gripper_only:
            continue
        for index, geom in enumerate(body.findall("./geom")):
            if not _is_collision_geom(geom):
                continue
            key_name = geom.attrib.get("name") or f"{body.attrib.get('name', 'body')}[{index}]"
            attrs = _normalize_attrs(geom.attrib)
            class_name = geom.attrib.get("class")
            effective = _resolved_default_attrs(class_name, "geom", defaults)
            effective.update(attrs)
            effective["parent_body"] = body_path
            records[f"geom:{body_path}:{key_name}"] = effective
    return records


def _extract_cameras(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        for camera in body.findall("./camera"):
            name = camera.attrib.get("name")
            if not name:
                continue
            records[f"camera:{name}"] = {
                "parent_body": body_path,
                **_normalize_attrs(camera.attrib),
            }
    return records


def _extract_solver_settings(root: ET.Element) -> dict[str, dict[str, Any]]:
    option = root.find("./option")
    if option is None:
        return {}
    return {"option:global": _normalize_attrs(option.attrib)}


def _extract_friction(
    root: ET.Element,
    defaults: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for class_name in ("so101", "so101_new_calib", "sts3215", "collision", "collision_gripper", "collision_gripper_mesh"):
        class_attrs = defaults.get(class_name, {})
        for tag_name in ("joint", "geom"):
            attrs = class_attrs.get(tag_name)
            if not attrs:
                continue
            filtered = {
                key: value
                for key, value in attrs.items()
                if key in {"damping", "frictionloss", "armature", "condim", "friction", "solref", "priority"}
            }
            if filtered:
                records[f"{tag_name}:{class_name}"] = filtered
    return records


def _extract_backlash(
    root: ET.Element,
    defaults: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    backlash_attrs = defaults.get("backlash", {}).get("joint")
    if backlash_attrs:
        records["declaration:backlash"] = backlash_attrs
    attached = []
    for _, body in _iter_bodies(root):
        for joint in body.findall("./joint"):
            if joint.attrib.get("class") == "backlash":
                attached.append(joint.attrib["name"])
    records["attachments:backlash"] = {"joint_names": sorted(attached)}
    return records


def _extract_named_sites(root: ET.Element) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for body_path, body in _iter_bodies(root):
        for site in body.findall("./site"):
            name = site.attrib.get("name")
            if not name:
                continue
            records[f"site:{name}"] = {
                "parent_body": body_path,
                **_normalize_attrs(site.attrib),
            }
    return records


def _iter_bodies(root: ET.Element) -> list[tuple[str, ET.Element]]:
    bodies: list[tuple[str, ET.Element]] = []

    def walk(body: ET.Element, prefix: str) -> None:
        name = body.attrib.get("name", "unnamed")
        path = f"{prefix}/{name}" if prefix else name
        bodies.append((path, body))
        for child in body.findall("./body"):
            walk(child, path)

    for body in root.findall("./worldbody/body"):
        walk(body, "")
    return bodies


def _compare_category(
    category_name: str,
    runtime_records: dict[str, dict[str, Any]],
    menagerie_records: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    matched: list[dict[str, Any]] = []
    mismatched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    extra: list[dict[str, Any]] = []
    for key in sorted(set(runtime_records) | set(menagerie_records)):
        runtime_value = runtime_records.get(key)
        menagerie_value = menagerie_records.get(key)
        if runtime_value is None:
            missing.append(
                {
                    "key": key,
                    "menagerie": menagerie_value,
                    **_reconciliation_decision(category_name, key, difference_kind="missing"),
                }
            )
            continue
        if menagerie_value is None:
            extra.append(
                {
                    "key": key,
                    "runtime": runtime_value,
                    **_reconciliation_decision(category_name, key, difference_kind="extra"),
                }
            )
            continue
        if runtime_value == menagerie_value:
            matched.append({"key": key, "value": runtime_value})
            continue
        mismatched.append(
            {
                "key": key,
                "runtime": runtime_value,
                "menagerie": menagerie_value,
                "numeric_deltas": _numeric_deltas(runtime_value, menagerie_value),
                **_reconciliation_decision(category_name, key, difference_kind="mismatched"),
            }
        )
    return {
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
        "extra": extra,
        "unknown": [],
    }


def _reconciliation_decision(
    category_name: str,
    key: str,
    *,
    difference_kind: str,
) -> dict[str, str]:
    if difference_kind == "extra":
        return {
            "decision": "retain",
            "rationale": "The active runtime remains the baseline until a later qualified adaptation supersedes it.",
        }
    if category_name in {
        "arm_collisions",
        "gripper_collisions",
        "cameras",
        "solver_settings",
        "friction",
        "backlash",
    }:
        return {
            "decision": "adapt",
            "rationale": "Menagerie encodes additional structure that should be reviewed explicitly rather than switched in silently.",
        }
    if key in {"joint:wrist_roll", "site:gripperframe"}:
        return {
            "decision": "retain",
            "rationale": "The active runtime carries a calibrated runtime-specific value that must stay explicit until requalified.",
        }
    return {
        "decision": "retain",
        "rationale": "This slice records the active runtime as the declared baseline and defers any structural replacement.",
    }


def _numeric_deltas(runtime_value: Any, menagerie_value: Any) -> dict[str, Any]:
    deltas: dict[str, Any] = {}
    if isinstance(runtime_value, dict) and isinstance(menagerie_value, dict):
        for key in sorted(set(runtime_value) & set(menagerie_value)):
            runtime_item = runtime_value[key]
            menagerie_item = menagerie_value[key]
            if isinstance(runtime_item, list) and isinstance(menagerie_item, list):
                if all(isinstance(item, (int, float)) for item in runtime_item + menagerie_item):
                    if len(runtime_item) == len(menagerie_item):
                        diff = [round(runtime_item[i] - menagerie_item[i], 9) for i in range(len(runtime_item))]
                        if any(value != 0 for value in diff):
                            deltas[key] = diff
            elif isinstance(runtime_item, (int, float)) and isinstance(menagerie_item, (int, float)):
                delta = round(runtime_item - menagerie_item, 9)
                if delta != 0:
                    deltas[key] = delta
    return deltas


def _build_summary(categories: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    summary = {
        "matched_records": 0,
        "mismatched_records": 0,
        "missing_records": 0,
        "extra_records": 0,
        "unknown_records": 0,
        "category_totals": {},
    }
    for category_name, buckets in categories.items():
        counts = {bucket: len(records) for bucket, records in buckets.items()}
        summary["matched_records"] += counts["matched"]
        summary["mismatched_records"] += counts["mismatched"]
        summary["missing_records"] += counts["missing"]
        summary["extra_records"] += counts["extra"]
        summary["unknown_records"] += counts["unknown"]
        summary["category_totals"][category_name] = counts
    return summary


def _resolved_default_attrs(
    class_name: str | None,
    tag_name: str,
    defaults: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    if not class_name:
        return {}
    return dict(defaults.get(class_name, {}).get(tag_name, {}))


def _is_collision_geom(geom: ET.Element) -> bool:
    class_name = geom.attrib.get("class", "")
    if "collision" in class_name:
        return True
    geom_name = geom.attrib.get("name", "")
    if geom_name.startswith(("fixed_jaw_", "moving_jaw_", "camera_box")):
        return True
    geom_type = geom.attrib.get("type")
    return geom_type in {"box", "sphere", "capsule"}


def _normalize_attrs(attrs: dict[str, str]) -> dict[str, Any]:
    return {key: _normalize_attr_value(value) for key, value in sorted(attrs.items())}


def _normalize_attr_value(value: str) -> Any:
    tokens = value.split()
    if not tokens:
        return value
    if len(tokens) == 1:
        return _normalize_scalar(tokens[0])
    normalized = [_normalize_scalar(token) for token in tokens]
    if any(isinstance(item, str) for item in normalized):
        return [str(item) for item in normalized]
    return normalized


def _normalize_scalar(token: str) -> Any:
    lowered = token.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        value = float(token)
    except ValueError:
        return token
    return round(value, 9)


def _normalize_vector(value: str | None) -> list[float]:
    if value is None:
        return []
    parsed = _normalize_attr_value(value)
    if isinstance(parsed, list):
        return parsed
    return [parsed]


def _verify_source_evidence(
    evidence: dict[str, Any],
    *,
    actual_path: Path,
    expected_rel_path: str,
    hash_error: str,
) -> None:
    if evidence["path"] != expected_rel_path:
        raise ValueError(f"Source path drifted: {expected_rel_path}")
    if not actual_path.exists():
        raise ValueError(f"Missing source file: {expected_rel_path}")
    contents = actual_path.read_bytes()
    digest = hashlib.sha256(contents).hexdigest()
    if digest != evidence["sha256"]:
        raise ValueError(hash_error)
    if len(contents) != evidence["size_bytes"]:
        raise ValueError(f"Source size drifted: {expected_rel_path}")


def _verify_payload_source_record(
    record: dict[str, Any],
    *,
    expected: dict[str, Any],
    hash_error: str,
) -> None:
    if record["path"] != expected["path"]:
        raise ValueError(f"Source path drifted: {expected['path']}")
    if record["sha256"] != expected["sha256"]:
        raise ValueError(hash_error)
    if record["size_bytes"] != expected["size_bytes"]:
        raise ValueError(f"Source size drifted: {expected['path']}")


def _sign(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _verify_identity(payload: dict[str, Any]) -> None:
    if payload.get("identity_sha256") != _sign(payload):
        raise ValueError("Structural twin diff identity hash is invalid")
