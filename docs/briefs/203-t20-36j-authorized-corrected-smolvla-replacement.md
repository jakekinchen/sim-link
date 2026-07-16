# Brief 203 - T20.36j Authorized Corrected SmolVLA Replacement

## Objective

Execute the owner-authorized correction and exactly one replacement local-MPS
SmolVLA Gate B attempt. Install only the four distributions already bound by
the offline cache manifest, prove the complete installed closure, construct
AutoProcessor offline before any marker, remotely verify a fresh central
authority and one-use permit, then run the unchanged Gate B attempt once.

## Owner Authority And Window

- Owner instruction: "Proceed. I authorize all of this." followed by
  "proceed" on 2026-07-16.
- Window: 2026-07-16 00:33:37 through 08:33:37 CDT; no new major slice after
  07:48:37 CDT.
- Authorized environment mutation: install exactly Accelerate 1.14.0, docopt
  0.6.2, num2words 0.5.14, and psutil 7.2.2 from local cache manifest
  `6cc7235c...`, with network disabled, into `external/lerobot/.venv`.
- Authorized live preflight: execute contract `cb018b69...`, including offline
  AutoProcessor construction before an attempt marker.
- Authorized attempt: at most one local-MPS replacement attempt under the
  unchanged SmolVLA spec and Gate B. A central composer decision, reviewed
  remote implementation, signed corrected preflight, and fresh one-use permit
  are still mandatory.

## Required Work

1. Implement the exact owner grant, central authority, installed-closure
   collector, guarded offline AutoProcessor smoke, corrected preflight CLI,
   fresh permit, and replacement runner/result paths without rewriting T20.36h.
2. Add deterministic tests for expired/stale authority, install-set drift,
   closure/marker ordering, network and tensor-read guards, consumed attempts,
   and unchanged Gate B routing.
3. Commit and push the implementation before any dependency installation.
4. Install only the four cached distributions using uv in explicit offline
   mode; sign exact installed versions and recursive metadata closure.
5. Construct AutoProcessor from the exact local VLM snapshot with network and
   weight/tensor reads guarded; sign the corrected preflight before any marker.
6. Commit and push the preflight/permit boundary, verify origin parity, then
   execute exactly one attempt. Preserve pass, fail, or counted runtime failure
   without retry.
7. If Gate B passes, route Gate C design only. If Gate B fails or runtime stops,
   close the SmolVLA replacement route with exact evidence.

## Acceptance

- All implementation, authority, environment, processor, permit, attempt, and
  result artifacts are content-addressed and mutually consistent.
- No marker exists before corrected preflight and remote preservation.
- Exactly zero or one replacement attempt exists; zero only if a pre-marker
  gate fails, one otherwise. No retry/sweep is possible.
- Gate B thresholds remain the frozen 0.10 objective ratio plus five-seed
  0.05-rad physical-action conjunction.

## Prohibited Actions

Network/download, packages outside the exact four, a second attempt, changed
Gate B, Gate C execution before Gate B pass, closed-loop rollout, hardware,
physical transfer/promotion, external compute, or Brev.
