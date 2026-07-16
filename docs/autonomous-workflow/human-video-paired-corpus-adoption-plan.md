# Human-Video Paired-Corpus Adoption Plan

**Date:** 2026-07-16

**Decision:** Adopt the direction and its preparatory schema contracts. Do not
build the pairing pipeline, any video-perception component, or any test-time
adaptation module until a policy passes Gate D; only zero-cost preparation is
sanctioned now.

**Assessment:** 9/10 strategic fit for the data-scaling thesis; 1/10 value
before Gate C/D. The preparation steps below cost near zero because they ride
on artifacts that already exist or are derivable by deterministic replay.

This is a roadmap and contract-design artifact, not an authority source. It
does not open any task, grant model/optimizer/rollout authority, or permit
camera capture, hardware, network, external compute, or Brev.

## Motivating external result

WAM-TTT (arXiv:2607.06988) steers a frozen world-action model by absorbing
raw, unlabeled human videos into a lightweight key-value memory via
self-supervised video prediction at test time. Its load-bearing ingredient is
a **meta-training corpus of paired human-and-robot executions of the same
task**. The general trend it represents: robot foundation models stay frozen;
adaptation moves into small reusable modules; cheap action-free human video
becomes the steering signal; and the scarce asset shifts from teleoperation
hours to *clean paired data*.

## Why sim-link is unusually positioned

Everyone can scrape human videos. Almost nobody can manufacture the robot
side of a pair without teleoperation. Sim-link can: given a human video's
scene configuration (object start/goal poses), the twin reconstructs the
scene and the geometry-derived constructive expert executes it —
deterministically, strict-v2-verified, with actions, multi-camera renders,
timing evidence, and content-addressed provenance. Every human video becomes
one verified pair plus arbitrarily many variant robot episodes. Contributors
need a phone and a printed registration mat, not a robot. The evidence
discipline (quarantine, provenance, licensing) is exactly what makes an
aggregated pair corpus trustworthy across contributors.

T20.42/R0 already proves the robot-side factory at scale: 128/128 fixed
pose-varied candidates passed strict-v2 exactly once, yielding 129 training
episodes, 31,366 frames, and 59,904 unpadded windows with frozen held-outs.

## The three layers (outermost first)

1. **Twin-mediated test-time steering (nearest, post-Gate-D).** Human video
   of a task variant → scene reconstruction → constructive-expert episode
   generation for that variant → minutes-scale frozen-trunk adapter tune →
   strict-v2 rollout verification. Same input/output contract as WAM-TTT
   (video in, adapted behavior out, trunk frozen) with the twin playing the
   role of the adaptive memory. No new learning system; uses R0 machinery
   plus the standard-rung recipes.
2. **Paired-corpus factory (the durable asset).** A `human_video` raw-record
   type and a pairing manifest binding human video ↔ twin-reconstructed robot
   episode, with aligned event structure: robot-side event times come free
   from strict-v2 predicates; human-side weak event labels start manual.
   Valuable regardless of which adaptation method wins externally.
3. **Memory-steered policy (the paper's mechanism, latest).** Meta-train a
   small alignment module (frozen trunk + memory/adapter) on the pair corpus
   so an unlabeled human video steers the policy to a task variant with zero
   new robot demonstrations, scored by the existing evaluator. Research risk
   is confined here: the paper is new and unreplicated, current candidates
   are not world models, and the human-to-SO-101 embodiment gap is real.
   Layers 1-2 pay off even if this layer's specific mechanism does not.

## Zero-cost preparation sanctioned now

- **Schema stubs only** (see the plan's schema-fields list): `human_video`
  raw record with capture, consent, license, and PII-handling fields; pairing
  manifest; `event_label_source` distinguishing robot-side strict-v2 event
  times from human-side weak labels.
- **Derived human-viewpoint renders by replay.** R0 episodes replay
  deterministically, so a standardized human-viewpoint camera render is a
  compiled-view addition when pairing work begins — no regeneration, no
  pressure on current rungs.
- **One physical registration anchor.** The T19.2 printed metric checkerboard
  doubles as the human-recording scene mat, serving twin calibration and
  video scene reconstruction with one artifact. Robo Scan's metric-capture
  lane is the eventual scene-from-video component; nothing new is built for
  it here.

## Preconditions before any active slice

Gate D pass (route R0-R3); Robo Scan first real metric bundle for
scene-from-video; T20.20 observable-evaluator vocabulary for human-side event
labels; a fresh owner decision opening the first pairing task. Governance
rule: **human video is evidence before it is data** — no human-derived frame
enters training without a separate source-bound compiler, mixture, and
central-authority decision, mirroring design rule 8.

## Relationship to the Gate F scene adversary

Complementary halves of the same substrate thesis: the CEGIS falsifier scales
*quality* (searches for worlds that break the policy); the pair factory
scales *data* (absorbs tasks humans demonstrate). Both write immutable,
policy-independent evidence into the same contracts, and neither may start
before its gate.
