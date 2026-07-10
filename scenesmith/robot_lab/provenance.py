"""Content-addressed runtime, model, and artifact provenance for PI0.5 cycles."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import sys

from pathlib import Path
from typing import Any


PROVENANCE_SCHEMA_VERSION = "scenesmith.pi05_provenance.v1"
PACKAGE_NAMES = (
    "accelerate",
    "datasets",
    "lerobot",
    "numpy",
    "peft",
    "safetensors",
    "torch",
    "transformers",
)


def build_pi05_provenance(
    *,
    model_root: Path,
    artifacts: list[Path],
) -> dict[str, Any]:
    import lerobot
    import torch

    lerobot_root = Path(lerobot.__file__).resolve().parent
    source_paths = [
        lerobot_root / "scripts" / "lerobot_train.py",
        lerobot_root / "configs" / "train.py",
        lerobot_root / "policies" / "pi05" / "modeling_pi05.py",
        lerobot_root / "policies" / "pi05" / "configuration_pi05.py",
        lerobot_root / "policies" / "pi05" / "processor_pi05.py",
        lerobot_root / "utils" / "sample_weighting.py",
    ]
    missing_sources = [str(path) for path in source_paths if not path.is_file()]
    if missing_sources:
        raise FileNotFoundError(f"Missing pinned LeRobot sources: {missing_sources}")
    artifact_evidence = [_file_evidence(path) for path in artifacts]
    payload: dict[str, Any] = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "python": {
            "executable": str(Path(sys.executable).resolve()),
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "torch": {
            "version": torch.__version__,
            "mps_available": bool(torch.backends.mps.is_available()),
            "mps_built": bool(torch.backends.mps.is_built()),
        },
        "packages": {
            name: importlib.metadata.version(name) for name in PACKAGE_NAMES
        },
        "lerobot_sources": [_file_evidence(path) for path in source_paths],
        "model": _tree_evidence(model_root),
        "artifacts": artifact_evidence,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["identity_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def verify_pi05_provenance(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        raise ValueError("Unsupported PI0.5 provenance manifest")
    expected = str(payload.get("identity_sha256") or "")
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    actual = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if actual != expected:
        raise ValueError("PI0.5 provenance manifest identity hash is invalid")
    for item in [*payload["lerobot_sources"], *payload["artifacts"]]:
        current = _file_evidence(Path(item["path"]))
        if current["sha256"] != item["sha256"]:
            raise ValueError(f"Provenance artifact mutated: {item['path']}")
    model = _tree_evidence(Path(payload["model"]["root"]))
    if model["tree_sha256"] != payload["model"]["tree_sha256"]:
        raise ValueError(f"Provenance model tree mutated: {payload['model']['root']}")


def _file_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _tree_evidence(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        evidence = _file_evidence(path)
        evidence["relative_path"] = str(path.relative_to(root))
        evidence.pop("path")
        files.append(evidence)
    digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "root": str(root),
        "file_count": len(files),
        "total_size_bytes": sum(int(item["size_bytes"]) for item in files),
        "tree_sha256": digest,
        "files": files,
    }
