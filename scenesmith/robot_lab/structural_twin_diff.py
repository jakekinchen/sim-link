"""Deterministic structural diff between the active SO-101 runtime and Menagerie."""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.robotics_dependency_lock import (
    MENAGERIE_VENDORED_ROOT,
    verify_robotics_dependency_lock,
)
from scenesmith.robot_lab.twin_contract import (
    DEFAULT_DEPENDENCY_LOCK_PATH,
    DEFAULT_TWIN_PROFILE_PATH,
    verify_twin_profile,
)


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
MUJOCO_OPTION_DEFAULTS = {
    "cone": "pyramidal",
    "impratio": 1.0,
    "integrator": "euler",
    "iterations": 100.0,
    "ls_iterations": 50.0,
    "timestep": 0.002,
}
IDENTITY_QUATERNION = [1.0, 0.0, 0.0, 0.0]
QUATERNION_SEMANTIC_CATEGORIES = {
    "joint_frames",
    "arm_collisions",
    "gripper_collisions",
    "cameras",
    "named_sites",
}
QUATERNION_TOLERANCE = 1e-7
FRICTION_RELEVANT_KEYS = {"damping", "frictionloss", "armature", "condim", "friction", "solref", "priority"}
UNNAMED_GEOM_IDENTITY_VERSION = "scenesmith.structural_twin_diff.unnamed_geom_identity.v1"
UNNAMED_GEOM_IDENTITY_FIELDS = (
    "type",
    "mesh",
    "size",
    "fromto",
    "pos",
    "quat",
    "axisangle",
    "euler",
    "xyaxes",
    "zaxis",
)


