# Slice Brief 071 - Full-Access No-Prompt Hardware Profile

**Date:** 2026-07-13

## Objective

Replace the future SceneSmith hardware-session Codex runtime requirement with
the owner's requested `danger-full-access` plus `never` approval semantics,
while preserving every independent robot authority, evidence, lease, session,
cleanup, and motion gate.

## Contract

- The trusted project default, explicit hardware profile, formal doctor command,
  active-turn verifier, live-candidate gate snapshot, and redacted-session review
  must all require `danger-full-access` plus `never`.
- The formal verifier must reject `workspace-write`, `on-request`, `untrusted`,
  stale, cross-thread, changed-during-capture, or profile-drifted evidence before
  a hardware constructor can be exposed.
- The hardware and offline profiles may share Codex permission semantics. Their
  authority remains distinct because permission profiles never grant a live
  gate, owner-presence lease, hardware session, proof label, training authority,
  or motion permit.
- Historical on-request evidence remains historical and must not be rewritten as
  no-prompt evidence.
- Update only canonical future requirements and current workflow summaries.

## Verification

- Run focused hardware-profile, candidate, live-session, and session-review tests
  in both pinned robotics runtimes.
- Run both static-pose source verifiers and the relevant broad authority/twin
  regression gate.
- Run strict JSON, workflow, compilation, privacy, and diff checks.
- Perform a fresh same-agent adversarial diff review before commit.

## Authority withheld

This slice is offline and opens no device or live gate. It grants no serial,
camera, servo, Studio, policy, MuJoCo, training, Brev, actuation, T16.5c proof,
T16.6 permit, or physical qualification authority. A fresh task must still prove
its effective same-thread runtime before any hardware access.
