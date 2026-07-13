# Reviewer Decision 102 - Accept Live Frame Metadata Adapter

**Date:** 2026-07-13

## Decision

`CONTINUE - ACCEPT BRIEF 076 LIVE FRAME METADATA ADAPTER`

The correction matches the reproduced failure and preserves strict boundaries.
It does not loosen the static-pose normalizer or generic FFmpeg reader. The
pinned live adapter recognizes exactly two known lower-level timing fields,
validates their type/order, rejects any other drift, and preserves semantic
frame bytes and metadata exactly.

Fresh same-agent adversarial review checked unknown-field smuggling, missing
metadata, booleans as integers, negative/non-increasing times, semantic-field
mutation, frame-byte mutation, authority escalation, and unintended generic-
camera behavior changes. The targeted test was red before implementation and
green after it; 79 focused tests pass per pinned runtime, 379 broad tests pass,
both source verifiers pass in both runtimes, and compile/diff checks pass.

This grants only adapter conformance. The consumed gate remains closed. A future
session requires a separate reviewed remote gate and full fresh preflight; no
observation, model, inference, replay, motion, qualification, training, or paid
compute is authorized.
