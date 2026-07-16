# Reviewer Decision 247 - Verify T20.36f Decode Localization Pre-Run

**Decision:** `VERIFY_PRE_RUN_OPEN_ONE_CHECKPOINT_DECODE_AUDIT_AFTER_REMOTE`

## Reviewed Boundary

Brief 197; T20.36e frozen source artifacts and ignored checkpoint files;
implementation `489be59`; central decision `de30947f...`; model-free preflight
`40e24b5e...`; one-use permit `d9daae7b...`; 41 T20.36 tests; complete scoped
diff; and branch/remote state.

## Adversarial Findings

- Source result, run, final evaluation, objective, five-repeat action hash, and
  checkpoint identity are exact constants. Any mismatch stops interpretation.
- Preflight rehashes the config and safe tensor without parsing tensor content;
  it binds MPS, dependencies, free disk, stack identity, and remote source.
- The marker must precede ACT model import, checkpoint tensor read, model load,
  and inference. Current attempt and result paths are absent.
- The permit authorizes one model load plus inference. Optimizer creation,
  training, retry, second audit, policy selection, and gate changes are false.
- The result requires the final objective within `1e-7`, all five queued hashes
  plus the direct hash equal to `ecaa2e4c...`, and direct/queue physical error
  within `1e-7` rad before per-joint evidence is accepted.
- Joint/time summaries cross-check their global maximum, predicted-target
  difference, region maximum, and exceedance counts. Non-finite or inconsistent
  evidence fails closed.
- Result routing cannot authorize SmolVLA, Gate B amendment, Gate C, rollout,
  policy acceptance, hardware, external compute, or Brev.

## Disposition

Verify the pre-run boundary. After this decision and its signed authority,
preflight, and permit are committed and confirmed on origin, execute exactly
one checkpoint decode audit and preserve its result. Do not retry.

## Withheld Authority

No optimizer, training, retry, second inference attempt, policy selection,
SmolVLA entry, Gate B change, Gate C, rollout, hardware, external compute, or
Brev.
