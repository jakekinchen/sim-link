# GOAL Proof-State History

This file is the append-only history formerly embedded in `GOAL.md`.  The
active goal keeps only the current mission, window, milestone, and pointers;
new verified proof-state entries belong here with their brief/reviewer anchors.

## 2026-07-16 - T19.1 live read-only hardware snapshot verified

- Brief 212 and Reviewers 281-282 bound one owner-present session to the exact
  Full Access/no-prompt thread, remote boundary `80628ee`, central decision
  `2fd92308...`, and one-use permit `93b229f4...`.
- Six STS3215 servos reported model 777, firmware 3.9, and torque disabled.
  The session completed 54/54 reads with zero retry, write, torque-change,
  motion, unexpected-operation, follower-command, or camera counts and one
  no-torque close.
- Manifest `f423f5d3...` grants only
  `t19_1_live_readonly_hardware_snapshot_observed`; the consumed live gate is
  closed. Calibration, physical-twin qualification, transfer, policy
  actuation, promotion, external compute, and Brev remain ungranted.

## Historical Proof State

- PI0.5 inference, five-step LoRA training, save, finalize, reload, evaluation,
  and rollback are proven on an MPS-backed runtime.
- Hybrid controller-assisted sorting is proven; strict autonomous sorting is not.
- M10 now rejects the malformed bootstrap aggregate and proves a corrected
  12-episode canary merge with exact frame tasks and pinned normalization.
- `cycle-001-mps` is interrupted and must not resume under its current recipe.
- The corrected 250-step rung is retained as historical evidence of a narrow
  reach improvement; rungs 500/1,000 are suspended behind M16-M19.
- The current T16.3 artifact proves deterministic source/hash plumbing,
  TwinProfile binding, effective solver defaults, full comparison-time
  quaternion semantics, explicit inertial unknown evidence, and effective
  friction/contact attachment truthfulness.
