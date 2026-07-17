# Owner Direction — Final Hour Before Freeze (2026-07-16, ~21:50–22:45 CDT)

Recorded ~21:50 CDT by Claude at the owner's explicit chat instruction. The
owner grants roughly one more hour of agent work, then the repository freezes
as the seed for a new hackathon fork. This document orders that hour. It is a
task-ordering source, not an authority source; the loop's own ceremony still
applies to anything it opens. Hardware authorization below is owner-present
and read-only. Network, package install, external compute, Brev, motion, and
depth-stream work remain closed.

## Priority 1 — land the reconstruction kit (loop thread, Brief 224 lane)

Complete and verify `reconstruction-kit/` before anything else. Three required
inclusions beyond the existing brief:

1. **T20.43c ready-package in `FORWARD_PLAN.md`.** ACT-on-R0 remains the
   project's most valuable unanswered question after two infrastructure
   kills at zero updates (T20.43 mirror venv `import mujoco`; T20.43b
   mirror-schema dispatch, fixed post-hoc at `37c5da6`). Package the exact
   fixed runtime, the unchanged 10,000-update recipe lineage `b3a510f8...`,
   and a pre-marker smoke extended to execute the **exact ACT trace mirror
   schema end-to-end** (the T20.44 smoke pattern that survived its full run),
   as the fork's designated hour-one experiment.
2. **Reference `hackathon-fork-annex-2026-07-16.md`** (same directory) as an
   optional-tier kit source in the manifest.
3. **Record the infrastructure lesson explicitly** in
   `RESULTS_AND_LESSONS.md`: three experiment slots died to a venv import, a
   renderer entrypoint, and a mirror schema — never to science. Rule for the
   fork: every one-use attempt requires a pre-marker smoke that executes the
   exact output-artifact path schemas, and infrastructure failures get
   replacement semantics by default.

## No third ACT attempt tonight

T20.43c may run only in the fork or a future unhurried window. Both prior
attempts died to haste-shaped gaps, and a third under freeze pressure risks
consuming the question's credibility along with another permit. The unresolved
state transfers cleanly; a rushed third failure does not.

### Later owner supersession in the active T20.43c thread

After this ordering note was recorded, the owner explicitly instructed the
active T20.43c thread: "proceed, i authorize anything further actions that
resolve this for us." Brief 227 and the dedicated owner addendum narrow that
newer instruction to one separately reviewed, local-simulation, exact
zero-update continuation. It supersedes only the scheduling prohibition above;
all central-composer, preflight, review, one-use, equivalence, no-retry,
hardware, network, external-compute, and Brev boundaries remain in force.

## Priority 2 — owner-present RGB camera census (physical thread)

The owner is present and authorizes one bounded, read-only, RGB-only camera
bring-up session in the T19.1 census pattern (≤10 minutes of capture, no
motion, no writes to hardware, no depth requirement):

- Devices confirmed enumerated on the Mac Studio at 21:46 CDT:
  Intel RealSense D405 as UVC (VendorID 32902 / ProductID 2907) and a
  Logitech C922 Pro Stream webcam — the C922 is the designated known-good
  RGB fallback for wrist/scene mounting.
- Deliverables: per-camera achievable stream configs (resolution/fps), one
  signed frame per camera, and a coarse observation-latency measure using the
  T20.22 timing-certificate vocabulary. Evidence lands as a short
  hardware-readiness note referenced by the kit.
- Depth is declared out-of-scope on macOS: policies are RGB+state by Gate A
  parity, and any future depth runs observer-role on the Linux box. Do not
  spend this hour on librealsense.

## Priority 3 — freeze protocol (final 15 minutes)

1. Final pointer sync (`sync_project_state_pointers.py --apply`) and a
   closeout ledger entry stating: kit verified, ACT-on-R0 open with the
   T20.43c package ready, camera census result, all other authorities closed.
2. Push so branch == origin; working tree clean except the known pre-existing
   `.codex/config.toml` and `external/` paths.
3. Create annotated tag `freeze-2026-07-16-hackathon-fork` at the final
   commit and push it. The fork clones at this tag.