def build_structural_twin_diff(
    *,
    repo_root: Path,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    dependency_lock = _load_dependency_lock(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    twin_profile = _load_twin_profile(
        repo_root=repo_root,
        twin_profile_path=twin_profile_path,
        dependency_lock_path=dependency_lock_path,
    )
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
        "twin_profile_ref": twin_profile["ref"],
        "identifier_strategy": {
            "unnamed_geom_identity": {
                "version": UNNAMED_GEOM_IDENTITY_VERSION,
                "key_fields": list(UNNAMED_GEOM_IDENTITY_FIELDS),
            }
        },
        "sources": {
            "runtime": _artifact_source_record(runtime_source),
            "menagerie": _artifact_source_record(menagerie_source),
        },
        "categories": {
            category_name: _compare_extracted_category(
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
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
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
        for bucket_name in ("mismatched", "missing", "extra", "unknown"):
            for record in category[bucket_name]:
                if record.get("decision") not in DIFF_DECISIONS:
                    raise ValueError(f"Structural diff record missing decision: {category_name}")

    dependency_lock = _load_dependency_lock(repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    if payload["dependency_lock_ref"] != dependency_lock["ref"]:
        raise ValueError("Structural diff dependency lock reference drifted")
    twin_profile = _load_twin_profile(
        repo_root=repo_root,
        twin_profile_path=twin_profile_path,
        dependency_lock_path=dependency_lock_path,
    )
    if payload.get("twin_profile_ref") != twin_profile["ref"]:
        raise ValueError("Twin profile identity drifted")

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
        twin_profile_path=twin_profile_path,
    )
    if payload != expected:
        raise ValueError("Structural twin diff artifact drifted from repo state")


def write_structural_twin_diff(
    *,
    repo_root: Path,
    output_path: Path = DEFAULT_STRUCTURAL_TWIN_DIFF_PATH,
    dependency_lock_path: Path = DEFAULT_DEPENDENCY_LOCK_PATH,
    twin_profile_path: Path = DEFAULT_TWIN_PROFILE_PATH,
) -> dict[str, Any]:
    payload = build_structural_twin_diff(
        repo_root=repo_root,
        dependency_lock_path=dependency_lock_path,
        twin_profile_path=twin_profile_path,
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


def _load_twin_profile(
    *,
    repo_root: Path,
    twin_profile_path: Path,
    dependency_lock_path: Path,
) -> dict[str, Any]:
    resolved = twin_profile_path if twin_profile_path.is_absolute() else repo_root / twin_profile_path
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    verify_twin_profile(payload, repo_root=repo_root, dependency_lock_path=dependency_lock_path)
    return {
        "payload": payload,
        "ref": {
            "path": str(Path(str(twin_profile_path)).as_posix()),
            "schema_version": payload["schema_version"],
            "identity_sha256": payload["identity_sha256"],
            "file_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        },
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
        "joint_frames": _category_records(_extract_joint_frames(root)),
        "joint_limits": _category_records(_extract_joint_limits(root)),
        "actuators": _category_records(_extract_actuators(root, defaults)),
        "arm_collisions": _category_records(_extract_collision_geoms(root, defaults, gripper_only=False)),
        "gripper_collisions": _category_records(_extract_collision_geoms(root, defaults, gripper_only=True)),
        "cameras": _category_records(_extract_cameras(root)),
        "solver_settings": _category_records(_extract_solver_settings(root)),
        "friction": _extract_friction(root, defaults),
        "backlash": _category_records(_extract_backlash(root, defaults)),
        "named_sites": _category_records(_extract_named_sites(root)),
    }
    return {"categories": categories}


def _category_records(
    records: dict[str, dict[str, Any]],
    *,
    unknown: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "records": records,
        "unknown": sorted(
            unknown or [],
            key=lambda record: (record.get("key", ""), record.get("side", ""), record.get("kind", "")),
        ),
    }


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


def _extract_inertials(root: ET.Element) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    unknown: list[dict[str, Any]] = []
    for body_path, body in _iter_bodies(root):
        inertial = body.find("./inertial")
        if inertial is not None:
            records[f"body:{body_path}"] = _normalize_attrs(inertial.attrib)
            continue
        inferred_geoms = []
        for index, geom in enumerate(body.findall("./geom")):
            if "mass" not in geom.attrib and "density" not in geom.attrib:
                continue
            inferred_geoms.append(
                {
                    "geom": geom.attrib.get("name") or f"geom[{index}]",
                    "mass": _normalize_attr_value(geom.attrib["mass"]) if "mass" in geom.attrib else None,
                    "density": _normalize_attr_value(geom.attrib["density"]) if "density" in geom.attrib else None,
                    "class": geom.attrib.get("class"),
                    "type": geom.attrib.get("type"),
                }
            )
        if inferred_geoms:
            unknown.append(
                {
                    "key": f"body:{body_path}",
                    "kind": "inferred_body_inertia",
                    "evidence": {"geoms": inferred_geoms},
                    "reason": "This body carries mass through attached geoms but no explicit inertial, so a truthful body inertia cannot be derived from the available XML alone.",
                }
            )
    return _category_records(records, unknown=unknown)


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
        for key_name, geom in _iter_collision_geom_keys(body_path, body):
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
    effective = dict(MUJOCO_OPTION_DEFAULTS)
    if option is not None:
        effective.update(_normalize_attrs(option.attrib))
    return {"option:global": effective}


def _extract_friction(
    root: ET.Element,
    defaults: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    unknown: list[dict[str, Any]] = []
    attached_joint_classes: set[str] = set()
    attached_geom_classes: set[str] = set()

    for body_path, body in _iter_bodies(root):
        for joint in body.findall("./joint"):
            class_name = joint.attrib.get("class")
            if class_name:
                attached_joint_classes.add(class_name)
            effective = _resolved_default_attrs(class_name, "joint", defaults)
            effective.update(_normalize_attrs(joint.attrib))
            filtered = {key: value for key, value in effective.items() if key in FRICTION_RELEVANT_KEYS}
            if filtered:
                joint_name = joint.attrib.get("name") or class_name or "unnamed_joint"
                records[f"joint:{body_path}:{joint_name}"] = filtered
        for geom_name, geom in _iter_collision_geom_keys(body_path, body):
            class_name = geom.attrib.get("class")
            if class_name:
                attached_geom_classes.add(class_name)
            effective = _resolved_default_attrs(class_name, "geom", defaults)
            effective.update(_normalize_attrs(geom.attrib))
            filtered = {key: value for key, value in effective.items() if key in FRICTION_RELEVANT_KEYS}
            if filtered:
                records[f"geom:{body_path}:{geom_name}"] = filtered

    for class_name, class_attrs in sorted(defaults.items()):
        for tag_name, attached_classes in (("joint", attached_joint_classes), ("geom", attached_geom_classes)):
            filtered = {
                key: value
                for key, value in class_attrs.get(tag_name, {}).items()
                if key in FRICTION_RELEVANT_KEYS
            }
            if not filtered or class_name in attached_classes:
                continue
            unknown.append(
                {
                    "key": f"declaration:{tag_name}:{class_name}",
                    "kind": "declaration_only_default",
                    "evidence": filtered,
                    "reason": "This default class carries contact-related settings but is not attached to a compared joint or geom, so it remains declaration-only evidence rather than effective runtime behavior.",
                }
            )
    return _category_records(records, unknown=unknown)


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


def _iter_collision_geom_keys(body_path: str, body: ET.Element) -> list[tuple[str, ET.Element]]:
    named: list[tuple[str, ET.Element]] = []
    unnamed_groups: dict[str, list[ET.Element]] = {}
    for geom in body.findall("./geom"):
        if not _is_collision_geom(geom):
            continue
        geom_name = geom.attrib.get("name")
        if geom_name:
            named.append((geom_name, geom))
            continue
        stem = _unnamed_geom_identity_stem(body_path, geom)
        unnamed_groups.setdefault(stem, []).append(geom)

    keys = list(named)
    for stem in sorted(unnamed_groups):
        geoms = unnamed_groups[stem]
        for occurrence_index, geom in enumerate(geoms, start=1):
            keys.append((f"{stem}#{occurrence_index}", geom))
    return keys


def _unnamed_geom_identity_stem(body_path: str, geom: ET.Element) -> str:
    identity_payload = {
        key: _normalize_attr_value(geom.attrib[key])
        for key in UNNAMED_GEOM_IDENTITY_FIELDS
        if key in geom.attrib
    }
    canonical = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"unnamed:{digest}"


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
        runtime_compared, menagerie_compared, comparison_metadata = _comparison_views(
            category_name,
            runtime_value,
            menagerie_value,
        )
        if _compared_records_equal(runtime_compared, menagerie_compared):
            matched.append({"key": key, "value": runtime_value})
            continue
        mismatch_record = {
            "key": key,
            "runtime": runtime_value,
            "menagerie": menagerie_value,
            "numeric_deltas": _numeric_deltas(runtime_compared, menagerie_compared),
            **_reconciliation_decision(category_name, key, difference_kind="mismatched"),
        }
        if comparison_metadata:
            mismatch_record["compared_values"] = comparison_metadata
        mismatched.append(mismatch_record)
    return {
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
        "extra": extra,
        "unknown": [],
    }


def _compare_extracted_category(
    category_name: str,
    runtime_category: dict[str, Any],
    menagerie_category: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    compared = _compare_category(
        category_name,
        runtime_category["records"],
        menagerie_category["records"],
    )
    compared["unknown"] = sorted(
        [
            _annotate_unknown_record(category_name, record, side="runtime")
            for record in runtime_category.get("unknown", [])
        ]
        + [
            _annotate_unknown_record(category_name, record, side="menagerie")
            for record in menagerie_category.get("unknown", [])
        ],
        key=lambda record: (record["key"], record["side"], record.get("kind", "")),
    )
    return compared


def _annotate_unknown_record(category_name: str, record: dict[str, Any], *, side: str) -> dict[str, Any]:
    annotated = dict(record)
    annotated["side"] = side
    decision = _unknown_decision(category_name, side=side)
    annotated["decision"] = annotated.get("decision", decision["decision"])
    annotated["rationale"] = annotated.get("rationale", decision["rationale"])
    return annotated


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


def _unknown_decision(category_name: str, *, side: str) -> dict[str, str]:
    if category_name == "inertials":
        decision = "adapt" if side == "menagerie" else "retain"
        return {
            "decision": decision,
            "rationale": "This body needs a measured or compiled inertia source before the structural diff can claim a truthful body-level inertial comparison.",
        }
    if category_name == "friction":
        decision = "adapt" if side == "menagerie" else "retain"
        return {
            "decision": decision,
            "rationale": "Declaration-only contact defaults stay explicit, but they are not compared as effective attachment behavior until they are actually attached in the source model.",
        }
    return {
        "decision": "retain",
        "rationale": "This evidence remains explicit without claiming a resolved structural comparison.",
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


def _comparison_views(
    category_name: str,
    runtime_value: dict[str, Any],
    menagerie_value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    runtime_compared = dict(runtime_value)
    menagerie_compared = dict(menagerie_value)
    metadata: dict[str, Any] = {}

    if category_name in QUATERNION_SEMANTIC_CATEGORIES:
        runtime_quat = _canonicalize_quaternion(
            runtime_value.get("quat"),
            use_identity_default=True,
        )
        menagerie_quat = _canonicalize_quaternion(
            menagerie_value.get("quat"),
            use_identity_default=True,
        )
        if runtime_quat is not None and menagerie_quat is not None:
            runtime_compared["quat"] = runtime_quat
            menagerie_compared["quat"] = menagerie_quat
            if runtime_value.get("quat") != runtime_quat or menagerie_value.get("quat") != menagerie_quat:
                metadata = {
                    "runtime": {"quat": runtime_quat},
                    "menagerie": {"quat": menagerie_quat},
                }

    return runtime_compared, menagerie_compared, metadata


def _canonicalize_quaternion(value: Any, *, use_identity_default: bool = False) -> list[float] | None:
    if use_identity_default and (value is None or value == []):
        return list(IDENTITY_QUATERNION)
    if not isinstance(value, list) or len(value) != 4 or not all(isinstance(item, (int, float)) for item in value):
        return None
    norm = math.sqrt(sum(float(item) * float(item) for item in value))
    if norm == 0:
        return None
    normalized = [round(float(item) / norm, 9) for item in value]
    sign = _canonical_quaternion_sign(normalized)
    return [round(item * sign, 9) for item in normalized]


def _canonical_quaternion_sign(value: list[float]) -> float:
    for item in value:
        if item > 0:
            return 1.0
        if item < 0:
            return -1.0
    return 1.0


def _compared_records_equal(runtime_value: Any, menagerie_value: Any) -> bool:
    if isinstance(runtime_value, dict) and isinstance(menagerie_value, dict):
        if set(runtime_value) != set(menagerie_value):
            return False
        return all(
            _compared_field_equal(key, runtime_value[key], menagerie_value[key])
            for key in runtime_value
        )
    if isinstance(runtime_value, list) and isinstance(menagerie_value, list):
        if len(runtime_value) != len(menagerie_value):
            return False
        return all(
            _compared_records_equal(runtime_item, menagerie_item)
            for runtime_item, menagerie_item in zip(runtime_value, menagerie_value)
        )
    return runtime_value == menagerie_value


def _compared_field_equal(field_name: str, runtime_value: Any, menagerie_value: Any) -> bool:
    if field_name == "quat":
        return _quaternion_lists_equal(runtime_value, menagerie_value)
    return _compared_records_equal(runtime_value, menagerie_value)


def _quaternion_lists_equal(runtime_value: Any, menagerie_value: Any) -> bool:
    if not isinstance(runtime_value, list) or not isinstance(menagerie_value, list):
        return runtime_value == menagerie_value
    if len(runtime_value) != len(menagerie_value):
        return False
    return all(_numbers_equal(runtime_item, menagerie_item) for runtime_item, menagerie_item in zip(runtime_value, menagerie_value))


def _numbers_equal(runtime_value: float, menagerie_value: float) -> bool:
    return math.isclose(float(runtime_value), float(menagerie_value), abs_tol=QUATERNION_TOLERANCE, rel_tol=0.0)


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
