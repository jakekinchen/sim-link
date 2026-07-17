# Reviewer Decision 320 - Verify F0 Release-Gap Diagnosis

**Date:** 2026-07-17

## Decision

`VERIFY_F0_RELEASE_GAP_DIAGNOSIS_ROUTE_TO_MODEL_FREE_F0A`

Brief 230 satisfies its deterministic, model-free acceptance criteria at
implementation commit `698d5644e9add156266f0ab4997aaa27c9b98b10` on origin.
Canonical result `807d3da7...` is independently reproducible from exact
hash-bound sources and grants no system authority.

## Verified findings

- The R2 runner uses `LeRobotDataset` target deltas 0-49 and
  `EpisodeAwareSampler` over every episode frame; ACT masks `action_is_pad`.
- Reconstructed exposure over 10,000 updates is not tail-starved: the minimum
  late/interior target-exposure ratio is 0.9708519498, late valid-loss mass is
  1.1388855154 of geometric share, and frame-200 start exposure is
  0.9786928323 of uniform expectation.
- The standalone unpadded H50 index contains no release window but is not an
  ACT runner input; it cannot diagnose the consumed training distribution.
- Required open gripper is within the pre-registered `1e-4` tolerance of the
  actual R0 action envelope and at 1.4173925665 standard deviations, so the
  normalization defect is false.
- Physical-L1 conversion yields a 2.6963081474 gripper coefficient, and the
  retained release error is same-direction and contact-relevant.
- The candidate release pattern is most informative at a 20-frame delay:
  aligned MAE 0.0489290261 rad versus 0.7417896319 rad at zero shift, a
  15.1605231282 improvement ratio.

## Adversarial review

The result retains all inputs required to reconstruct sampler counts, phase
mass, normalization, weighting, and the 44-frame late trace. Source references
are unique, sorted, repository-relative, traversal-free, hash-bound, and not
symlink aliases. Numbers are finite. Mutations to routing, training authority,
or episode coverage fail verification. The implementation reads retained prior
inference and rollout evidence but executes no new inference or rollout and
does not read checkpoint tensors.

The apparent gripper-weight mechanism is real but is not a license to train:
the pre-registered continuation route required release-mixture underweight as
well, and that hypothesis is false. Selecting a weighted continuation now
would change the rule after seeing the result. The 20-frame delayed release is
a fresher and more discriminating timing/observability hypothesis.

## Verification evidence

- canonical live verifier: pass, identity `807d3da7...`;
- relevant deterministic unit suite: 46 pass, including five focused F0 tests;
- continuation/replacement regression suite: 14 pass;
- Ruff, JSON/non-finite, path/symlink, and whitespace checks: pass;
- implementation commit and origin branch: exact match before this closeout.

## Authority disposition

F0 is verified and closed. The single corrective ACT rung remains unconsumed.
A fresh model-free F0a brief may open after this closeout is exact on origin.
Corrective training, checkpoint/model action, rollout, dataset mutation,
threshold changes, network/package installation, F1/Brev, hardware, Gate C,
physical transfer, promotion, destructive operations, and the freeze tag
remain closed.
