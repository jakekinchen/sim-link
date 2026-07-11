# Session 072 - Rejected Live Attempt 005 Output Dimensions

**Date:** 2026-07-11

Reviewer 067's one-session gate was remotely confirmed at `09fc358`. Discovery
v2 `b8b11e74...` observed four serial candidates, two cameras, 209 C922 modes,
and 26 RealSense modes without opening a device. Both signed follower paths
were holder-free.

Contract v3 `f76ea66f...` and lease `4680d13a...` selected YUYV `160x90@30`
and `424x240@30`. The census completed 54 reads with zero retries, writes,
torque changes, motion, or unexpected operations; all six
`Torque_Enable` values were zero and no-torque close succeeded. Both aliases
remained `[0,0]` and no FFmpeg process remained.

The harness initially emitted candidate manifest `0d7b4400...`. Same-agent
post-run review compared decoded PNGs to the contract: camera 0 matched
`160x90`; both camera-1 frames were `640x480`, not signed `424x240`. This
exposed a verifier gap, so the session is rejected and the uncommitted tracked
manifest was removed.

Private candidate `ebb4934c...`/file `c341fdf3...` is retained under ignored
outputs only. Its four frame hashes and file sizes remain content-addressed for
diagnosis. Candidate proof labels are rejected and canonical accepted labels
remain empty. The live gate reclosed at `2026-07-11T11:05:47-05:00`.

The follower was not reconnected. No Studio request, signal,
configuration/register write, torque transition, motion, policy actuation,
physical qualification, optimizer, paid compute, or destructive action
occurred. Brief 046 owns exact decoded-dimension enforcement.
