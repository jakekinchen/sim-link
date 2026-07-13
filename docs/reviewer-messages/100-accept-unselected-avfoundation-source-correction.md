# Reviewer Decision 100 - Accept Unselected AVFoundation Source Correction

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT BRIEF 074 UNSELECTED AVFOUNDATION SOURCE CORRECTION`

The correction is bounded to the reproduced discovery failure. It does not
weaken selected-camera identity: system names and unique IDs remain unique,
every system camera must appear in AVFoundation, the signed RealSense/C922
hashes and exact modes still match, and selecting the screen source fails.

Fresh same-agent adversarial review checked target substitution, duplicate
names/IDs, ambiguous selection, index churn, missing system identity, screen
selection, stale evidence, authority escalation, cleanup, and nondeterminism.
The actual discovery builds only the two signed cameras and reports no hardware
access. Seventy-eight focused tests pass in both pinned runtimes, 378 broad
tests pass, both source verifiers pass in both runtimes, and diff checks pass.

This grants only local resolver conformance. It grants no accepted observation,
reviewed policy input, model, inference, replay, motion, qualification, training,
or paid compute. The correction must be confirmed on origin before a new lease
or the sole candidate session.
