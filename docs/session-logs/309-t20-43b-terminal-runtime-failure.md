# Session Log 309 - T20.43b Terminal Runtime Failure

**Date:** 2026-07-16

## Outcome

The single unchanged ACT replacement attempt was consumed at
`2026-07-16T21:32:02-05:00` and terminated during checkpoint-0 evaluation
before any optimizer update. The terminal boundary is independently verified;
ACT-on-R0 capability remains unresolved.

## Execution chronology

1. Local branch and origin were exact at acceptance commit `a6b2c94...`.
2. Epoch-2 acceptance `c6af1030...` reconstructed and the owner interval was
   active.
3. The runner wrote marker `d67cf38e...` before model/backbone/optimizer work.
4. It constructed fresh ACT and AdamW objects, saved checkpoint 0, and ran the
   first policy-owned chunk-50 simulation rollout.
5. The rollout failed strict-v2 with zero strict-contact frames and
   `0.000304225` mm maximum lift.
6. The required mirror subprocess rejected the T20.43b trace schema. The outer
   fail-closed handler wrote terminal receipt `89b6dbff...`; no training update,
   receding-10 rollout, later checkpoint, result, scorecard, or retention
   artifact was produced.

## Content-addressed evidence

| Evidence | Identity/file SHA-256 |
| --- | --- |
| Attempt marker | identity `d67cf38e7d7a441da93c3af55cdcfeefe64b55ce9cf3f0b95894299a88fdca09`; file `f816fbac541124a4393e0a4d329732965c2e7d0f20c56319fb067cfecd2b8d9b` |
| Terminal failure | identity `89b6dbff17f5da345b1c8d8fa9951989eda092998b702737dd7da16c42db2e92`; file `429431d6f00e9078685184660a3be07b69bc8a5cd9f67c96be86fe6a3bda2cd9` |
| Progress | file `af8e75d048a7653e9393fe8e655941202b2c8dc1f942e4dad0006bc33268ae93` |
| Checkpoint-0 config | file `1b2ba89880e421180962a0c862b37bfc854d16e5f8811e82210a64ecf6d09aaf` |
| Checkpoint-0 model | file `acc865fb2504849ce39a403b08c5bff6b6660460d5622d3089f243c8868cf912` |
| Chunk-50 trace | identity `b707b815ab3b204e29dbbc8e50114307058019da3116f8f5ac496c1b6e05f4bd`; file `0c01265d4536bff9f2220a0e6e26462342b5987927204db7b998f7e50f3eac46` |

The terminal receipt itself binds the four-file local partial tree. Large
checkpoint/trace evidence remains local; only the compact marker and failure
receipt are tracked.

## Root cause and verifier repair

The mirror renderer recognizes original T20.43 and T20.44 trace schemas but
not T20.43b. The reviewed smoke used an original-T20.43 retained trace, so it
did not prove new-schema dispatch. The failure receipt was valid, but the
generic verifier initially assumed `run_summary.json` existed. A deterministic
terminal verification branch now rejects success/failure coexistence and
binds the receipt to the attempt and exact partial tree.

Validation:

- 6 focused T20.43b runner tests pass.
- 35 T20.43/T20.43b/T20.44 regressions pass.
- Live `run_t20_43b_r1_act.py --verify` exits 0 and returns receipt
  `89b6dbff...`.
- Offline Ruff lint/format, compilation, strict JSON, and whitespace pass.

## Authority closeout

No retry, continuation, second replacement, recipe/schedule/threshold change,
T20.45 activation, hardware, camera, serial, physical motion, network,
external compute, Brev, transfer, promotion, or destructive action occurred
or is authorized. The training lock closes with the consumed attempt.
