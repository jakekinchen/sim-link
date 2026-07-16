# Session Log 296 - T20.44 R2 SmolVLA Standard Brief

**Date:** 2026-07-16
**Task:** T20.44 / Brief 220

Origin commit `2e6a3e3` preserves T20.43's consumed renderer-dependency failure
and makes R2 next under the owner-signed T20.41 route. Brief 220 freezes one
cached-base SmolVLA standard fine-tune on the exact R0 dataset: validated
expert-plus-state-projection scope, batch 8, official AdamW/cosine schedule,
5,000 updates, checkpoints `[0,500,1000,2500,5000]`, and chunk-50 plus
receding-10 rollout-primary strict-v2 evaluation.

The brief adds a mandatory pre-marker correction for T20.43's defect: the exact
future runner interpreter must successfully execute the real mirror renderer
on retained trace `6133ce58...`, produce a nonempty content-addressed MP4 and
manifest under MuJoCo 3.3.5, and bind its environment and outputs. This slice
opens implementation/tests only. Model weights, renderer smoke execution,
authority materialization, optimizer work, rollout, retry, hardware, network,
external compute, and Brev remain closed.
