# Reviewer Decision 189 - Verify T20.28 Sampler Exposure Audit

`ACCEPT_VERIFIED_REJECT_LOW_EARLY_PHASE_EXPOSURE`

Reviewed Brief 159 through artifact commit `72a6360` and audit identity
`2445c5d0711ebd29d6f6c92ca637b80e9c6d3e6725e39d7b427eb3b215937d38`.

The actual pinned `EpisodeAwareSampler` reconstructs both campaigns as a pure
function of seed and epoch. T20.17 consumed 250 unique indices from 1,464
nominal frames; T20.24 consumed 500 unique indices from 2,330 frames, split 314
nominal and 186 recovery. Every sampled position binds to one exact episode,
frame, source class, and phase.

Clean exposure contains 14 approach frames and zero frame-zero samples.
Recovery-campaign exposure contains 26 approach frames—21 nominal and 5
recovery—and three frame-zero samples—2 nominal and 1 recovery. The recovery
campaign therefore did not have less early-phase exposure than clean. Exposure
count alone cannot explain the T20.27 regression and is not optimizer causality.

Same-agent adversarial review checked sampler source hash, seed/epoch/resume,
batch/world size, update count, episode boundaries, absolute indices, duplicate
and range handling, source/phase binding, unique coverage, signed mutation,
authority escalation, and cleanup side effects. Eighty-three relevant tests
pass, and the audit reconstructs exactly from live pinned sources.

T20.28 grants only a verified offline sampler audit. It does not authorize
model inference, an optimizer, action application, policy acceptance, transfer,
promotion, hardware, external compute, or Brev. The next safe diagnostic is the
clean-versus-recovery dataset quantile/postprocessor shift.
