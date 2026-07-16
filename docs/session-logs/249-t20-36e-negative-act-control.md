# Session Log 249 - T20.36e Negative ACT Control

## Evidence

- Result: `2ea2c2460527ee863275da11a008aa2b75832f08040daf4fd64459c9520769c6`.
- Run: `9911e51c45dad591691502a47d6ea3baa871ca6c3e3b6b549f81bc2af4423478`.
- Checkpoint: `01b5713472ae6113ea55b265cbeb02042f3be2b473178a366a6b996e1b75dd21`.
- Updates: 2,000 finite; evaluation schedule 0/100/250/500/1,000/2,000.
- Objective: `1.385815` baseline, `0.0761061` final, `0.054918` ratio.
- Final action: five identical hashes `ecaa2e4c...`; mean error `0.0145525`
  rad; maximum error `0.442487` rad.
- Exact run verification passes; checkpoint config and safe tensor match the
  signed tree.

## Result

Gate B fails only the unchanged physical-maximum conjunct; the result is
negative and no retry or Gate C is opened. Reviewer 246 routes Brief 197 to
exact checkpoint/direct-queue/per-joint localization before SmolVLA or any gate
amendment. No policy is selected and no hardware, external compute, or Brev
action occurred.
