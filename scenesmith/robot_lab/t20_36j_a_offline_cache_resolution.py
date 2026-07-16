"""Read-only offline cache-resolution audit for T20.36j-A."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess

from email.parser import BytesParser
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from scenesmith.robot_lab.artifact_contract import (
    dump_canonical_json,
    load_strict_json,
    sign_payload,
    verify_signed_payload,
)
from scenesmith.robot_lab.t20_36i_smolvla_dependency_closure import (
    RESULT_PATH as DEPENDENCY_CLOSURE_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON_PATH = Path("external/lerobot/.venv/bin/python")
RESULT_PATH = Path(
    "configurations/robot_lab/t20_36j_a_offline_cache_resolution.json"
)
SCHEMA_VERSION = "scenesmith.t20_36j_a_offline_cache_resolution.v1"
TASK_ID = "T20.36j-A"
EXPECTED_DEPENDENCY_CLOSURE_IDENTITY = (
    "0804fd4fda9b255509428f70c50f24672bf99ea91f9a2c6166410d5b6a45cee8"
)
EXPECTED_ENVIRONMENT_MANIFEST_IDENTITY = (
    "8fbb324c8352afebf2d3c8b8b08452a535679276aa0fe50907bacd35d5eb8d08"
)
ROOT_REQUIREMENTS = (
    "num2words>=0.5.14,<0.6.0",
    "accelerate>=1.14.0,<2.0.0",
)
EXPECTED_INSTALLS = {
    "accelerate": "1.14.0",
    "docopt": "0.6.2",
    "num2words": "0.5.14",
    "psutil": "7.2.2",
}


def load_sources(
    *,
    repo_root: Path = REPO_ROOT,
    cache_root: Path | None = None,
    uv_binary: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root)
    uv_path = Path(uv_binary or shutil.which("uv") or "")
    if not uv_path.is_file():
        raise ValueError("T20.36j-A uv executable is unavailable")
    resolved_uv = uv_path.resolve()
    resolved_cache = Path(cache_root or Path.home() / ".cache/uv").resolve()
    if not resolved_cache.is_dir():
        raise ValueError("T20.36j-A local uv cache is unavailable")
    python_path = root / VENV_PYTHON_PATH
    python = _python_identity(python_path)
    closure = load_strict_json(root / DEPENDENCY_CLOSURE_PATH)
    dry_run = _offline_dry_run(
        uv_binary=resolved_uv,
        python_path=python_path,
        repo_root=root,
    )
    cache_packages = [
        _cache_package_row(
            cache_root=resolved_cache,
            package=package,
            version=version,
        )
        for package, version in sorted(EXPECTED_INSTALLS.items())
    ]
    return {
        "dependency_closure": closure,
        "python": python,
        "uv": {
            "version": _uv_version(resolved_uv),
            "binary_sha256": _sha256_file(resolved_uv),
        },
        "dry_run": dry_run,
        "cache_packages": cache_packages,
        "cache_root_kind": "user_uv_cache",
        "host": {
            "machine": platform.machine(),
            "system": platform.system(),
        },
    }


def build_result(*, sources: dict[str, Any]) -> dict[str, Any]:
    _verify_sources(sources)
    cache_packages = sources["cache_packages"]
    cache_manifest = {
        "cache_root_kind": sources["cache_root_kind"],
        "packages": cache_packages,
    }
    cache_manifest_identity = hashlib.sha256(
        canonical_bytes(cache_manifest)
    ).hexdigest()
    dry_run = sources["dry_run"]
    exact_installs = dry_run["would_install"]
    resolution = {
        "root_requirements": list(ROOT_REQUIREMENTS),
        "resolved_package_count": dry_run["resolved_package_count"],
        "would_install": exact_installs,
        "existing_environment_package_count": (
            dry_run["resolved_package_count"] - len(exact_installs)
        ),
        "offline": True,
        "dry_run": True,
        "exit_code": 0,
    }
    resolution_identity = hashlib.sha256(canonical_bytes(resolution)).hexdigest()
    closure = sources["dependency_closure"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "scope": "read_only_offline_uv_cache_resolution_and_content_binding",
        "source_dependency_closure_identity_sha256": closure["identity_sha256"],
        "source_environment_manifest_identity_sha256": (
            closure["environment_manifest_identity_sha256"]
        ),
        "python": sources["python"],
        "host": sources["host"],
        "resolver": sources["uv"],
        "offline_resolution": resolution,
        "offline_resolution_identity_sha256": resolution_identity,
        "cache_manifest": cache_manifest,
        "cache_manifest_identity_sha256": cache_manifest_identity,
        "all_required_packages_available_offline": True,
        "network_acquisition_required": False,
        "planned_offline_install": {
            "environment": str(VENV_PYTHON_PATH.parent.parent),
            "exact_packages": exact_installs,
            "cache_manifest_identity_sha256": cache_manifest_identity,
            "offline_only": True,
            "must_fail_if_cache_identity_drifts": True,
            "requires_new_owner_authority": True,
        },
        "replacement_boundary": {
            "dependency_install_must_precede_new_environment_manifest": True,
            "all_installed_versions_must_be_signed": True,
            "offline_auto_processor_smoke_must_precede_attempt_marker": True,
            "full_policy_construction_remains_after_attempt_marker": True,
            "at_most_one_replacement_attempt": True,
            "gate_b_unchanged": True,
            "requires_new_owner_authority": True,
        },
        "dependency_install_performed": False,
        "environment_mutated": False,
        "network_accessed": False,
        "weights_downloaded": False,
        "auto_processor_constructed": False,
        "model_constructed": False,
        "checkpoint_tensor_read": False,
        "attempt_marker_created": False,
        "replacement_attempt_ready": False,
        "replacement_attempt_authorized": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
        "smolvla_gate_b_evaluated": False,
        "gate_b_threshold_changed": False,
        "gate_c_authorized": False,
        "physical_actuation": False,
        "external_compute_started": False,
        "brev_compute_started": False,
    }
    return sign_payload(payload)


def verify_result(payload: dict[str, Any], *, sources: dict[str, Any]) -> None:
    verify_signed_payload(payload, label="T20.36j-A offline cache resolution")
    if payload != build_result(sources=sources):
        raise ValueError("T20.36j-A offline cache resolution drifted")


def write_result(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    result = build_result(sources=load_sources(repo_root=repo_root))
    dump_canonical_json(Path(repo_root) / RESULT_PATH, result)
    return result


def verify_result_file(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    sources = load_sources(repo_root=repo_root)
    result = load_strict_json(Path(repo_root) / RESULT_PATH)
    verify_result(result, sources=sources)
    return result


def _verify_sources(sources: dict[str, Any]) -> None:
    closure = sources.get("dependency_closure")
    if not isinstance(closure, dict):
        raise ValueError("T20.36j-A dependency closure source is missing")
    verify_signed_payload(closure, label="T20.36j-A dependency closure")
    if (
        closure.get("identity_sha256") != EXPECTED_DEPENDENCY_CLOSURE_IDENTITY
        or closure.get("environment_manifest_identity_sha256")
        != EXPECTED_ENVIRONMENT_MANIFEST_IDENTITY
        or closure.get("all_requirements_satisfied") is not False
        or sorted(
            row.get("package") for row in closure.get("missing_requirements", [])
        )
        != ["accelerate", "num2words"]
        or sources.get("python", {}).get("major_minor") != [3, 12]
        or sources.get("host", {}).get("system") != "Darwin"
        or sources.get("host", {}).get("machine") != "arm64"
        or sources.get("cache_root_kind") != "user_uv_cache"
    ):
        raise ValueError("T20.36j-A frozen source identity drifted")
    dry_run = sources.get("dry_run")
    if not isinstance(dry_run, dict):
        raise ValueError("T20.36j-A offline dry-run result is missing")
    would_install = dry_run.get("would_install")
    if (
        dry_run.get("offline") is not True
        or dry_run.get("dry_run") is not True
        or dry_run.get("exit_code") != 0
        or not isinstance(dry_run.get("resolved_package_count"), int)
        or dry_run["resolved_package_count"] < len(EXPECTED_INSTALLS)
        or would_install
        != [
            {"package": package, "version": version}
            for package, version in sorted(EXPECTED_INSTALLS.items())
        ]
    ):
        raise ValueError("T20.36j-A offline resolver closure drifted")
    rows = sources.get("cache_packages")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_INSTALLS):
        raise ValueError("T20.36j-A cache package manifest is incomplete")
    if (
        [row.get("package") for row in rows] != sorted(EXPECTED_INSTALLS)
        or len({row.get("resolved_archive_entry") for row in rows}) != len(rows)
    ):
        raise ValueError("T20.36j-A cache package manifest is ambiguous")
    for row in rows:
        package = row.get("package")
        if (
            package not in EXPECTED_INSTALLS
            or row.get("version") != EXPECTED_INSTALLS[package]
            or row.get("content_file_count", 0) <= 0
            or row.get("content_total_bytes", 0) <= 0
            or not _is_sha256(row.get("content_tree_sha256"))
            or not _is_sha256(row.get("metadata_sha256"))
            or (
                row.get("artifact_sha256") is not None
                and not _is_sha256(row.get("artifact_sha256"))
            )
        ):
            raise ValueError("T20.36j-A cache content identity drifted")


def _offline_dry_run(
    *, uv_binary: Path, python_path: Path, repo_root: Path
) -> dict[str, Any]:
    command = [
        str(uv_binary),
        "pip",
        "install",
        "--dry-run",
        "--offline",
        "--python",
        str(python_path),
        *ROOT_REQUIREMENTS,
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "UV_OFFLINE": "1",
            "UV_PYTHON_DOWNLOADS": "never",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    completed = subprocess.run(
        command,
        cwd=repo_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    if completed.returncode != 0:
        raise ValueError(f"T20.36j-A offline resolver failed: {output.strip()}")
    resolved_match = re.search(r"^Resolved (\d+) packages", output, re.MULTILINE)
    installs = sorted(
        (
            {
                "package": canonicalize_name(match.group(1)),
                "version": match.group(2),
            }
            for match in re.finditer(
                r"^\s*\+\s+([A-Za-z0-9_.-]+)==([^\s]+)\s*$",
                output,
                re.MULTILINE,
            )
        ),
        key=lambda row: row["package"],
    )
    if resolved_match is None or not installs:
        raise ValueError("T20.36j-A offline resolver output is incomplete")
    return {
        "resolved_package_count": int(resolved_match.group(1)),
        "would_install": installs,
        "offline": True,
        "dry_run": True,
        "exit_code": completed.returncode,
    }


def _cache_package_row(
    *, cache_root: Path, package: str, version: str
) -> dict[str, Any]:
    if package == "docopt":
        base = cache_root / "sdists-v9/pypi/docopt" / version
        wheels = sorted(base.glob(f"*/docopt-{version}-*.whl"))
        if len(wheels) != 1:
            raise ValueError("T20.36j-A docopt cached wheel is ambiguous")
        artifact = wheels[0]
        content_entry = artifact.with_suffix("")
        cache_kind = "cached_sdist_built_wheel"
    else:
        base = cache_root / "wheels-v5/pypi" / package
        candidates = sorted(
            path
            for path in base.glob(f"{version}-*")
            if path.suffix not in {".http", ".msgpack"}
            and (path.is_symlink() or path.is_dir())
        )
        candidates = [
            path
            for path in candidates
            if _metadata_identity(path)[0:2] == (package, version)
        ]
        if len(candidates) != 1:
            raise ValueError(f"T20.36j-A {package} cache candidate is ambiguous")
        content_entry = candidates[0]
        artifact = None
        cache_kind = "cached_wheel"
    resolved_content = content_entry.resolve()
    if not resolved_content.is_dir() or not resolved_content.is_relative_to(cache_root):
        raise ValueError("T20.36j-A cache content escaped the uv cache")
    metadata_name, metadata_version, metadata_path, message = _metadata_identity(
        content_entry
    )
    if (metadata_name, metadata_version) != (package, version):
        raise ValueError("T20.36j-A cached distribution metadata drifted")
    tree = _content_tree_identity(resolved_content)
    runtime_requirements = []
    for raw in message.get_all("Requires-Dist") or []:
        requirement = Requirement(raw)
        if requirement.marker is None:
            runtime_requirements.append(str(requirement))
    return {
        "package": package,
        "version": version,
        "cache_kind": cache_kind,
        "cache_entry": str(content_entry.relative_to(cache_root)),
        "resolved_archive_entry": str(resolved_content.relative_to(cache_root)),
        "artifact": (
            str(artifact.relative_to(cache_root)) if artifact is not None else None
        ),
        "artifact_sha256": (
            _sha256_file(artifact) if artifact is not None else None
        ),
        "metadata": str(metadata_path.resolve().relative_to(resolved_content)),
        "metadata_sha256": _sha256_file(metadata_path),
        "requires_python": message.get("Requires-Python"),
        "runtime_requirements": sorted(runtime_requirements),
        **tree,
    }


def _metadata_identity(path: Path):
    metadata = sorted(path.glob("*.dist-info/METADATA"))
    if len(metadata) != 1:
        raise ValueError("T20.36j-A cached METADATA is missing or ambiguous")
    message = BytesParser().parsebytes(metadata[0].read_bytes())
    return (
        canonicalize_name(message["Name"]),
        message["Version"],
        metadata[0],
        message,
    )


def _content_tree_identity(root: Path) -> dict[str, Any]:
    rows = []
    total_bytes = 0
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        size = path.stat().st_size
        total_bytes += size
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "size": size,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "content_file_count": len(rows),
        "content_total_bytes": total_bytes,
        "content_tree_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
    }


def _python_identity(python_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            str(python_path),
            "-I",
            "-c",
            (
                "import json,platform,sys;"
                "print(json.dumps({'version':platform.python_version(),"
                "'major_minor':list(sys.version_info[:2]),"
                "'implementation':platform.python_implementation()}))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _uv_version(uv_binary: Path) -> str:
    return subprocess.run(
        [str(uv_binary), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
