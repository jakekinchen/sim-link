# Reviewer Decision 089 - Current-Thread Preflight And Camera/Task Decision

**Date:** 2026-07-12

## Decision

`STOP PHYSICAL WORK; ACCEPT CAMERA SEMANTICS AND EXACT CHECKPOINT PROMPT; KEEP PRODUCTION INPUT BLOCKED`

Evidence anchor `100`: current thread `019f5804...` is not using `on-request`
approval, so no live-gate transition, lease, discovery, holder census, or device
open is permitted. The preflight rejection is preserved without pretending a
candidate session started.

Accepted T16.5b content rejects the fixture role hypothesis. Stable camera
`69d55167...` is the rigid wrist-mounted RealSense and maps to
`observation.images.wrist` then `observation.images.left_wrist_0_rgb`. Stable
camera `9931d030...` is the external workcell overview and maps to
`observation.images.top` then `observation.images.base_0_rgb`. The decision is
bound to review-frame hashes `c77e4c7e...` and `caab2f5d...`; no volatile
numeric camera index or false wrist label is used.

The exact current-checkpoint prompt is `Sort each cube into the same-colored
tray: red cubes into the red tray and blue cubes into the blue tray.` It must
not be paraphrased for the shadow experiment. A future grasp-first prompt must
use a separate task identity.

The role and prompt decisions are reviewed physical semantics, not production
reviewed-input artifacts. The existing gate must retain
`accepted_live_session_review_decision` as missing and must bind both decisions
to the newly accepted session before issuing a real PI0.5 input bundle. No
model, shadow, replay, actuation, qualification, training, or paid-compute
authority is granted.

Same-agent adversarial review found no live-gate opening, session-count change,
production-input mutation, volatile-index binding, false wrist label, hardware
path, model path, or authority escalation. Thirty-four focused tests pass in
each pinned runtime, and the 376-test broad authority/twin gate passes in
92.437 seconds.
