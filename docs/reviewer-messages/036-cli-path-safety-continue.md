# Reviewer Decision 036 - CLI Path Safety Continue

**Date:** 2026-07-10

## Decision

`CONTINUE`

## Evidence Reviewed

- `GOAL.md`
- `executor-reviewer-pair-programming.md`
- `docs/autonomous-workflow/README.md`
- `docs/autonomous-workflow/02-role-contracts.md`
- `docs/autonomous-workflow/03-planning-system.md`
- `docs/autonomous-workflow/04-execution-protocol.md`
- `docs/briefs/028-synthetic-ready-closeout-and-cli-path-safety.md`
- `docs/session-logs/040-executor-cli-path-safety.md`
- `docs/reviewer-messages/035-embedded-prior-integrity-continue.md`
- `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- Latest commit `7461620`
- Current `git status --short`
- Current `git diff --stat`
- `scripts/robot_lab/write_measured_inertial_intake.py`
- `tests/unit/test_measured_inertial_intake.py`
- Validation reruns:
  - `python -m unittest tests.unit.test_measured_inertial_intake`
  - `python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py`
  - `python scripts/robot_lab/write_measured_inertial_intake.py --verify`
  - `python scripts/robot_lab/write_measured_inertial_intake.py --verify --require-ready`
  - External absolute-path CLI write, verify, `--require-ready`, and forged-input no-overwrite reruns in a temp directory
  - `./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff`

## Findings

- Commit `7461620` is a valid narrow fix for the brief-028 path-safety defect.
  `_relative_to_repo()` now preserves caller-provided absolute paths outside
  `REPO_ROOT` while still normalizing tracked repo-local paths.
- The new CLI regressions in `tests/unit/test_measured_inertial_intake.py`
  cover the intended surface directly: external absolute-path write, verify,
  blocked `--require-ready`, and forged-input no-overwrite behavior.
- Independent reruns confirm the default checked-in current-arm identities are
  unchanged on the real product path:
  intake `35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88`
  and output `5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4`.
- Independent external-path reruns confirm the live CLI now writes and verifies
  outside-repo absolute paths, still fails closed under `--require-ready`, and
  preserves the preexisting external output byte-for-byte when a correctly
  re-signed forged intake drifts from the deterministic repo rebuild.
- Broad regression coverage passed at 59 tests, so this slice did not reopen
  the surrounding dependency-lock, twin-contract, or structural-diff gates.
- T16.4 remains `in_progress`. Repo state still does not contain the synthetic
  `ready` compiler path, golden aggregate mass/COM/full inertia proof, or ready
  identity invariance required to close the milestone task.

## Routing

- Accept session 040 as valid partial progress for T16.4.
- Keep the checked-in real current-arm artifacts blocked and unchanged.
- Supersede brief 028 with a narrower follow-on brief that isolates the next
  smallest useful slice: the bounded synthetic `ready` happy path and its
  deterministic golden proof.
- Refresh `GOAL.md` so the current slice points at that synthetic-only brief.

## Next Action

Execute brief 029 to add a `synthetic_test_only` ready-state compiler path with
deterministic golden mass/COM/full inertia and stable ready identity, while
leaving the default real current-arm artifact unchanged and blocked.

## Manager / Human Escalation

- None.
