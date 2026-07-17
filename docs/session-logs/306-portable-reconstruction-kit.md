# Session 306 - Portable Reconstruction Kit

**Date:** 2026-07-16  
**Support task:** K1  
**Brief:** 224  
**Policy task preserved:** T20.43b

## Outcome

Created `reconstruction-kit/` as a non-authorizing seed-repository capsule for
the current SO-101/MuJoCo/LeRobot program. The capsule leads with the verified
R0 source/data boundary, the terminal-negative SmolVLA result, the unconsumed
ACT replacement, the five-plane architecture, dual-cadence action contract,
lessons, pinned third-party stack, quick start, and dependency-ordered forward
route. It does not claim learned-policy success or physical readiness.

The living documentation hub, architecture, requirement index, current-versus-
historical guide, MVP plan, root README, and GOAL were reconciled against code,
signed T20.42-T20.44 evidence, and `project_state.json`. Stale statements that
treated T20.20-T20.22 as future, SmolVLA as upcoming, the dataset as pre-R0, or
the Robo Scan reference handoff as wholly future were corrected.

## Portable boundary

- Result-state snapshot: `6c53d9309f7f41f0d3ac351c049436ddda20e50f`.
- Portable implementation/documentation commit:
  `605e4d3624a87593a1b5da9a97cd263f6bade78a`, confirmed on origin.
- Source-selection SHA-256:
  `e85e1c593a839ff98373a474c4077b208e1169d22efd0031164f86a7ed29e6c2`.
- Source-manifest identity:
  `5067d1c29c4a285f70a96720f90f52e312a8f61d60e74a2de030c9d3ec910303`.
- Curated source: 321 files, 8,614,788 bytes.
- Explicit omissions: five artifacts, 22,811,274 bytes. These are four bulky
  historical replay/tensor payloads plus repository-bound live project state;
  every omission retains its exact source hash and reason.
- Clean export receipt:
  `729addbb9d52ddd8ec7e6917ec6c5f18e06220d6c85a5ec43775474742cc2404`.
- Export: 336 receipted files, 8,782,408 bytes, with authority, physical proof,
  learned-policy success, bulk-output copy, and external-checkout copy all
  explicitly false.

## Portability correction discovered during verification

The broader model-free regression found that T20.42 still expected the
original `e9d0507` owner-route bytes after the same Markdown path later received
the T20.43b addendum. The exact original Git blob is now retained at
`configurations/robot_lab/t20_41_owner_route_decision_e9d0507.snapshot.md`
with SHA-256 `ae75bb59...`; T20.42 reads that snapshot while preserving its
original logical path/commit reference. This restores the existing signed R0
identities without editing history or weakening the guard.

Clean-export testing also exposed missing Python package initializers and
literal test fixtures. The manifest builder now parses package initializers as
part of the transitive import closure and includes reached `tests/fixtures/`
files. No external checkout was copied to solve those failures.

## Verification

- `python3 reconstruction-kit/tests/test_kit.py -v`: six tests pass.
- The kit tests cover generated-manifest equality, strict export/receipt,
  parent traversal, rehashed incomplete manifests, authority escalation,
  existing/in-repo destinations, unreceipted drift, link resolution, package
  initializers, fixtures, and clean-export imports.
- 153 focused robotics tests pass with the already pinned Python 3.12
  interpreter and MuJoCo support tree. This includes artifact/authority,
  contact, coordinates, processor, strict-v2, R0, ACT, SmolVLA, trace, receipt,
  dependency-lock, and Robo Scan boundaries.
- A pristine clean export verifies before and after 31 dependency-light tests;
  both checks return receipt identity `729addbb...`.
- Python compilation, strict JSON rendering, `build-manifest --check`, manifest
  verification, Markdown local-link checks, and `git diff --check` pass.

## Authority and exclusions

No model/checkpoint download, package installation, network acquisition, model
construction, inference, optimizer, simulation campaign, marker, hardware,
camera, serial, motion, external compute, Brev, physical-transfer, promotion,
or destructive data operation occurred. Existing untracked external checkouts,
`tmp/`, and the user's `.codex/config.toml` change were neither staged nor
modified. T20.43b remains unconsumed and unchanged.
