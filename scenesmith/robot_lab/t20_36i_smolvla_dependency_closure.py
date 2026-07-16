"""Read-only exact SmolVLA optional-dependency closure audit for T20.36i."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys
import tomllib

from email.parser import BytesParser
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (
    FAILURE_RESULT_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEROBOT_ROOT = REPO_ROOT / "external/lerobot"
PYPROJECT_PATH = Path("external/lerobot/pyproject.toml")
METADATA_PATH = Path(
    "external/lerobot/.venv/lib/python3.12/site-packages/"
    "lerobot-0.6.1.dist-info/METADATA"
)
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36i_smolvla_dependency_closure.json"
)
SCHEMA_VERSION = "scenesmith.t20_36i_smolvla_dependency_closure.v1"
TASK_ID = "T20.36i"
EXPECTED_FAILURE_RESULT_IDENTITY = (
    "3804eff6962470e22166fd6bb7c4c22c0f97832b914aafb2ed40f4295be4ce33"
)
EXPECTED_LEROBOT_HEAD = "e40b58a8dfa9e7b86918c374791599d070518d11"
EXPECTED_PYPROJECT_SHA256 = (
    "d9e8960c33b69f963af3e7753ef05b902385c5f632444a73a10fd52fbc79851c"
)
EXPECTED_METADATA_SHA256 = (
    "ceb9917f6a38410b5dff2dd1020d7385a32468f286cbe32b1ca6719c5c40ea6c"
)
ROOT_EXTRA = "smolvla"


def load_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    pyproject_path = root / PYPROJECT_PATH
    metadata_path = root / METADATA_PATH
    pyproject_bytes = pyproject_path.read_bytes()
    metadata_bytes = metadata_path.read_bytes()
    pyproject = tomllib.loads(pyproject_bytes.decode("utf-8"))
    message = BytesParser().parsebytes(metadata_bytes)
    return {
        "failure_result": load_strict_json(root / FAILURE_RESULT_PATH),
        "lerobot_head": _git_head(root / "external/lerobot"),
        "pyproject": pyproject,
        "pyproject_sha256": hashlib.sha256(pyproject_bytes).hexdigest(),
        "metadata_requires_dist": message.get_all("Requires-Dist") or [],
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "major_minor": list(sys.version_info[:2]),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
    }


def build_result(*, sources: dict[str, Any]) -> dict[str, Any]:
    _verify_sources(sources)
    project = sources["pyproject"]["project"]
    extras = project["optional-dependencies"]
    root_requirements = _requirement_tuples(extras[ROOT_EXTRA])
    metadata_requirements = _metadata_extra_tuples(
        sources["metadata_requires_dist"], ROOT_EXTRA
    )
    if root_requirements != metadata_requirements:
        raise ValueError("T20.36i source and installed SmolVLA extras disagree")
    requirements, delegation_edges = _resolve_local_extra_closure(
        extras, ROOT_EXTRA
    )
    rows = [
        _installed_requirement_row(row) for row in requirements
    ]
    lerobot_version = importlib.metadata.version("lerobot")
    rows.append(
        {
            "package": "lerobot",
            "requirement": f"lerobot=={project['version']}",
            "source_extra": "project",
            "installed_version": lerobot_version,
            "status": (
                "present"
                if lerobot_version == project["version"]
                else "version_mismatch"
            ),
        }
    )
    rows.sort(key=lambda row: (row["package"], row["source_extra"]))
    missing = [row for row in rows if row["status"] == "missing"]
    mismatched = [
        row for row in rows if row["status"] == "version_mismatch"
    ]
    manifest = {
        "python": sources["python"],
        "requirements": rows,
    }
    manifest_identity = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    failure = sources["failure_result"]
    observed = failure["missing_dependency_observed"]
    missing_names = [row["package"] for row in missing]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "read_only_exact_pinned_smolvla_optional_dependency_closure",
        "source_failure_result_identity_sha256": failure["identity_sha256"],
        "lerobot_head": sources["lerobot_head"],
        "pyproject": {
            "path": str(PYPROJECT_PATH),
            "sha256": sources["pyproject_sha256"],
            "project_version": project["version"],
            "root_extra": ROOT_EXTRA,
        },
        "installed_metadata": {
            "path": str(METADATA_PATH),
            "sha256": sources["metadata_sha256"],
            "root_extra_matches_source": True,
        },
        "delegation_edges": delegation_edges,
        "environment_manifest": manifest,
        "environment_manifest_identity_sha256": manifest_identity,
        "requirement_count": len(rows),
        "missing_requirements": missing,
        "version_mismatched_requirements": mismatched,
        "all_requirements_satisfied": not missing and not mismatched,
        "observed_failure_dependency": observed,
        "observed_failure_is_in_declared_closure": observed in missing_names,
        "additional_missing_dependencies": [
            row for row in missing if row["package"] != observed
        ],
        "root_cause": (
            "preflight_checked_selected_versions_but_not_recursive_"
            "lerobot_smolvla_extra_closure"
        ),
        "correction_design": {
            "future_preflight_requires_recursive_extra_closure": True,
            "future_preflight_requires_all_versions_within_bounds": True,
            "future_preflight_requires_exact_environment_manifest": True,
            "future_preflight_requires_offline_auto_processor_construction": True,
            "auto_processor_smoke_must_precede_attempt_marker": True,
            "full_policy_construction_remains_after_attempt_marker": True,
            "missing_or_mismatched_dependency_fails_before_attempt": True,
            "post_install_exact_versions_must_be_newly_signed": True,
            "replacement_permit_must_bind_new_environment_manifest": True,
            "replacement_attempt_requires_new_owner_authority": True,
        },
        "dependency_install_performed": False,
        "environment_mutated": False,
        "replacement_attempt_ready": False,
        "replacement_attempt_authorized": False,
        "model_constructed": False,
        "checkpoint_tensor_read": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "smolvla_gate_b_evaluated": False,
        "policy_track_selected": False,
        "gate_b_threshold_changed": False,
        "gate_c_authorized": False,
        "physical_actuation": False,
        "network_accessed": False,
        "weights_downloaded": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def verify_result(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36i dependency closure")
    if payload != build_result(sources=sources):
        raise ValueError("T20.36i dependency closure drifted")


def write_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_result(sources=load_sources(repo_root=repo_root))
    dump_canonical_json(Path(repo_root) / RESULT_PATH, result)
    return result


def verify_result_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_sources(repo_root=repo_root)
    result = load_strict_json(Path(repo_root) / RESULT_PATH)
    verify_result(result, sources=sources)
    return result


def _resolve_local_extra_closure(extras, root_extra):
    requirements = []
    edges = []
    visited = set()
    active = set()

    def visit(extra):
        if extra in active:
            raise ValueError("T20.36i local extra dependency cycle detected")
        if extra in visited:
            return
        if extra not in extras:
            raise ValueError(f"T20.36i delegated local extra is missing: {extra}")
        active.add(extra)
        for raw in extras[extra]:
            requirement = Requirement(raw)
            if canonicalize_name(requirement.name) == "lerobot":
                if requirement.specifier:
                    raise ValueError("T20.36i local extra delegation is versioned")
                if not requirement.extras:
                    raise ValueError("T20.36i bare local self-dependency is invalid")
                for child in sorted(requirement.extras):
                    edges.append({"from_extra": extra, "to_extra": child})
                    visit(child)
                continue
            requirements.append(
                {
                    "package": canonicalize_name(requirement.name),
                    "requirement": str(requirement),
                    "source_extra": extra,
                }
            )
        active.remove(extra)
        visited.add(extra)

    visit(root_extra)
    requirements.sort(key=lambda row: (row["package"], row["source_extra"]))
    edges.sort(key=lambda row: (row["from_extra"], row["to_extra"]))
    return requirements, edges


def _installed_requirement_row(row):
    requirement = Requirement(row["requirement"])
    try:
        installed = importlib.metadata.version(requirement.name)
    except importlib.metadata.PackageNotFoundError:
        installed = None
    if installed is None:
        status = "missing"
    elif requirement.specifier and Version(installed) not in requirement.specifier:
        status = "version_mismatch"
    else:
        status = "present"
    return {**row, "installed_version": installed, "status": status}


def _requirement_tuples(values):
    return sorted(_requirement_tuple(Requirement(value)) for value in values)


def _metadata_extra_tuples(values, extra):
    rows = []
    for value in values:
        requirement = Requirement(value)
        if requirement.marker is None:
            continue
        if requirement.marker.evaluate({"extra": extra}):
            rows.append(_requirement_tuple(requirement))
    return sorted(rows)


def _requirement_tuple(requirement):
    return (
        canonicalize_name(requirement.name),
        tuple(sorted(requirement.extras)),
        str(requirement.specifier),
    )


def _verify_sources(sources):
    failure = sources.get("failure_result")
    if not isinstance(failure, dict):
        raise ValueError("T20.36i failure source is missing")
    verify_signed_payload(failure, label="T20.36i failure result")
    if (
        failure.get("identity_sha256") != EXPECTED_FAILURE_RESULT_IDENTITY
        or failure.get("smolvla_gate_b_evaluated") is not False
        or sources.get("lerobot_head") != EXPECTED_LEROBOT_HEAD
        or sources.get("pyproject_sha256") != EXPECTED_PYPROJECT_SHA256
        or sources.get("metadata_sha256") != EXPECTED_METADATA_SHA256
        or sources.get("python", {}).get("major_minor") != [3, 12]
        or not isinstance(sources.get("pyproject"), dict)
        or not isinstance(sources.get("metadata_requires_dist"), list)
    ):
        raise ValueError("T20.36i frozen source identity drifted")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _git_head(root: Path) -> str:
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
