#!/usr/bin/env python3
"""Recreate the exact legacy R0 boundary in one local, non-live epoch."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid

from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
EXPORTED_LAYOUT = SCRIPT_PATH.parent.name == "tools"
REPO_ROOT = SCRIPT_PATH.parents[1] if EXPORTED_LAYOUT else SCRIPT_PATH.parents[2]
ASSET_TOOL = (
    REPO_ROOT / "tools/portable_assets.py"
    if EXPORTED_LAYOUT
    else REPO_ROOT / "reconstruction-kit/scripts/portable_assets.py"
)
ASSET_ROOT = REPO_ROOT / "reconstruction-kit/assets"
TEMPLATE_PATH = (
    REPO_ROOT / "docs/reconstruction/R0_LOCAL_EPOCH_TEMPLATE.json"
    if EXPORTED_LAYOUT
    else REPO_ROOT / "reconstruction-kit/templates/R0_LOCAL_EPOCH_TEMPLATE.json"
)
SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "docs/reconstruction/SOURCE_MANIFEST.json"
    if EXPORTED_LAYOUT
    else REPO_ROOT / "reconstruction-kit/SOURCE_MANIFEST.json"
)
RUN_RECEIPT_PATH = REPO_ROOT / "RUN_RECEIPT.json"
EPOCHS_ROOT = Path("outputs/reconstruction/r0_local_epochs")
BASE_DATASET_ROOT = Path("outputs/reconstruction/r0_base_dataset")
HISTORICAL_STATISTICS_PATH = Path(
    "configurations/robot_lab/t20_42_r0_dataset_statistics.json"
)
HISTORICAL_MIXTURE_PATH = Path(
    "configurations/robot_lab/t20_42_r0_dataset_mixture_manifest.json"
)
HISTORICAL_RESULT_PATH = Path(
    "configurations/robot_lab/t20_42_r0_generation_result.json"
)

TEMPLATE_SCHEMA = "scenesmith.fork_r0_local_epoch_template.v1"
EPOCH_SCHEMA = "scenesmith.fork_r0_local_scratch_authority_epoch.v1"
RECEIPT_SCHEMA = "scenesmith.fork_r0_run_receipt.v1"
EXPECTED_TEMPLATE_IDENTITY = (
    "853e08f3b7905085b6fffcac3f0ac54be6904bb7e7ff73b93f24629faf6a32c1"
)
EVIDENCE_LABELS = ["fixture", "simulation", "replay"]
MINIMUM_FREE_BYTES = 2_000_000_000

EXPECTED_RUNTIME = {
    "python": "3.12.12",
    "lerobot": "0.6.1",
    "mujoco": "3.3.5",
    "numpy": "2.2.6",
    "pillow": "12.3.0",
    "pyarrow": "25.0.0",
    "datasets": "4.8.5",
}

LEGACY_META_STATS_KEY_ORDER = (
    "action",
    "frame_index",
    "index",
    "observation.images.left_wrist_0_rgb",
    "episode_index",
    "timestamp",
    "observation.state",
    "task_index",
    "observation.images.base_0_rgb",
)
EXPECTED_DATASET_META_STATS_FILE_SHA256 = (
    "e11f73c259c3fa6383ab53630432b12b51d1ad2afa1e08630cb2464a5adb53d1"
)

# These are compatibility constants, not authority. The historical permit and
# marker remain expired, inert evidence. Their identities are projected into
# the legacy store/result payloads solely so exact signed bytes can be proven.
EXPECTED = {
    "asset_manifest_identity_sha256": (
        "935c3da1cc59cc1236716056be7226b4527032c036fc80b3df36ce07f77916aa"
    ),
    "base_dataset_manifest_identity_sha256": (
        "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa"
    ),
    "construction_identity_sha256": (
        "b58a6b31d0a3d892cfce8e319c4736d2da9aab2864663a5b2fc89c752e221458"
    ),
    "historical_generation_permit_identity_sha256": (
        "94d7f2b21045e80c84d54678bdd8e1e5a92dac85dce96ce38bc211df12de55ea"
    ),
    "historical_attempt_marker_identity_sha256": (
        "1ff232aa4b9af03cac113ed5aff8d909cfe3a49f194f29f8c780eb3397b9fd66"
    ),
    "episode_store_identity_sha256": (
        "922c2ef8c5f6050d67981b2d4b51ce1d21338252044461c9ace1885311fe780a"
    ),
    "episode_store_file_sha256": (
        "1e1ffea5e6660efd0b2819549dd07a8bb8f794244c0a01c46609b193ab48e491"
    ),
    "dataset_manifest_identity_sha256": (
        "bd36b7c491ba3c3e08ae3efd87febdbbb1f52f917cb258399484ba4f5311a184"
    ),
    "dataset_manifest_file_sha256": (
        "6b7abd88602a20a01dc446b04439200a7b38ae4d24da37675235baab8d5dc387"
    ),
    "dataset_meta_stats_file_sha256": EXPECTED_DATASET_META_STATS_FILE_SHA256,
    "statistics_identity_sha256": (
        "02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae"
    ),
    "statistics_file_sha256": (
        "67e47d618f36ae1989e55a6fba3aa55a3aa95e78f66a9a062f97c4c2f419c608"
    ),
    "mixture_identity_sha256": (
        "37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df"
    ),
    "mixture_file_sha256": (
        "5b2618b0b0bea3b7ae1801ef1df3a83fc187a32079b52e06748df1dac5826f1e"
    ),
    "result_identity_sha256": (
        "d238379bce62d884833da0a449535e3dc24f988b8da573513ae684bbb19a5969"
    ),
    "result_file_sha256": (
        "3c1a853e4a476d68610288a35f475ad398c7b5dc29793a724ae0cf4fd42b0807"
    ),
    "compiler_manifest_file_sha256": (
        "47637a52cabcb11b937c06a112c49da9ac49644f43ac3fd83432e6b76a0543fa"
    ),
    "window_manifest_file_sha256": (
        "7f230e1697b3201a6a99cd2032caeb06e9a4efa4e7ac9f699e0d59c8a0cd08d3"
    ),
    "compiler_frames_sha256": (
        "ba0226ab226ac9540b75d8463c8fc0338e723027a5ae801971d202328b8171cc"
    ),
    "compiler_segments_sha256": (
        "bb44aa1be3d5fd82af142509cb29803c2312126ba657957e49629871d2072166"
    ),
    "window_index_sha256": (
        "af8e2ef312460ecad2bef3b94d135d859bf7f58f869c1c570a003df27cc36fce"
    ),
    "configured_candidate_count": 128,
    "completed_episode_count": 128,
    "new_training_strict_success_count": 119,
    "fresh_held_out_strict_success_count": 9,
    "training_episode_count": 129,
    "training_frame_count": 31366,
    "compiler_frame_count": 31232,
    "compiler_segment_count": 1408,
    "window_count": 59904,
}

REFERENCE_FILES = {
    "statistics": (
        HISTORICAL_STATISTICS_PATH,
        EXPECTED["statistics_identity_sha256"],
        EXPECTED["statistics_file_sha256"],
    ),
    "mixture": (
        HISTORICAL_MIXTURE_PATH,
        EXPECTED["mixture_identity_sha256"],
        EXPECTED["mixture_file_sha256"],
    ),
    "result": (
        HISTORICAL_RESULT_PATH,
        EXPECTED["result_identity_sha256"],
        EXPECTED["result_file_sha256"],
    ),
}

# The W2 route is intentionally local-only. These guards make any accidental
# Hugging Face or Transformers acquisition fail instead of silently widening
# the reproduction boundary.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(REPO_ROOT))

FALSE_AUTHORITY_FIELDS = (
    "authority_transferred",
    "current_live_authority",
    "historical_permit_reused_as_authority",
    "training_authorized",
    "model_constructed",
    "model_inference",
    "optimizer_created",
    "optimizer_training",
    "learned_policy_rollout",
    "hardware_accessed",
    "camera_accessed",
    "serial_accessed",
    "physical_motion",
    "network_accessed",
    "package_installed",
    "external_compute_started",
    "brev_compute_started",
    "physical_transfer_ready",
    "promotion_eligible",
)


class R0RecreationError(RuntimeError):
    """Raised whenever exact legacy R0 recreation cannot be proven."""


class R0MismatchError(R0RecreationError):
    """Raised when generated bytes describe a new dataset, not a recreation."""

    def __init__(self, mismatches: dict[str, Any]):
        self.mismatches = mismatches
        super().__init__("new dataset, not a recreation")


def _reject_constant(value: str) -> None:
    raise R0RecreationError(f"non-finite JSON constant is forbidden: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise R0RecreationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise R0RecreationError(f"required regular JSON file is absent: {path}")
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicate_keys,
        parse_constant=_reject_constant,
    )
    if not isinstance(payload, dict):
        raise R0RecreationError(f"JSON root must be an object: {path}")
    return payload


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _payload_identity(payload: dict[str, Any]) -> str:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("identity_sha256", None)
    return hashlib.sha256(_canonical_bytes(unsigned)).hexdigest()


def _sign(payload: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(payload)
    result.pop("identity_sha256", None)
    result["identity_sha256"] = _payload_identity(result)
    return result


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_file_sha(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _safe_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise R0RecreationError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise R0RecreationError(f"unsafe relative path: {value!r}")
    if path.as_posix() != value or value.endswith("/"):
        raise R0RecreationError(f"non-canonical relative path: {value!r}")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _normalize_legacy_meta_stats(dataset_root: Path) -> None:
    """Remove parallel-worker key-order drift without changing any value."""

    path = dataset_root / "meta/stats.json"
    payload = _load(path)
    if set(payload) != set(LEGACY_META_STATS_KEY_ORDER):
        raise R0MismatchError(
            {
                "dataset_meta_stats_keys": {
                    "expected": list(LEGACY_META_STATS_KEY_ORDER),
                    "observed": list(payload),
                }
            }
        )
    ordered = {key: payload[key] for key in LEGACY_META_STATS_KEY_ORDER}
    data = json.dumps(ordered, indent=4, allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_DATASET_META_STATS_FILE_SHA256:
        raise R0MismatchError(
            {
                "dataset_meta_stats_file_sha256": {
                    "expected": EXPECTED_DATASET_META_STATS_FILE_SHA256,
                    "observed": digest,
                }
            }
        )
    temporary = path.with_name(f".{path.name}.r0-normalize-{uuid.uuid4().hex}")
    _write_bytes(temporary, data)
    os.replace(temporary, path)
    if path.is_symlink() or _sha_file(path) != EXPECTED_DATASET_META_STATS_FILE_SHA256:
        raise R0RecreationError("normalized LeRobot metadata statistics drifted")


def _runtime_versions() -> dict[str, str]:
    distributions = {
        "lerobot": "lerobot",
        "mujoco": "mujoco",
        "numpy": "numpy",
        "pillow": "Pillow",
        "pyarrow": "pyarrow",
        "datasets": "datasets",
    }
    result = {"python": platform.python_version()}
    for label, distribution in distributions.items():
        try:
            result[label] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError as error:
            raise R0RecreationError(
                f"required runtime package absent: {label}"
            ) from error
    if result != EXPECTED_RUNTIME:
        raise R0RecreationError(
            f"runtime version drifted: expected {EXPECTED_RUNTIME}, observed {result}"
        )
    return result


def _git(checkout: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(checkout), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _dependency(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [
        row
        for row in manifest.get("external_dependencies", [])
        if row.get("name") == name
    ]
    if len(matches) != 1:
        raise R0RecreationError(f"external dependency is absent or duplicated: {name}")
    return matches[0]


def _verify_local_dependencies() -> dict[str, Any]:
    manifest = _load(SOURCE_MANIFEST_PATH)
    lerobot = _dependency(manifest, "LeRobot")
    lerobot_root = REPO_ROOT / "external/lerobot"
    if not (lerobot_root / ".git").exists():
        raise R0RecreationError("pinned local LeRobot checkout is absent")
    if _git(lerobot_root, "rev-parse", "HEAD") != lerobot["revision"]:
        raise R0RecreationError("pinned local LeRobot revision drifted")
    patch_path = REPO_ROOT / lerobot["local_patch"]
    if _sha_file(patch_path) != lerobot["patch_sha256"]:
        raise R0RecreationError("tracked LeRobot patch drifted")
    applied = subprocess.run(
        ["git", "-C", str(lerobot_root), "diff", "--binary", "HEAD", "--"],
        check=True,
        capture_output=True,
    ).stdout
    if applied != patch_path.read_bytes():
        raise R0RecreationError("local LeRobot patch bytes drifted")

    arm = _dependency(manifest, "SO-ARM100")
    arm_root = REPO_ROOT / "external/SO-ARM100"
    if not (arm_root / ".git").exists():
        raise R0RecreationError("pinned local SO-ARM100 checkout is absent")
    if _git(arm_root, "rev-parse", "HEAD") != arm["revision"]:
        raise R0RecreationError("pinned local SO-ARM100 revision drifted")
    required = arm_root / arm["required_file"]
    if (
        not required.is_file()
        or required.is_symlink()
        or _sha_file(required) != arm["required_file_sha256"]
    ):
        raise R0RecreationError("SO-ARM100 simulation asset drifted")
    return {
        "LeRobot": {
            "revision": lerobot["revision"],
            "patch_sha256": lerobot["patch_sha256"],
        },
        "SO-ARM100": {
            "revision": arm["revision"],
            "required_file_sha256": arm["required_file_sha256"],
        },
    }


def _verify_template() -> dict[str, Any]:
    template = _load(TEMPLATE_PATH)
    if (
        template.get("schema_version") != TEMPLATE_SCHEMA
        or template.get("identity_sha256") != EXPECTED_TEMPLATE_IDENTITY
        or _payload_identity(template) != EXPECTED_TEMPLATE_IDENTITY
        or template.get("non_live_template") is not True
        or template.get("live_authority") is not False
        or template.get("historical_authority_is_inert_evidence_only") is not True
        or template.get("evidence_labels_preserved") != EVIDENCE_LABELS
        or template.get("dataset_tiers", {}).get("compatibility")
        != "exact_existing_full_r0_recreation"
        or template.get("dataset_tiers", {}).get("future_fast_rl")
        != "light_state_only_parquet_follow_on_not_part_of_w2"
    ):
        raise R0RecreationError("non-live R0 epoch template drifted")
    return template


def _verify_reference_files() -> dict[str, dict[str, Any]]:
    references = {}
    for label, (relative, identity, file_sha) in REFERENCE_FILES.items():
        path = REPO_ROOT / relative
        payload = _load(path)
        if (
            payload.get("identity_sha256") != identity
            or _payload_identity(payload) != identity
            or _sha_file(path) != file_sha
        ):
            raise R0RecreationError(f"historical {label} reference drifted")
        references[label] = payload
    return references


def _ensure_output_absence() -> None:
    import scenesmith.robot_lab.t20_42b_r0_runner as runner

    paths = (
        RUN_RECEIPT_PATH,
        REPO_ROOT / BASE_DATASET_ROOT,
        REPO_ROOT / runner.RUN_ROOT,
    )
    for path in paths:
        if os.path.lexists(path):
            raise R0RecreationError(f"fresh-output precondition failed: {path}")
    free_bytes = os.statvfs(REPO_ROOT).f_bavail * os.statvfs(REPO_ROOT).f_frsize
    if free_bytes < MINIMUM_FREE_BYTES:
        raise R0RecreationError(
            f"insufficient free space: {free_bytes} < {MINIMUM_FREE_BYTES}"
        )


def _materialize_epoch(
    template: dict[str, Any],
    *,
    epoch_id: str | None = None,
    created_at: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    source_manifest = _load(SOURCE_MANIFEST_PATH)
    if source_manifest.get("identity_sha256") != _payload_identity(source_manifest):
        raise R0RecreationError("reconstruction source manifest identity drifted")
    identifier = epoch_id or uuid.uuid4().hex
    if not re.fullmatch(r"[0-9a-f]{32}", identifier):
        raise R0RecreationError("local epoch id must be 32 lowercase hex characters")
    timestamp = created_at or datetime.now().astimezone().isoformat(timespec="seconds")
    payload = _sign(
        {
            "schema_version": EPOCH_SCHEMA,
            "epoch_id": identifier,
            "created_at": timestamp,
            "template_ref": {
                "path": TEMPLATE_PATH.relative_to(REPO_ROOT).as_posix(),
                "identity_sha256": template["identity_sha256"],
            },
            "source_manifest_ref": {
                "path": SOURCE_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(),
                "source_commit": source_manifest["source_commit"],
                "identity_sha256": source_manifest["identity_sha256"],
            },
            "target": template["target"],
            "allowed_actions": template["allowed_actions"],
            "authority_not_granted": template["authority_not_granted"],
            "evidence_labels_preserved": EVIDENCE_LABELS,
            "dataset_tiers": template["dataset_tiers"],
            "full_audiovisual_lerobot_dataset_role": template[
                "full_audiovisual_lerobot_dataset_role"
            ],
            "short_60_frame_success_terminated_state_tasks": template[
                "short_60_frame_success_terminated_state_tasks"
            ],
            "run_receipt_role": template["run_receipt_role"],
            "historical_compatibility_constants": {
                "generation_permit_identity_sha256": EXPECTED[
                    "historical_generation_permit_identity_sha256"
                ],
                "attempt_marker_identity_sha256": EXPECTED[
                    "historical_attempt_marker_identity_sha256"
                ],
                "use": "inert_compatibility_projection_only",
            },
            **{field: False for field in FALSE_AUTHORITY_FIELDS},
        }
    )
    relative = EPOCHS_ROOT / identifier / "LOCAL_EPOCH.json"
    path = REPO_ROOT / relative
    _write_json(path, payload)
    return relative, payload


def _materialize_base() -> tuple[Any, dict[str, Any]]:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from scenesmith.robot_lab.artifact_contract import verify_signed_payload
    from scenesmith.robot_lab.lerobot_native_episode_manifest import (
        verify_lerobot_episode_manifest,
    )

    asset_manifest = _load(ASSET_ROOT / "ASSET_MANIFEST.json")
    if (
        asset_manifest.get("identity_sha256")
        != EXPECTED["asset_manifest_identity_sha256"]
    ):
        raise R0RecreationError("portable asset pack identity drifted")
    subprocess.run(
        [
            sys.executable,
            str(ASSET_TOOL),
            "materialize-base",
            "--destination",
            str(REPO_ROOT / BASE_DATASET_ROOT),
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    manifest_path = (
        REPO_ROOT
        / "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
    )
    manifest = _load(manifest_path)
    verify_signed_payload(manifest, label="portable R0 base dataset manifest")
    if (
        manifest.get("identity_sha256")
        != EXPECTED["base_dataset_manifest_identity_sha256"]
    ):
        raise R0RecreationError("base dataset manifest identity drifted")
    dataset = LeRobotDataset(
        manifest["dataset"]["repo_id"],
        root=REPO_ROOT / BASE_DATASET_ROOT,
        return_uint8=True,
    )
    annotations = [
        {
            "episode_index": row["episode_index"],
            "raw_rollout_identity_sha256": row["raw_rollout_identity_sha256"],
            "eligible": row["eligible"],
            "quarantine_reason": row["quarantine_reason"],
        }
        for row in manifest["episodes"]
    ]
    verify_lerobot_episode_manifest(
        manifest,
        dataset,
        dataset_label=manifest["dataset"]["label"],
        episode_annotations=annotations,
    )
    return dataset, manifest


def _load_construction() -> dict[str, Any]:
    from scenesmith.robot_lab.t20_42_r0_dataset_construction import (
        load_source_snapshot,
        verify_construction_spec,
    )

    path = REPO_ROOT / "configurations/robot_lab/t20_42_r0_construction_spec.json"
    construction = _load(path)
    verify_construction_spec(
        construction,
        source_snapshot=load_source_snapshot(repo_root=REPO_ROOT),
    )
    if construction.get("identity_sha256") != EXPECTED["construction_identity_sha256"]:
        raise R0RecreationError("R0 construction identity drifted")
    return construction


def _compatibility_projection(
    construction: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = construction["generation_plan"]
    permit = {
        "identity_sha256": EXPECTED["historical_generation_permit_identity_sha256"],
        "training_candidate_ids": plan["training_candidate_ids"],
        "fresh_held_out_candidate_ids": plan["fresh_held_out_candidate_ids"],
    }
    marker = {"identity_sha256": EXPECTED["historical_attempt_marker_identity_sha256"]}
    return permit, marker


def _generate_store(
    construction: dict[str, Any], permit: dict[str, Any]
) -> tuple[Any, dict[str, Any]]:
    import scenesmith.robot_lab.t20_42b_r0_runner as runner
    from scenesmith.robot_lab.scripted_grasp_episode_generation import (
        generate_bounded_episode_payload,
    )

    store_root = REPO_ROOT / runner.RAW_STORE_ROOT
    store_root.mkdir(parents=True, exist_ok=False)
    candidates = runner.candidate_sequence(
        construction_spec=construction,
        permit=permit,
    )
    outcomes = []
    for index, candidate in enumerate(candidates, start=1):
        print(
            f"R0 candidate {index:03d}/{len(candidates)} "
            f"{candidate['candidate_id'][:12]}",
            flush=True,
        )
        generation_spec = runner._generation_spec(candidate)
        try:
            episode = generate_bounded_episode_payload(generation_spec)
            outcome = runner._write_episode(
                episode,
                candidate=candidate,
                store_root=store_root,
            )
        except (RuntimeError, ValueError) as error:
            outcome = {
                "candidate_id": candidate["candidate_id"],
                "split_role": candidate["split_role"],
                "generation_spec": generation_spec,
                "runtime_status": "runtime_failure",
                "strict_success": False,
                "error": str(error),
            }
        outcomes.append(outcome)
    store = runner.build_store_manifest(
        outcomes=outcomes,
        construction_spec=construction,
        permit=permit,
    )
    store_path = REPO_ROOT / runner.STORE_MANIFEST_PATH
    _write_json(store_path, store)
    runner.verify_store_manifest(
        store,
        construction_spec=construction,
        permit=permit,
        repo_root=REPO_ROOT,
    )
    return runner, store


def _materialize_dataset(
    runner: Any,
    *,
    base_dataset: Any,
    base_manifest: dict[str, Any],
    store: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from scenesmith.robot_lab.lerobot_native_episode_manifest import (
        build_lerobot_episode_manifest,
        verify_lerobot_episode_manifest,
    )
    from scenesmith.robot_lab.t20_17_clean_base_preflight import _features

    target = LeRobotDataset.create(
        repo_id=runner.DATASET_REPO_ID,
        fps=30,
        root=REPO_ROOT / runner.LEROBOT_DATASET_ROOT,
        robot_type="so101_follower",
        features=_features(),
        use_videos=False,
        image_writer_processes=0,
        image_writer_threads=0,
    )
    annotations = []
    for episode in base_dataset.meta.episodes:
        episode_index = int(episode["episode_index"])
        for frame_index in range(
            int(episode["dataset_from_index"]),
            int(episode["dataset_to_index"]),
        ):
            target.add_frame(runner._copy_base_frame(base_dataset[frame_index]))
        target.save_episode(parallel_encoding=False)
        source = base_manifest["episodes"][episode_index]
        annotations.append(
            {
                "episode_index": episode_index,
                "raw_rollout_identity_sha256": source["raw_rollout_identity_sha256"],
                "eligible": True,
                "quarantine_reason": None,
            }
        )
    admitted = set(store["admitted_training_candidate_ids"])
    for row in store["outcomes"]:
        if row["candidate_id"] not in admitted:
            continue
        episode = _load(REPO_ROOT / runner.RAW_STORE_ROOT / row["relative_path"])
        for frame in episode["frames"]:
            target.add_frame(runner._dataset_frame(frame))
        target.save_episode(parallel_encoding=False)
        annotations.append(
            {
                "episode_index": len(annotations),
                "raw_rollout_identity_sha256": row[
                    "raw_rollout_record_identity_sha256"
                ],
                "eligible": True,
                "quarantine_reason": None,
            }
        )
    target.finalize()
    _normalize_legacy_meta_stats(REPO_ROOT / runner.LEROBOT_DATASET_ROOT)
    loaded = LeRobotDataset(
        runner.DATASET_REPO_ID,
        root=REPO_ROOT / runner.LEROBOT_DATASET_ROOT,
        return_uint8=True,
    )
    manifest = build_lerobot_episode_manifest(
        loaded,
        dataset_label=runner.DATASET_LABEL,
        episode_annotations=annotations,
    )
    manifest_path = REPO_ROOT / runner.DATASET_MANIFEST_PATH
    _write_json(manifest_path, manifest)
    verify_lerobot_episode_manifest(
        manifest,
        loaded,
        dataset_label=runner.DATASET_LABEL,
        episode_annotations=annotations,
    )
    return loaded, manifest


def _build_compact_legacy_artifacts(
    runner: Any,
    *,
    marker: dict[str, Any],
    permit: dict[str, Any],
    store: dict[str, Any],
    compiler: dict[str, Any],
    windows: dict[str, Any],
    dataset: Any,
    dataset_manifest: dict[str, Any],
    base_manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from scenesmith.robot_lab.artifact_contract import artifact_ref

    statistics = runner.build_statistics_artifact(
        dataset_stats=dataset.meta.stats,
        dataset_manifest_ref=artifact_ref(
            path=runner.DATASET_MANIFEST_PATH,
            payload=dataset_manifest,
            repo_root=REPO_ROOT,
        ),
        training_episode_count=dataset.meta.total_episodes,
        training_frame_count=dataset.meta.total_frames,
        excluded_candidate_ids=permit["fresh_held_out_candidate_ids"],
    )
    mixture = runner._build_mixture(
        REPO_ROOT,
        store=store,
        base_manifest=base_manifest,
        native_manifest=dataset_manifest,
        statistics=statistics,
    )
    result = runner._build_result(
        REPO_ROOT,
        status="verified_success",
        marker=marker,
        permit=permit,
        store=store,
        compiler=compiler,
        windows=windows,
        mixture=mixture,
        statistics=statistics,
        native_manifest=dataset_manifest,
    )
    return statistics, mixture, result


def _observed_boundary(
    runner: Any,
    *,
    store: dict[str, Any],
    compiler: dict[str, Any],
    windows: dict[str, Any],
    dataset: Any,
    dataset_manifest: dict[str, Any],
    statistics: dict[str, Any],
    mixture: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "asset_manifest_identity_sha256": _load(ASSET_ROOT / "ASSET_MANIFEST.json")[
            "identity_sha256"
        ],
        "base_dataset_manifest_identity_sha256": _load(
            REPO_ROOT
            / "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
        )["identity_sha256"],
        "construction_identity_sha256": _load(
            REPO_ROOT / "configurations/robot_lab/t20_42_r0_construction_spec.json"
        )["identity_sha256"],
        "historical_generation_permit_identity_sha256": EXPECTED[
            "historical_generation_permit_identity_sha256"
        ],
        "historical_attempt_marker_identity_sha256": EXPECTED[
            "historical_attempt_marker_identity_sha256"
        ],
        "episode_store_identity_sha256": store["identity_sha256"],
        "episode_store_file_sha256": _sha_file(REPO_ROOT / runner.STORE_MANIFEST_PATH),
        "dataset_manifest_identity_sha256": dataset_manifest["identity_sha256"],
        "dataset_manifest_file_sha256": _sha_file(
            REPO_ROOT / runner.DATASET_MANIFEST_PATH
        ),
        "dataset_meta_stats_file_sha256": _sha_file(
            REPO_ROOT / runner.LEROBOT_DATASET_ROOT / "meta/stats.json"
        ),
        "statistics_identity_sha256": statistics["identity_sha256"],
        "statistics_file_sha256": _json_file_sha(statistics),
        "mixture_identity_sha256": mixture["identity_sha256"],
        "mixture_file_sha256": _json_file_sha(mixture),
        "result_identity_sha256": result["identity_sha256"],
        "result_file_sha256": _json_file_sha(result),
        "compiler_manifest_file_sha256": _sha_file(
            REPO_ROOT / runner.COMPILER_ROOT / "compiler_manifest.json"
        ),
        "window_manifest_file_sha256": _sha_file(
            REPO_ROOT / runner.WINDOW_ROOT / "window_manifest.json"
        ),
        "compiler_frames_sha256": compiler["manifest"]["output_sha256"][
            "frames.parquet"
        ],
        "compiler_segments_sha256": compiler["manifest"]["output_sha256"][
            "segments.parquet"
        ],
        "window_index_sha256": windows["manifest"]["output_sha256"][
            "window_index.parquet"
        ],
        "configured_candidate_count": store["configured_candidate_count"],
        "completed_episode_count": store["completed_episode_count"],
        "new_training_strict_success_count": store["new_training_strict_success_count"],
        "fresh_held_out_strict_success_count": len(
            store["fresh_held_out_strict_success_candidate_ids"]
        ),
        "training_episode_count": dataset.meta.total_episodes,
        "training_frame_count": dataset.meta.total_frames,
        "compiler_frame_count": compiler["manifest"]["frame_count"],
        "compiler_segment_count": compiler["manifest"]["segment_count"],
        "window_count": windows["manifest"]["window_count"],
    }


def _mismatches(observed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        key: {"expected": expected, "observed": observed.get(key)}
        for key, expected in EXPECTED.items()
        if observed.get(key) != expected
    }


def _dataset_tiers() -> dict[str, Any]:
    return {
        "compatibility": {
            "dataset": "exact_existing_full_r0_recreation",
            "evidence_role": "compatibility_evidence",
            "w2_hard_gate": True,
            "episode_count": 129,
            "frame_count": 31366,
        },
        "future_fast_rl": {
            "dataset": "light_state_only_parquet",
            "status": "deferred_fork_birth_follow_on_not_part_of_w2",
            "short_success_terminated_task_frames": 60,
            "may_alter_w2_gate": False,
        },
        "full_audiovisual_lerobot_dataset": {
            "role": "VLA/demo-only",
            "may_replace_fast_rl_tier": False,
        },
    }


def _pass_receipt(
    *,
    started_at: str,
    elapsed_seconds: float,
    epoch_path: Path,
    epoch: dict[str, Any],
    runtime: dict[str, str],
    local_dependencies: dict[str, Any],
    observed: dict[str, Any],
    generated_paths: dict[str, str],
) -> dict[str, Any]:
    return _sign(
        {
            "schema_version": RECEIPT_SCHEMA,
            "status": "exact_legacy_r0_recreation",
            "classification": "compatibility_evidence",
            "message": "exact legacy R0 recreated; not current live authority",
            "started_at": started_at,
            "elapsed_seconds": round(elapsed_seconds, 6),
            "local_epoch_ref": {
                "path": epoch_path.as_posix(),
                "identity_sha256": epoch["identity_sha256"],
            },
            "runtime": runtime,
            "runtime_interpreter": str(Path(sys.executable).resolve()),
            "local_dependencies": local_dependencies,
            "expected": EXPECTED,
            "observed": observed,
            "mismatches": {},
            "generated_paths": generated_paths,
            "evidence_labels_preserved": EVIDENCE_LABELS,
            "dataset_tiers": _dataset_tiers(),
            "historical_authority_disposition": (
                "expired_inert_evidence_only_not_reused_as_authority"
            ),
            "receipt_role": "fork_handoff_receipt_not_current_live_authority",
            **{field: False for field in FALSE_AUTHORITY_FIELDS},
        }
    )


def _failure_receipt(
    *,
    started_at: str,
    elapsed_seconds: float,
    stage: str,
    error: BaseException,
    epoch_path: Path | None,
    epoch: dict[str, Any] | None,
) -> dict[str, Any]:
    mismatches = (
        error.mismatches
        if isinstance(error, R0MismatchError)
        else {
            "execution": {
                "expected": "exact legacy R0 recreation",
                "observed": f"{type(error).__name__}: {error}",
            }
        }
    )
    return _sign(
        {
            "schema_version": RECEIPT_SCHEMA,
            "status": "new_dataset_not_recreation",
            "classification": "failed_closed",
            "message": "new dataset, not a recreation",
            "started_at": started_at,
            "elapsed_seconds": round(elapsed_seconds, 6),
            "failure_stage": stage,
            "local_epoch_ref": (
                {
                    "path": epoch_path.as_posix(),
                    "identity_sha256": epoch["identity_sha256"],
                }
                if epoch_path is not None and epoch is not None
                else None
            ),
            "expected": EXPECTED,
            "observed": {},
            "mismatches": mismatches,
            "evidence_labels_preserved": EVIDENCE_LABELS,
            "dataset_tiers": _dataset_tiers(),
            "historical_authority_disposition": (
                "expired_inert_evidence_only_not_reused_as_authority"
            ),
            "receipt_role": "fork_handoff_receipt_not_current_live_authority",
            **{field: False for field in FALSE_AUTHORITY_FIELDS},
        }
    )


def _verify_receipt(receipt: dict[str, Any]) -> None:
    if (
        receipt.get("schema_version") != RECEIPT_SCHEMA
        or receipt.get("identity_sha256") != _payload_identity(receipt)
        or receipt.get("status") != "exact_legacy_r0_recreation"
        or receipt.get("classification") != "compatibility_evidence"
        or receipt.get("mismatches") != {}
        or receipt.get("expected") != EXPECTED
        or receipt.get("observed") != EXPECTED
        or receipt.get("evidence_labels_preserved") != EVIDENCE_LABELS
        or any(receipt.get(field) is not False for field in FALSE_AUTHORITY_FIELDS)
    ):
        raise R0RecreationError("RUN_RECEIPT.json does not prove exact recreation")
    epoch_ref = receipt.get("local_epoch_ref")
    if not isinstance(epoch_ref, dict):
        raise R0RecreationError("RUN_RECEIPT.json lacks its local epoch")
    relative = _safe_relative(epoch_ref.get("path")).as_posix()
    if not relative.startswith(EPOCHS_ROOT.as_posix() + "/"):
        raise R0RecreationError("local epoch path escapes the R0 epoch root")
    epoch = _load(REPO_ROOT / relative)
    if (
        epoch.get("schema_version") != EPOCH_SCHEMA
        or epoch.get("identity_sha256") != epoch_ref.get("identity_sha256")
        or epoch.get("identity_sha256") != _payload_identity(epoch)
        or any(epoch.get(field) is not False for field in FALSE_AUTHORITY_FIELDS)
    ):
        raise R0RecreationError("local epoch identity or authority boundary drifted")
    generated = receipt.get("generated_paths")
    if not isinstance(generated, dict):
        raise R0RecreationError("RUN_RECEIPT.json lacks generated artifact paths")
    for label, expected_identity in (
        ("statistics", EXPECTED["statistics_identity_sha256"]),
        ("mixture", EXPECTED["mixture_identity_sha256"]),
        ("result", EXPECTED["result_identity_sha256"]),
    ):
        relative_path = _safe_relative(generated.get(label)).as_posix()
        payload = _load(REPO_ROOT / relative_path)
        if (
            payload.get("identity_sha256") != expected_identity
            or _payload_identity(payload) != expected_identity
        ):
            raise R0RecreationError(f"generated {label} identity drifted")


def run() -> dict[str, Any]:
    started_monotonic = time.monotonic()
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    stage = "preflight"
    epoch_path: Path | None = None
    epoch: dict[str, Any] | None = None
    try:
        template = _verify_template()
        references = _verify_reference_files()
        runtime = _runtime_versions()
        local_dependencies = _verify_local_dependencies()
        _ensure_output_absence()

        stage = "local_epoch"
        epoch_path, epoch = _materialize_epoch(template)

        stage = "portable_base"
        base_dataset, base_manifest = _materialize_base()

        stage = "construction"
        construction = _load_construction()
        permit, marker = _compatibility_projection(construction)

        stage = "episode_generation"
        runner, store = _generate_store(construction, permit)
        early_observed = {
            "episode_store_identity_sha256": store["identity_sha256"],
            "episode_store_file_sha256": _sha_file(
                REPO_ROOT / runner.STORE_MANIFEST_PATH
            ),
            "configured_candidate_count": store["configured_candidate_count"],
            "completed_episode_count": store["completed_episode_count"],
            "new_training_strict_success_count": store[
                "new_training_strict_success_count"
            ],
            "fresh_held_out_strict_success_count": len(
                store["fresh_held_out_strict_success_candidate_ids"]
            ),
        }
        early_expected = {key: EXPECTED[key] for key in early_observed}
        early_mismatches = {
            key: {"expected": early_expected[key], "observed": value}
            for key, value in early_observed.items()
            if value != early_expected[key]
        }
        if early_mismatches:
            raise R0MismatchError(early_mismatches)

        stage = "frame_segment_window_compilation"
        compiler, windows = runner._compile_store(REPO_ROOT, store=store)

        stage = "legacy_full_dataset_materialization"
        dataset, dataset_manifest = _materialize_dataset(
            runner,
            base_dataset=base_dataset,
            base_manifest=base_manifest,
            store=store,
        )

        stage = "signed_legacy_boundary"
        statistics, mixture, result = _build_compact_legacy_artifacts(
            runner,
            marker=marker,
            permit=permit,
            store=store,
            compiler=compiler,
            windows=windows,
            dataset=dataset,
            dataset_manifest=dataset_manifest,
            base_manifest=base_manifest,
        )
        observed = _observed_boundary(
            runner,
            store=store,
            compiler=compiler,
            windows=windows,
            dataset=dataset,
            dataset_manifest=dataset_manifest,
            statistics=statistics,
            mixture=mixture,
            result=result,
        )
        mismatches = _mismatches(observed)
        for label, payload in (
            ("statistics", statistics),
            ("mixture", mixture),
            ("result", result),
        ):
            if payload != references[label]:
                mismatches[f"{label}_payload_equality"] = {
                    "expected": "byte-equivalent signed historical payload",
                    "observed": "payload differs",
                }
        if mismatches:
            raise R0MismatchError(mismatches)

        stage = "handoff_receipt"
        epoch_directory = (REPO_ROOT / epoch_path).parent
        generated_paths = {}
        for label, payload in (
            ("statistics", statistics),
            ("mixture", mixture),
            ("result", result),
        ):
            relative = (epoch_directory / f"generated_{label}.json").relative_to(
                REPO_ROOT
            )
            _write_json(REPO_ROOT / relative, payload)
            generated_paths[label] = relative.as_posix()
        receipt = _pass_receipt(
            started_at=started_at,
            elapsed_seconds=time.monotonic() - started_monotonic,
            epoch_path=epoch_path,
            epoch=epoch,
            runtime=runtime,
            local_dependencies=local_dependencies,
            observed=observed,
            generated_paths=generated_paths,
        )
        _write_json(RUN_RECEIPT_PATH, receipt)
        _verify_receipt(_load(RUN_RECEIPT_PATH))
        return receipt
    except BaseException as error:
        if not os.path.lexists(RUN_RECEIPT_PATH):
            failure = _failure_receipt(
                started_at=started_at,
                elapsed_seconds=time.monotonic() - started_monotonic,
                stage=stage,
                error=error,
                epoch_path=epoch_path,
                epoch=epoch,
            )
            _write_json(RUN_RECEIPT_PATH, failure)
        raise


def verify() -> dict[str, Any]:
    receipt = _load(RUN_RECEIPT_PATH)
    _verify_receipt(receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "verify"), nargs="?", default="run")
    args = parser.parse_args(argv)
    try:
        receipt = run() if args.command == "run" else verify()
    except (R0RecreationError, OSError, subprocess.CalledProcessError) as error:
        print(
            f"R0 regeneration failed closed: new dataset, not a recreation: {error}",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
