# Morning Summary - 2026-07-16

## Operational verdict

No learned policy reached Gate C. The owner-designated X bridge completed its
single 2,500-update bounded correction but failed all five registered forward
probes, so the ACT/SmolVLA/X candidate field and Gate C route closed without a
closed-loop rollout. The loop then completed the authorized T20.38/T20.39
model-free filler work and stopped at a genuine owner-route decision.

## Gate status

| Gate | Status | Evidence |
| --- | --- | --- |
| A - train/inference parity | Largely verified | Existing processor, normalization, determinism, sampler, and coordinate evidence remains valid. |
| B - one-batch memorization | Mixed/closed for current field | X passed the old uniform gate once, but only 3/5 seeds under amendment `463477dc...`; ACT and SmolVLA failed; X failed every episode-0 bridge checkpoint. |
| C - one-episode reproduction | Not executed; route closed | T20.36o never passed the five chunk-start acceptance gate required to request a rollout. |
| D - full training set | Not reached | Requires Gate C. |
| E - held-out nominal | Not reached | Prior 0/2 evidence remains; requires earlier gates. |
| F - robustness/recovery | Not reached | Explicitly out of scope before D/E. |

## Overnight results

- T20.36m reproduced the retained SmolVLA outputs exactly and failed the
  consequence-amended gate with 162 violations; result `4f101f38...`.
- T20.36n reproduced X exactly. Uniform 0.05 rad passed, but the amendment
  passed only 3/5 seeds with five small grasp/gripper misses; result
  `f8d7866e...`.
- T20.36o baseline result `e6537428...` passed 3/5 at start zero and 0/5 at
  starts 50/100/150/200 with 2,215 violations, while retaining all 50 chunks
  and 500 denoise records.
- T20.36o optimizer result `ec7fb323...` completed 2,500 finite updates. Every
  source-objective ratio passed, but amended violation counts were
  2,045/2,010/1,368/1,738/1,677 and the final checkpoint passed 0/25 probes.
  Update 2,000 briefly passed only the five start-zero probes. Uniform report
  `70e98c06...` also failed at the selected checkpoint: 0/25, 3,613
  violations, 0.553656 rad worst error. No retry.
- T20.38 receipt `02268a1a...` added 33 direction-correct strict-v2 margins,
  hard actor/evidence guards, and a deterministic zero-headroom contact-count
  bottleneck without upgrading analytic fixture proof.
- T20.39 receipt `8277b09f...` and index `05908b6d...` bootstrapped one truthful
  evidence-only source-controller counterexample. Replay and training remain
  inactive because full T20.19 trace bytes are not remotely retained.

## Retained checkpoints

| Candidate | Checkpoint identity | Local path | Disposition |
| --- | --- | --- | --- |
| ACT control | `01b5713472ae6113ea55b265cbeb02042f3be2b473178a366a6b996e1b75dd21` | `outputs/robot_lab/t20_36e_exact_act_gate_b_control_run_001/checkpoint/` | Gate B negative; result `2ea2c246...`; not product policy. |
| SmolVLA | `32f0bd3035a984d3b0ee2a752c1195fd252f61e9b2a560d1762e856f44ce81fa` | `outputs/robot_lab/t20_36j_exact_smolvla_gate_b/checkpoint/` | Gate B negative; result `08ef923d...`; no retry. |
| PI0.5 X | `40c94f66e24f0e949c1b48c057de7643b868468cc3ee0025e15778c25b8cad50` | `outputs/robot_lab/t20_35x_physical_gate_joint_weighted_run_001/checkpoint/` | Uniform pass, amended mixed-negative, bridge source. |
| PI0.5 X bridge final | `6e202dc58c6c6d67796b9f963eb4b2a9e13ea08dc2faa2cdab2fc26e14f76314` | `outputs/robot_lab/t20_36o_bounded_optimizer_run_001/checkpoint/` | Terminal bridge negative; result `ec7fb323...`; no retry. |

These multi-gigabyte checkpoint directories are local/gitignored. Their signed
tree identities and compact result evidence are tracked; a fresh checkout does
not contain the checkpoint tensors themselves.

## Where the path terminated

The bridge learned the retained paths and preserved source objective, but did
not cover downstream chunk-start observations. Its best checkpoint still
failed starts 50/100/150/200, dominated by shoulder lift and gripper. More
updates were non-monotonic: start zero passed at 2,000 then regressed at 2,500.
The pre-registered no-retry rule therefore closes X rather than opening another
alphabet rung. Gate C cannot distinguish closed-loop compounding because its
open-loop entry gate never passed.

## Single next task

**T20.41 - owner route decision.** Choose and authorize the next capability
strategy after the adjudicated ACT/SmolVLA/X field failed. The next session
must begin with a new brief; it must not silently resume T20.35/T20.36, weaken
amendment `463477dc...`, or treat the local final checkpoint as accepted.

## Open risks

- No learned-policy closed-loop success exists; Gate C evidence is absent.
- Source objective is not predictive of forward chunk-start action accuracy.
- All four retained checkpoint tensor trees are local-only and require an
  explicit preservation decision if cross-machine replay matters.
- T20.39 cannot replay seed `0001` from tracked files because its full trace is
  gitignored; the archive correctly marks it evidence-only.
- Physical gaps remain: sorting-scene mismatch, no metric camera/workcell
  transform, and no physical aperture/current mapping.
- The local Python stack emits a nonfatal duplicate `cv2`/`av` Objective-C
  class warning; no camera was accessed.
- The owner hardware-access window was unused. Any future camera/serial/robot
  session still needs runtime verification, central composition, and a finite
  permit.

## Repository and cost closeout

All scoped commits were pushed to `origin/codex/pi05-autolearn-loop`; final
origin parity is verified by the closeout commit containing this summary. No
Brev resource was created or used, so the Brev inventory protocol was not
triggered. Unrelated pre-existing dirty/untracked paths were preserved rather
than cleaned destructively.
