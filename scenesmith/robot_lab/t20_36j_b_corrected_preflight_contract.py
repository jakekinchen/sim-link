"""Model-free corrected replacement-preflight contract for T20.36j-B."""

from __future__ import annotations

import hashlib
import re

from collections import defaultdict, deque
from pathlib import Path, PurePosixPath
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from scenesmith.robot_lab.artifact_contract import (
    artifact_ref,
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    require_nonblank,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36g_exact_smolvla_gate_b_entry_design import (
    SPEC_PATH,
    verify_spec_file,
)
from scenesmith.robot_lab.t20_36h_exact_smolvla_gate_b import (
    FAILURE_RESULT_PATH,
)
from scenesmith.robot_lab.t20_36i_smolvla_dependency_closure import (
    RESULT_PATH as DEPENDENCY_CLOSURE_PATH,
)
from scenesmith.robot_lab.t20_36j_a_offline_cache_resolution import (
    RESULT_PATH as OFFLINE_CACHE_RESOLUTION_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_b_corrected_preflight_contract.json"
)
CORRECTED_PREFLIGHT_PATH = Path(
    "configurations/robot_lab/t20_36j_corrected_environment_preflight.json"
)
OWNER_AUTHORIZATION_PATH = Path(
    "configurations/robot_lab/t20_36j_owner_replacement_authorization.json"
)
AUTHORITY_DECISION_PATH = Path(
    "configurations/robot_lab/t20_36j_simulation_training_authority_decision.json"
)
TRAINING_PERMIT_PATH = Path(
    "configurations/robot_lab/t20_36j_exact_smolvla_gate_b_permit.json"
)
ATTEMPT_PATH = Path(
    "outputs/robot_lab/t20_36j_exact_smolvla_gate_b/attempt.json"
)
RUN_SUMMARY_PATH = ATTEMPT_PATH.parent / "run_summary.json"
RUN_RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_exact_smolvla_gate_b_result.json"
)
TASK_ID = "T20.36j-B"
CONTRACT_SCHEMA_VERSION = (
    "scenesmith.t20_36j_b_corrected_preflight_contract.v1"
)
INSTALLED_CLOSURE_SCHEMA_VERSION = (
    "scenesmith.t20_36j_installed_dependency_closure.v1"
)
PROCESSOR_SMOKE_SCHEMA_VERSION = (
    "scenesmith.t20_36j_offline_auto_processor_smoke.v1"
)
CORRECTED_PREFLIGHT_SCHEMA_VERSION = (
    "scenesmith.t20_36j_corrected_environment_preflight.v1"
)
EXPECTED_SPEC_IDENTITY = (
    "fb217f3e142bf082cc8628928bdb2b26c5abdaf8e3355ecd04c32ae17ff8f175"
)
EXPECTED_FAILURE_RESULT_IDENTITY = (
    "3804eff6962470e22166fd6bb7c4c22c0f97832b914aafb2ed40f4295be4ce33"
)
EXPECTED_DEPENDENCY_CLOSURE_IDENTITY = (
    "0804fd4fda9b255509428f70c50f24672bf99ea91f9a2c6166410d5b6a45cee8"
)
EXPECTED_OFFLINE_RESOLUTION_IDENTITY = (
    "8dec69ae95e87718405be8e5ef5e580aeda9e3b665254b9aded0c0bc796a5530"
)
EXPECTED_CACHE_MANIFEST_IDENTITY = (
    "6cc7235cbc19c79fca9b180836a3996f5fc9afa7dd10e064d765394271790b7c"
)
EXPECTED_CONTRACT_IDENTITY = (
    "cb018b69c89e4410499e3d7d1f13a15d8cfd57774455c6055c78be25833e679c"
)
EXPECTED_OFFLINE_INSTALLS = {
    "accelerate": "1.14.0",
    "docopt": "0.6.2",
    "num2words": "0.5.14",
    "psutil": "7.2.2",
}
ROOT_REQUIREMENTS = (
    "lerobot==0.6.1",
    "transformers>=5.5.0,<6.0.0",
    "num2words>=0.5.14,<0.6.0",
    "accelerate>=1.14.0,<2.0.0",
)
MINIMUM_FREE_DISK_BYTES = 6 * 1024 * 1024 * 1024
OFFLINE_ENVIRONMENT = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
}
WEIGHT_OR_TENSOR_SUFFIXES = (
    ".bin",
    ".ckpt",
    ".npy",
    ".npz",
    ".pt",
    ".pth",
    ".safetensors",
)


