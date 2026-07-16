# Reviewer Decision 295 - Verify T20.44 Stable Interpreter Correction

**Date:** 2026-07-16

## Decision

`ACCEPT_T20_44_STABLE_INTERPRETER_CORRECTION_REMATERIALIZE_ONLY`

## Findings

- The first model-free renderer smoke itself passed and produced valid MP4/
  manifest evidence, but its recorded interpreter was a deleted temporary
  `uv --with` build path. The prospective runner would therefore fail the
  exact-interpreter check before its marker. Those seven materialized authority
  artifacts remain untracked and rejected; no attempt marker, model tensor
  deserialization, model, optimizer, or rollout occurred.
- The correction selects the existing stable
  `external/lerobot/.venv/bin/python` and the already-cached immutable MuJoCo
  3.3.5 support site-packages at uv archive `jImpGSbF...`. Together they import
  the exact full dependency set without package installation or network.
- Spec `ec45331c...` binds both stable paths and explicitly forbids temporary
  uv build interpreters. Preflight hashes the support tree, renderer smoke
  records the stable interpreter, the runner requires both at entry, and every
  mirror subprocess receives the same bound PYTHONPATH.
- Snapshot hashing remains raw-byte/no-deserialization evidence. Policy and
  VLM tensor deserialization still follows the one-use marker.

## Adversarial disposition

Temporary interpreter paths, a missing support path, support-tree drift,
parent/child mismatch, package installation, network fallback, and a renderer
smoke that does not use the future runner now fail before permit issuance.
T20.43 remains consumed, and the rejected T20.44 materialization cannot be
reused or committed.

## Verification

- Stable interpreter directly imports MuJoCo 3.3.5, Torch 2.11.0,
  Transformers 5.5.4, PyArrow 25.0.0, and the full SmolVLA closure.
- 22 focused/pointer tests pass after the correction.
- Ruff, formatting, compilation, strict spec `ec45331c...`, JSON, and
  whitespace checks pass.

## Disposition

Commit and push this correction. After origin confirmation, remove only the
untracked rejected T20.44 authority/smoke outputs created in this correction
cycle, then rematerialize once with the stable direct interpreter. A fresh
Reviewer 296 must reconstruct and accept that new boundary before any marker.

## Authority withheld

No use or preservation of the rejected ephemeral authority, no marker, tensor
deserialization, model, inference, optimizer, checkpoint, rollout, retry,
package install, network, hardware, external compute, Brev, transfer,
promotion, or destructive operation outside cleanup of these newly created
untracked rejected artifacts.
