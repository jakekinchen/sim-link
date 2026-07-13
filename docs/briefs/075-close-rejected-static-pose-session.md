# Slice Brief 075 - Close Rejected Static-Pose Session

**Date:** 2026-07-13

## Objective

Close the consumed T16.5c gate and preserve the exact rejected live-candidate
boundary without granting a success label or retry.

## Evidence

- Session: `t16-5c-20260713-0845-cdt`.
- Discovery `673ff2d2...`, profile `69e86eda...`, lease `43fc0c72...`, and
  contract `e6bf4f62...` were issued.
- The session started and rejected during camera-frame normalization with
  `ValueError: Static pose fixture camera frame fields are invalid`.
- Immutable private failure `b117e797...` verifies
  `physical_follower_commanded=false`, no policy inference, no motion authority,
  no training authority, and no private success.
- Post-close Studio status reports follower disconnected and torque false;
  canonical and TTY holder counts are `[0,0]`.

## Disposition

The gate is consumed and closed with sessions started one. No retry is allowed.
Exactly one narrow offline frame-contract correction may follow before any new,
separately reviewed gate.
