# Brief 200 - T20.36i SmolVLA Dependency Closure Audit

## Objective

Compile and sign the exact pinned LeRobot SmolVLA optional-dependency closure,
compare it with the consumed-attempt Python 3.12 environment, and design the
smallest fail-closed environment correction without installing a package,
constructing a model, or authorizing a replacement attempt.

## Frozen Inputs

- T20.36h tracked failure result `3804eff6...`, attempt `43c2d0a1...`, and
  preflight `b7e2938f...`.
- Pinned LeRobot head `e40b58a8...`, its `pyproject.toml` and installed
  distribution metadata, Transformers version and processor dependency checks,
  and the exact Python 3.12 virtual environment used by the attempt.
- Reviewer 251's no-retry disposition. The observed failure is not a Gate B
  result and grants no replacement model access.

## Required Work

1. Parse the `smolvla` extra and recursively resolve its local LeRobot extras
   into exact distribution requirements and version bounds.
2. Inventory installed versions without importing model code; classify present,
   missing, version-mismatched, and unresolved requirements deterministically.
3. Prove the observed `num2words` failure is covered by the closure and identify
   any later missing prerequisite that the old preflight would also have missed.
4. Emit a signed correction design that requires full closure validation before
   any future model construction and binds an exact environment-manifest hash.
5. Keep installation, environment mutation, replacement authority, and model
   execution false. A future replacement attempt requires a new owner-signed
   decision after this audit is remotely verified.

## Acceptance

- The audit is source/metadata/environment bound, deterministic, test covered,
  and remotely preserved.
- Missing and mismatched dependencies fail closed before attempt creation.
- Claims distinguish runtime-dependency failure from Gate B policy failure.

## Prohibited Actions

Package installation, lockfile/environment mutation, network/download,
attempt-marker creation, replacement attempt, checkpoint/model access,
inference, optimizer, Gate B change, Gate C, rollout, hardware, external
compute, or Brev.
