"""Hash-pinned access to completed grasp diagnostics.

The T19.0 search streak is historical evidence.  Its JSON artifacts remain
tracked and signed, but their expensive builders are intentionally not part of
the active verification path.  This module has no imports from diagnostic
builders so loading the registry cannot re-run a historical experiment.
"""

from __future__ import annotations

import hashlib

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.artifact_contract import load_strict_json, verify_signed_payload


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FrozenArtifact:
    """The immutable file-level identity of one retained diagnostic."""

    path: str
    schema_version: str
    identity_sha256: str
    file_sha256: str


# These values are deliberately explicit.  Updating a frozen artifact requires
# an intentional maintenance slice that changes both the evidence and this
# registry, rather than silently regenerating it during a broad test run.
FROZEN_GRASP_DIAGNOSTICS: dict[str, FrozenArtifact] = {
    "mujoco_grasp_contact_search": FrozenArtifact(
        "configurations/robot_lab/mujoco_grasp_contact_search.json",
        "scenesmith.mujoco_grasp_contact_search.v1",
        "abf05433677d9ac367a44622dd1544c99a766c47e27d2288acfcf4c949ad74cd",
        "9959265bda0c846976e2ef6b7086e99d16b237e71cefc548cc8afe5bbedad947",
    ),
    "explicit_pad_proxy_search": FrozenArtifact(
        "configurations/robot_lab/explicit_pad_proxy_search.json",
        "scenesmith.explicit_pad_proxy_search.v1",
        "58c231affa3fc6617950e699ce5d7744f8f6ecebd82761d882698cbb6da5757d",
        "09dbfdca4731d15777ab84ef2756defe21e276e69b425ad4be5915ef567ca580",
    ),
    "pad_midpoint_search": FrozenArtifact(
        "configurations/robot_lab/pad_midpoint_search.json",
        "scenesmith.pad_midpoint_grasp_search.v1",
        "f8a38d566a2c7515e6c2df9d86289710ceee6d693cea4a622da9479d94bd8343",
        "662c7d13995c90ebc00d783bdcd12e54e613e616ac7d61c69bbae9099d3d608f",
    ),
    "post_yaw_settle_search": FrozenArtifact(
        "configurations/robot_lab/post_yaw_settle_search.json",
        "scenesmith.post_yaw_settle_grasp_search.v1",
        "832c42a49a4e0e68c8a1d23c0bc722efe8e3eacf37a525ae3b22ff4f0ef65d7a",
        "3d12e99c28957b2c0f42c29de0ea409658074ac54928b4880577a05d30f85bf8",
    ),
    "principal_axis_grasp_search": FrozenArtifact(
        "configurations/robot_lab/principal_axis_grasp_search.json",
        "scenesmith.principal_axis_grasp_search.v1",
        "ba930e4de811f77031786ca9c19c62de67c252ba58e46092e090099208229306",
        "ed370f4b5a2a8e4f4b8354a5ab8f6deb9a5cd2a6513ebdaebe8adbc9f7d9d137",
    ),
    "horizontal_axis_grasp_search": FrozenArtifact(
        "configurations/robot_lab/horizontal_axis_grasp_search.json",
        "scenesmith.horizontal_axis_grasp_search.v1",
        "4b98dca2f0e85232780af98c19a74d37f0c85259e5909834be96458f121f557a",
        "db86aef121956abf5ecea0a6272a9163e288433e5b5a34a03942233bd2062cd4",
    ),
    "best_axis_grasp_search": FrozenArtifact(
        "configurations/robot_lab/best_axis_grasp_search.json",
        "scenesmith.best_axis_grasp_search.v1",
        "5d4e323e9763e74be45bdd4baf83947e5280b6267102fbc6887fb3b6fa9783f1",
        "940b9ddfe4e3dcbe97778a89596bacfa8679b4378205aa354087a1ee4da31af8",
    ),
    "centered_axis_grasp_search": FrozenArtifact(
        "configurations/robot_lab/centered_axis_grasp_search.json",
        "scenesmith.centered_axis_grasp_search.v1",
        "6e95d8a64dd57a69cfd21d521e5c3151609c377e5d9ecab8fb5a91b57ba0c94c",
        "c5d684b89bee2b27ec0f43b7a3e47d868a1ead91f9ef159f93b6fa4ebf95c136",
    ),
    "centered_contact_face_audit": FrozenArtifact(
        "configurations/robot_lab/centered_contact_face_audit.json",
        "scenesmith.centered_contact_face_audit.v1",
        "0a0c48a149214ba40153b57db7cc616a0e48d9ccb3a1b65add7ec0c6ecd25d47",
        "d141fea2b6b57b32c91e5ab12c774e881a29c0793b2135016e21b1f9a2ed3167",
    ),
    "geometry_first_grasp_search": FrozenArtifact(
        "configurations/robot_lab/geometry_first_grasp_search.json",
        "scenesmith.geometry_first_grasp_search.v1",
        "fae4130c967982136ae58263c68a3f81fbb7a25aef02dfdaef651e7404379594",
        "9805ecb0f6f2122cc377aa6698fd986302841bb147917d173f0bc860f18cfa4c",
    ),
    "geometry_derived_unilateral_grasp": FrozenArtifact(
        "configurations/robot_lab/geometry_derived_unilateral_grasp.json",
        "scenesmith.geometry_derived_unilateral_grasp.v1",
        "bec0a3d689b9deaea6b851f32eb3cd7353bc98c5dd514307ea96f4f2ca19739b",
        "7e2b7cc2d06799eeccbe560e9366a9dfc8b3f0f19b0411930227b1bcfff90006",
    ),
}


def load_frozen_artifact(name: str) -> dict[str, Any]:
    """Load one retained artifact and verify its signed and file identities."""

    try:
        expected = FROZEN_GRASP_DIAGNOSTICS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown frozen grasp diagnostic: {name}") from exc
    path = REPO_ROOT / expected.path
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Frozen grasp diagnostic is not a regular file: {expected.path}")
    actual_file_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_file_sha256 != expected.file_sha256:
        raise ValueError(f"Frozen grasp diagnostic file hash drifted: {name}")
    payload = load_strict_json(path)
    verify_signed_payload(payload, label=f"frozen grasp diagnostic {name}")
    if payload.get("schema_version") != expected.schema_version:
        raise ValueError(f"Frozen grasp diagnostic schema drifted: {name}")
    if payload.get("identity_sha256") != expected.identity_sha256:
        raise ValueError(f"Frozen grasp diagnostic identity drifted: {name}")
    return payload
