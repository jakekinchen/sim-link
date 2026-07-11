# Reviewer Decision 070 - Brief 047 Camera Floor Reviewed

**Date:** 2026-07-11

## Decision

`ACCEPT BRIEF 047 OFFLINE; KEEP LIVE GATE CLOSED FOR A SEPARATE REVIEW COMMIT`

## Evidence anchor

`e68068a6331723e46f09edd82531b964dffd9f5c`

The selector now filters each camera's own signed modes to at least `640x480`
and integer 30 fps within the reviewed 0.01-fps tolerance before deterministic
area/pixel-format ordering. A camera with only sub-floor modes rejects; no
default, alias, or cross-camera fallback exists.

Against the actual attempt-005 discovery, C922 resolves to YUYV 640x480 and
RealSense to UYVY 640x480. Brief 046 exact decoded-dimension checks remain at
capture, private-success, and manifest layers.

Verification: 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests
in 71.477 seconds; actual discovery selection regression; both offline
verifiers; compile, authority, privacy, and diff checks. No hardware access or
actuation occurred. Any final live session requires a separate remotely
confirmed one-session transition.
