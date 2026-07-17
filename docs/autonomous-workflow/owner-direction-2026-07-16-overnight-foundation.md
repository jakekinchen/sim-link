# Owner Direction — Overnight Foundation Run (2026-07-16 22:20 CDT → morning)

Recorded ~22:20 CDT by Claude at the owner's explicit chat instruction. The
freeze moves from tonight to tomorrow morning: overnight worker agents make
the fork foundation as strong as possible so that four team members each make
real progress in their own simulator instance on day one. This supersedes the
final-hour freeze timing (tag now lands in the morning as
`freeze-2026-07-17-hackathon-fork`); everything else in the final-hour
direction stands. Task-ordering source, not an authority source. Hardware
(beyond the already-authorized camera census), package installs from the
network, external compute, and Brev remain closed. Network remains closed:
all rehearsals clone external pins from the LOCAL existing checkouts
(`git clone /path/to/sim-link/external/lerobot …`), never the internet.

## Mission test

Tomorrow at 9 a.m., four people each run a bootstrap command on a fresh
export and reach: pinned runtime verified → one constructive-expert episode
with a strict-v2 receipt → regenerated R0 dataset matching the signed
boundary → one policy rollout with a v2 mirror — with zero tribal knowledge.
Every overnight priority serves that test.

## Worker priorities (parallelize W1/W2/W4/W5 while W0 runs)

**W0 — Finish T20.43c, unhurried.** Already owner-authorized and mid-ceremony.
Apply a completion-budget check before the marker; the run has all night. A
completed result (pass or trained negative) answers ACT-on-R0; fold the
outcome into the kit at W6. Infrastructure failure closes it again without
automatic retry, exactly per Brief 227.

**W1 — One-command fork bootstrap.** Wrap QUICKSTART stages 0–1 into a single
unattended script (`reconstruction-kit/scripts/bootstrap.sh` or equivalent):
export → local-pin external acquisition → runtime creation → stack verify →
focused model-free suite → one expert episode with strict-v2 receipt → one
all-schema render smoke using `render_rollout_mirror_v2.py` on a real trace.
The venv/renderer duality killed three one-use attempts; the bootstrap must
prove every output-artifact schema before it reports success. Rehearse once
end-to-end tonight in a scratch export; record wall-clock (target: under ~30
minutes on a 96 GB Mac) and a signed rehearsal receipt.

**W2 — Turnkey R0 regeneration.** Wrap QUICKSTART stage-2 route 1 as one
command: fresh local authority epoch from a template, generation, and a hard
hash gate against the signed boundary (119 training + 9 fresh-held-out
successes, 129 episodes, 31,366 frames, 59,904 windows, mixture `37b30d34...`,
statistics `02ba0e70...`). Any mismatch fails closed as "new dataset, not a
recreation." Rehearse once tonight; record timing so members can plan.

**W3 — Multi-instance portability rehearsal.** Export to three or four fresh
directories and run the W1 bootstrap concurrently in each (simulating the
four laptops). Define and document the match/drift contract: dataset
identities, receipts, and evaluator verdicts MUST match bit-exactly;
training-side nondeterminism (MPS) is tolerated and never part of a claim.

**W4 — Episode-hub and frozen-evaluator skeleton.** Minimal ceremony-light
scripts, no new frameworks: export episodes to a LeRobotDataset v3 shard,
merge pools with provenance, replay candidates on frozen seeded scenes, and
emit `leaderboard.json` plus counterexample-archive hooks (T20.39 schema).
Seed the leaderboard with the constructive expert. These are kit helpers
under the three rules (frozen held-outs, replayable artifacts, eval owned
separately) — not authority surfaces.

**W5 — NVIDIA gateway specification plus sim loopback.** The NVIDIA box's
roles for the hackathon: episode hub, central evaluator, RealSense depth
observer, and — new — **robot gateway**: a policy-inference server exposing a
thin action-chunk protocol so any checkpoint of any size (ACT, SmolVLA,
π0.5, anything Brev produces) can drive the robot while a Mac keeps the
serial driver. Execute, don't recreate: evaluate the pinned LeRobot async
inference server/client for this role, and carry the T20.22 timing fields
(observation age, inference latency, action hold) on the wire. Tonight:
write the spec and run one localhost loopback test (policy server serving a
cached checkpoint to a MuJoCo sim client). Day-one checklist item: run
`nvidia-smi` on the box — "800 GB" is almost certainly system RAM; actual
VRAM class decides whether π0.5 fine-tunes locally there (~70 GB+ needed) or
the $500 Brev reserve stays the plan.

**W6 — Morning K1b kit refresh, then freeze.** Fold into the kit with a full
re-verify (build-manifest, verify, export rehearsal): the T20.43c outcome,
W1/W2 bootstrap and regeneration receipts with timings, the W3 match/drift
contract, the W5 gateway spec, and the camera census evidence if the physical
thread produced it. Remove the superseded "no third ACT attempt tonight"
lines from FORWARD_PLAN/QUICKSTART in favor of the recorded supersession.
Write the morning summary, sync pointers, push, and tag
`freeze-2026-07-17-hackathon-fork`.

## Red flags this run must clear (the honest list)

1. **The dataset does not ship** — without W2 rehearsed, day one stalls at
   stage 2 for all four members.
2. **The renderer/venv duality** — three one-use attempts died there; W1
   bakes the all-schema smoke into the bootstrap so it can never recur
   unproven.
3. **ACT-on-R0 unresolved** — W0 is the last chance to answer it with the
   original evidence chain intact.
4. **External pins require network on day one** — members clone from the
   internet themselves; tonight's rehearsals prove the pins and patch apply
   cleanly from local checkouts.
5. **"800 GB" is unverified** — the W5 gateway decouples model size from the
   robot Mac regardless of what nvidia-smi reveals.
6. **Heterogeneous-device determinism** — W3's match/drift contract prevents
   day-two arguments about "my hash differs."
7. **Ceremony weight** — W4/W1 helpers stay three-rules light; historical
   grants/permits are expired artifacts and must never be copied into the
   fork as live authority.

## Rules for the night

One-use attempts require a completion-budget check and an all-schema smoke
before their marker. Rehearsals run in scratch exports, never in this repo's
tracked tree. Prefer finishing fewer priorities completely over starting all
of them; W1 and W2 outrank W4 and W5 if capacity forces a choice.
