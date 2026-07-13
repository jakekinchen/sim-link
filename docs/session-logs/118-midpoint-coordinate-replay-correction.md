# Session 118 - Midpoint Coordinate Replay Correction

**Date:** 2026-07-13

Brief 088 reproduced Reviewer 113's projection and shoulder/lower-arm contact
without hardware, then traced them to use of the legacy simulation-policy
offsets with the pinned midpoint-calibrated `so101_new_calib.xml` model. The
legacy v1 mapping remains unchanged for its existing datasets.

A finite seven-candidate audit combined the physical LeRobot calibration
profile, pinned model documentation and limits, measured `q_after`, MuJoCo
contacts, and the accepted external articulated frame. The shared midpoint-zero
sources reject the offset candidates. The measured pose rejects the legacy
sign candidate on self-contact, and the observed folded near-base topology
rejects the sign-inverted shoulder/elbow candidate. Private review
`b98445cb...` selects direct identity only for offline replay; it explicitly
does not accept a metric physical transform.

The immutable proposal was replayed twice exactly at horizons 5, 10, and 15
under the reviewed midpoint candidate. Diagnostic `a0179263...` records no
start projection, no proposal projection events, no initial/settled/prefix
robot self-contact, no warnings, and effectively zero cube movement. This
corrects the earlier coordinate-projection and false-collision diagnosis.
Maximum simulated joint velocity is still 5.43238 rad/s, the physical scene
still lacks the checkpoint's sorting trays/cubes, wrist roll remains outside
observed checkpoint support, and the proposal deltas remain unsafe. The result
is still `DO_NOT_ACTUATE`; matched replay and accepted shadow remain false.

Adversarial broad testing caught that changing the legacy coordinate module
would unnecessarily invalidate the complete dependency/twin/authority chain.
The candidate therefore lives in a new module; the legacy coordinate source,
dependency lock, preprocessing contract, reviewed-input gate, fixture parity,
and all twin/authority identities remain byte-for-byte unchanged. One hundred
eighty-eight focused tests pass in each pinned runtime, and the 293-test broad
authority/twin gate passes. No hardware, model inference, optimizer, training,
Brev, paid compute, or external network was used.
