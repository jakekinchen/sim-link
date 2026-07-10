"""Tracked dependency lock for the SceneSmith PI0.5 robot-lab stack."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tomllib

from pathlib import Path
from typing import Any

from scenesmith.robot_lab.spec import RobotLabRobot


ROBOTICS_DEPENDENCY_LOCK_SCHEMA_VERSION = "scenesmith.robotics_dependency_lock.v1"
OPENPI_REPOSITORY_URL = "https://github.com/Physical-Intelligence/openpi"
MENAGERIE_REPOSITORY_URL = "https://github.com/google-deepmind/mujoco_menagerie"
MENAGERIE_MODEL_PATH = "robotstudio_so101"
OPENPI_LICENSE_ID = "Apache-2.0"
MENAGERIE_LICENSE_ID = "Apache-2.0"

_LEROBOT_GIT_DEPENDENCY_RE = re.compile(
    r"^lerobot(?:\[[^]]+\])?\s*@\s*git\+(?P<url>[^@]+)@(?P<ref>\S+)$"
)


def build_robotics_dependency_lock(*, repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    robot = RobotLabRobot()
    spec_sources = [
        repo_root / "scenesmith/robot_lab/spec.py",
        repo_root / "scenesmith/robot_lab/so101_coordinates.py",
        repo_root / "scenesmith/robot_lab/mujoco_export.py",
    ]
    lelab_root = repo_root / "external/leLab"
    lerobot_root = repo_root / "external/lerobot"
    robotstudio_root = repo_root / "external/SO-ARM100"
    lelab_project = _read_toml(lelab_root / "pyproject.toml")
    lerobot_project = _read_toml(lerobot_root / "pyproject.toml")
    lelab_lerobot_dependency = _extract_lerobot_git_dependency(lelab_project)
    active_mjcf = repo_root / robot.source_mjcf
    active_urdf = repo_root / robot.source_urdf
    payload: dict[str, Any] = {
        "schema_version": ROBOTICS_DEPENDENCY_LOCK_SCHEMA_VERSION,
        "repo_root": str(repo_root),
        "spec_sources": [_file_evidence(path, repo_root=repo_root) for path in spec_sources],
        "runtime_contract": {
            "robot_model": robot.model,
            "joint_names": list(robot.joint_names),
            "source_mjcf": _file_evidence(active_mjcf, repo_root=repo_root),
            "source_urdf": _file_evidence(active_urdf, repo_root=repo_root),
        },
        "dependencies": {
            "lelab_runtime": {
                "role": "active_runtime_entrypoint",
                "repository_url": _project_source_url(
                    lelab_project,
                    default="https://github.com/huggingface/leLab.git",
                ),
                "license_id": _project_license_id(lelab_project),
                "git": _git_repo_evidence(lelab_root, repo_root=repo_root),
                "package": {
                    "name": lelab_project["project"]["name"],
                    "version": str(lelab_project["project"]["version"]),
                    "pyproject": _file_evidence(lelab_root / "pyproject.toml", repo_root=repo_root),
                    "license_file": _file_evidence(lelab_root / "LICENSE", repo_root=repo_root),
                },
                "runtime_lerobot_dependency": lelab_lerobot_dependency,
                "active_urdf": _file_evidence(active_urdf, repo_root=repo_root),
            },
            "local_lerobot_checkout": {
                "role": "local_patch_checkout",
                "resolution": "split_runtime_unresolved",
                "resolution_reason": (
                    "LeLab pins lerobot by tag for runtime, but this repo also carries a "
                    "separate local lerobot checkout with uncommitted PI0.5 changes."
                ),
                "repository_url": _project_source_url(
                    lerobot_project,
                    default="https://github.com/huggingface/lerobot",
                ),
                "license_id": _project_license_id(lerobot_project),
                "git": _git_repo_evidence(lerobot_root, repo_root=repo_root),
                "package": {
                    "name": lerobot_project["project"]["name"],
                    "version": str(lerobot_project["project"]["version"]),
                    "pyproject": _file_evidence(lerobot_root / "pyproject.toml", repo_root=repo_root),
                    "license_file": _file_evidence(lerobot_root / "LICENSE", repo_root=repo_root),
                },
                "relevant_sources": _path_set_evidence(
                    lerobot_root,
                    repo_root=repo_root,
                    relative_paths=[
                        "src/lerobot/policies/pi05/configuration_pi05.py",
                        "src/lerobot/policies/pi05/modeling_pi05.py",
                        "src/lerobot/policies/pi05/processor_pi05.py",
                        "src/lerobot/processor/relative_action_processor.py",
                        "src/lerobot/scripts/lerobot_train.py",
                    ],
                ),
            },
            "openpi_semantic_reference": {
                "role": "semantic_reference_only",
                "repository_url": OPENPI_REPOSITORY_URL,
                "license_id": OPENPI_LICENSE_ID,
                "resolution": "unresolved_remote_reference",
                "revision": None,
                "resolution_reason": (
                    "No OpenPI checkout is vendored or pinned in this repo; SceneSmith currently "
                    "references OpenPI semantics through LeRobot PI0.5 ports and parity fixtures."
                ),
                "local_reference_files": [_file_evidence(path, repo_root=repo_root) for path in [
                    lerobot_root / "docs/source/policy_pi05_README.md",
                    lerobot_root / "src/lerobot/policies/pi05/modeling_pi05.py",
                    lerobot_root / "src/lerobot/policies/pi05/processor_pi05.py",
                    lerobot_root / "tests/policies/pi0_pi05/utils/openpi_parity.py",
                ]],
            },
            "robotstudio_so101": {
                "role": "active_structural_model",
                "repository_url": "https://github.com/TheRobotStudio/SO-ARM100.git",
                "license_id": "Apache-2.0",
                "git": _git_repo_evidence(robotstudio_root, repo_root=repo_root),
                "license_file": _file_evidence(robotstudio_root / "LICENSE", repo_root=repo_root),
                "active_mjcf": _file_evidence(active_mjcf, repo_root=repo_root),
            },
            "menagerie_robotstudio_so101": {
                "role": "proposed_structural_lineage",
                "repository_url": MENAGERIE_REPOSITORY_URL,
                "license_id": MENAGERIE_LICENSE_ID,
                "model_path": MENAGERIE_MODEL_PATH,
                "resolution": "unresolved_remote_reference",
                "revision": None,
                "resolution_reason": (
                    "SceneSmith has not vendored or pinned a local MuJoCo Menagerie checkout yet; "
                    "this records the intended upstream structural lineage without switching runtime "
                    "inputs in place."
                ),
            },
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["identity_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def verify_robotics_dependency_lock(payload: dict[str, Any], *, repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    if payload.get("schema_version") != ROBOTICS_DEPENDENCY_LOCK_SCHEMA_VERSION:
        raise ValueError("Unsupported robotics dependency lock schema")
    _verify_identity_hash(payload)
    if Path(payload["repo_root"]).resolve() != repo_root:
        raise ValueError("Dependency lock repo_root does not match verification root")
    for evidence in payload["spec_sources"]:
        _verify_file_evidence(evidence, repo_root=repo_root)
    _verify_runtime_contract(payload["runtime_contract"], repo_root=repo_root)
    dependencies = payload["dependencies"]
    _verify_lelab_runtime(dependencies["lelab_runtime"], repo_root=repo_root)
    _verify_local_lerobot_checkout(dependencies["local_lerobot_checkout"], repo_root=repo_root)
    _verify_remote_reference(
        dependencies["openpi_semantic_reference"],
        expected_repository_url=OPENPI_REPOSITORY_URL,
        expected_license_id=OPENPI_LICENSE_ID,
        require_local_reference_files=True,
        repo_root=repo_root,
    )
    _verify_robotstudio_so101(dependencies["robotstudio_so101"], repo_root=repo_root)
    _verify_remote_reference(
        dependencies["menagerie_robotstudio_so101"],
        expected_repository_url=MENAGERIE_REPOSITORY_URL,
        expected_license_id=MENAGERIE_LICENSE_ID,
        require_local_reference_files=False,
        repo_root=repo_root,
    )


def _verify_runtime_contract(runtime_contract: dict[str, Any], *, repo_root: Path) -> None:
    robot = RobotLabRobot()
    if runtime_contract["robot_model"] != robot.model:
        raise ValueError("Runtime contract robot model drifted")
    if runtime_contract["joint_names"] != list(robot.joint_names):
        raise ValueError("Runtime contract joint names drifted")
    _verify_file_evidence(runtime_contract["source_mjcf"], repo_root=repo_root)
    _verify_file_evidence(runtime_contract["source_urdf"], repo_root=repo_root)


def _verify_lelab_runtime(entry: dict[str, Any], *, repo_root: Path) -> None:
    lelab_root = repo_root / "external/leLab"
    project = _read_toml(lelab_root / "pyproject.toml")
    if entry["repository_url"] != _project_source_url(project, default=entry["repository_url"]):
        raise ValueError("LeLab repository URL drifted")
    if entry["license_id"] != _project_license_id(project):
        raise ValueError("LeLab license drifted")
    _verify_git_repo_evidence(entry["git"], repo_root=repo_root)
    _verify_file_evidence(entry["package"]["pyproject"], repo_root=repo_root)
    _verify_file_evidence(entry["package"]["license_file"], repo_root=repo_root)
    current_dependency = _extract_lerobot_git_dependency(project)
    if current_dependency != entry["runtime_lerobot_dependency"]:
        raise ValueError("LeLab runtime lerobot dependency drifted")
    _verify_file_evidence(entry["active_urdf"], repo_root=repo_root)


def _verify_local_lerobot_checkout(entry: dict[str, Any], *, repo_root: Path) -> None:
    lerobot_root = repo_root / "external/lerobot"
    project = _read_toml(lerobot_root / "pyproject.toml")
    if entry["resolution"] != "split_runtime_unresolved":
        raise ValueError("Local LeRobot resolution state drifted")
    if not entry.get("resolution_reason"):
        raise ValueError("Local LeRobot split state must explain why it is unresolved")
    if entry["repository_url"] != _project_source_url(project, default=entry["repository_url"]):
        raise ValueError("Local LeRobot repository URL drifted")
    if entry["license_id"] != _project_license_id(project):
        raise ValueError("Local LeRobot license drifted")
    _verify_git_repo_evidence(entry["git"], repo_root=repo_root)
    _verify_file_evidence(entry["package"]["pyproject"], repo_root=repo_root)
    _verify_file_evidence(entry["package"]["license_file"], repo_root=repo_root)
    _verify_path_set_evidence(entry["relevant_sources"], repo_root=repo_root)


def _verify_robotstudio_so101(entry: dict[str, Any], *, repo_root: Path) -> None:
    if entry["license_id"] != "Apache-2.0":
        raise ValueError("Robot Studio SO-101 license drifted")
    _verify_git_repo_evidence(entry["git"], repo_root=repo_root)
    _verify_file_evidence(entry["license_file"], repo_root=repo_root)
    _verify_file_evidence(entry["active_mjcf"], repo_root=repo_root)


def _verify_remote_reference(
    entry: dict[str, Any],
    *,
    expected_repository_url: str,
    expected_license_id: str,
    require_local_reference_files: bool,
    repo_root: Path,
) -> None:
    if entry["repository_url"] != expected_repository_url:
        raise ValueError(f"Remote reference URL drifted: {expected_repository_url}")
    if entry["license_id"] != expected_license_id:
        raise ValueError(f"Remote reference license drifted: {expected_repository_url}")
    if entry.get("resolution") != "unresolved_remote_reference":
        raise ValueError(f"Remote reference unexpectedly resolved: {expected_repository_url}")
    if entry.get("revision") not in (None, ""):
        raise ValueError(f"Unresolved remote reference cannot claim a pinned revision: {expected_repository_url}")
    if not entry.get("resolution_reason"):
        raise ValueError(f"Missing unresolved reason for remote reference: {expected_repository_url}")
    if require_local_reference_files:
        files = entry.get("local_reference_files") or []
        if not files:
            raise ValueError(f"Missing local reference files for remote reference: {expected_repository_url}")
        for evidence in files:
            _verify_file_evidence(evidence, repo_root=repo_root)


def _verify_identity_hash(payload: dict[str, Any]) -> None:
    expected = str(payload.get("identity_sha256") or "")
    unsigned = {key: value for key, value in payload.items() if key != "identity_sha256"}
    actual = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if actual != expected:
        raise ValueError("Robotics dependency lock identity hash is invalid")


def _verify_git_repo_evidence(git_payload: dict[str, Any], *, repo_root: Path) -> None:
    repo_path = repo_root / git_payload["path"]
    current = _git_repo_evidence(repo_path, repo_root=repo_root)
    if current["revision"] != git_payload["revision"]:
        raise ValueError(f"Git revision drifted for {git_payload['path']}")
    if current["remote_origin_url"] != git_payload["remote_origin_url"]:
        raise ValueError(f"Git remote drifted for {git_payload['path']}")
    if current["is_dirty"] != git_payload["is_dirty"]:
        raise ValueError(f"Git dirty state drifted for {git_payload['path']}")
    if current["tracked_changes"] != git_payload["tracked_changes"]:
        raise ValueError(f"Git tracked-change set drifted for {git_payload['path']}")
    if current["untracked_files"] != git_payload["untracked_files"]:
        raise ValueError(f"Git untracked-file set drifted for {git_payload['path']}")
    if current.get("tracked_diff_sha256") != git_payload.get("tracked_diff_sha256"):
        raise ValueError(f"Git tracked diff drifted for {git_payload['path']}")
    if current.get("untracked_tree_sha256") != git_payload.get("untracked_tree_sha256"):
        raise ValueError(f"Git untracked tree drifted for {git_payload['path']}")
    for evidence in git_payload.get("untracked_file_evidence", []):
        _verify_file_evidence(evidence, repo_root=repo_root)


def _verify_path_set_evidence(payload: dict[str, Any], *, repo_root: Path) -> None:
    current = _path_set_evidence(
        repo_root / payload["root"],
        repo_root=repo_root,
        relative_paths=payload["relative_paths"],
    )
    if current["tree_sha256"] != payload["tree_sha256"]:
        raise ValueError(f"Tracked source tree drifted for {payload['root']}")
    for evidence in payload["files"]:
        _verify_file_evidence(evidence, repo_root=repo_root)


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _project_source_url(project: dict[str, Any], *, default: str) -> str:
    return str(project.get("project", {}).get("urls", {}).get("source", default))


def _project_license_id(project: dict[str, Any]) -> str:
    raw_license = project["project"]["license"]
    if isinstance(raw_license, str):
        return raw_license
    if isinstance(raw_license, dict):
        if "text" in raw_license:
            return str(raw_license["text"])
    raise ValueError("Unsupported project license format")


def _extract_lerobot_git_dependency(project: dict[str, Any]) -> dict[str, Any]:
    for dependency in project["project"]["dependencies"]:
        match = _LEROBOT_GIT_DEPENDENCY_RE.match(str(dependency))
        if not match:
            continue
        return {
            "dependency": str(dependency),
            "repository_url": match.group("url"),
            "revision": match.group("ref"),
        }
    raise ValueError("LeLab pyproject does not pin lerobot via git dependency")


def _git_repo_evidence(repo_path: Path, *, repo_root: Path) -> dict[str, Any]:
    tracked_changes: list[str] = []
    untracked_files: list[str] = []
    for line in _git(repo_path, "status", "--porcelain=v1").splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if status == "??":
            untracked_files.append(path)
        else:
            tracked_changes.append(path)
    tracked_diff_sha256 = None
    if tracked_changes:
        diff = _git(repo_path, "diff", "HEAD", "--")
        tracked_diff_sha256 = hashlib.sha256(diff.encode()).hexdigest()
    untracked_file_evidence = [
        _file_evidence(repo_path / relative, repo_root=repo_root)
        for relative in untracked_files
        if (repo_path / relative).is_file()
    ]
    untracked_tree_sha256 = None
    if untracked_file_evidence:
        untracked_tree_sha256 = hashlib.sha256(
            json.dumps(untracked_file_evidence, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    payload: dict[str, Any] = {
        "path": str(repo_path.resolve().relative_to(repo_root)),
        "revision": _git(repo_path, "rev-parse", "HEAD").strip(),
        "remote_origin_url": _git(repo_path, "remote", "get-url", "origin").strip(),
        "is_dirty": bool(tracked_changes or untracked_files),
        "tracked_changes": tracked_changes,
        "untracked_files": untracked_files,
    }
    if tracked_diff_sha256 is not None:
        payload["tracked_diff_sha256"] = tracked_diff_sha256
    if untracked_file_evidence:
        payload["untracked_file_evidence"] = untracked_file_evidence
        payload["untracked_tree_sha256"] = untracked_tree_sha256
    if payload["is_dirty"] and not (
        payload.get("tracked_diff_sha256") or payload.get("untracked_tree_sha256")
    ):
        raise ValueError(f"Dirty dependency lacks patch identity: {repo_path}")
    return payload


def _path_set_evidence(
    root: Path,
    *,
    repo_root: Path,
    relative_paths: list[str],
) -> dict[str, Any]:
    files = [_file_evidence(root / relative_path, repo_root=repo_root) for relative_path in relative_paths]
    digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "root": str(root.resolve().relative_to(repo_root)),
        "relative_paths": relative_paths,
        "tree_sha256": digest,
        "files": files,
    }


def _file_evidence(path: Path, *, repo_root: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": str(path.resolve().relative_to(repo_root)),
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _verify_file_evidence(payload: dict[str, Any], *, repo_root: Path) -> None:
    current = _file_evidence(repo_root / payload["path"], repo_root=repo_root)
    if current["sha256"] != payload["sha256"]:
        raise ValueError(f"File hash drifted for {payload['path']}")
    if current["size_bytes"] != payload["size_bytes"]:
        raise ValueError(f"File size drifted for {payload['path']}")


def _git(repo_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout
