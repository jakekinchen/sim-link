"""Run the pinned LeRobot processor and sign only its observed outputs."""

from __future__ import annotations

import copy
import hashlib
import os
import socket

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.lerobot_native_episode_manifest import (
    describe_lerobot_value,
    verify_lerobot_episode_manifest,
)


LEROBOT_ACTUAL_PROCESSOR_OBSERVATION_SCHEMA_VERSION = (
    "scenesmith.lerobot_actual_processor_observation.v1"
)
_PROCESSOR_CONFIG = "policy_preprocessor.json"
_AUTHORITY_NOT_GRANTED = [
    "simulation_model_load",
    "simulation_model_inference",
    "simulation_optimizer_training",
    "simulation_policy_accepted",
    "physical_transfer_ready",
    "promotion_eligible",
    "physical_actuation",
    "external_compute",
    "brev_compute",
]


def build_lerobot_processor_observation(
    dataset: Any,
    *,
    episode_manifest: dict[str, Any],
    dataset_label: str,
    episode_annotations: Iterable[dict[str, Any]],
    frame_index: int,
    processor_root: Path,
    tokenizer_root: Path,
) -> dict[str, Any]:
    """Invoke the actual pinned PI0.5 processor for one source-bound sample.

    SceneSmith does not perform any preprocessing here. It verifies the
    provenance view, selects a package-returned sample, loads the package's
    serialized processor, runs it once offline, and records finite descriptors
    of the values that the package returned.
    """

    verify_lerobot_episode_manifest(
        episode_manifest,
        dataset,
        dataset_label=dataset_label,
        episode_annotations=episode_annotations,
    )
    index = _frame_index(frame_index, dataset_length=len(dataset))
    sample = dataset[index]
    if not isinstance(sample, dict):
        raise ValueError("LeRobot processor source sample is not an object")
    episode_index = _scalar_episode_index(sample.get("episode_index"))
    episode = _manifest_episode(episode_manifest, episode_index)
    processor, pipeline = _load_pinned_processor(
        Path(processor_root), tokenizer_root=Path(tokenizer_root)
    )
    with _strict_offline_runtime() as network_attempts:
        output = processor(copy.deepcopy(sample))
    if network_attempts:
        raise ValueError("Pinned LeRobot processor attempted network access")
    if not isinstance(output, dict):
        raise ValueError("Pinned LeRobot processor output is not an object")

    input_entries = {key: describe_lerobot_value(value) for key, value in sorted(sample.items())}
    output_entries = {key: describe_lerobot_value(value) for key, value in sorted(output.items())}
    payload = {
        "schema_version": LEROBOT_ACTUAL_PROCESSOR_OBSERVATION_SCHEMA_VERSION,
        "evidence_mode": "actual_pinned_lerobot_processor_observation",
        "qualification_scope": "simulation_dataset_processor_observability_only",
        "episode_manifest_identity_sha256": episode_manifest["identity_sha256"],
        "source": {
            "dataset_label": dataset_label,
            "frame_index": index,
            "episode_index": episode_index,
            "episode_content_sha256": episode["episode_content_sha256"],
            "raw_rollout_identity_sha256": episode["raw_rollout_identity_sha256"],
            "eligible": episode["eligible"],
            "quarantine_reason": episode["quarantine_reason"],
            "input": _descriptor_collection(input_entries),
        },
        "pipeline": pipeline,
        "output": _descriptor_collection(output_entries),
        "processor_executed": True,
        "normalization_reimplemented": False,
        "renaming_reimplemented": False,
        "tokenization_reimplemented": False,
        "image_preprocessing_reimplemented": False,
        "model_instantiated": False,
        "model_weights_read": False,
        "policy_inference_executed": False,
        "optimizer_training": False,
        "simulator_stepped": False,
        "raw_bytes_rewritten": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
        "local_capabilities": ["actual_pinned_lerobot_processor_output_observed"],
        "proof_labels": [],
        "authority_not_granted": list(_AUTHORITY_NOT_GRANTED),
    }
    return sign_payload(payload)


def verify_lerobot_processor_observation(
    payload: dict[str, Any],
    dataset: Any,
    *,
    episode_manifest: dict[str, Any],
    dataset_label: str,
    episode_annotations: Iterable[dict[str, Any]],
    frame_index: int,
    processor_root: Path,
    tokenizer_root: Path,
) -> None:
    """Replay the real package call and reject changed source, pipeline, or output."""

    if not isinstance(payload, dict):
        raise ValueError("LeRobot processor observation must be an object")
    if payload.get("schema_version") != LEROBOT_ACTUAL_PROCESSOR_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("LeRobot processor observation schema is unsupported")
    verify_signed_payload(payload, label="LeRobot actual processor observation")
    expected = build_lerobot_processor_observation(
        dataset,
        episode_manifest=episode_manifest,
        dataset_label=dataset_label,
        episode_annotations=episode_annotations,
        frame_index=frame_index,
        processor_root=processor_root,
        tokenizer_root=tokenizer_root,
    )
    if payload != expected:
        raise ValueError("LeRobot processor observation drifted from actual package output")