- Independent reviewer reruns now confirm the v2 unnamed-geom identity
  strategy closes the quaternion-spelling and sibling-order gaps, with tracked
  structural artifact identity
  `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.
- Reviewer decision 039 reopens T16.1, T16.2, and T16.4 at their production
  authority boundaries. T16.1 retains a verified dependency inventory but not
  a unified executable stack; T16.2 retains a verified schema scaffold but not
  mechanically computed qualification decisions; T16.4 retains a verified
  synthetic compiler scaffold and truthful blocked real template but not a
  production measured-input path or downstream authority. T16.5 is pending.
- Reviewer decision 040 verifies T16.1b at commit `dca2b45`: collection,
  training, finalization, inference, and LeLab now share one pinned base plus
  tracked patch-set identity. This grants executable-stack reproducibility only;
  the training lock remains closed.
- Commit `69df54d` and reviewer decision 041 establish the strict finite artifact,
  content-addressed evidence, physical inertia, graph-link, and scoped-gate
  layer. T16.4b remains partial at `3cd142e`.
- Reviewer decision 042 keeps T16.4b open but makes T16.2b-A the active first
  slice. Component artifacts may report local capabilities only; the central
  composer owns global readiness. No optimizer, hardware, transfer, or
  promotion authority is granted.
- Reviewer decision 043 verifies T16.2b-A at `c0b9629`: the central composer is
  the only global-decision path, assembly-inertials v2 carries local capability
  facts only, and the checked-in fixture composition mechanically withholds all
  global decisions. The remote preserves the implementation and review through
  `e1d59ca`; `training_lock` remains closed.
- Reviewer decision 045 verifies Brief 036 implementation `7d05629`:
  deterministic normalized Jacobi convergence, eigenpair residuals,
  scale-relative physical-inertia tolerances, and the adversarial NumPy corpus
  pass. The implementation and review are preserved on the named remote through
  `dbdd1ef`; T16.4b is closed on declared fixture evidence only.
- Reviewer decision 046 verifies Brief 037 implementation `710960b`:
  caller-declared execution is closed, v2 qualification results are generated
  and independently recomputed, freshness is bounded by source evidence, and
  fixture numeric passes remain authority-withheld. Implementation and review
  are preserved on the named remote through `383557b`; T16.2b is closed on
  declared fixture evidence only.
- Reviewer decision 047 verifies Brief 038 implementation `f200087`:
  the injected census surface is read-only, lifecycle and retries are bounded,
  partial-connect cleanup closes without torque writes, exact follower and six-
  servo identity are checked, and the signed fixture remains
  `census_trace_conformant` with no hardware opened or follower commanded.
  Implementation and review are preserved on the named remote through
  `d002c80`; T16.5a is closed on declared fixture evidence only.
- Reviewer decision 048 supersedes that closeout after a pre-live source audit
  found protocol `1` in the fixture versus protocol `0` in the pinned STS3215
  runtime. T16.5a is reopened, `census_trace_conformant` is withdrawn, and
  T16.5b remains closed until Brief 040 is reviewed and remotely preserved.
- Reviewer decision 049 accepts the Brief 040 correction locally: the v2
  contract uses protocol 0 and independently verifies exact runtime source
  hashes and semantics, including no-write open/close guards. T16.5a remains
  correction and review are preserved on the named remote through `2407299`;
  T16.5a is reclosed as corrected `census_trace_conformant` fixture evidence.
- The owner is physically present and has granted conditional read-only
  hardware/camera authority after verified T16.5a plus final operator
  confirmation for exactly one initial session-scoped `supervised_micro_motion`
  permit after T16.5a-T16.5c. No second prompt is required; every permit and
  lease check remains mandatory, and any expansion remains unauthorized.
- Reviewer decision 052 rejects T16.5b live attempt 001: the no-write serial and
  finite-camera path reached post-close discovery, but AVFoundation swapped the
  two index-to-name mappings and a pre-existing July 8 Studio server still held
  the follower serial device. No evidence bundle, tracked manifest, live proof
  label, write, torque change, or motion claim survived. Brief 041 keeps all
  further live access closed while the camera path is corrected offline.
- Reviewer decision 053 accepts the Brief 041 offline correction at commits
  `ea99ec9`/`66003d8`/`fd13bf6`/`01802a0`: exact-name ffmpeg capture replaces
  OpenCV indexes, PNG framing and pixel streams are finite and validated,
  subprocess/evidence counts are content-bound, and zero-holder checks run
  immediately before and after the serial census. The live gate remains closed
  because exclusive ownership has not been re-established after the
  pre-existing Studio server was observed holding the follower device.
- Reviewer decision 055 resumes T16.5b after the owner explicitly authorized
  virtual disconnect/reconnect. The accepted immediate action is one exact
  follower disconnect call plus response/status/zero-holder proof; reconnect is
  deferred unless it can be proven no-motion-safe. No live proof label, motion,
  general register-write, or physical qualification is granted by the
  resumption itself.
- Reviewer decision 056 verifies the one-call disconnect boundary: HTTP 200,
  follower disconnected, follower torque off, leader retained, unchanged
  safety/routing, zero jobs, and zero follower holders. The live gate remains
  closed pending remote preservation and a separate reopen decision.
- Reviewer decision 057 opens the T16.5b live gate after remote confirmation of
  `b211562` and a second zero-holder/torque-off check. The grant is one fresh
  session under the existing finite lease/contract and no-write guards; it does
  not itself grant a live proof label or any write/motion authority.
- Reviewer decision 058 rejects live attempt 002 and recloses the gate. The
  exact follower census closed with zero holders before exact-name camera
  capture returned a nonzero ffmpeg status. No evidence bundle, manifest,
  label, write beyond the earlier authorized disconnect, motion, or physical
  qualification survived the attempt.
- Reviewer decision 059 accepts Brief 042 implementation `2d1cd97` on offline
  evidence only. Manager intervention 015 applies the owner review: canonical
  disconnect proof, consumed-permit state, all-alias holder coverage, and
  `Torque_Enable` evidence are mandatory before another live-gate review.
- Reviewer decision 277 verifies T20.36o as a terminal bounded negative:
  2,500 finite updates preserve source objective but the final checkpoint
  passes 0/25 amended bridge probes. Gate C was not executed and no retry or
  policy acceptance follows.
- Reviewer decision 278 verifies quantitative strict-v2 receipt `02268a1a...`
  on analytic fixture evidence only; its 33 predicates and hard conjunction do
  not create pure-policy, actual-MuJoCo, physical, or training proof.
- Reviewer decision 279 verifies counterexample archive seed `8277b09f...`
  and index `05908b6d...` as evidence-only. The missing remotely retained trace
  keeps replay/training inactive. T20.40 is deferred and T20.41 requires a new
  owner route decision.
- Reviewer decision 280 amends the verifier-completeness portion of Decisions
  278-279. Current receipt identities are T20.38 `042bf0be...` and T20.39
  receipt/index `60babc53...`/`043d45b3...`; hard guards preempt the effective
  bottleneck, top-level archive authority is routing-bound, conflicting
  inactive duplicates fail, and stale sources require invalid/no-replay/no-
  delete disposition. The analytic/evidence-only proof boundaries and blocked
  T20.41 route are unchanged.
