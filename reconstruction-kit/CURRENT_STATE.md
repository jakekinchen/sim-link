# Current Proof State

Current route snapshot: the portable source commit recorded in
`SOURCE_MANIFEST.json` on `codex/pi05-autolearn-loop`, 2026-07-16. Historical
T20.43b, original T20.43c, and T20.43c-R2 artifacts remain immutable; this
snapshot interprets them without rewriting or conflating any result.

## Operational verdict

| Layer | State | Exact meaning |
| --- | --- | --- |
| Constructive simulation source | Verified | Deterministic geometry-derived controller produces strict-v2 grasp/lift episodes under the bounded R0 construction space. |
| Dataset and processor | Verified | R0 has 129 training episodes, 31,366 frames, 59,904 windows, training-only MEAN_STD statistics, and zero held-out rows admitted to training. |
| Evidence and authority | Verified | Canonical JSON/SHA-256, source identities, central composition, renderer smoke, trace mirroring, and one-use permits fail closed. |
| SmolVLA learned policy | Verified terminal negative | One 5,000-update, five-checkpoint, ten-rollout campaign produced no Gate C pass. |
| ACT learned policy | Verified terminal negative | T20.43b ended in mirror-schema infrastructure at zero updates. Original T20.43c proved exact continuation and ended inconclusively at update 728. T20.43c-R2 then completed 10,000 updates, seven checkpoints, and fourteen rollouts without a Gate C pass or infrastructure failure. |
| PI0.5 learned policy | Negative diagnostic history | Extensive Gate B work localized structured decode/objective mismatch; no learned Gate C success exists. |
| RGB camera readiness | Terminal infrastructure failure | One D405 decoded frame failed signed input-mode dimension validation; C922 was not opened and no frame, mode census, latency result, or readiness label was accepted. |
| Physical twin/transfer | Not qualified | Physical calibration, metric Robo Scan handoff, task proof, transfer, and promotion remain open. |

## Verified R0 source package

- Result identity: `d238379bce62d884833da0a449535e3dc24f988b8da573513ae684bbb19a5969`.
- 119/119 newly generated training episodes pass strict-v2.
- 9/9 fresh held-out episodes pass strict-v2 and remain excluded from training.
- Exact T20.23 base is included once, producing 129 training episodes total.
- 31,366 training frames and 59,904 indexed windows.
- Mixture identity: `37b30d342313710f51c05b6c53f80f3dddc93c93cb0ff2c443bf5970dff203df`.
- Statistics identity: `02ba0e701da708680e162493aecececa5827914be2d07a0e1f9e20335d9388ae`.

This proves source behavior and dataset construction, not learned-policy
competence.

## SmolVLA result

- Result identity: `9d916206cbbb86b67a42d3449953bc7b272e1de5171996df224e29772369e14f`.
- Training: 5,000 finite MPS updates.
- Evaluation: checkpoints 0, 500, 1,000, 2,500, and 5,000 under chunk-50 and
  receding-10 semantics; ten strict-v2 rollouts total.
- Outcome: zero Gate C passes and no selected checkpoint.
- Strongest partial: checkpoint 1,000/receding-10, 73 strict-contact frames,
  18.061304 mm lift, still below the unchanged 25 mm/phase-duration gate.
- Retry/replacement: closed.

This is a clean model result, not an infrastructure failure.

## ACT terminal boundaries

- Spec identity: `13c5bb4b2cadf8c451a25e7c11e9e0a1d824468f593774fdb60dbf7fa5197461`.
- Fixed recipe: ACT, batch 8, training seed 20260801, AdamW at `1e-5`, no
  scheduler, 10,000 updates, checkpoints 0/500/1,000/2,500/5,000/7,500/10,000,
  chunk-50 and receding-10 evaluation.
- Epoch-2 pre-run acceptance:
  `c6af103096710491a7ec9f1439b349e0d9bca7033a2709ba367ebc1d786127c7`.
- Consumed marker:
  `d67cf38e7d7a441da93c3af55cdcfeefe64b55ce9cf3f0b95894299a88fdca09`.
- Terminal receipt:
  `89b6dbff17f5da345b1c8d8fa9951989eda092998b702737dd7da16c42db2e92`.
