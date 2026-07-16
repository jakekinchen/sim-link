# Brief 202 - T20.36j-B Corrected Replacement Preflight Contract

## Objective

Implement and sign the corrected fail-closed replacement-preflight contract
before any dependency installation or model access. The contract must validate
the full installed runtime closure, bind the verified offline cache content,
and make offline AutoProcessor construction a mandatory pre-marker gate while
keeping full policy construction inside the one counted attempt.

## Frozen Inputs

- SmolVLA Gate B entry spec `fb217f3e...` and unchanged Gate B thresholds.
- T20.36h consumed runtime failure `3804eff6...`.
- T20.36i closure audit `0804fd4f...` and T20.36j-A offline resolution
  `8dec69ae...` with cache manifest `6cc7235c...`.
- Reviewer 253's exact owner blocker. No replacement owner grant exists yet.

## Required Work

1. Emit a signed contract binding the exact four-package offline install set,
   verified source artifacts, output paths, ordering invariants, and withheld
   authority.
2. Implement a deterministic installed-distribution closure validator that
   recursively evaluates active `Requires-Dist` edges, version bounds, Python
   markers, distribution metadata hashes, and missing/mismatched packages.
3. Implement a fail-closed AutoProcessor-smoke evidence contract requiring the
   exact local VLM snapshot, offline flags, `local_files_only`, zero network,
   and zero weight/tensor-file reads.
4. Implement the corrected runtime-preflight builder so it cannot sign unless
   the recursive closure passes, cache manifest matches, processor smoke passes,
   owner and central authority identities are present, and no marker/run/result
   exists.
5. Add deterministic tests for missing dependencies, version/marker drift,
   cache aliasing, processor/network/weight-file drift, sequencing, and
   authority escalation.

## Acceptance

- The contract and reusable preflight implementation are deterministic,
  test-covered, same-agent reviewed, and remotely preserved.
- The code makes `environment -> AutoProcessor smoke -> attempt marker -> full
  policy construction` mechanically unavoidable.
- T20.36j remains blocked pending the exact owner decision and live post-install
  preflight execution.

## Prohibited Actions

Package installation, venv/cache mutation, network/download, live
AutoProcessor construction, model/checkpoint access, attempt-marker creation,
replacement execution, inference, optimizer, Gate B change, Gate C, rollout,
hardware, external compute, or Brev.
