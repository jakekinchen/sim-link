# Executor Session 159 - T20.7 Four-Model Canary

T20.7 froze a common 20-window, 50-action plan and then ran the same source
start 0 through PI0.5, SmolVLA, compact ACT, and compact Diffusion Policy on
local MPS. Promoted run 003 records finite forward loss and finite gradient norm
for every model, with zero optimizer steps and no policy inference claim.

The hardened plan binds all pretrained model and preprocessing dependencies,
the deterministic empty SmolVLA camera, random-init architectures, T20.1 tensor
view, T20.6 semantics, sample order, and LeRobot runtime. Twenty-eight focused
plan, canary, semantics, authority, and pointer tests pass.

One exploratory runtime command began resolving a fresh `uv` environment. It
was stopped and the newly created environment removed before model loading; no
promoted canary depends on it. Run 003 used the existing local leLab runtime,
offline Hugging Face mode, and cached Diffusers package only. No optimizer,
hardware, external compute, or Brev was used. T20.7 remains in progress.
