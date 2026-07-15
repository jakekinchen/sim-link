# Session Log 213 - T20.35g Cadence Result

## Runtime Result

- Replacement attempt: `83c215caa75bdbb11b667eaf2576fe1c4efbd48979c86292a3301e34155993f6`.
- Signed result: `57f1f0dd5190fa1e0dc2b84cf25546b8f4e520bb75d2a15616797c5f311b2ea2`.
- Result file SHA-256:
  `8ac42c3e63d436287cc482e57105e5195d9e4f220e4bb29fb254372fe5b2d4af`.
- Result boundary: `48e2b3f323b31155614a15ccb43d68089cce5c91`.
- Baseline exact-hash reproduction: pass for all five seeds.
- Gate B: fail; cadence effect: rejected.

## Metrics

| Inference steps | Worst maximum error (rad) | Aggregate mean error (rad) | Directionally positive |
| ---: | ---: | ---: | --- |
| 10 | 0.150321 | 0.030990 | baseline |
| 20 | 0.159251 | 0.033813 | no |
| 50 | 0.167722 | 0.035237 | no |

Reviewer 210 routes T20.35h to a model-free leave-one-seed-out output-bias
correction ceiling. The sole replacement permit is consumed. No optimizer,
training, mutation, closed-loop rollout, Gate C, hardware, external compute,
or Brev action occurred.
