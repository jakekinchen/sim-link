# Slice Brief 062 - Resumed Session-Metadata Profile Correction

**Date:** 2026-07-12

## Objective

Remove the concrete preflight blocker created by legitimate ChatGPT desktop
resume records while preserving the hardware profile gate's fail-closed identity
and latest-turn checks.

## Contract

- Permit repeated `session_meta` records only when each later record preserves
  every existing field byte-for-byte and adds no field except the observed
  desktop-resume `memory_mode` field.
- Continue to require every metadata record to carry the exact active thread
  ID and to resolve exactly one rollout path.
- Use the latest complete metadata record for the evidence hash and the latest
  persisted `turn_context` for the active runtime decision.
- Reject cwd, git, timestamp, source, CLI version, model provider, thread ID,
  field removal, unexpected addition, or existing-value mutation before running
  `codex doctor`.
- Preserve the exact `danger-full-access`/`on-request`, same-thread, same-cwd,
  before/after stability, five-minute age, and authority-withholding checks.

## Evidence and authority

This is the single correction demonstrated necessary by the failed real
preflight. It opens no gate and grants no hardware, observation, input, model,
shadow, replay, actuation, qualification, or training authority.
