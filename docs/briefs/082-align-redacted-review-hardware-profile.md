# Slice Brief 082 - Align Redacted Review Hardware Profile

**Date:** 2026-07-13

## Objective

Correct the exact offline review failure for the already verified candidate
without modifying or rerunning the physical session.

## Reproduced failure

The formal `hardware_execution_profile_evidence.v1` verifier requires an exact
field set that excludes `proof_labels`. The redacted static-pose review source
check nevertheless requires `hardware_execution_profile.proof_labels == []`,
making every real formal profile impossible to review.

## Contract

- Remove only the impossible hardware-profile `proof_labels` expectation from
  the redacted review source classifier.
- Update the review fixture to match the formal profile field surface.
- Preserve all profile schema, signature, exact Full Access/no-prompt policy,
  capabilities, denied authority, and no-hardware/no-motion checks.
- Rebuild and verify the redacted manifest from the existing immutable success;
  do not reopen hardware or create a new candidate.

This correction grants only review compatibility. Candidate acceptance remains
a separate same-agent review decision.
