# Session Log 190 - T20.26 Frame-Zero Inference Variability

## Scope

Brief 157 measured frozen frame-zero PI0.5 sampling variability in four
independent local-MPS processes. No action was applied; no rollout, optimizer,
hardware, camera, external compute, or Brev was used.

## Evidence

- Clean batch 1: `8e0085fd6f753f6708dc789ac458a54a35458ba97821d69313059b235e777dd8`.
- Clean batch 2: `adbb5c42ef8e9bf0c8f873bcd84654aab86081b349f31c5b0ad45892a3bf54f5`.
- Recovery batch 1: `887c7ccdea02d3c5d3ea6c5d0f1b8cdbb6f53eee47475a69204b3a3df81e142a`.
- Recovery batch 2: `cfa7304c51c95add36e65f37a9cacabfd2a4f3cfd50e2cd3e84f73456865f8ac`.
- Aggregate gate: `b1bbe7b27855ac738cf740ec04e03339b1f7897b03576b3b2757001c63163c0b`.

All batches bind the same source episode, stack, frame index, phase, top/wrist
raw-image hashes, qpos, and qvel. Maximum source-state error is 3.98e-8.

## Result

| Candidate | Within-process same-seed max | Cross-process same-seed max | Distinct-seed max pairwise |
| --- | ---: | ---: | ---: |
| Clean base | 0.0 rad | 0.0 rad | 0.18478 rad |
| Recovery augmented | 0.0 rad | 0.0 rad | 0.14797 rad |

The current runtime is bit-exact under reset plus a fixed inference seed. The
older clean action hash remains historical-runtime-specific because its gap is
not reproduced. Distinct inference seeds create material action dispersion, so
future clean-versus-recovery comparisons must be paired over the same seed set.

## Validation

Eighty relevant tests passed. Same-agent review covered source/checkpoint/runtime
substitution, observation equality, candidate/batch/sample ordering, finiteness,
seed/reset ordering, hidden action application, process separation, signed
mutation, authority escalation, and cleanup.

T20.26 is a verified inference diagnostic only. It creates no optimizer,
policy-acceptance, transfer, promotion, hardware, external-compute, or Brev
authority.
