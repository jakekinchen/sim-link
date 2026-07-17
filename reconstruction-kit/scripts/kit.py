#!/usr/bin/env python3
"""Build, verify, and safely export the SceneSmith SO-101 reconstruction kit."""

from __future__ import annotations

import argparse
import ast
import copy
import fnmatch
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys

from pathlib import Path, PurePosixPath
from typing import Any


KIT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ROOT = KIT_ROOT.parent
SELECTION_PATH = KIT_ROOT / "source-selection.json"
MANIFEST_PATH = KIT_ROOT / "SOURCE_MANIFEST.json"
RECEIPT_NAME = "RECONSTRUCTION_RECEIPT.json"
MANIFEST_SCHEMA = "scenesmith.reconstruction_source_manifest.v1"
RECEIPT_SCHEMA = "scenesmith.reconstruction_export_receipt.v1"

KIT_EXPORTS = {
    "templates/README.md": "README.md",
    "templates/AGENTS.md": "AGENTS.md",
    "templates/pyproject.toml": "pyproject.toml",
    "templates/gitignore": ".gitignore",
    "README.md": "docs/reconstruction/README.md",
    "CURRENT_STATE.md": "docs/reconstruction/CURRENT_STATE.md",
    "CURRENT_STATE.json": "docs/reconstruction/CURRENT_STATE.json",
    "ARCHITECTURE.md": "docs/reconstruction/ARCHITECTURE.md",
    "QUICKSTART.md": "docs/reconstruction/QUICKSTART.md",
    "RESULTS_AND_LESSONS.md": "docs/reconstruction/RESULTS_AND_LESSONS.md",
    "FORWARD_PLAN.md": "docs/reconstruction/FORWARD_PLAN.md",
    "THIRD_PARTY.md": "docs/reconstruction/THIRD_PARTY.md",
    "SOURCE_MANIFEST.json": "docs/reconstruction/SOURCE_MANIFEST.json",
    "source-selection.json": "docs/reconstruction/source-selection.json",
    "scripts/kit.py": "tools/reconstruction_kit.py",
}


class KitError(ValueError):
    """Raised when the reconstruction boundary fails closed."""


def _reject_constant(value: str) -> None:
    raise KitError(f"non-finite JSON constant is forbidden: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KitError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicate_keys,
        parse_constant=_reject_constant,
    )
    if not isinstance(payload, dict):
        raise KitError(f"JSON root must be an object: {path}")
    return payload


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def payload_identity(payload: dict[str, Any]) -> str:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("identity_sha256", None)
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise KitError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise KitError(f"unsafe relative path: {value!r}")
    if path.as_posix() != value or value.endswith("/"):
        raise KitError(f"non-canonical relative path: {value!r}")
    return path


