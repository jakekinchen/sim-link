#!/usr/bin/env python3
"""Build, verify, and materialize the minimal portable reconstruction assets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import uuid

from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO


SCRIPT_PATH = Path(__file__).resolve()
if SCRIPT_PATH.parent.name == "tools":
    REPO_ROOT = SCRIPT_PATH.parents[1]
    ASSET_ROOT = REPO_ROOT / "reconstruction-kit/assets"
else:
    REPO_ROOT = SCRIPT_PATH.parents[2]
    ASSET_ROOT = REPO_ROOT / "reconstruction-kit/assets"

MANIFEST_PATH = ASSET_ROOT / "ASSET_MANIFEST.json"
SCHEMA_VERSION = "scenesmith.reconstruction_asset_pack.v1"
CHUNK_SIZE_BYTES = 1_900_000
BASE_DATASET_SOURCE_ROOT = Path("outputs/robot_lab/t20_23_recovery_augmented_dataset")
BASE_DATASET_TARGET_ROOT = Path("outputs/reconstruction/r0_base_dataset")
BASE_DATASET_MANIFEST_PATH = Path(
    "configurations/robot_lab/t20_23_recovery_augmented_dataset_manifest.json"
)
BASE_DATASET_MANIFEST_IDENTITY = (
    "f12c95a3cdf3e0005fa093000a5e44e1cddd08dbfb049ab405f462e2c9e760fa"
)
BASE_DATASET_MANIFEST_FILE_SHA256 = (
    "df6e63d86cd053937c9e4d4c267f057b76aaf418761e7dc3356a9ae08c06fea5"
)

BASE_FILES = (
    (
        "data/chunk-000/file-000.parquet",
        66_114_877,
        "fc861cd7a7fb0dcced958fcd5f3bbebeab6172202e438da92cc387e1c02c4ecf",
    ),
    (
        "meta/episodes/chunk-000/file-000.parquet",
        59_881,
        "01974d0f5e66b2fa96fcfe8a263e2765e755f65847eaa22ef3fa6173a40e50bd",
    ),
    (
        "meta/info.json",
        2_445,
        "789ab860cae39d100f1d28e0e547e2229b860cdcacc2916c230074ff5e7ed9fc",
    ),
    (
        "meta/stats.json",
        13_075,
        "aae49a26834aa3684d17bede1da1407f2664c61d0bb9f33a650b269af6123bc1",
    ),
    (
        "meta/tasks.parquet",
        2_372,
        "75d507d99b8f12e63006844a0034e3ce8570ca47b22d7417f2096c29dbfa3f4f",
    ),
)

TRACE_SOURCES = (
    {
        "name": "t20_43_act_chunk_50",
        "source_path": "outputs/robot_lab/t20_43_r1_act_run_001/rollouts/step_00000_chunk_50.json",
        "asset_path": "traces/t20_43_act_chunk_50.json",
        "schema_version": "scenesmith.t20_43_r1_act_closed_loop_trace.v1",
        "identity_sha256": "6133ce582936d6f2057cff2877df1a7d66b7cb2397fbcc1032286fbf16a59507",
        "file_sha256": "f9dc0e6d2b74a817dbe5005a6dc1a46c478a8b4fe7d6198c1f981f0e45c24373",
        "size_bytes": 818_993,
    },
    {
        "name": "t20_43b_act_chunk_50",
        "source_path": "outputs/robot_lab/t20_43b_r1_act_run_001/rollouts/step_00000_chunk_50.json",
        "asset_path": "traces/t20_43b_act_chunk_50.json",
        "schema_version": "scenesmith.t20_43b_r1_act_closed_loop_trace.v1",
        "identity_sha256": "b707b815ab3b204e29dbbc8e50114307058019da3116f8f5ac496c1b6e05f4bd",
        "file_sha256": "0c01265d4536bff9f2220a0e6e26462342b5987927204db7b998f7e50f3eac46",
        "size_bytes": 819_002,
    },
    {
        "name": "t20_44_smolvla_chunk_50",
        "source_path": "outputs/robot_lab/t20_44_r2_smolvla_run_001/rollouts/step_00000_chunk_50.json",
        "asset_path": "traces/t20_44_smolvla_chunk_50.json",
        "schema_version": "scenesmith.t20_44_r2_smolvla_closed_loop_trace.v1",
        "identity_sha256": "927c6e3dde1387cffcd3da18c0cd80df52a71a03813fd5f6f846b34f1578e49b",
        "file_sha256": "cc2d3b90bdc85c7f2ac09b12125de6112730fed7947905b6ea9054a27763dde4",
        "size_bytes": 804_438,
    },
)


class AssetError(ValueError):
    """Raised when the portable asset pack fails closed."""


def _reject_constant(value: str) -> None:
    raise AssetError(f"non-finite JSON constant is forbidden: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssetError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_no_duplicate_keys,
        parse_constant=_reject_constant,
    )
    if not isinstance(payload, dict):
        raise AssetError(f"JSON root must be an object: {path}")
    return payload


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _payload_identity(payload: dict[str, Any]) -> str:
    unsigned = copy.deepcopy(payload)
    unsigned.pop("identity_sha256", None)
    return hashlib.sha256(_canonical_bytes(unsigned)).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AssetError(f"unsafe asset path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise AssetError(f"unsafe asset path: {value!r}")
    if path.as_posix() != value or value.endswith("/"):
        raise AssetError(f"non-canonical asset path: {value!r}")
    return path


def _write_chunked(source: Path, staging: Path, relative: str) -> list[dict[str, Any]]:
    rows = []
    with source.open("rb") as handle:
        index = 0
        while True:
            data = handle.read(CHUNK_SIZE_BYTES)
            if not data:
                break
            path = f"base_dataset/{relative}.parts/part-{index:05d}"
            target = staging / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append(
                {
                    "path": path,
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            index += 1
    if not rows:
        raise AssetError(f"source asset is empty: {source}")
    return rows


def build_asset_pack(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    if ASSET_ROOT.exists():
        return verify_asset_pack()
    source_manifest = load_strict_json(root / BASE_DATASET_MANIFEST_PATH)
    if (
        source_manifest.get("identity_sha256") != BASE_DATASET_MANIFEST_IDENTITY
        or _sha_file(root / BASE_DATASET_MANIFEST_PATH)
        != BASE_DATASET_MANIFEST_FILE_SHA256
    ):
        raise AssetError("base dataset manifest drifted")

    staging = ASSET_ROOT.parent / f".asset-staging-{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        base_rows = []
        for relative, size, digest in BASE_FILES:
            source = root / BASE_DATASET_SOURCE_ROOT / relative
            if (
                not source.is_file()
                or source.is_symlink()
                or source.stat().st_size != size
                or _sha_file(source) != digest
            ):
                raise AssetError(f"base dataset source drifted: {relative}")
            base_rows.append(
                {
                    "relative_path": relative,
                    "size_bytes": size,
                    "sha256": digest,
                    "chunks": _write_chunked(source, staging, relative),
                }
            )

        trace_rows = []
        for expected in TRACE_SOURCES:
            source = root / expected["source_path"]
            if (
                not source.is_file()
                or source.is_symlink()
                or source.stat().st_size != expected["size_bytes"]
                or _sha_file(source) != expected["file_sha256"]
            ):
                raise AssetError(f"trace source drifted: {expected['name']}")
            payload = load_strict_json(source)
            if (
                payload.get("schema_version") != expected["schema_version"]
                or payload.get("identity_sha256") != expected["identity_sha256"]
            ):
                raise AssetError(f"trace identity drifted: {expected['name']}")
            target = staging / expected["asset_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            trace_rows.append(dict(expected))

        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "chunk_size_bytes": CHUNK_SIZE_BYTES,
            "base_dataset": {
                "source_root": BASE_DATASET_SOURCE_ROOT.as_posix(),
                "materialized_target_root": BASE_DATASET_TARGET_ROOT.as_posix(),
                "source_manifest_path": BASE_DATASET_MANIFEST_PATH.as_posix(),
                "source_manifest_identity_sha256": BASE_DATASET_MANIFEST_IDENTITY,
                "source_manifest_file_sha256": BASE_DATASET_MANIFEST_FILE_SHA256,
                "episode_count": 10,
                "frame_count": 2330,
                "files": base_rows,
            },
            "trace_fixtures": trace_rows,
            "full_r0_dataset_included": False,
            "model_checkpoint_included": False,
            "private_observation_included": False,
            "authority_transferred": False,
        }
        manifest["identity_sha256"] = _payload_identity(manifest)
        (staging / "ASSET_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, ASSET_ROOT)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return verify_asset_pack()


def _stream_chunks(rows: list[dict[str, Any]]) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    for row in rows:
        path = _safe_relative(row.get("path")).as_posix()
        target = ASSET_ROOT / path
        if (
            not target.is_file()
            or target.is_symlink()
            or target.stat().st_size != row.get("size_bytes")
            or _sha_file(target) != row.get("sha256")
        ):
            raise AssetError(f"asset chunk drifted: {path}")
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    return digest.hexdigest(), size


def verify_asset_pack() -> dict[str, Any]:
    manifest = load_strict_json(MANIFEST_PATH)
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("identity_sha256") != _payload_identity(manifest)
        or manifest.get("chunk_size_bytes") != CHUNK_SIZE_BYTES
    ):
        raise AssetError("asset manifest identity or schema drifted")
    if any(
        manifest.get(field) is not False
        for field in (
            "full_r0_dataset_included",
            "model_checkpoint_included",
            "private_observation_included",
            "authority_transferred",
        )
    ):
        raise AssetError("asset pack widened its proof or authority boundary")
    base = manifest.get("base_dataset")
    if not isinstance(base, dict) or (
        base.get("source_manifest_identity_sha256") != BASE_DATASET_MANIFEST_IDENTITY
        or base.get("source_manifest_file_sha256") != BASE_DATASET_MANIFEST_FILE_SHA256
        or base.get("episode_count") != 10
        or base.get("frame_count") != 2330
    ):
        raise AssetError("base dataset asset contract drifted")
    files = base.get("files")
    if not isinstance(files, list) or len(files) != len(BASE_FILES):
        raise AssetError("base dataset asset file set drifted")
    expected_by_path = {path: (size, digest) for path, size, digest in BASE_FILES}
    for row in files:
        relative = _safe_relative(row.get("relative_path")).as_posix()
        if relative not in expected_by_path or not isinstance(row.get("chunks"), list):
            raise AssetError(f"unexpected base dataset asset: {relative}")
        digest, size = _stream_chunks(row["chunks"])
        expected_size, expected_digest = expected_by_path[relative]
        if (
            row.get("size_bytes") != expected_size
            or row.get("sha256") != expected_digest
            or size != expected_size
            or digest != expected_digest
        ):
            raise AssetError(f"base dataset reconstruction drifted: {relative}")
    traces = manifest.get("trace_fixtures")
    if not isinstance(traces, list) or len(traces) != len(TRACE_SOURCES):
        raise AssetError("trace fixture set drifted")
    expected_traces = {row["name"]: row for row in TRACE_SOURCES}
    for row in traces:
        expected = expected_traces.get(row.get("name"))
        if row != expected:
            raise AssetError(f"trace fixture contract drifted: {row.get('name')}")
        path = ASSET_ROOT / _safe_relative(row["asset_path"]).as_posix()
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != row["size_bytes"]
            or _sha_file(path) != row["file_sha256"]
        ):
            raise AssetError(f"trace fixture bytes drifted: {row['name']}")
        payload = load_strict_json(path)
        if (
            payload.get("schema_version") != row["schema_version"]
            or payload.get("identity_sha256") != row["identity_sha256"]
        ):
            raise AssetError(f"trace fixture identity drifted: {row['name']}")
    return manifest


def _copy_chunks(rows: list[dict[str, Any]], handle: BinaryIO) -> None:
    for row in rows:
        source = ASSET_ROOT / _safe_relative(row["path"]).as_posix()
        with source.open("rb") as chunk_handle:
            shutil.copyfileobj(chunk_handle, handle, 1024 * 1024)


def materialize_base_dataset(destination: Path | None = None) -> Path:
    manifest = verify_asset_pack()
    relative = Path(manifest["base_dataset"]["materialized_target_root"])
    target = (
        Path(destination) if destination is not None else REPO_ROOT / relative
    ).resolve()
    try:
        target.relative_to(REPO_ROOT.resolve())
    except ValueError as error:
        raise AssetError("base dataset destination escapes the repository") from error
    if os.path.lexists(target):
        raise FileExistsError(f"base dataset destination already exists: {target}")
    staging = target.parent / f".{target.name}.staging-{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        for row in manifest["base_dataset"]["files"]:
            relative_path = _safe_relative(row["relative_path"])
            output = staging.joinpath(*relative_path.parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                _copy_chunks(row["chunks"], handle)
            if (
                output.stat().st_size != row["size_bytes"]
                or _sha_file(output) != row["sha256"]
            ):
                raise AssetError(f"materialized base dataset drifted: {relative_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build")
    subparsers.add_parser("verify")
    materialize = subparsers.add_parser("materialize-base")
    materialize.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        payload = build_asset_pack()
        print(payload["identity_sha256"])
    elif args.command == "verify":
        payload = verify_asset_pack()
        print(payload["identity_sha256"])
    else:
        target = materialize_base_dataset(args.destination)
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
