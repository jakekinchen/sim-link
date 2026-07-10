"""Bounded, Git-audited PI0.5 DAgger cycle orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from scenesmith.robot_lab.autolearn import (
    PromotionGate,
    decide_promotion,
    summarize_evaluation,
)


SENSITIVE_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY")
FORBIDDEN_COMMAND_MARKERS = (
    "/dev/cu.usbmodem5b3d0406411",
    "so101follower",
    "send_action",
)
SHELL_EXECUTABLES = {"bash", "sh", "zsh", "fish"}


class CycleExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class StageSpec:
    name: str
    argv: tuple[str, ...]
    timeout_s: float
    required_artifacts: tuple[str, ...] = ()
    allowed_exit_codes: tuple[int, ...] = (0,)
    log_path: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StageSpec":
        argv = payload.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise ValueError("Stage argv must be a non-empty string array")
        timeout_s = float(payload.get("timeout_s") or 0)
        if timeout_s <= 0:
            raise ValueError(f"Stage {payload.get('name')!r} requires a positive timeout_s")
        allowed = tuple(int(value) for value in payload.get("allowed_exit_codes", [0]))
        if not allowed:
            raise ValueError("allowed_exit_codes cannot be empty")
        env = payload.get("env") or {}
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in env.items()
        ):
            raise ValueError("Stage env must be a string mapping")
        if any(_looks_sensitive_env_key(key) for key in env):
            raise ValueError("Do not put credentials in cycle config env; inherit them from the host")
        stage = cls(
            name=str(payload.get("name") or ""),
            argv=tuple(argv),
            timeout_s=timeout_s,
            required_artifacts=tuple(str(path) for path in payload.get("required_artifacts", [])),
            allowed_exit_codes=allowed,
            log_path=str(payload["log_path"]) if payload.get("log_path") else None,
            env=dict(env),
        )
        stage.validate_command()
        return stage

    def render(self, context: dict[str, Any]) -> "StageSpec":
        rendered = StageSpec(
            name=self.name,
            argv=tuple(value.format_map(context) for value in self.argv),
            timeout_s=self.timeout_s,
            required_artifacts=tuple(value.format_map(context) for value in self.required_artifacts),
            allowed_exit_codes=self.allowed_exit_codes,
            log_path=self.log_path.format_map(context) if self.log_path else None,
            env={key: value.format_map(context) for key, value in self.env.items()},
        )
        rendered.validate_command()
        return rendered

    def validate_command(self) -> None:
        if not self.name:
            raise ValueError("Stage name cannot be empty")
        executable = Path(self.argv[0]).name.lower()
        if executable in SHELL_EXECUTABLES and "-c" in self.argv[1:]:
            raise ValueError(f"Stage {self.name} may not use shell -c")
        joined = " ".join(self.argv).lower()
        marker = next((value for value in FORBIDDEN_COMMAND_MARKERS if value in joined), None)
        if marker:
            raise ValueError(f"Stage {self.name} contains forbidden follower command marker: {marker}")


@dataclass(frozen=True)
class ExternalComputeSpec:
    provider: str
    cleanup: StageSpec
    inventory: StageSpec

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "ExternalComputeSpec | None":
        if not payload:
            return None
        provider = str(payload.get("provider") or "")
        cleanup = StageSpec.from_dict(payload["cleanup"])
        inventory = StageSpec.from_dict(payload["inventory"])
        if provider != "brev":
            raise ValueError(f"Unsupported external compute provider: {provider}")
        cleanup_argv = tuple(Path(value).name if index == 0 else value for index, value in enumerate(cleanup.argv))
        if cleanup_argv[0] != "brev" or len(cleanup_argv) < 3 or cleanup_argv[1] not in {"stop", "delete"}:
            raise ValueError("Brev cleanup must be `brev stop NAME` or `brev delete NAME`")
        inventory_argv = tuple(Path(value).name if index == 0 else value for index, value in enumerate(inventory.argv))
        if inventory_argv[:2] != ("brev", "ls"):
            raise ValueError("Brev inventory must start with `brev ls`")
        return cls(provider=provider, cleanup=cleanup, inventory=inventory)


@dataclass(frozen=True)
class CycleConfig:
    cycle_id: str
    train_seeds: tuple[int, ...]
    eval_seeds: tuple[int, ...]
    accepted_model: str
    candidate_model: str
    manifest_path: str
    accepted_pointer_path: str
    baseline_evaluation: str
    candidate_evaluation: str
    stages: tuple[StageSpec, ...]
    training_stage: str
    max_training_steps: int
    git_auto_commit: bool
    git_clean_paths: tuple[str, ...]
    promotion_gate: PromotionGate
    external_compute: ExternalComputeSpec | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CycleConfig":
        if payload.get("schema_version") != "scenesmith.pi05_autolearn.v1":
            raise ValueError("Unsupported cycle schema_version")
        train_seeds = tuple(int(value) for value in payload.get("train_seeds", []))
        eval_seeds = tuple(int(value) for value in payload.get("eval_seeds", []))
        if not train_seeds or not eval_seeds:
            raise ValueError("Cycle requires non-empty train_seeds and eval_seeds")
        if len(set(train_seeds)) != len(train_seeds) or len(set(eval_seeds)) != len(eval_seeds):
            raise ValueError("Train and evaluation seeds must be unique")
        overlap = sorted(set(train_seeds) & set(eval_seeds))
        if overlap:
            raise ValueError(f"Train and evaluation seeds overlap: {overlap}")
        if not _is_contiguous(train_seeds) or not _is_contiguous(eval_seeds):
            raise ValueError("Train and evaluation seed lists must each be contiguous")
        stages = tuple(StageSpec.from_dict(item) for item in payload.get("stages", []))
        names = [stage.name for stage in stages]
        if len(names) != len(set(names)):
            raise ValueError("Stage names must be unique")
        training = payload.get("training") or {}
        training_stage = str(training.get("stage") or "")
        max_training_steps = int(training.get("max_steps") or 0)
        if training_stage not in names:
            raise ValueError("training.stage must name a configured stage")
        if max_training_steps <= 0:
            raise ValueError("training.max_steps must be positive")
        training_spec = next(stage for stage in stages if stage.name == training_stage)
        if not _declares_step_bound(training_spec.argv, max_training_steps):
            raise ValueError("Training argv must declare the configured finite max_steps")
        git = payload.get("git") or {}
        promotion = payload.get("promotion") or {}
        config = cls(
            cycle_id=str(payload.get("cycle_id") or ""),
            train_seeds=train_seeds,
            eval_seeds=eval_seeds,
            accepted_model=str(payload.get("accepted_model") or ""),
            candidate_model=str(payload.get("candidate_model") or ""),
            manifest_path=str(payload.get("manifest_path") or ""),
            accepted_pointer_path=str(payload.get("accepted_pointer_path") or ""),
            baseline_evaluation=str(payload.get("baseline_evaluation") or ""),
            candidate_evaluation=str(payload.get("candidate_evaluation") or ""),
            stages=stages,
            training_stage=training_stage,
            max_training_steps=max_training_steps,
            git_auto_commit=bool(git.get("auto_commit")),
            git_clean_paths=tuple(str(value) for value in git.get("clean_paths", [])),
            promotion_gate=PromotionGate(
                expected_seeds=eval_seeds,
                min_pure_success_rate=float(promotion.get("min_pure_success_rate", 0.8)),
                min_success_rate_delta=float(promotion.get("min_success_rate_delta", 0.0)),
                allow_contact_gated_grasp_assist=bool(
                    promotion.get("allow_contact_gated_grasp_assist", False)
                ),
            ),
            external_compute=ExternalComputeSpec.from_dict(payload.get("external_compute")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        required_strings = {
            "cycle_id": self.cycle_id,
            "accepted_model": self.accepted_model,
            "candidate_model": self.candidate_model,
            "manifest_path": self.manifest_path,
            "accepted_pointer_path": self.accepted_pointer_path,
            "baseline_evaluation": self.baseline_evaluation,
            "candidate_evaluation": self.candidate_evaluation,
        }
        missing = [name for name, value in required_strings.items() if not value]
        if missing:
            raise ValueError(f"Cycle config missing values: {missing}")
        if not self.git_clean_paths:
            raise ValueError("git.clean_paths cannot be empty")

    def context(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "accepted_model": self.accepted_model,
            "candidate_model": self.candidate_model,
            "train_seed_start": min(self.train_seeds),
            "train_episodes": len(self.train_seeds),
            "eval_seed_start": min(self.eval_seeds),
            "eval_episodes": len(self.eval_seeds),
            "max_steps": self.max_training_steps,
        }


@dataclass(frozen=True)
class StageResult:
    exit_code: int
    duration_s: float
    log_path: str
    log_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StageRunner(Protocol):
    def run(self, stage: StageSpec, *, repo_root: Path) -> StageResult:
        ...


class SubprocessStageRunner:
    def run(self, stage: StageSpec, *, repo_root: Path) -> StageResult:
        log_path = repo_root / (
            stage.log_path
            or f"outputs/robot_lab/autolearn/logs/{stage.name}.log"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(stage.env)
        started = time.monotonic()
        with log_path.open("wb") as handle:
            try:
                completed = subprocess.run(
                    list(stage.argv),
                    cwd=repo_root,
                    env=env,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    timeout=stage.timeout_s,
                    check=False,
                )
                exit_code = completed.returncode
            except subprocess.TimeoutExpired:
                exit_code = 124
        return StageResult(
            exit_code=exit_code,
            duration_s=round(time.monotonic() - started, 3),
            log_path=str(log_path.relative_to(repo_root)),
            log_sha256=_sha256(log_path),
        )


class GitRecorder:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def head(self) -> str:
        return self._run("rev-parse", "HEAD").strip()

    def require_clean(self, paths: tuple[str, ...]) -> None:
        output = self._run("status", "--porcelain", "--untracked-files=all", "--", *paths)
        if output.strip():
            raise CycleExecutionError(
                "Learning-loop paths are dirty; commit feature/config changes before training:\n"
                + output
            )

    def commit(self, paths: list[Path], message: str) -> str:
        relative = [str(path.relative_to(self.repo_root)) for path in paths]
        self._run("add", "--", *relative)
        self._run("commit", "--only", "-m", message, "--", *relative)
        return self.head()

    def _run(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if completed.returncode != 0:
            raise CycleExecutionError(f"git {' '.join(args)} failed: {completed.stdout.strip()}")
        return completed.stdout


class CycleRunner:
    def __init__(
        self,
        config: CycleConfig,
        *,
        repo_root: Path,
        config_path: Path,
        stage_runner: StageRunner | None = None,
        git_recorder: GitRecorder | None = None,
        enforce_git: bool = True,
    ) -> None:
        self.config = config
        self.repo_root = repo_root.resolve()
        self.config_path = config_path.resolve()
        self.stage_runner = stage_runner or SubprocessStageRunner()
        self.git = git_recorder or GitRecorder(self.repo_root)
        self.enforce_git = enforce_git
        self.context = config.context()
        self.stages = tuple(stage.render(self.context) for stage in config.stages)
        self.external_cleaned = False

    def run(self, *, dry_run: bool = False) -> dict[str, Any]:
        manifest_path = self._path(self.config.manifest_path.format_map(self.context))
        accepted_path = self._path(self.config.accepted_pointer_path.format_map(self.context))
        if not dry_run and self.enforce_git:
            if not self.config.git_auto_commit:
                raise CycleExecutionError("Real cycles require git.auto_commit=true")
            self.git.require_clean(self.config.git_clean_paths)
        source_commit = self.git.head() if self.enforce_git else "test-no-git"
        manifest: dict[str, Any] = {
            "schema_version": "scenesmith.pi05_autolearn_cycle.v1",
            "cycle_id": self.config.cycle_id,
            "status": "dry_run" if dry_run else "running",
            "source_commit": source_commit,
            "config_path": str(self.config_path.relative_to(self.repo_root)),
            "config_sha256": _sha256(self.config_path),
            "accepted_model": self.config.accepted_model,
            "candidate_model": self.config.candidate_model,
            "train_seeds": list(self.config.train_seeds),
            "eval_seeds": list(self.config.eval_seeds),
            "max_training_steps": self.config.max_training_steps,
            "stages": [self._planned_stage(stage) for stage in self.stages],
            "external_compute": (
                {"provider": self.config.external_compute.provider, "cleanup_required": True}
                if self.config.external_compute
                else {"provider": "none", "cleanup_required": False}
            ),
            "promotion": None,
        }
        _write_json(manifest_path, manifest)
        if dry_run:
            return manifest

        completed_stages: list[dict[str, Any]] = []
        training_attempted = False
        try:
            for stage in self.stages:
                record = self._planned_stage(stage)
                record["git_commit_before"] = self.git.head() if self.enforce_git else source_commit
                if stage.name == self.config.training_stage:
                    training_attempted = True
                result = self.stage_runner.run(stage, repo_root=self.repo_root)
                record["result"] = result.to_dict()
                record["artifacts"] = self._artifact_evidence(stage.required_artifacts)
                completed_stages.append(record)
                manifest["stages"] = completed_stages + [
                    self._planned_stage(item)
                    for item in self.stages[len(completed_stages) :]
                ]
                if stage.name == self.config.training_stage:
                    cleanup_error = self._cleanup_external(manifest)
                    if cleanup_error:
                        raise CycleExecutionError(cleanup_error)
                if result.exit_code not in stage.allowed_exit_codes:
                    raise CycleExecutionError(
                        f"Stage {stage.name} exited {result.exit_code}; see {result.log_path}"
                    )
                missing = [
                    path for path, evidence in record["artifacts"].items() if not evidence["exists"]
                ]
                if missing:
                    raise CycleExecutionError(f"Stage {stage.name} missing artifacts: {missing}")
                _write_json(manifest_path, manifest)
                self._commit_boundary(manifest_path, stage.name)

            baseline_payload = _read_json(
                self._path(self.config.baseline_evaluation.format_map(self.context))
            )
            candidate_payload = _read_json(
                self._path(self.config.candidate_evaluation.format_map(self.context))
            )
            baseline = summarize_evaluation(
                baseline_payload,
                allow_contact_gated_grasp_assist=(
                    self.config.promotion_gate.allow_contact_gated_grasp_assist
                ),
            )
            candidate = summarize_evaluation(
                candidate_payload,
                allow_contact_gated_grasp_assist=(
                    self.config.promotion_gate.allow_contact_gated_grasp_assist
                ),
            )
            decision = decide_promotion(baseline, candidate, self.config.promotion_gate)
            manifest["promotion"] = decision.to_dict()
            manifest["status"] = "complete"
            commit_paths = [manifest_path]
            if decision.accepted:
                pointer = {
                    "schema_version": "scenesmith.pi05_accepted_checkpoint.v1",
                    "cycle_id": self.config.cycle_id,
                    "model": self.config.candidate_model,
                    "source_commit": source_commit,
                    "candidate_metrics": candidate.to_dict(),
                }
                _write_json(accepted_path, pointer)
                commit_paths.append(accepted_path)
            _write_json(manifest_path, manifest)
            self._commit_paths(commit_paths, "promotion" if decision.accepted else "rejection")
            return manifest
        except Exception as exc:
            if training_attempted and not self.external_cleaned:
                self._cleanup_external(manifest)
            manifest["status"] = "failed"
            manifest["error"] = {"type": type(exc).__name__, "message": str(exc)}
            _write_json(manifest_path, manifest)
            self._commit_paths([manifest_path], "failure")
            raise

    def _cleanup_external(self, manifest: dict[str, Any]) -> str | None:
        if self.config.external_compute is None or self.external_cleaned:
            return None
        cleanup = self.config.external_compute.cleanup.render(self.context)
        inventory = self.config.external_compute.inventory.render(self.context)
        cleanup_result = self.stage_runner.run(cleanup, repo_root=self.repo_root)
        inventory_result = self.stage_runner.run(inventory, repo_root=self.repo_root)
        self.external_cleaned = True
        manifest["external_compute"]["cleanup"] = cleanup_result.to_dict()
        manifest["external_compute"]["inventory"] = inventory_result.to_dict()
        if cleanup_result.exit_code not in cleanup.allowed_exit_codes:
            return f"External cleanup failed with exit {cleanup_result.exit_code}"
        if inventory_result.exit_code not in inventory.allowed_exit_codes:
            return f"External inventory failed with exit {inventory_result.exit_code}"
        return None

    def _planned_stage(self, stage: StageSpec) -> dict[str, Any]:
        return {
            "name": stage.name,
            "argv": list(stage.argv),
            "timeout_s": stage.timeout_s,
            "allowed_exit_codes": list(stage.allowed_exit_codes),
            "required_artifacts": list(stage.required_artifacts),
            "log_path": stage.log_path,
            "env_keys": sorted(stage.env),
        }

    def _artifact_evidence(self, paths: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        evidence: dict[str, dict[str, Any]] = {}
        for value in paths:
            path = self._path(value)
            item: dict[str, Any] = {"exists": path.exists(), "path": value}
            if path.is_file():
                item.update({"kind": "file", "size_bytes": path.stat().st_size, "sha256": _sha256(path)})
            elif path.is_dir():
                item.update({"kind": "directory", "file_count": sum(p.is_file() for p in path.rglob("*"))})
            evidence[value] = item
        return evidence

    def _path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.repo_root / path

    def _commit_boundary(self, manifest_path: Path, stage_name: str) -> None:
        self._commit_paths([manifest_path], stage_name)

    def _commit_paths(self, paths: list[Path], boundary: str) -> None:
        if not self.config.git_auto_commit or not self.enforce_git:
            return
        self.git.commit(
            paths,
            f"chore(pi05-autolearn): {self.config.cycle_id} {boundary}",
        )


def load_cycle_config(path: Path) -> CycleConfig:
    return CycleConfig.from_dict(_read_json(path))


def _declares_step_bound(argv: tuple[str, ...], max_steps: int) -> bool:
    expected = str(max_steps)
    for index, token in enumerate(argv):
        rendered = token.replace("{max_steps}", expected)
        if rendered == f"--steps={expected}":
            return True
        if rendered == "--steps" and index + 1 < len(argv):
            return argv[index + 1].replace("{max_steps}", expected) == expected
    return False


def _is_contiguous(values: tuple[int, ...]) -> bool:
    ordered = tuple(sorted(values))
    return ordered == tuple(range(ordered[0], ordered[0] + len(ordered)))


def _looks_sensitive_env_key(key: str) -> bool:
    upper = key.upper()
    return any(upper == marker or upper.endswith(f"_{marker}") for marker in SENSITIVE_ENV_MARKERS)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