def _git(repo_root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout if text else result.stdout


def git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    safe_relative_path(path)
    return _git(repo_root, "show", f"{commit}:{path}", text=False)  # type: ignore[return-value]


def git_entry_mode(repo_root: Path, commit: str, path: str) -> str:
    safe_relative_path(path)
    output = str(_git(repo_root, "ls-tree", commit, "--", path)).strip()
    if not output:
        raise KitError(f"source path is absent at {commit}: {path}")
    metadata, actual_path = output.split("\t", 1)
    mode, object_type, _object_id = metadata.split(" ", 2)
    if actual_path != path or object_type != "blob":
        raise KitError(f"source path is not a regular blob: {path}")
    if mode == "120000":
        raise KitError(f"symlink source is forbidden: {path}")
    return mode


def _source_tree(repo_root: Path, commit: str) -> set[str]:
    output = str(_git(repo_root, "ls-tree", "-r", "--name-only", commit))
    return {line for line in output.splitlines() if line}


def _module_path(module: str, tree: set[str]) -> str | None:
    candidate = module.replace(".", "/") + ".py"
    if candidate in tree:
        return candidate
    package = module.replace(".", "/") + "/__init__.py"
    return package if package in tree else None


def _imported_modules(tree: ast.AST, current_path: str) -> set[str]:
    modules: set[str] = set()
    current_module = current_path[:-3].replace("/", ".")
    package_parts = current_module.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = len(package_parts) - (node.level - 1)
                base = package_parts[: max(0, keep)]
                if node.module:
                    base.extend(node.module.split("."))
                if base:
                    modules.add(".".join(base))
            elif node.module:
                modules.add(node.module)
    return {module for module in modules if module.startswith("scenesmith")}


def _literal_dependencies(
    tree: ast.AST,
    *,
    source_tree: set[str],
    allowed_prefixes: tuple[str, ...],
) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        if not value.startswith(allowed_prefixes):
            continue
        try:
            safe_relative_path(value)
        except KitError:
            continue
        if value in source_tree:
            result.add(value)
    return result


def _classification(path: str) -> tuple[str, str]:
    if path == "LICENSE" or path.endswith("/LICENSE"):
        return "license", "required"
    if path.startswith("scenesmith/"):
        return "portable implementation", "core"
    if path.startswith("scripts/"):
        return "reproduction entrypoint", "entrypoint"
    if path.startswith("tests/"):
        return "focused regression", "validation"
    if path.startswith("configurations/"):
        return "signed compact evidence or contract", "evidence"
    if path.startswith("third_party/"):
        return "vendored structural reference", "third_party"
    if path.startswith("docs/"):
        return "canonical reference", "reference"
    return "source", "reference"


def _validate_selection(selection: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "source_commit",
        "source_repository",
        "maximum_file_bytes",
        "forbidden_prefixes",
        "literal_dependency_prefixes",
        "excluded_literal_paths",
        "explicit_paths",
        "path_globs",
        "python_seeds",
        "external_dependencies",
    }
    if set(selection) != required:
        raise KitError("source selection fields drifted")
    commit = selection["source_commit"]
    if not isinstance(commit, str) or len(commit) != 40 or any(
        c not in "0123456789abcdef" for c in commit
    ):
        raise KitError("source commit is not a full lowercase SHA-1")
    if not isinstance(selection["maximum_file_bytes"], int) or selection[
        "maximum_file_bytes"
    ] <= 0:
        raise KitError("maximum file size is invalid")
    for field in (
        "forbidden_prefixes",
        "literal_dependency_prefixes",
        "excluded_literal_paths",
        "explicit_paths",
        "path_globs",
        "python_seeds",
        "external_dependencies",
    ):
        if not isinstance(selection[field], list):
            raise KitError(f"selection field must be a list: {field}")


def build_manifest(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    selection = load_strict_json(SELECTION_PATH)
    _validate_selection(selection)
    commit = selection["source_commit"]
    subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
        check=True,
    )
    source_tree = _source_tree(root, commit)
    excluded_literal_paths: dict[str, str] = {}
    for exclusion in selection["excluded_literal_paths"]:
        if not isinstance(exclusion, dict) or set(exclusion) != {"path", "reason"}:
            raise KitError("excluded literal path fields drifted")
        path = exclusion["path"]
        reason = exclusion["reason"]
        safe_relative_path(path)
        if path in excluded_literal_paths:
            raise KitError(f"duplicate excluded literal path: {path}")
        if path not in source_tree:
            raise KitError(f"excluded literal path is absent at closeout commit: {path}")
        if not isinstance(reason, str) or not reason.strip():
            raise KitError(f"excluded literal path reason is empty: {path}")
        excluded_literal_paths[path] = reason
    selected = set(selection["explicit_paths"])
    for pattern in selection["path_globs"]:
        if not isinstance(pattern, str) or pattern.startswith("/") or ".." in pattern:
            raise KitError(f"unsafe source glob: {pattern!r}")
        matches = {path for path in source_tree if fnmatch.fnmatchcase(path, pattern)}
        if not matches:
            raise KitError(f"source glob matched nothing: {pattern}")
        selected.update(matches)

    queue = list(selection["python_seeds"])
    seen_python: set[str] = set()
    encountered_exclusions: set[str] = set()
    literal_prefixes = tuple(selection["literal_dependency_prefixes"])
    while queue:
        path = queue.pop(0)
        safe_relative_path(path)
        if path in seen_python:
            continue
        if path not in source_tree or not path.endswith(".py"):
            raise KitError(f"Python seed/import is absent: {path}")
        seen_python.add(path)
        selected.add(path)
        parsed = ast.parse(git_blob(root, commit, path), filename=path)
        for dependency in _literal_dependencies(
            parsed,
            source_tree=source_tree,
            allowed_prefixes=literal_prefixes,
        ):
            if dependency in excluded_literal_paths:
                encountered_exclusions.add(dependency)
            else:
                selected.add(dependency)
        for module in _imported_modules(parsed, path):
            imported = _module_path(module, source_tree)
            if imported and imported not in seen_python:
                queue.append(imported)

    stale_exclusions = set(excluded_literal_paths) - encountered_exclusions
    if stale_exclusions:
        raise KitError(
            "excluded literal paths are no longer reached by the selected closure: "
            + ", ".join(sorted(stale_exclusions))
        )

    entries: list[dict[str, Any]] = []
    forbidden = tuple(selection["forbidden_prefixes"])
    for path in sorted(selected):
        safe_relative_path(path)
        if path.startswith(forbidden):
            raise KitError(f"forbidden source class selected: {path}")
        if path not in source_tree:
            raise KitError(f"selected source is absent at closeout commit: {path}")
        mode = git_entry_mode(root, commit, path)
        data = git_blob(root, commit, path)
        if len(data) > selection["maximum_file_bytes"]:
            raise KitError(f"selected source exceeds size ceiling: {path}")
        role, tier = _classification(path)
        entries.append(
            {
                "path": path,
                "role": role,
                "tier": tier,
                "git_mode": mode,
                "size_bytes": len(data),
                "sha256": file_sha256(data),
            }
        )

    omitted_source_artifacts = []
    for path, reason in sorted(excluded_literal_paths.items()):
        data = git_blob(root, commit, path)
        omitted_source_artifacts.append(
            {
                "path": path,
                "reason": reason,
                "size_bytes": len(data),
                "sha256": file_sha256(data),
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "source_repository": selection["source_repository"],
        "source_commit": commit,
        "selection_sha256": file_sha256(SELECTION_PATH.read_bytes()),
        "maximum_file_bytes": selection["maximum_file_bytes"],
        "forbidden_prefixes": selection["forbidden_prefixes"],
        "excluded_data_classes": [
            "credentials and environment secrets",
            "untracked external checkouts",
            "datasets and camera observations",
            "model checkpoints and optimizer state",
            "gitignored outputs and rendered campaign media",
            "physical hardware receipts containing private observations",
        ],
        "external_dependencies": selection["external_dependencies"],
        "omitted_source_artifacts": omitted_source_artifacts,
        "files": entries,
        "authority_transferred": False,
        "physical_proof_transferred": False,
        "learned_policy_success_claimed": False,
    }
    manifest["identity_sha256"] = payload_identity(manifest)
    return manifest


def verify_manifest(manifest: dict[str, Any], repo_root: Path) -> None:
    root = repo_root.resolve()
    expected_fields = {
        "schema_version",
        "source_repository",
        "source_commit",
        "selection_sha256",
        "maximum_file_bytes",
        "forbidden_prefixes",
        "excluded_data_classes",
        "external_dependencies",
        "omitted_source_artifacts",
        "files",
        "authority_transferred",
        "physical_proof_transferred",
        "learned_policy_success_claimed",
        "identity_sha256",
    }
    if set(manifest) != expected_fields or manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise KitError("source manifest fields or schema drifted")
    if manifest.get("identity_sha256") != payload_identity(manifest):
        raise KitError("source manifest identity drifted")
    if manifest.get("selection_sha256") != file_sha256(SELECTION_PATH.read_bytes()):
        raise KitError("source selection identity drifted")
    if any(
        manifest.get(field) is not False
        for field in (
            "authority_transferred",
            "physical_proof_transferred",
            "learned_policy_success_claimed",
        )
    ):
        raise KitError("source manifest escalates a proof or authority claim")
    expected = build_manifest(root)
    if manifest != expected:
        raise KitError(
            "source manifest does not exactly match the selected commit, closure, "
            "omissions, dependencies, and source bytes"
        )


def _write_bytes(path: Path, data: bytes, *, executable: bool = False) -> None:
    if path.exists() or path.is_symlink():
        raise KitError(f"export target collision: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o755 if executable else 0o644)


def _receipt_entry(root: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    safe_relative_path(relative)
    if path.is_symlink() or not path.is_file():
        raise KitError(f"exported path is not a regular file: {relative}")
    data = path.read_bytes()
    return {
        "path": relative,
        "size_bytes": len(data),
        "sha256": file_sha256(data),
        "executable": bool(path.stat().st_mode & stat.S_IXUSR),
    }


def export_kit(repo_root: Path, destination: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    dest = destination.expanduser().resolve()
    try:
        dest.relative_to(root)
    except ValueError:
        pass
    else:
        raise KitError("export destination must be outside the source repository")
    if dest.exists() or dest.is_symlink():
        raise KitError("export destination must not already exist")
    manifest = load_strict_json(MANIFEST_PATH)
    verify_manifest(manifest, root)
    dest.mkdir(parents=True, exist_ok=False)
    try:
        for source, target in KIT_EXPORTS.items():
            source_path = KIT_ROOT / safe_relative_path(source)
            if source_path.is_symlink() or not source_path.is_file():
                raise KitError(f"kit export source is absent or aliased: {source}")
            _write_bytes(
                dest / safe_relative_path(target),
                source_path.read_bytes(),
                executable=source.endswith("scripts/kit.py"),
            )
        for entry in manifest["files"]:
            path = entry["path"]
            _write_bytes(
                dest / safe_relative_path(path),
                git_blob(root, manifest["source_commit"], path),
                executable=entry["git_mode"] == "100755",
            )
        exported = sorted(
            (_receipt_entry(dest, path) for path in dest.rglob("*") if path.is_file()),
            key=lambda row: row["path"],
        )
        receipt: dict[str, Any] = {
            "schema_version": RECEIPT_SCHEMA,
            "source_repository": manifest["source_repository"],
            "source_commit": manifest["source_commit"],
            "source_manifest_identity_sha256": manifest["identity_sha256"],
            "file_count": len(exported),
            "files": exported,
            "authority_transferred": False,
            "physical_proof_transferred": False,
            "learned_policy_success_claimed": False,
            "bulk_outputs_copied": False,
            "external_checkouts_copied": False,
        }
        receipt["identity_sha256"] = payload_identity(receipt)
        _write_bytes(
            dest / RECEIPT_NAME,
            (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        )
        verify_export(dest)
        return receipt
    except BaseException:
        shutil.rmtree(dest)
        raise


def verify_export(destination: Path) -> dict[str, Any]:
    root = destination.expanduser().resolve()
    receipt_path = root / RECEIPT_NAME
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise KitError("export receipt is absent or aliased")
    receipt = load_strict_json(receipt_path)
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise KitError("export receipt schema drifted")
    if receipt.get("identity_sha256") != payload_identity(receipt):
        raise KitError("export receipt identity drifted")
    false_fields = (
        "authority_transferred",
        "physical_proof_transferred",
        "learned_policy_success_claimed",
        "bulk_outputs_copied",
        "external_checkouts_copied",
    )
    if any(receipt.get(field) is not False for field in false_fields):
        raise KitError("export receipt escalates a forbidden claim")
    files = receipt.get("files")
    if not isinstance(files, list) or receipt.get("file_count") != len(files):
        raise KitError("export receipt file count drifted")
    expected = {RECEIPT_NAME}
    previous = ""
    for entry in files:
        if set(entry) != {"path", "size_bytes", "sha256", "executable"}:
            raise KitError("export receipt entry fields drifted")
        relative = entry["path"]
        safe_relative_path(relative)
        if relative <= previous:
            raise KitError("export receipt paths are not unique and sorted")
        previous = relative
        expected.add(relative)
        path = root / relative
        actual = _receipt_entry(root, path)
        if actual != entry:
            raise KitError(f"exported bytes or mode drifted: {relative}")
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_paths != expected:
        raise KitError("export contains unreceipted or missing paths")
    return receipt


def _write_or_check_manifest(repo_root: Path, *, check: bool) -> dict[str, Any]:
    manifest = build_manifest(repo_root)
    rendered = json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if check:
        if not MANIFEST_PATH.is_file() or MANIFEST_PATH.read_text() != rendered:
            raise KitError("generated source manifest is stale")
    else:
        MANIFEST_PATH.write_text(rendered, encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-manifest")
    build.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    build.add_argument("--check", action="store_true")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    export = subparsers.add_parser("export")
    export.add_argument("destination", type=Path)
    export.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    verify_export_parser = subparsers.add_parser("verify-export")
    verify_export_parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    if args.command == "build-manifest":
        result = _write_or_check_manifest(args.repo_root, check=args.check)
    elif args.command == "verify":
        result = load_strict_json(MANIFEST_PATH)
        verify_manifest(result, args.repo_root)
    elif args.command == "export":
        result = export_kit(args.repo_root, args.destination)
    else:
        result = verify_export(args.destination)
    print(result["identity_sha256"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KitError, OSError, subprocess.CalledProcessError) as error:
        print(f"reconstruction kit error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
