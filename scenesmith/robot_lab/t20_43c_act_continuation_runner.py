"""One-use runner and evidence verifier for the T20.43c ACT continuation."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

from datetime import datetime
from pathlib import Path
from typing import Any

from scenesmith.robot_lab.act_grasp_closed_loop import (
    FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
    run_policy_grasp_closed_loop,
)
from scenesmith.robot_lab.artifact_contract import (
    canonical_json_bytes,
    dump_canonical_json,
    load_strict_json,
    verify_signed_payload,
)
from scenesmith.robot_lab.geometry_derived_grasp_primitives import (
    has_valid_antipodal_contact,
)
from scenesmith.robot_lab.strict_grasp import strict_grasp_spec_v2
from scenesmith.robot_lab.t20_43b_r1_act_contracts import (
    BATCH_SIZE,
    BRANCH,
    CHECKPOINT_SCHEDULE,
    CHUNK_SIZE,
    EVALUATION_ACTION_STEPS,
    MAXIMUM_OPTIMIZER_UPDATES,
    MUJOCO_SUPPORT_SITE_PACKAGES,
    R0_DATASET_REPO_ID,
    R0_DATASET_ROOT,
    STABLE_RUNNER_INTERPRETER,
    TRAINING_SEED,
)
from scenesmith.robot_lab.t20_43b_r1_act_runner import (
    ACTRolloutAdapter,
    build_comparison_rows,
    build_result,
    build_run_summary,
    build_scorecard,
    build_trace,
    verify_result,
    verify_run_summary,
    verify_trace,
    _act_config,
    _cycle,
    _file_tree,
    _seed_all,
    _sha_file,
    _source_episode_zero,
    _variant_id,
)
from scenesmith.robot_lab.t20_43c_act_continuation import (
    ACCEPTANCE_PATH,
    CHECKPOINT_ROOT,
    EQUIVALENCE_PATH,
    FAILURE_PATH,
    FINAL_RECEIPT_PATH,
    MARKER_PATH,
    OWNER_PATH,
    PERMIT_PATH,
    PROGRESS_PATH,
    RESULT_PATH,
    RETENTION_PATH,
    ROLLOUT_ROOT,
    RUN_ROOT,
    RUN_SUMMARY_PATH,
    SCORECARD_PATH,
    SOURCE_CHECKPOINT_IDENTITY,
    SOURCE_CHECKPOINT_PATH,
    SOURCE_FAILURE_IDENTITY,
    SOURCE_TRACE_PATH,
    VIDEO_ROOT,
    build_continuation_marker,
    build_equivalence_receipt,
    build_final_receipt,
    build_retention_receipt,
    build_terminal_failure,
    load_continuation_sources,
    verify_acceptance,
    verify_continuation_marker,
    verify_equivalence_receipt,
    verify_materialized_authority,
    verify_terminal_failure,
)
from scenesmith.robot_lab.t20_43c_act_continuation_materialization import (
    IMPLEMENTATION_SCOPED_PATHS,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_authorized_continuation(
    *, started_at: str, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    try:
        return _run_authorized_continuation(started_at=started_at, repo_root=root)
    except Exception as error:
        if (
            (root / MARKER_PATH).is_file()
            and not (root / FAILURE_PATH).exists()
            and not (root / FINAL_RECEIPT_PATH).exists()
        ):
            marker = load_strict_json(root / MARKER_PATH)
            progress = (
                load_strict_json(root / PROGRESS_PATH)
                if (root / PROGRESS_PATH).is_file()
                else {
                    "stage": "unknown_after_marker",
                    "optimizer_update_count": 0,
                    "training_batches_consumed": 0,
                    "equivalence_proven": False,
                }
            )
            partial_tree = _partial_run_tree(root / RUN_ROOT)
            failure = build_terminal_failure(
                marker=marker,
                progress=progress,
                partial_run_tree=partial_tree,
                error_type=type(error).__name__,
                error_message=str(error) or repr(error),
            )
            dump_canonical_json(root / FAILURE_PATH, failure)
            verify_terminal_failure(
                failure, marker=marker, partial_run_tree=partial_tree
            )
        raise


def _run_authorized_continuation(*, started_at: str, repo_root: Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_continuation_sources(repo_root=root)
    bundle = verify_materialized_authority(repo_root=root)
    owner = bundle[OWNER_PATH.as_posix()]
    permit = bundle[PERMIT_PATH.as_posix()]
    acceptance = load_strict_json(root / ACCEPTANCE_PATH)
    verify_acceptance(acceptance, permit=permit)
    _require_active_time(owner, started_at)
    _require_remote_preservation(permit=permit, acceptance=acceptance, repo_root=root)
    if Path(sys.executable).resolve() != (root / STABLE_RUNNER_INTERPRETER).resolve():
        raise ValueError("T20.43c runner interpreter drifted")
    if str(MUJOCO_SUPPORT_SITE_PACKAGES) not in sys.path:
        raise ValueError("T20.43c stable MuJoCo support path is absent")
    if any(
        os.path.lexists(root / path)
        for path in (
            MARKER_PATH,
            EQUIVALENCE_PATH,
            RUN_ROOT,
            RESULT_PATH,
            SCORECARD_PATH,
            RETENTION_PATH,
            FINAL_RECEIPT_PATH,
            FAILURE_PATH,
        )
    ):
        raise FileExistsError("T20.43c immutable continuation/output already exists")
    if any(
        _path_or_parent_is_symlink(root, path)
        for path in (
            MARKER_PATH,
            EQUIVALENCE_PATH,
            RUN_ROOT,
            RESULT_PATH,
            SCORECARD_PATH,
            RETENTION_PATH,
            FINAL_RECEIPT_PATH,
            FAILURE_PATH,
        )
    ):
        raise ValueError("T20.43c continuation/output path is aliased")

    marker = build_continuation_marker(
        permit=permit,
        source_commit=_git(root, "rev-parse", "HEAD"),
        started_at=started_at,
    )
    dump_canonical_json(root / MARKER_PATH, marker)
    verify_continuation_marker(marker, permit=permit)
    (root / CHECKPOINT_ROOT).mkdir(parents=True, exist_ok=False)
    (root / ROLLOUT_ROOT).mkdir(parents=True, exist_ok=False)
    (root / VIDEO_ROOT).mkdir(parents=True, exist_ok=False)
    progress = {
        "stage": "post_marker_equivalence",
        "optimizer_update_count": 0,
        "training_batches_consumed": 0,
        "equivalence_proven": False,
        "model_constructed": False,
        "model_loaded": False,
        "model_inference": False,
        "optimizer_created": False,
        "optimizer_training": False,
    }
    dump_canonical_json(root / PROGRESS_PATH, progress)

    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
        }
    )
    import torch
    from safetensors.torch import load_file as load_safetensors
    from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
    from lerobot.datasets import EpisodeAwareSampler, LeRobotDataset
    from lerobot.datasets.dataset_metadata import LeRobotDatasetMetadata
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.act.processor_act import make_act_pre_post_processors

    if not torch.backends.mps.is_available():
        raise RuntimeError("T20.43c requires MPS")
    _seed_all(TRAINING_SEED, torch)
    config = _act_config(
        ACTConfig=ACTConfig,
        FeatureType=FeatureType,
        NormalizationMode=NormalizationMode,
        PolicyFeature=PolicyFeature,
    )
    metadata = LeRobotDatasetMetadata(R0_DATASET_REPO_ID, root=root / R0_DATASET_ROOT)
    dataset = LeRobotDataset(
        R0_DATASET_REPO_ID,
        root=root / R0_DATASET_ROOT,
        delta_timestamps={
            "action": [index / metadata.fps for index in range(CHUNK_SIZE)]
        },
        return_uint8=False,
    )
    sampler = EpisodeAwareSampler(
        dataset.meta.episodes["dataset_from_index"],
        dataset.meta.episodes["dataset_to_index"],
        episode_indices_to_use=dataset.episodes,
        shuffle=True,
        seed=TRAINING_SEED,
        absolute_to_relative_idx=dataset.absolute_to_relative_idx,
    )
    policy = ACTPolicy(config)
    progress["model_constructed"] = True
    dump_canonical_json(root / PROGRESS_PATH, progress)
    saved_state = load_safetensors(
        str(root / SOURCE_CHECKPOINT_PATH / "model.safetensors"), device="cpu"
    )
    fresh_state = policy.state_dict()
    equivalence_evidence = _prove_tensor_equivalence(
        fresh_state=fresh_state, saved_state=saved_state, torch=torch
    )
    policy.load_state_dict(saved_state, strict=True)
    progress["model_loaded"] = True
    policy = policy.to("mps")
    optimizer = torch.optim.AdamW(policy.get_optim_params(), lr=1e-5, weight_decay=1e-4)
    progress["optimizer_created"] = True
    if optimizer.state or any(
        group.get("params") is None for group in optimizer.param_groups
    ):
        raise ValueError("T20.43c optimizer is not empty before update 1")
    equivalence = build_equivalence_receipt(marker=marker, **equivalence_evidence)
    dump_canonical_json(root / EQUIVALENCE_PATH, equivalence)
    verify_equivalence_receipt(equivalence, marker=marker)
    progress.update({"stage": "checkpoint_0_evaluation", "equivalence_proven": True})
    dump_canonical_json(root / PROGRESS_PATH, progress)

    preprocessor, postprocessor = make_act_pre_post_processors(
        config, dataset_stats=dataset.meta.stats
    )
    source_ref, source_frames = _source_episode_zero(root)
    thresholds = sources["source_bundle"]["frozen_gate"]["amended_gate_b_conjunction"]
    thresholds = thresholds["phase_joint_maximum_error_rad"]
    losses: list[float] = []
    gradient_norms: list[float] = []
    checkpoints: list[dict[str, Any]] = [
        {
            "optimizer_update_count": 0,
            "path": SOURCE_CHECKPOINT_PATH.as_posix(),
            "tree": sources["checkpoint_tree"],
            "identity_sha256": SOURCE_CHECKPOINT_IDENTITY,
        }
    ]
    evaluations: list[dict[str, Any]] = []

    def evaluate(update: int, checkpoint_identity: str) -> None:
        variants = []
        for n_action_steps in EVALUATION_ACTION_STEPS:
            variant_id = _variant_id(n_action_steps)
            if update == 0 and variant_id == "chunk_50":
                trace = sources["trace"]
                trace_path = SOURCE_TRACE_PATH
                rollout = trace["closed_loop"]
            else:
                policy.reset()
                observed: list[dict[str, Any]] = []
                adapter = ACTRolloutAdapter(
                    policy=policy,
                    preprocessor=preprocessor,
                    postprocessor=postprocessor,
                    torch=torch,
                    source_frames=source_frames,
                    n_action_steps=n_action_steps,
                    thresholds=thresholds,
                )
                rollout = run_policy_grasp_closed_loop(
                    adapter,
                    checkpoint_sha256=checkpoint_identity,
                    training_run_summary_sha256=sources["spec"]["identity_sha256"],
                    seed=0,
                    schema_version="scenesmith.t20_43b_r1_act_rollout.v1",
                    task_id="T20.43b",
                    evidence_mode=f"step_{update}_{variant_id}",
                    policy_label="ACT_R1_STANDARD",
                    frame_observer=observed.append,
                    release_clearance_basis=FORCE_BEARING_RELEASE_CLEARANCE_BASIS,
                    capture_images=True,
                )
                progress["model_inference"] = True
                dump_canonical_json(root / PROGRESS_PATH, progress)
                requirement = strict_grasp_spec_v2()["antipodal_contact_requirement"]
                for row in observed:
                    row["t20_43b_strict_contact"] = has_valid_antipodal_contact(
                        row, requirement
                    )
                rows = build_comparison_rows(
                    source_frames=source_frames,
                    candidate_frames=observed,
                    n_action_steps=n_action_steps,
                )
                trace = build_trace(
                    update=update,
                    variant_id=variant_id,
                    n_action_steps=n_action_steps,
                    checkpoint_identity_sha256=checkpoint_identity,
                    source_ref=source_ref,
                    rows=rows,
                    decode_rows=adapter.decode_rows,
                    closed_loop=rollout,
                )
                trace_path = ROLLOUT_ROOT / f"step_{update:05d}_{variant_id}.json"
                dump_canonical_json(root / trace_path, trace)
            video_path = VIDEO_ROOT / f"step_{update:05d}_{variant_id}.mp4"
            _render_mirror_v2(
                trace_path=trace_path, video_path=video_path, repo_root=root
            )
            manifest_path = video_path.with_suffix(".manifest.json")
            manifest = load_strict_json(root / manifest_path)
            variants.append(
                {
                    "variant_id": variant_id,
                    "n_action_steps": n_action_steps,
                    "strict_v2_passed": rollout["simulation_semantic_strict_success"],
                    "terminal_outcome": rollout["terminal_outcome"],
                    "trace_path": trace_path.as_posix(),
                    "trace_identity_sha256": trace["identity_sha256"],
                    "video_path": video_path.as_posix(),
                    "video_file_sha256": _sha_file(root / video_path),
                    "video_manifest_path": manifest_path.as_posix(),
                    "video_manifest_identity_sha256": manifest["identity_sha256"],
                }
            )
        evaluations.append({"optimizer_update_count": update, "variants": variants})
        print(
            "evaluation",
            update,
            [(row["variant_id"], row["strict_v2_passed"]) for row in variants],
            flush=True,
        )

    evaluate(0, SOURCE_CHECKPOINT_IDENTITY)
    progress.update({"stage": "optimizer_training", "optimizer_training": True})
    dump_canonical_json(root / PROGRESS_PATH, progress)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        sampler=sampler,
        shuffle=False,
        num_workers=0,
        drop_last=False,
    )
    iterator = _cycle(dataloader)
    for update in range(1, MAXIMUM_OPTIMIZER_UPDATES + 1):
        policy.train()
        batch = next(iterator)
        progress["training_batches_consumed"] = update
        batch = preprocessor(batch)
        optimizer.zero_grad(set_to_none=True)
        loss, _ = policy(batch)
        if not torch.isfinite(loss):
            raise ValueError(f"T20.43c non-finite loss at update {update}")
        loss.backward()
        if not all(
            torch.isfinite(parameter.grad).all().item()
            for parameter in policy.parameters()
            if parameter.grad is not None
        ):
            raise ValueError(f"T20.43c non-finite gradient at update {update}")
        norm = torch.nn.utils.clip_grad_norm_(policy.parameters(), 10.0)
        if not torch.isfinite(norm):
            raise ValueError(f"T20.43c non-finite gradient norm at update {update}")
        optimizer.step()
        torch.mps.synchronize()
        losses.append(float(loss.detach().cpu()))
        gradient_norms.append(float(norm.detach().cpu()))
        progress["optimizer_update_count"] = update
        dump_canonical_json(root / PROGRESS_PATH, progress)
        if update % 100 == 0:
            print("update", update, losses[-1], flush=True)
        if update in CHECKPOINT_SCHEDULE[1:]:
            progress["stage"] = f"checkpoint_{update}_evaluation"
            dump_canonical_json(root / PROGRESS_PATH, progress)
            checkpoint_path = CHECKPOINT_ROOT / f"step_{update:05d}"
            policy.save_pretrained(root / checkpoint_path, safe_serialization=True)
            tree = _file_tree(root / checkpoint_path)
            checkpoint_identity = hashlib.sha256(canonical_json_bytes(tree)).hexdigest()
            checkpoints.append(
                {
                    "optimizer_update_count": update,
                    "path": checkpoint_path.as_posix(),
                    "tree": tree,
                    "identity_sha256": checkpoint_identity,
                }
            )
            evaluate(update, checkpoint_identity)
            progress["stage"] = "optimizer_training"
            dump_canonical_json(root / PROGRESS_PATH, progress)

    progress["stage"] = "terminal_evidence"
    dump_canonical_json(root / PROGRESS_PATH, progress)
    run = build_run_summary(
        attempt=marker,
        spec=sources["spec"],
        optimizer_update_count=MAXIMUM_OPTIMIZER_UPDATES,
        losses=losses,
        gradient_norms=gradient_norms,
        checkpoints=checkpoints,
        evaluations=evaluations,
    )
    dump_canonical_json(root / RUN_SUMMARY_PATH, run)
    result = build_result(run=run)
    dump_canonical_json(root / RESULT_PATH, result)
    scorecard = build_scorecard(result=result, run=run)
    dump_canonical_json(root / SCORECARD_PATH, scorecard)
    trees = {
        "checkpoints": _file_tree(root / CHECKPOINT_ROOT),
        "rollouts": _file_tree(root / ROLLOUT_ROOT),
        "mirrors": _file_tree(root / VIDEO_ROOT),
    }
    retention = build_retention_receipt(
        result=result, run=run, local_output_trees=trees
    )
    dump_canonical_json(root / RETENTION_PATH, retention)
    final = build_final_receipt(
        marker=marker, equivalence=equivalence, result=result, retention=retention
    )
    dump_canonical_json(root / FINAL_RECEIPT_PATH, final)
    return verify_all_continuation_outputs(repo_root=root)


def verify_all_continuation_outputs(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    sources = load_continuation_sources(repo_root=root)
    bundle = verify_materialized_authority(repo_root=root)
    permit = bundle[PERMIT_PATH.as_posix()]
    marker = load_strict_json(root / MARKER_PATH)
    verify_continuation_marker(marker, permit=permit)
    if (root / FAILURE_PATH).is_file():
        if (root / FINAL_RECEIPT_PATH).exists():
            raise ValueError("T20.43c failure and final receipt coexist")
        failure = load_strict_json(root / FAILURE_PATH)
        partial_tree = _partial_run_tree(root / RUN_ROOT)
        verify_terminal_failure(failure, marker=marker, partial_run_tree=partial_tree)
        return failure
    equivalence = load_strict_json(root / EQUIVALENCE_PATH)
    verify_equivalence_receipt(equivalence, marker=marker)
    run = load_strict_json(root / RUN_SUMMARY_PATH)
    verify_run_summary(run)
    if run.get("attempt_identity_sha256") != marker["identity_sha256"]:
        raise ValueError("T20.43c run marker linkage drifted")
    for checkpoint in run["checkpoints"]:
        if _file_tree(root / checkpoint["path"]) != checkpoint["tree"]:
            raise ValueError("T20.43c checkpoint tree drifted")
    for evaluation in run["evaluations"]:
        for variant in evaluation["variants"]:
            trace = load_strict_json(root / variant["trace_path"])
            verify_trace(trace)
            if trace["identity_sha256"] != variant["trace_identity_sha256"]:
                raise ValueError("T20.43c trace identity drifted")
            video = root / variant["video_path"]
            manifest = load_strict_json(root / variant["video_manifest_path"])
            verify_signed_payload(manifest, label="T20.43c mirror manifest")
            if (
                not video.is_file()
                or video.is_symlink()
                or _sha_file(video) != variant["video_file_sha256"]
                or manifest.get("trace_identity_sha256") != trace["identity_sha256"]
                or manifest.get("output_sha256") != variant["video_file_sha256"]
            ):
                raise ValueError("T20.43c mirror evidence drifted")
    result = load_strict_json(root / RESULT_PATH)
    verify_result(result, run=run)
    scorecard = load_strict_json(root / SCORECARD_PATH)
    if scorecard != build_scorecard(result=result, run=run):
        raise ValueError("T20.43c scorecard drifted")
    trees = {
        "checkpoints": _file_tree(root / CHECKPOINT_ROOT),
        "rollouts": _file_tree(root / ROLLOUT_ROOT),
        "mirrors": _file_tree(root / VIDEO_ROOT),
    }
    retention = load_strict_json(root / RETENTION_PATH)
    if retention != build_retention_receipt(
        result=result, run=run, local_output_trees=trees
    ):
        raise ValueError("T20.43c retention drifted")
    final = load_strict_json(root / FINAL_RECEIPT_PATH)
    if final != build_final_receipt(
        marker=marker, equivalence=equivalence, result=result, retention=retention
    ):
        raise ValueError("T20.43c final continuation receipt drifted")
    if sources["failure"]["identity_sha256"] != SOURCE_FAILURE_IDENTITY:
        raise ValueError("T20.43c original failure was not preserved")
    return final


def _prove_tensor_equivalence(
    *, fresh_state: dict[str, Any], saved_state: dict[str, Any], torch: Any
) -> dict[str, Any]:
    if set(fresh_state) != set(saved_state):
        missing = sorted(set(fresh_state) ^ set(saved_state))[:5]
        raise ValueError(f"T20.43c checkpoint key set mismatch: {missing}")
    digest = hashlib.sha256()
    element_count = 0
    dtype_counts: dict[str, int] = {}
    for key in sorted(fresh_state):
        fresh = fresh_state[key].detach().cpu().contiguous()
        saved = saved_state[key].detach().cpu().contiguous()
        if fresh.shape != saved.shape or fresh.dtype != saved.dtype:
            raise ValueError(f"T20.43c checkpoint tensor metadata mismatch: {key}")
        if not torch.equal(fresh, saved):
            maximum = float(torch.max(torch.abs(fresh.float() - saved.float())).item())
            raise ValueError(f"T20.43c checkpoint tensor mismatch: {key} max={maximum}")
        dtype = str(fresh.dtype)
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
        element_count += fresh.numel()
        digest.update(key.encode())
        digest.update(dtype.encode())
        digest.update(str(list(fresh.shape)).encode())
        digest.update(fresh.reshape(-1).view(torch.uint8).numpy().tobytes())
    return {
        "tensor_key_count": len(fresh_state),
        "tensor_element_count": element_count,
        "tensor_dtype_counts": dtype_counts,
        "compared_tensor_sha256": digest.hexdigest(),
    }


def _render_mirror_v2(*, trace_path: Path, video_path: Path, repo_root: Path) -> None:
    command = [
        STABLE_RUNNER_INTERPRETER.as_posix(),
        str(repo_root / "scripts/robot_lab/render_rollout_mirror_v2.py"),
        "--trace",
        trace_path.as_posix(),
        "--output-mp4",
        video_path.as_posix(),
        "--fps",
        "25",
    ]
    subprocess.run(
        command,
        cwd=repo_root,
        check=True,
        env={
            **os.environ,
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONPATH": (
                f"{repo_root / 'external/lerobot/src'}:"
                f"{repo_root / 'external/lerobot/.venv/lib/python3.12/site-packages'}:"
                f"{MUJOCO_SUPPORT_SITE_PACKAGES}"
            ),
        },
    )


def _require_active_time(owner: dict[str, Any], started_at: str) -> None:
    started = datetime.fromisoformat(started_at)
    valid_from = datetime.fromisoformat(owner["valid_from"])
    valid_until = datetime.fromisoformat(owner["valid_until"])
    if started.tzinfo is None or not valid_from <= started <= valid_until:
        raise ValueError("T20.43c continuation start is outside authority window")
    if datetime.now(started.tzinfo) > valid_until:
        raise ValueError("T20.43c authority window expired before marker")


def _require_remote_preservation(
    *, permit: dict[str, Any], acceptance: dict[str, Any], repo_root: Path
) -> None:
    head = _git(repo_root, "rev-parse", "HEAD")
    branch = _git(repo_root, "branch", "--show-current")
    if branch != BRANCH:
        raise ValueError("T20.43c branch drifted")
    for ancestor in (permit["required_source_commit"], acceptance["authority_commit"]):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "merge-base",
                "--is-ancestor",
                ancestor,
                head,
            ],
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("T20.43c reviewed authority is not in current history")
    remote = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "merge-base",
            "--is-ancestor",
            head,
            f"refs/remotes/origin/{BRANCH}",
        ],
        check=False,
    )
    if remote.returncode != 0:
        raise ValueError("T20.43c current source is not preserved on origin")
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if dirty.strip():
        raise ValueError("T20.43c implementation paths are dirty")
    implementation_diff = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "diff",
            "--quiet",
            permit["required_source_commit"],
            head,
            "--",
            *[path.as_posix() for path in IMPLEMENTATION_SCOPED_PATHS],
        ],
        check=False,
    )
    if implementation_diff.returncode != 0:
        raise ValueError("T20.43c reviewed implementation changed after authority")
    reviewer = repo_root / acceptance["reviewer_path"]
    if (
        not reviewer.is_file()
        or reviewer.is_symlink()
        or _sha_file(reviewer) != acceptance["reviewer_file_sha256"]
    ):
        raise ValueError("T20.43c reviewer acceptance evidence drifted")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _path_or_parent_is_symlink(root: Path, relative: Path) -> bool:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return True
    return False


def _partial_run_tree(root: Path) -> list[dict[str, Any]]:
    """Hash any partial files without rejecting a just-created empty run root."""

    if not root.exists():
        return []
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"T20.43c partial run tree is absent or aliased: {root}")
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"T20.43c partial run tree contains a symlink: {path}")
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha_file(path),
                }
            )
    return rows


__all__ = [
    "run_authorized_continuation",
    "verify_all_continuation_outputs",
    "_partial_run_tree",
    "_prove_tensor_equivalence",
]
