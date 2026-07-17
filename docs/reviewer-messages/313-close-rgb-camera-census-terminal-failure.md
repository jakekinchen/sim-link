# Reviewer Decision 313 - Close RGB Camera Census Terminal Failure

**Date:** 2026-07-16

## Decision

`CLOSE_K3_AS_SAFE_TERMINAL_INFRASTRUCTURE_FAILURE`

Session `rgb-census-20260716-2242-cdt` consumed the only K3 permit. The D405
named RGB source returned one decoded PNG and released, but exact dimension
validation rejected it before a signed frame or result could be created. The
sequential C922 path was never opened. Tracked failure manifest `5c0edf59...`
binds request `a9371156...`, decision `7990e413...`, permit `6341a190...`,
runtime `a7d61d0e...`, private failure `0093685a...`, and origin boundary
`105bc4e...`.

## Adversarial disposition

The terminal receipt grants no proof label and truthfully records zero accepted
frames, no preserved stream-config census, no latency result, and no hardware
readiness. Source order plus the exact raised validator prove D405 was first and
C922 was not reached. Release completed; a post-failure process check found no
live ffmpeg capture. Depth, librealsense, serial, register operations, torque,
motion, audio, inference, optimizer work, follower commands, transfer, and
promotion remained closed.

One offline localization audit identifies the evidence gap: requested and
decoded dimensions plus discovery/modes must be persisted before validation.
The gate is closed and no replacement or retry is authorized. A future owner
grant must open a new, separately reviewed one-use session.
