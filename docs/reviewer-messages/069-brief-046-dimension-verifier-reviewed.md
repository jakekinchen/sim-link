# Reviewer Decision 069 - Brief 046 Dimension Verifier Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT BRIEF 046 OFFLINE; KEEP LIVE GATE CLOSED; CONTINUE WITH BRIEF 047`

## Evidence anchor

`6eb5f898f1f80fdde684b19027a8c63c391c3867`

The named backend now rejects any parsed PNG whose dimensions differ from its
signed camera mode before returning a frame. Captured-frame/private-success and
redacted-manifest construction independently repeat the check. Mismatches use
the bounded `png_validation` failure path and retain no success label.

The corrected verifier rejects the actual attempt-005 private candidate for its
camera-1 `424x240` contract versus `640x480` output, proving the fix against the
real failure rather than only fixtures. Exact matches, mixed dimensions,
metadata tampering, manifest tampering, strict stderr/nonzero/timeout/PNG
handling, cleanup, privacy, no-write close, and legacy failures remain covered.

Verification: 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests
in 71.943 seconds; both offline verifiers; actual candidate rejection;
`py_compile`; authority/privacy review; and diff checks. No hardware access or
actuation occurred. Both signed camera mode sets contain `640x480` at
30.000030 fps, so Brief 047 may correct selection offline. No live session is
authorized by this decision.