- Execution: fresh ACT and AdamW objects, checkpoint 0, one untrained chunk-50
  rollout, zero optimizer updates, zero strict-contact frames, and
  0.000304225 mm maximum anchor lift.
- Root cause: the legacy mirror supported T20.43 and T20.44 schemas but not
  `scenesmith.t20_43b_r1_act_closed_loop_trace.v1`; its smoke used an older
  T20.43 trace and therefore could not prove this dispatch.
- Disposition at this boundary: no retry, continuation, or second replacement.
  T20.43b alone did not resolve trained ACT-on-R0 capability; the later R2
  result below did.

`scripts/robot_lab/render_rollout_mirror_v2.py` adds T20.43b dispatch without
changing the legacy renderer bytes bound by the historical spec. It is a
diagnostic entrypoint, not permission to rerun a consumed campaign.

T20.43c then established the missing facts:

- continuation marker identity: `e086c293505385d8d85b095d86f993a65266b70abe7047bc83d5bba319d9ed60`;
- equivalence receipt identity: `85087b2ae94d54ea493ec49a10e6a183369b43c6160e73f79205a7624bb65014`;
- tensor values, keys, shapes, and dtypes matched fresh seed-20260801 ACT with
  maximum absolute error 0; AdamW had zero state entries and zero steps; the
  sampler had consumed zero batches;
- actual-schema mirrors passed, updates 1–728 ran, checkpoint 500 and its
  chunk-50/receding-10 evidence were retained; and
- terminal identity `d848a1a8d9c803c0d8782e2c51c102cfd4550f1ca5bf22a629a16f34f834bd68`
  records SIGINT after another agent applied a superseded scheduling note.

The correct disposition of this original boundary is **inconclusive
owner-directive interruption**. It is not a trained negative, not an
infrastructure failure, and not a Gate C pass. The continuation marker is
consumed and `retry_authorized=false`.

T20.43c-R2 later resolved the scientific question without changing that
history:

- replacement marker:
  `dfe3ff05a78f65122d44d87c84dea72f1b40f539eb77ec34a09c8efe5ceba63b`;
- equivalence receipt:
  `fdc062972a8aef00b77e8719d9c61451f5ed3d05dd4187aa98fb7db1e9df9548`;
- run identity:
  `82a0608386375f029a56be8ca9f972bc0e83939d30ad286164db828aa22dc851`;
- result identity:
  `bf2c8b466597ac23ff76ad88e8697b7b5d70a09b9016bc11442010243c984327`;
- scorecard:
  `6f848570dafbc2fde2558a4e62613315890fbc251b93b1ee0c92cdf73ebb1ab7`;
- retention receipt:
  `e565e17a5d4f8a52c4d894d3d61f03cf4b38beaf1df0bec3b83ade7f05afc023`;
- final receipt:
  `be11a258b6662baa10341acac13fe09055cd4ded7c2eaba4236d466977dfac5e`.

R2 completed 10,000 updates, seven checkpoints, and fourteen rollouts. Gate C
is false, no infrastructure failure occurred, and no retry is authorized. The
release-phase counterexample is the useful forward signal: final chunk-50
lifted 0.037655304225193253 m and failed only
`release_final_contact_clear`; maximum chunk-50 lift was
0.04567430422519325 m. Final receding-10 had no grasp hold and lifted only
0.000502 m. The kit transfers this evidence, never its consumed authority.

See the optional [hackathon fork annex](../docs/autonomous-workflow/hackathon-fork-annex-2026-07-16.md)
for the three-day distributed plan. It is task direction, not transferred
authority.

The reviewed [RGB camera readiness note](./HARDWARE_READINESS_RGB_CAMERAS.md)
preserves the K3 failure boundary and exact discovery-first replacement
requirement. It carries no private frame and grants no new camera session.

## Claims that remain false

- `learned_policy_strict_v2_success`
- `physical_twin_qualified`
- `physical_transfer_ready`
- `promotion_eligible`
- `hardware_authorized`
- `external_compute_authorized`
- `brev_compute_authorized`

See `CURRENT_STATE.json` for the same boundary in machine-readable form.
