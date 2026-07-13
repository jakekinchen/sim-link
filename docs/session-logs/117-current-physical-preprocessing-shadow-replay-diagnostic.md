# Session 117 - Current Physical Preprocessing, Shadow, And Replay Diagnostic

**Date:** 2026-07-13

The exact current private-success v2 frame index 1 and `q_after` state were
processed four times with the pinned real PI0.5 processor under strict offline
guards. Diagnostic `57acad57...` is byte-stable. External and wrist model-image
tensors are `89644c19...` and `8041d823...`; the missing right-wrist tensor is
`811b0abf...`. Wrist roll is outside the checkpoint's observed min/max, while
elbow flex, wrist flex, and wrist roll are outside mean plus/minus one standard
deviation. Sorting-scene semantics and policy-input validity remain rejected.

The exact local checkpoint revision `84b551af...` loaded on MPS from weight
SHA-256 `471adf9a...` with every state-dict key accepted. Fixed seed 1605 and a
recorded 1x50x32 noise tensor produced two bit-identical inference passes.
Postprocessing produced finite absolute LeRobot action chunk `4d350587...`,
shape 1x50x6. The first proposal differs from measured `q_after` by
`[-1.4553, -9.2574, 7.7736, 1.6717, 54.4099, -3.7432]`; maximum absolute
chunk deltas are `[8.4577, 10.8691, 51.5712, 22.0192, 55.8645, 25.7961]`.
Diagnostic `c116f473...` therefore records `DO_NOT_ACTUATE`.

MuJoCo diagnostic `42499e46...` replayed horizons 5, 10, and 15 twice with
exact equality at 10 Hz and 0.002-second simulation steps. Mapping the measured
start state clamps shoulder lift from -2.64223 to -1.74533 radians and elbow
flex from 2.70119 to 1.69 radians. Every proposal action also projects those
two joints. All replays remain finite and within final joint ranges with zero
MuJoCo warnings and maximum cube displacement `1.21694e-11` m, but all retain
shoulder-to-lower-arm self-contact and reach maximum wrist-roll velocity
5.42916 rad/s. The canonical sorting scene also does not match the accepted
physical pixels. Prefix control replay is observed, but matched replay,
accepted shadow, and motion suitability are rejected.

No hardware, follower command, optimizer, training, Brev, paid compute, or
external network was used. The live gate remains closed and the follower
remains disconnected, torque false, and holder-free from the accepted session
closeout.

Verification reran the exact preprocessing artifact to byte equality, the
final MuJoCo artifact to byte equality, and 183 focused authority,
preprocessing, static-session, calibration, and observation tests in each
pinned runtime. Project-state JSON, whitespace, privacy, and scoped-diff checks
also pass.
