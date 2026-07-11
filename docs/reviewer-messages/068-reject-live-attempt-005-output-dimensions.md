# Reviewer Decision 068 - Reject Live Attempt 005 Output Dimensions

**Date:** 2026-07-11

## Decision

`REJECT LIVE ATTEMPT 005; REMOVE CANDIDATE MANIFEST; KEEP LIVE GATE CLOSED; CONTINUE OFFLINE WITH BRIEF 046`

## Evidence

- Session: `t16-5b-20260711-1105-cdt`.
- Discovery: `b8b11e74ef3a70e2fbfc3ab220b2ab50f8a4239d327d6fe7b763a9fc99468177`.
- Contract: `f76ea66f1633472c36b4c6238b01d0273e137f50e2713504ada935592bf1847e`.
- Private candidate:
  `ebb4934c18ef77bb5563800a0cea36a847b1568e8c0ce03bd397ff0eb0036671`.
- Removed candidate manifest:
  `0d7b4400ccd5f926176ae083be37c33824d59753ffeb186adcd46d663b723da3`.

## Review

Discovery v2 opened no device and bound 209 C922 modes plus 26 RealSense modes.
Both aliases were holder-free. Contract v3 selected exact YUYV 30-fps modes:
`160x90` for camera 0 and `424x240` for camera 1.

The census completed 54 allowlisted reads with zero retries, writes, torque
changes, motion, or unexpected operations. All six servos reported
`Torque_Enable=0`; no-torque close and pre/post holder checks passed. Two FFmpeg
processes each completed and released once, and no process remained.

Post-run adversarial review found that camera 0's PNGs were `160x90`, but camera
1's PNGs were `640x480`, contradicting its signed `424x240` mode. The current
private/manifest verifier accepted this because it checks PNG validity and the
requested command/audit mode without comparing decoded dimensions to that mode.

The candidate tracked manifest was uncommitted and removed. The ignored private
candidate remains only as diagnostic evidence. Its candidate labels are
rejected; canonical accepted proof labels remain empty. Sequential evidence is
not synchronized or policy-shadow-input-valid. `physical_follower_commanded=false`.

Brief 046 may proceed offline to enforce exact decoded dimensions at capture and
independent evidence layers. No additional live session is authorized.