def load_sources(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root)
    spec = verify_spec_file(repo_root=root)
    failure = load_strict_json(root / FAILURE_RESULT_PATH)
    dependency_closure = load_strict_json(root / DEPENDENCY_CLOSURE_PATH)
    offline_resolution = load_strict_json(root / OFFLINE_CACHE_RESOLUTION_PATH)
    return {
        "spec": spec,
        "failure": failure,
        "dependency_closure": dependency_closure,
        "offline_resolution": offline_resolution,
        "source_refs": {
            "spec": artifact_ref(path=SPEC_PATH, payload=spec, repo_root=root),
            "failure": artifact_ref(
                path=FAILURE_RESULT_PATH, payload=failure, repo_root=root
            ),
            "dependency_closure": artifact_ref(
                path=DEPENDENCY_CLOSURE_PATH,
                payload=dependency_closure,
                repo_root=root,
            ),
            "offline_resolution": artifact_ref(
                path=OFFLINE_CACHE_RESOLUTION_PATH,
                payload=offline_resolution,
                repo_root=root,
            ),
        },
    }


def build_contract(*, sources: dict[str, Any]) -> dict[str, Any]:
    _verify_contract_sources(sources)
    spec = sources["spec"]
    offline = sources["offline_resolution"]
    exact_install = offline["offline_resolution"]["would_install"]
    payload = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "model_free_corrected_replacement_preflight_contract",
        "source_refs": sources["source_refs"],
        "source_identities": {
            "smolvla_gate_b_spec": spec["identity_sha256"],
            "consumed_runtime_failure": sources["failure"]["identity_sha256"],
            "dependency_closure": sources["dependency_closure"][
                "identity_sha256"
            ],
            "offline_resolution": offline["identity_sha256"],
            "offline_cache_manifest": offline[
                "cache_manifest_identity_sha256"
            ],
        },
        "exact_offline_install": exact_install,
        "exact_offline_cache_packages": offline["cache_manifest"]["packages"],
        "root_requirements": list(ROOT_REQUIREMENTS),
        "installed_closure_contract": {
            "recursive_requires_dist_required": True,
            "active_marker_evaluation_required": True,
            "optional_extras_ignored_unless_explicitly_active": True,
            "every_version_bound_must_pass": True,
            "every_distribution_metadata_sha256_required": True,
            "missing_or_mismatched_package_fails_before_processor": True,
            "exact_environment_manifest_identity_required": True,
        },
        "processor_smoke": {
            "constructor": "transformers.AutoProcessor.from_pretrained",
            "exact_vlm_snapshot": spec["local_cache"]["vlm_snapshot"],
            "local_files_only_required": True,
            "offline_environment": dict(OFFLINE_ENVIRONMENT),
            "network_attempt_forbidden": True,
            "weight_or_tensor_file_read_forbidden": True,
            "must_complete_before_attempt_marker": True,
            "is_model_construction": False,
        },
        "required_stage_order": [
            {"ordinal": 1, "stage": "recursive_installed_closure"},
            {"ordinal": 2, "stage": "offline_auto_processor_smoke"},
            {"ordinal": 3, "stage": "attempt_marker"},
            {"ordinal": 4, "stage": "full_policy_construction"},
        ],
        "artifact_paths": {
            "owner_authorization": str(OWNER_AUTHORIZATION_PATH),
            "authority_decision": str(AUTHORITY_DECISION_PATH),
            "corrected_preflight": str(CORRECTED_PREFLIGHT_PATH),
            "training_permit": str(TRAINING_PERMIT_PATH),
            "attempt_marker": str(ATTEMPT_PATH),
            "run_summary": str(RUN_SUMMARY_PATH),
            "result": str(RUN_RESULT_PATH),
        },
        "replacement_boundary": {
            "new_owner_authorization_required": True,
            "new_central_authority_decision_required": True,
            "authorized_attempt_count_if_granted": 1,
            "full_policy_construction_is_counted": True,
            "runtime_smoke_after_policy_load_is_counted": True,
            "retry_or_sweep_allowed": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
        },
        "dependency_install_performed": False,
        "environment_mutated": False,
        "network_accessed": False,
        "live_auto_processor_smoke_performed": False,
        "model_constructed": False,
        "checkpoint_tensor_read": False,
        "attempt_marker_created": False,
        "replacement_attempt_ready": False,
        "replacement_attempt_authorized": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "smolvla_gate_b_evaluated": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def verify_contract(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36j-B corrected preflight contract")
    if payload != build_contract(sources=sources):
        raise ValueError("T20.36j-B corrected preflight contract drifted")


def write_contract(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_contract(sources=load_sources(repo_root=repo_root))
    dump_canonical_json(Path(repo_root) / RESULT_PATH, result)
    return result


def verify_contract_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_sources(repo_root=repo_root)
    result = load_strict_json(Path(repo_root) / RESULT_PATH)
    verify_contract(result, sources=sources)
    return result


def build_installed_closure(
    *,
    root_requirements: tuple[str, ...] | list[str],
    distributions: dict[str, dict[str, Any]],
    marker_environment: dict[str, str],
) -> dict[str, Any]:
    if list(root_requirements) != list(ROOT_REQUIREMENTS):
        raise ValueError("T20.36j installed-closure roots drifted")
    roots = [Requirement(raw) for raw in root_requirements]
    normalized_distributions: dict[str, dict[str, Any]] = {}
    for raw_name, distribution in distributions.items():
        name = canonicalize_name(raw_name)
        if name in normalized_distributions:
            raise ValueError("T20.36j installed distribution aliases collide")
        if not isinstance(distribution, dict):
            raise ValueError("T20.36j installed distribution entry is invalid")
        version = require_nonblank(
            distribution.get("version"), label=f"{name} installed version"
        )
        metadata_sha256 = distribution.get("metadata_sha256")
        _sha(metadata_sha256, f"{name} METADATA")
        requires_dist = distribution.get("requires_dist")
        if not isinstance(requires_dist, list) or not all(
            isinstance(raw, str) and raw.strip() for raw in requires_dist
        ):
            raise ValueError(f"T20.36j {name} Requires-Dist is invalid")
        normalized_distributions[name] = {
            "version": version,
            "metadata_sha256": metadata_sha256,
            "requires_dist": list(requires_dist),
        }
    if not isinstance(marker_environment, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in marker_environment.items()
    ):
        raise ValueError("T20.36j marker environment is invalid")
    if (
        marker_environment.get("python_version") != "3.12"
        or marker_environment.get("sys_platform") != "darwin"
        or marker_environment.get("platform_machine") != "arm64"
        or marker_environment.get("extra") != ""
    ):
        raise ValueError("T20.36j marker environment drifted")

    pending: deque[tuple[str, Requirement]] = deque(
        ("root", requirement) for requirement in roots
    )
    expanded: set[str] = set()
    inbound: dict[str, set[str]] = defaultdict(set)
    packages: dict[str, dict[str, Any]] = {}
    active_edges: set[tuple[str, str, str]] = set()
    ignored_edges: set[tuple[str, str, str]] = set()
    missing: set[tuple[str, str, str]] = set()
    mismatches: set[tuple[str, str, str, str]] = set()

    while pending:
        source, requirement = pending.popleft()
        marker = requirement.marker
        if marker is not None and not marker.evaluate(environment=marker_environment):
            ignored_edges.add((source, str(requirement), str(marker)))
            continue
        name = canonicalize_name(requirement.name)
        inbound[name].add(str(requirement))
        active_edges.add((source, name, str(requirement)))
        distribution = normalized_distributions.get(name)
        if distribution is None:
            missing.add((source, name, str(requirement)))
            continue
        installed_version = distribution["version"]
        if requirement.specifier and Version(installed_version) not in requirement.specifier:
            mismatches.add(
                (source, name, str(requirement), installed_version)
            )
        if name not in packages:
            packages[name] = {
                "package": name,
                "installed_version": installed_version,
                "metadata_sha256": distribution["metadata_sha256"],
                "requires_dist": sorted(distribution["requires_dist"]),
            }
        if name in expanded:
            continue
        expanded.add(name)
        for raw_child in distribution["requires_dist"]:
            pending.append((name, Requirement(raw_child)))

    package_rows = []
    for name, row in sorted(packages.items()):
        package_rows.append(
            {
                **row,
                "inbound_requirements": sorted(inbound[name]),
            }
        )
    missing_rows = [
        {"source": source, "package": name, "requirement": requirement}
        for source, name, requirement in sorted(missing)
    ]
    mismatch_rows = [
        {
            "source": source,
            "package": name,
            "requirement": requirement,
            "installed_version": installed_version,
        }
        for source, name, requirement, installed_version in sorted(mismatches)
    ]
    manifest = {
        "root_requirements": list(ROOT_REQUIREMENTS),
        "marker_environment": dict(sorted(marker_environment.items())),
        "packages": package_rows,
        "active_edges": [
            {"source": source, "package": name, "requirement": requirement}
            for source, name, requirement in sorted(active_edges)
        ],
        "ignored_marker_edges": [
            {"source": source, "requirement": requirement, "marker": marker}
            for source, requirement, marker in sorted(ignored_edges)
        ],
        "missing_requirements": missing_rows,
        "version_mismatches": mismatch_rows,
    }
    return sign_payload(
        {
            "schema_version": INSTALLED_CLOSURE_SCHEMA_VERSION,
            "task_id": "T20.36j",
            **manifest,
            "environment_manifest_identity_sha256": hashlib.sha256(
                canonical_json_bytes(manifest)
            ).hexdigest(),
            "all_requirements_satisfied": not missing_rows and not mismatch_rows,
            "model_imported": False,
            "network_accessed": False,
        }
    )


def verify_installed_closure(payload: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36j installed closure")
    packages = payload.get("packages")
    if not isinstance(packages, list):
        raise ValueError("T20.36j installed closure packages are missing")
    distributions = {}
    for row in packages:
        if not isinstance(row, dict):
            raise ValueError("T20.36j installed closure package row is invalid")
        name = require_nonblank(row.get("package"), label="closure package")
        if name in distributions:
            raise ValueError("T20.36j installed closure package is duplicated")
        distributions[name] = {
            "version": row.get("installed_version"),
            "metadata_sha256": row.get("metadata_sha256"),
            "requires_dist": row.get("requires_dist"),
        }
    expected = build_installed_closure(
        root_requirements=payload.get("root_requirements"),
        distributions=distributions,
        marker_environment=payload.get("marker_environment"),
    )
    if payload != expected:
        raise ValueError("T20.36j installed closure drifted")


def build_processor_smoke_evidence(
    *,
    expected_vlm_snapshot: str,
    observed_vlm_snapshot: str,
    processor_class: str,
    tokenizer_class: str,
    image_processor_class: str,
    opened_snapshot_files: list[str],
    offline_environment: dict[str, str],
    local_files_only: bool,
    network_attempted: bool,
    constructed: bool,
) -> dict[str, Any]:
    expected = require_nonblank(
        expected_vlm_snapshot, label="expected VLM snapshot"
    )
    observed = require_nonblank(
        observed_vlm_snapshot, label="observed VLM snapshot"
    )
    classes = {
        "processor": require_nonblank(processor_class, label="processor class"),
        "tokenizer": require_nonblank(tokenizer_class, label="tokenizer class"),
        "image_processor": require_nonblank(
            image_processor_class, label="image processor class"
        ),
    }
    normalized_files = []
    if not isinstance(opened_snapshot_files, list) or not opened_snapshot_files:
        raise ValueError("T20.36j processor smoke opened-file evidence is required")
    for raw_path in opened_snapshot_files:
        path = PurePosixPath(
            require_nonblank(raw_path, label="processor opened snapshot file")
        )
        if path.is_absolute() or ".." in path.parts or str(path) in normalized_files:
            raise ValueError("T20.36j processor opened-file path is unsafe or duplicate")
        if str(path).lower().endswith(WEIGHT_OR_TENSOR_SUFFIXES):
            raise ValueError("T20.36j processor smoke read a weight or tensor file")
        normalized_files.append(str(path))
    normalized_files.sort()
    if (
        observed != expected
        or offline_environment != OFFLINE_ENVIRONMENT
        or local_files_only is not True
        or network_attempted is not False
        or constructed is not True
    ):
        raise ValueError("T20.36j offline AutoProcessor smoke failed closed")
    return sign_payload(
        {
            "schema_version": PROCESSOR_SMOKE_SCHEMA_VERSION,
            "task_id": "T20.36j",
            "constructor": "transformers.AutoProcessor.from_pretrained",
            "expected_vlm_snapshot": expected,
            "observed_vlm_snapshot": observed,
            "classes": classes,
            "opened_snapshot_files": normalized_files,
            "offline_environment": dict(OFFLINE_ENVIRONMENT),
            "local_files_only": True,
            "network_attempted": False,
            "weight_or_tensor_file_opened": False,
            "constructed": True,
            "model_constructed": False,
            "checkpoint_tensor_read": False,
        }
    )


def verify_processor_smoke_evidence(
    payload: dict[str, Any], *, expected_vlm_snapshot: str
) -> None:
    verify_signed_payload(payload, label="T20.36j processor smoke")
    classes = payload.get("classes")
    if not isinstance(classes, dict):
        raise ValueError("T20.36j processor smoke classes are missing")
    expected = build_processor_smoke_evidence(
        expected_vlm_snapshot=expected_vlm_snapshot,
        observed_vlm_snapshot=payload.get("observed_vlm_snapshot"),
        processor_class=classes.get("processor"),
        tokenizer_class=classes.get("tokenizer"),
        image_processor_class=classes.get("image_processor"),
        opened_snapshot_files=payload.get("opened_snapshot_files"),
        offline_environment=payload.get("offline_environment"),
        local_files_only=payload.get("local_files_only"),
        network_attempted=payload.get("network_attempted"),
        constructed=payload.get("constructed"),
    )
    if payload != expected:
        raise ValueError("T20.36j processor smoke drifted")


def build_corrected_preflight(
    *,
    contract: dict[str, Any],
    owner_authorization_identity_sha256: str,
    authority_decision_identity_sha256: str,
    installed_closure: dict[str, Any],
    processor_smoke: dict[str, Any],
    python_major_minor: list[int],
    mps_available: bool,
    free_disk_bytes: int,
    lerobot_stack_identity_sha256: str,
    batch_evidence_identity_sha256: str,
    checkpoint_tree_identity_sha256: str,
    source_commit: str,
    remote_source_commit: str,
    branch: str,
    scoped_dirty_paths: list[str],
    attempt_exists: bool,
    run_exists: bool,
    result_exists: bool,
) -> dict[str, Any]:
    verify_signed_payload(contract, label="T20.36j corrected preflight contract")
    if (
        contract.get("schema_version") != CONTRACT_SCHEMA_VERSION
        or contract.get("task_id") != TASK_ID
        or contract.get("identity_sha256") != EXPECTED_CONTRACT_IDENTITY
        or contract.get("source_identities", {}).get("offline_cache_manifest")
        != EXPECTED_CACHE_MANIFEST_IDENTITY
    ):
        raise ValueError("T20.36j corrected preflight contract is invalid")
    verify_installed_closure(installed_closure)
    verify_processor_smoke_evidence(
        processor_smoke,
        expected_vlm_snapshot=contract["processor_smoke"]["exact_vlm_snapshot"],
    )
    for value, label in (
        (owner_authorization_identity_sha256, "owner authorization"),
        (authority_decision_identity_sha256, "authority decision"),
        (lerobot_stack_identity_sha256, "LeRobot stack"),
        (batch_evidence_identity_sha256, "batch evidence"),
        (checkpoint_tree_identity_sha256, "checkpoint tree"),
    ):
        _sha(value, label)
    _commit(source_commit, "source commit")
    _commit(remote_source_commit, "remote source commit")
    installed_rows = {
        row.get("package"): row.get("installed_version")
        for row in installed_closure.get("packages", [])
        if isinstance(row, dict)
    }
    if any(
        installed_rows.get(package) != version
        for package, version in EXPECTED_OFFLINE_INSTALLS.items()
    ):
        raise ValueError("T20.36j exact offline install set is not present")
    if (
        installed_closure.get("schema_version")
        != INSTALLED_CLOSURE_SCHEMA_VERSION
        or installed_closure.get("root_requirements") != list(ROOT_REQUIREMENTS)
        or installed_closure.get("all_requirements_satisfied") is not True
        or installed_closure.get("missing_requirements") != []
        or installed_closure.get("version_mismatches") != []
        or processor_smoke.get("schema_version") != PROCESSOR_SMOKE_SCHEMA_VERSION
        or processor_smoke.get("expected_vlm_snapshot")
        != contract["processor_smoke"]["exact_vlm_snapshot"]
        or processor_smoke.get("observed_vlm_snapshot")
        != contract["processor_smoke"]["exact_vlm_snapshot"]
        or processor_smoke.get("constructed") is not True
        or processor_smoke.get("network_attempted") is not False
        or processor_smoke.get("weight_or_tensor_file_opened") is not False
        or processor_smoke.get("model_constructed") is not False
        or python_major_minor != [3, 12]
        or mps_available is not True
        or isinstance(free_disk_bytes, bool)
        or not isinstance(free_disk_bytes, int)
        or free_disk_bytes < MINIMUM_FREE_DISK_BYTES
        or source_commit != remote_source_commit
        or branch != "codex/pi05-autolearn-loop"
        or scoped_dirty_paths != []
        or attempt_exists is not False
        or run_exists is not False
        or result_exists is not False
    ):
        raise ValueError("T20.36j corrected preflight failed closed")
    stage_evidence = [
        {
            "ordinal": 1,
            "stage": "recursive_installed_closure",
            "completed": True,
            "evidence_identity_sha256": installed_closure["identity_sha256"],
        },
        {
            "ordinal": 2,
            "stage": "offline_auto_processor_smoke",
            "completed": True,
            "evidence_identity_sha256": processor_smoke["identity_sha256"],
        },
        {
            "ordinal": 3,
            "stage": "attempt_marker",
            "completed": False,
            "evidence_identity_sha256": None,
        },
        {
            "ordinal": 4,
            "stage": "full_policy_construction",
            "completed": False,
            "evidence_identity_sha256": None,
        },
    ]
    return sign_payload(
        {
            "schema_version": CORRECTED_PREFLIGHT_SCHEMA_VERSION,
            "task_id": "T20.36j",
            "contract_identity_sha256": contract["identity_sha256"],
            "owner_authorization_identity_sha256": (
                owner_authorization_identity_sha256
            ),
            "authority_decision_identity_sha256": (
                authority_decision_identity_sha256
            ),
            "offline_cache_manifest_identity_sha256": (
                EXPECTED_CACHE_MANIFEST_IDENTITY
            ),
            "installed_closure": installed_closure,
            "processor_smoke": processor_smoke,
            "python_major_minor": [3, 12],
            "mps_available": True,
            "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
            "free_disk_bytes": free_disk_bytes,
            "lerobot_stack_identity_sha256": lerobot_stack_identity_sha256,
            "batch_evidence_identity_sha256": batch_evidence_identity_sha256,
            "checkpoint_tree_identity_sha256": checkpoint_tree_identity_sha256,
            "source_commit": source_commit,
            "remote_source_commit": remote_source_commit,
            "branch": branch,
            "scoped_dirty_paths": [],
            "stage_evidence": stage_evidence,
            "dependency_install_verified": True,
            "dependency_install_performed_by_preflight": False,
            "environment_mutated_by_preflight": False,
            "auto_processor_constructed": True,
            "auto_processor_is_model_construction": False,
            "attempt_marker_created": False,
            "model_constructed": False,
            "checkpoint_content_read_as_raw_bytes": True,
            "checkpoint_tensor_deserialized": False,
            "model_inference": False,
            "optimizer_created": False,
            "optimizer_training": False,
            "network_accessed": False,
            "weights_downloaded": False,
            "training_permit_created": False,
            "replacement_attempt_ready": False,
            "replacement_attempt_started": False,
            "gate_b_threshold_changed": False,
            "gate_c_authorized": False,
            "physical_actuation": False,
            "external_compute_started": False,
            "brev_compute_started": False,
        }
    )


def verify_corrected_preflight(
    payload: dict[str, Any], *, contract: dict[str, Any]
) -> None:
    verify_signed_payload(payload, label="T20.36j corrected preflight")
    expected = build_corrected_preflight(
        contract=contract,
        owner_authorization_identity_sha256=payload.get(
            "owner_authorization_identity_sha256"
        ),
        authority_decision_identity_sha256=payload.get(
            "authority_decision_identity_sha256"
        ),
        installed_closure=payload.get("installed_closure"),
        processor_smoke=payload.get("processor_smoke"),
        python_major_minor=payload.get("python_major_minor"),
        mps_available=payload.get("mps_available"),
        free_disk_bytes=payload.get("free_disk_bytes"),
        lerobot_stack_identity_sha256=payload.get(
            "lerobot_stack_identity_sha256"
        ),
        batch_evidence_identity_sha256=payload.get(
            "batch_evidence_identity_sha256"
        ),
        checkpoint_tree_identity_sha256=payload.get(
            "checkpoint_tree_identity_sha256"
        ),
        source_commit=payload.get("source_commit"),
        remote_source_commit=payload.get("remote_source_commit"),
        branch=payload.get("branch"),
        scoped_dirty_paths=payload.get("scoped_dirty_paths"),
        attempt_exists=payload.get("attempt_marker_created"),
        run_exists=payload.get("replacement_attempt_started"),
        result_exists=False,
    )
    if payload != expected:
        raise ValueError("T20.36j corrected preflight drifted")


def _verify_contract_sources(sources: dict[str, Any]) -> None:
    expected = (
        ("spec", EXPECTED_SPEC_IDENTITY),
        ("failure", EXPECTED_FAILURE_RESULT_IDENTITY),
        ("dependency_closure", EXPECTED_DEPENDENCY_CLOSURE_IDENTITY),
        ("offline_resolution", EXPECTED_OFFLINE_RESOLUTION_IDENTITY),
    )
    for key, identity in expected:
        payload = sources.get(key)
        if not isinstance(payload, dict):
            raise ValueError(f"T20.36j-B {key} source is missing")
        verify_signed_payload(payload, label=f"T20.36j-B {key} source")
        if payload.get("identity_sha256") != identity:
            raise ValueError(f"T20.36j-B {key} source identity drifted")
    spec = sources["spec"]
    failure = sources["failure"]
    offline = sources["offline_resolution"]
    if (
        failure.get("smolvla_gate_b_evaluated") is not False
        or failure.get("retry_or_sweep_allowed") is not False
        or offline.get("cache_manifest_identity_sha256")
        != EXPECTED_CACHE_MANIFEST_IDENTITY
        or offline.get("network_acquisition_required") is not False
        or offline.get("dependency_install_performed") is not False
        or offline.get("offline_resolution", {}).get("would_install")
        != [
            {"package": package, "version": version}
            for package, version in sorted(EXPECTED_OFFLINE_INSTALLS.items())
        ]
        or spec.get("runtime_contract", {}).get("network_access_allowed") is not False
        or spec.get("runtime_contract", {}).get("local_files_only") is not True
    ):
        raise ValueError("T20.36j-B source claims drifted")
    refs = sources.get("source_refs")
    if not isinstance(refs, dict) or sorted(refs) != sorted(key for key, _ in expected):
        raise ValueError("T20.36j-B source references are incomplete")
    paths = {
        "spec": SPEC_PATH,
        "failure": FAILURE_RESULT_PATH,
        "dependency_closure": DEPENDENCY_CLOSURE_PATH,
        "offline_resolution": OFFLINE_CACHE_RESOLUTION_PATH,
    }
    for key, path in paths.items():
        reference = refs[key]
        payload = sources[key]
        if (
            not isinstance(reference, dict)
            or reference.get("path") != str(path)
            or reference.get("schema_version") != payload.get("schema_version")
            or reference.get("identity_sha256") != payload.get("identity_sha256")
        ):
            raise ValueError(f"T20.36j-B {key} source reference drifted")
        _sha(reference.get("file_sha256"), f"{key} source file")


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"T20.36j {label} must be lowercase SHA-256")
    return value


def _commit(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError(f"T20.36j {label} must be a full commit")
    return value