def _load_pinned_processor(root: Path, *, tokenizer_root: Path) -> tuple[Any, dict[str, Any]]:
    source_root = root.expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError("Pinned LeRobot processor root is missing")
    config_path = source_root / _PROCESSOR_CONFIG
    step_paths = sorted(source_root.glob("policy_preprocessor_step_*"))
    paths = [config_path, *step_paths]
    if not config_path.is_file() or not step_paths:
        raise ValueError("Pinned LeRobot processor files are incomplete")
    files = [_file_descriptor(path, root=source_root) for path in paths]
    tokenizer = _file_tree(Path(tokenizer_root), label="Pinned tokenizer root")
    with _strict_offline_runtime() as network_attempts:
        # Transformers snapshots its offline flags at import time. Import it
        # after entering the guard so the tokenizer step cannot fall back to
        # a Hub lookup while the package pipeline is being instantiated.
        import transformers  # noqa: F401
        import lerobot.policies.pi05.processor_pi05  # noqa: F401 - registers the actual step
        from lerobot.processor.pipeline import DataProcessorPipeline

        processor = DataProcessorPipeline.from_pretrained(
            source_root,
            config_filename=_PROCESSOR_CONFIG,
            local_files_only=True,
            overrides={
                "device_processor": {"device": "cpu"},
                "tokenizer_processor": {"tokenizer_name": tokenizer["root"]},
            },
        )
    if network_attempts:
        raise ValueError("Pinned LeRobot processor load attempted network access")
    if not isinstance(processor, DataProcessorPipeline):
        raise TypeError("Pinned processor is not a LeRobot DataProcessorPipeline")
    step_classes = [type(step).__name__ for step in processor.steps]
    if not step_classes:
        raise ValueError("Pinned LeRobot processor has no steps")
    return processor, {
        "package_class": "lerobot.processor.pipeline.DataProcessorPipeline",
        "config_filename": _PROCESSOR_CONFIG,
        "files": files,
        "identity_sha256": hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
        "step_classes": step_classes,
        "tokenizer": {
            "files": tokenizer["files"],
            "identity_sha256": tokenizer["identity_sha256"],
        },
        "device_override": "cpu",
        "local_files_only": True,
    }


def _file_descriptor(path: Path, *, root: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("Pinned LeRobot processor file is missing")
    relative = path.relative_to(root).as_posix()
    data = path.read_bytes()
    return {
        "path": relative,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _file_tree(path: Path, *, label: str) -> dict[str, Any]:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"{label} is missing")
    files = []
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        files.append(_file_descriptor(candidate, root=root))
    if not files:
        raise ValueError(f"{label} contains no files")
    return {
        "root": str(root),
        "files": files,
        "identity_sha256": hashlib.sha256(canonical_json_bytes(files)).hexdigest(),
    }


def _descriptor_collection(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        raise ValueError("LeRobot processor descriptor collection is empty")
    return {
        "entries": entries,
        "identity_sha256": hashlib.sha256(canonical_json_bytes(entries)).hexdigest(),
    }


def _manifest_episode(payload: dict[str, Any], episode_index: int) -> dict[str, Any]:
    verify_signed_payload(payload, label="LeRobot episode manifest")
    episodes = payload.get("episodes")
    if not isinstance(episodes, list):
        raise ValueError("LeRobot episode manifest episodes are malformed")
    matches = [item for item in episodes if item.get("episode_index") == episode_index]
    if len(matches) != 1:
        raise ValueError("LeRobot source sample episode is absent or ambiguous in manifest")
    return matches[0]


def _frame_index(value: Any, *, dataset_length: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < dataset_length:
        raise ValueError("LeRobot processor frame_index is out of range")
    return value


def _scalar_episode_index(value: Any) -> int:
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("LeRobot processor source episode_index is invalid")
    return value


@contextmanager
def _strict_offline_runtime() -> Iterator[list[str]]:
    keys = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")
    previous = {key: os.environ.get(key) for key in keys}
    attempts: list[str] = []
    original_connect = socket.socket.connect

    def blocked_connect(instance: socket.socket, address: Any) -> None:
        attempts.append(repr(address))
        raise RuntimeError("LeRobot processor observation forbids network access")

    for key in keys:
        os.environ[key] = "1"
    socket.socket.connect = blocked_connect
    try:
        yield attempts
    finally:
        socket.socket.connect = original_connect
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
