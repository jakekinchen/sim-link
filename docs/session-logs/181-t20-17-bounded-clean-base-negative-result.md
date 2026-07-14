# Session Log 181 - T20.17 Bounded Clean-Base Negative Result

## Scope

Brief 148 executed the fixed official-LeRobot clean-base campaign and the one
frozen seed-6 unassisted evaluation authorized by Brief 147. No hardware,
camera, physical transfer, external compute, Hub publishing, or Brev was used.

## Execution

- Failed run 001 is preserved: it stopped before model load or optimization
  because the evidence wrapper pre-created LeRobot's output directory.
- The minimal reviewed correction separated evidence from trainer output in
  run 002; it did not alter data, base, seed, optimizer budget, or evaluation.
- Official LeRobot loaded all base keys, wrapped PI0.5 with rank-4 LoRA, and
  completed 250/250 local-MPS updates over the 1,464-frame dataset.
- All 250 logged losses were finite: first 0.829, last 0.135, minimum 0.017.
- The final adapter is 1,299,944 bytes with sha256
  `ed1e16ebb7d53307f7d3494ff27264d803a2bee7cf2cb7cacee371147700a07a`.
- Held-out seed 6 ran 244 unassisted frames with zero projected and zero active
  assist frames, no strict contact, and 0.000307 mm maximum lift.

## Validation

- 30 focused campaign, preflight, manifest, authority, and composer tests
  passed.
- 6 documentation information-architecture tests passed.
- Both campaign modules and all entrypoints compiled.
- Workflow audit, diff checks, commit integrity, scoped staging, pushes, and
  remote preservation passed through `dce1995`.

## Adversarial Review

The same-agent review checked source/held-out leakage, policy-internal padding
versus source semantics, local-cache substitution, incomplete base or adapter
bytes, PEFT rank drift, extra/missing updates, non-finite loss/action values,
processor-statistics substitution, output overwrite, nondeterministic seed
drift, projection/assistance, false policy acceptance, physical/external state,
and cleanup side effects. Unrelated `.codex/config.toml` and vendored checkouts
were preserved.

## Result

Brief 148 is a verified negative result under Reviewer Decision 178. T20.17 is
complete without policy acceptance. The next dependency-ready task is T20.18:
use the existing T18.4 state-fork primitive to generate labelled recovery,
near-failure, and failure episodes from policy-visited states before any
additional training campaign.
