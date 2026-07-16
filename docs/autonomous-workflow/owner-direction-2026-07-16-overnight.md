# Owner Direction — 2026-07-16 Overnight Window

Recorded 2026-07-16T01:53 CDT by Claude at the owner's explicit chat
instruction, inside the owner continuation window the loop has already
recorded (ledger `run_window`, Brief 206: 01:44:12–09:44:12 CDT, no new major
slice after 08:59:12). This document adds the owner's priority ordering,
branch routing, and stop rules for that window. Like the MVP execution plan,
it is a task-ordering source, not an authority source: it grants no authority
class by itself, and every attempt still requires the loop's own central
authority composition, runtime preflight, one-use permit, and remote
preservation. Hardware, physical transfer, promotion, network/downloads,
external compute, and Brev remain closed regardless of any success tonight.

## What "success by morning" means

The owner's stated intent: make maximal verified progress toward a working
system by 09:44 CDT, self-updating plans, using a research → critique →
iterate-or-maintain-course loop on failures. The deliverable that counts as
"working" tonight is a **verified Gate C result**: one unassisted closed-loop
MuJoCo rollout reproducing training episode seed 0 through strict-v2, signed
trace plus mirror MP4, by any retained candidate. Gate D (all training
episodes) is the stretch goal. Model-free schema work (T20.38/T20.39) is
filler while training runs execute or in the final hour — never the mainline
while a Gate C route remains open.

## Priority order

1. **T20.36m exactly as Brief 206** (in flight). No scope change.
2. **Complete the candidate comparison honestly.** Immediately after the
   T20.36m disposition — on either branch — score the retained T20.35x decoded
   evidence under frozen amended gate `463477dc...`. If the signed X result
   (`e79dacff...`, preserved at `afa421d`) retains the five 50x6 decoded
   tensors, this is model-free. If it does not, fold X into the same
   hash-bound inference-reproduction pattern as T20.36m (one load, five
   registered seeds, fail closed on hash mismatch). Do not skip this: X is the
   only candidate that ever passed frozen uniform Gate B, and it must not
   remain unscored under the amended gate while ACT and SmolVLA are scored.
3. **One-episode Gate C bridge** for the best amended-gate candidate:
   - If SmolVLA passes T20.36m scoring → SmolVLA is the bridge candidate
     (this is Brief 206's own pass route).
   - If SmolVLA fails → the owner re-designates the retained T20.35x
     checkpoint from "rollback capability only" (T20.36b decision
     `e709c30c...`) to **eligible Gate C bridge candidate**. Closing the
     Gate B adjudication branch closes candidate *entry*, not the ladder:
     X's frozen-gate pass (Reviewer 238) is the standing Gate B evidence that
     unblocks one one-episode bridge.
   - Bridge definition: extend the proven X recipe (physical-Jacobian
     joint/time-weighted correction plus paired deterministic standard
     replay) from the single batch to the episode-0 windows at exactly the
     chunk-boundary states implied by the frozen Gate C execution semantics
     (for full 50-step chunk consumption over 244 frames: starts 0/50/100/
     150/200; derive the actual set from the execution contract, do not
     assume). Bounded updates; checkpoint and open-loop probe at fixed
     intervals **during** the run so a T20.36-style coverage regression is
     caught mid-run instead of at the end. Acceptance: amended gate
     `463477dc...` at every chunk-start state; frozen uniform 0.05 rad stays
     report-only on the same result.
4. **Gate C probe.** One authorized closed-loop rollout on training seed 0
   with complete trace and mirror MP4. Run it even if open-loop chunk-start
   errors are marginal on non-consequence joints — a failed rollout with a
   full trace is high-value evidence (it localizes chunk-boundary execution
   or compounding, Gate C's named fault classes) and costs minutes.
5. **If Gate C passes:** one bounded Gate D extension — same recipe over the
   episode 0–5 window set with the memorized bridge set kept in replay,
   mid-run probes mandatory, stop on first probe regression (the T20.36
   500-window regression is the known dragon). If that holds, a single
   evaluation-only held-out probe (seeds 6–7) as Gate E evidence. Do not open
   Gate F scene search tonight under any outcome (plan order: Gate D, then
   E, before F).
6. **Filler and closeout tasks:** T20.38 quantitative receipt contract, then
   T20.39 archive bootstrap, during training waits or the final hour. Also
   reconcile the plan's capability-ladder Gate B status row, which still says
   "Still unmet" — the accurate state is: passed once by T20.35x under the
   frozen uniform gate; regressed under T20.36 coverage; consequence
   amendment frozen at T20.36l.

## Decision rules for the autonomous loop

- Research → critique → iterate-or-maintain-course: after any failed attempt,
  at most one localization audit, then either one corrective rung or a route
  switch. Three same-signature failures force a route switch (T19.0 lesson:
  interrogate the frozen constants, inspect a rendered frame, prefer
  constructive derivation over another sweep).
- No new candidate architectures this window — no new SmolVLA variants, no
  ACT capacity hunts, no fourth policy. The adjudicated field is ACT, SmolVLA,
  and π0.5/X; the marginal information now lives in closed loop, not in more
  open-loop candidates.
- Reuse verified runtime surfaces (the T20.35v/T20.35x dependency-preflight
  pattern) instead of constructing fresh environments; a permit burned on a
  missing package (T20.35u, T20.36h) must not recur tonight.
- Amended gate `463477dc...` (owner decision `32d7e193...`) is the
  forward-routing instrument only. Frozen uniform 0.05 rad is reported on
  every result. No retroactive relabeling of any historical result.
- Time discipline: prefer the smallest slice that moves the current priority;
  if a slice's boundary ceremony would exceed its experiment time, shrink the
  slice, not the evidence.

## Mandatory closeout (begin no later than 09:00 CDT)

Reconcile ledger / plan / `project_state.json` pointers, push so branch and
origin match, and write `docs/autonomous-workflow/morning-summary-2026-07-16.md`
containing: gate-by-gate status; every retained checkpoint with exact
identities; what passed and failed tonight with one-line causes; where the
path terminated and why; the single next task; and open risks. Leave the
working tree clean.
