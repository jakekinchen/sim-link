#!/usr/bin/env python3
"""Bootstrap and rehearse a portable SceneSmith SO-101 reconstruction export."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import time

from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = (
    SCRIPT_PATH.parents[1]
    if SCRIPT_PATH.parent.name == "tools"
    else SCRIPT_PATH.parents[2]
)
ASSET_TOOL = (
    REPO_ROOT / "tools/portable_assets.py"
    if SCRIPT_PATH.parent.name == "tools"
    else REPO_ROOT / "reconstruction-kit/scripts/portable_assets.py"
)
RUNTIME_TOOL = (
    REPO_ROOT / "tools/bootstrap_runtime.py"
    if SCRIPT_PATH.parent.name == "tools"
    else REPO_ROOT / "reconstruction-kit/scripts/bootstrap_runtime.py"
)
EXPORT_TOOL = (
    REPO_ROOT / "tools/reconstruction_kit.py"
    if SCRIPT_PATH.parent.name == "tools"
    else REPO_ROOT / "reconstruction-kit/scripts/kit.py"
)
SOURCE_MANIFEST = (
    REPO_ROOT / "docs/reconstruction/SOURCE_MANIFEST.json"
    if SCRIPT_PATH.parent.name == "tools"
    else REPO_ROOT / "reconstruction-kit/SOURCE_MANIFEST.json"
)
EXPORT_RECEIPT = REPO_ROOT / "RECONSTRUCTION_RECEIPT.json"
OUTPUT_ROOT = REPO_ROOT / "outputs/reconstruction/bootstrap_run_001"
RECEIPT_PATH = OUTPUT_ROOT / "bootstrap_receipt.json"
SCHEMA_VERSION = "scenesmith.reconstruction_bootstrap.v1"
EXPECTED_RUNTIME = {
    "datasets": "4.8.5",
    "lerobot": "0.6.1",
    "mujoco": "3.3.5",
    "numpy": "2.2.6",
    "Pillow": "12.3.0",
    "pyarrow": "25.0.0",
    "torch": "2.11.0",
    "torchvision": "0.26.0",
}
TEST_MODULES = (
    "tests.unit.test_artifact_contract",
    "tests.unit.test_authority_composer",
    "tests.unit.test_so101_coordinates",
    "tests.unit.test_so101_processor",
    "tests.unit.test_strict_grasp_v2",
    "tests.unit.test_lerobot_stack",
)
REQUIRED_CHECKOUT_NAMES = ("LeRobot", "SO-ARM100", "leLab")


class BootstrapError(RuntimeError):
    """Raised when bootstrap parity cannot be proven."""


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sign(payload: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(payload)
    result.pop("identity_sha256", None)
    result["identity_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest()
    return result


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_json(path: Path) -> dict[str, Any]:
    def reject(value: str) -> None:
        raise BootstrapError(f"non-finite JSON constant in {path}: {value}")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise BootstrapError(f"duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=reject,
    )
    if not isinstance(payload, dict):
        raise BootstrapError(f"JSON root must be an object: {path}")
    return payload


def _run(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    rendered = " ".join(command)
    print(f"+ {rendered}", flush=True)
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture,
    )


def _git(path: Path, *args: str) -> str:
    return _run(["git", *args], cwd=path, capture=True).stdout.strip()


def _dependency(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [
        row for row in manifest["external_dependencies"] if row.get("name") == name
    ]
    if len(matches) != 1:
        raise BootstrapError(f"external dependency is absent or duplicated: {name}")
    return matches[0]


def _required_dependencies(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {name: _dependency(manifest, name) for name in REQUIRED_CHECKOUT_NAMES}


def _clone_exact(
    dependency: dict[str, Any],
    destination: Path,
    *,
    local_source_root: Path | None,
    source_directory_name: str,
) -> None:
    if destination.exists() or destination.is_symlink():
        raise BootstrapError(
            f"external checkout destination already exists: {destination}"
        )
    if local_source_root is None:
        source = dependency["repository"]
    else:
        source_path = (local_source_root / "external" / source_directory_name).resolve()
        if not (source_path / ".git").is_dir():
            raise BootstrapError(f"local dependency checkout is absent: {source_path}")
        source = str(source_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = ["git", "clone", "--no-checkout"]
    if local_source_root is not None:
        command.extend(["--local", "--no-hardlinks"])
    command.extend([source, str(destination)])
    _run(command)
    _run(["git", "checkout", "--detach", dependency["revision"]], cwd=destination)
    if _git(destination, "rev-parse", "HEAD") != dependency["revision"]:
        raise BootstrapError(
            f"external checkout revision drifted: {dependency['name']}"
        )


def _prepare_checkouts(
    manifest: dict[str, Any], *, local_source_root: Path | None
) -> list[dict[str, Any]]:
    external = REPO_ROOT / "external"
    if external.exists() or external.is_symlink():
        raise BootstrapError("external/ must be absent at bootstrap start")

    dependencies = _required_dependencies(manifest)
    lerobot = dependencies["LeRobot"]
    lerobot_root = external / "lerobot"
    _clone_exact(
        lerobot,
        lerobot_root,
        local_source_root=local_source_root,
        source_directory_name="lerobot",
    )
    patch = REPO_ROOT / lerobot["local_patch"]
    if _sha_file(patch) != lerobot["patch_sha256"]:
        raise BootstrapError("tracked LeRobot patch drifted")
    _run(["git", "apply", str(patch)], cwd=lerobot_root)
    actual_patch = _run(
        ["git", "diff", "--binary", "HEAD", "--"],
        cwd=lerobot_root,
        capture=True,
    ).stdout.encode()
    if actual_patch != patch.read_bytes():
        raise BootstrapError(
            "applied LeRobot patch bytes do not match the tracked patch"
        )

    arm = dependencies["SO-ARM100"]
    arm_root = external / "SO-ARM100"
    _clone_exact(
        arm,
        arm_root,
        local_source_root=local_source_root,
        source_directory_name="SO-ARM100",
    )
    required = arm_root / arm["required_file"]
    if not required.is_file() or _sha_file(required) != arm["required_file_sha256"]:
        raise BootstrapError("SO-ARM100 required simulation asset drifted")

    evidence = [
        {
            "name": "LeRobot",
            "revision": lerobot["revision"],
            "patch_sha256": lerobot["patch_sha256"],
        },
        {
            "name": "SO-ARM100",
            "revision": arm["revision"],
            "required_file_sha256": arm["required_file_sha256"],
        },
    ]
    lelab = dependencies["leLab"]
    lelab_root = external / "leLab"
    _clone_exact(
        lelab,
        lelab_root,
        local_source_root=local_source_root,
        source_directory_name="leLab",
    )
    required = lelab_root / lelab["required_file"]
    if not required.is_file() or _sha_file(required) != lelab["required_file_sha256"]:
        raise BootstrapError("leLab required URDF drifted")
    evidence.append(
        {
            "name": "leLab",
            "revision": lelab["revision"],
            "required_file_sha256": lelab["required_file_sha256"],
        }
    )
    return evidence


def _install_runtime(*, offline: bool) -> Path:
    if shutil.which("uv") is None:
        raise BootstrapError("uv is required for the pinned runtime")
    command = [
        "uv",
        "sync",
        "--project",
        "external/lerobot",
        "--frozen",
        "--extra",
        "dataset",
        "--python",
        "3.12",
    ]
    if offline:
        command.append("--offline")
    _run(command)
    python = REPO_ROOT / "external/lerobot/.venv/bin/python"
    install = [
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        *[
            f"{name}=={version}"
            for name, version in EXPECTED_RUNTIME.items()
            if name != "lerobot"
        ],
    ]
    if offline:
        install.append("--offline")
    _run(install)
    return python


def _runtime_versions(python: Path) -> dict[str, str]:
    command = [
        str(python),
        "-c",
        (
            "import importlib.metadata as m,json;"
            f"names={list(EXPECTED_RUNTIME)!r};"
            "print(json.dumps({n:m.version(n) for n in names},sort_keys=True))"
        ),
    ]
    actual = json.loads(_run(command, capture=True).stdout)
    if actual != EXPECTED_RUNTIME:
        raise BootstrapError(f"runtime versions drifted: {actual!r}")
    return actual


def _bootstrap_receipt_identity() -> str | None:
    if not EXPORT_RECEIPT.is_file():
        return None
    receipt = _strict_json(EXPORT_RECEIPT)
    return receipt.get("identity_sha256")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local-source-root",
        type=Path,
        help="Clone exact dependency pins from another checkout instead of the network.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Require all Python artifacts to be present in the local uv cache.",
    )
    args = parser.parse_args()
    started = time.monotonic()

    if OUTPUT_ROOT.exists() or OUTPUT_ROOT.is_symlink():
        raise BootstrapError(f"bootstrap output already exists: {OUTPUT_ROOT}")
    if EXPORT_RECEIPT.is_file():
        _run([sys.executable, str(EXPORT_TOOL), "verify-export", str(REPO_ROOT)])
    _run([sys.executable, str(ASSET_TOOL), "verify"])
    manifest = _strict_json(SOURCE_MANIFEST)
    local_source_root = (
        args.local_source_root.resolve() if args.local_source_root else None
    )
    checkout_evidence = _prepare_checkouts(
        manifest,
        local_source_root=local_source_root,
    )
    python = _install_runtime(offline=args.offline)
    versions = _runtime_versions(python)

    stack_report = json.loads(
        _run(
            [str(python), "scripts/robot_lab/verify_lerobot_stack.py"],
            capture=True,
        ).stdout
    )
    _run([str(python), "-m", "unittest", *TEST_MODULES])
    runtime_report = json.loads(
        _run(
            [
                str(python),
                str(RUNTIME_TOOL),
                "rehearse",
                "--output-root",
                str(OUTPUT_ROOT),
            ],
            capture=True,
        ).stdout
    )

    payload = _sign(
        {
            "schema_version": SCHEMA_VERSION,
            "source_commit": manifest["source_commit"],
            "source_manifest_identity_sha256": manifest["identity_sha256"],
            "pristine_export_receipt_identity_sha256": _bootstrap_receipt_identity(),
            "portable_asset_manifest_identity_sha256": runtime_report[
                "portable_asset_manifest_identity_sha256"
            ],
            "dependency_source": "local" if local_source_root else "network",
            "python_install_offline": args.offline,
            "external_checkouts": checkout_evidence,
            "runtime_versions": versions,
            "stack_identity_sha256": stack_report["stack_identity_sha256"],
            "focused_test_modules": list(TEST_MODULES),
            "expert_episode": runtime_report["expert_episode"],
            "renderer_smokes": runtime_report["renderer_smokes"],
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "authority_transferred": False,
            "training_authorized": False,
            "optimizer_created": False,
            "physical_hardware_accessed": False,
            "external_compute_used": False,
        }
    )
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BootstrapError, OSError, subprocess.CalledProcessError) as error:
        print(f"bootstrap error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
