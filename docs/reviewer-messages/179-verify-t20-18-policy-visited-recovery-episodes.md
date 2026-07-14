# Reviewer Decision 179 - Verify T20.18 Policy-Visited Recovery Episodes

`CONTINUE_T20_19_DISCRETE_ENSEMBLE`

Reviewed Brief 149 through implementation commit `9b359a5`.

The exact frozen T20.17 candidate replay reproduced the complete signed
seed-6 evaluation while capturing all 244 pre-action MuJoCo integration
states. Four deterministic parents were selected from approach, grasp, hold,
and release. Each parent produced one nominal and one bounded joint-offset
child using only the matching measured source-action suffix. All eight children
were replayed twice with zero tolerance. The observed result—not the intended
correction—assigned four recoveries, two near-failures, and two failures.

The causal manifest identity is
`f97c784f2f68ce3028a221acb715576c8c3fcaf0e66917e77ad28ecef11dd0b3`.
Its durable episode supplement identity is
`4123e8d40e5e1fd80702c4dc40ceb7a31922c2da2f36c797c91a20677f208e7c`:
eight episodes, 1,290 child frames, and 2,580 branch-rendered top/wrist images.
Every episode binds its exact parent, `generation_reason`, perturbation,
measured actions and source record IDs, state/action/contact trace, observed
outcome, and image bytes. No action is padded or inferred.

Adversarial review checked source or adapter substitution, parent/path aliasing,
state-specification drift, non-finite state/action values, perturbation escape,
duplicate branches, action/source misalignment, intended-versus-observed label
forgery, discarded trace bytes, image substitution, nondeterministic replay,
authority escalation, and output overwrite. Fifty focused and relevant tests
plus 273 subtests passed; compilation, artifact re-verification, documentation,
project-pointer, workflow, and diff gates passed.

T20.18 is verified as a simulation recovery-episode capability and training
candidate only. It grants no dataset mixture freeze, simulation training
readiness, optimizer authority, policy acceptance, physical transfer,
promotion, hardware access, external compute, or Brev authority. T20.19 is
next: a small discrete ensemble around the now-proven recovery branches.
