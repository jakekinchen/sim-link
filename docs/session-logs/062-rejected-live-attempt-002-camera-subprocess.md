# Session 062 - Rejected Live Attempt 002 Camera Subprocess

**Date:** 2026-07-11

## Attempt identity

- session: `t16-5b-20260711-0904-cdt`;
- discovery: `7766ed1c8930ff9c99586c331abc31989023798980b9b1cbac60b98b1261fdbb`;
- execution contract: `51467ec79ec6df04af2cc7d77772d47fb9a4363656fa44ad0a2c8fa13c86f03c`;
- owner-presence lease: `980b555ccfac8511d467e4f8af11f1fb300ba34ba4e0366f2542ff3a68107ab3`;
- validity: `2026-07-11T09:03:42-05:00` through `09:08:42-05:00`.

The `.mujoco_venv` discovery command first failed before enumeration because it
lacks `pyserial`; it created no output and opened no device. The same metadata-
only command then succeeded in the reviewed `external/leLab/.venv` runtime with
four serial candidates, two stable named cameras, and zero opens.

## Rejection

The capture passed contract verification and progressed through the exact
follower's read-only census, no-torque close, and post-close zero-holder check.
The first exact-name ffmpeg finite camera batch returned nonzero, raising
`Named camera ffmpeg subprocess failed`. The cleanup path left no ffmpeg
process. Production code did not retain bounded stderr diagnostics, so the
failure cannot yet be truthfully classified as contention, format negotiation,
or backend/command error.

No private evidence directory or tracked redacted manifest was written. A
fresh cleanup audit reports follower disconnected, torque false, leader
connected, and empty holder identity
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
No live proof label, policy actuation, motion, general register write, physical
qualification, or training claim is granted. The live gate is reclosed.
