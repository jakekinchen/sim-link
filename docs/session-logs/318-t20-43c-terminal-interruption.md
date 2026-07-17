# Session 318 - T20.43c Terminal Interruption

**Date:** 2026-07-16
**Task:** T20.43c / Brief 227
**Reviewer:** 314

## Outcome

The sole T20.43c continuation marker was consumed. Exact zero-update
equivalence passed, the fixed ACT recipe ran through optimizer update 728, and
the partial tree retained checkpoint-500 dual-cadence rollout/mirror evidence.
The process then received SIGINT after a sibling thread acted on the older
same-night scheduling direction. The later overnight direction had already
superseded that cutoff.

This is an inconclusive owner-directive interruption. It is not a trained ACT
negative, an evidence-path infrastructure failure, a Gate C pass, or authority
to retry.

## Signed evidence

| Artifact | Identity SHA-256 | File SHA-256 |
| --- | --- | --- |
| Continuation marker | `e086c293505385d8d85b095d86f993a65266b70abe7047bc83d5bba319d9ed60` | `ba42bc00abe1eabd79e1dca57f05b4d51cb8d534729659b546cd03fa33edf34b` |
| Equivalence receipt | `85087b2ae94d54ea493ec49a10e6a183369b43c6160e73f79205a7624bb65014` | `8f7db4957e63babddd49d9c3599b54bc32485111051c8995a0951f03db89149d` |
| Terminal interruption | `d848a1a8d9c803c0d8782e2c51c102cfd4550f1ca5bf22a629a16f34f834bd68` | `b8f5d245a2a4082e3fc86380afe983a9286bea517ddeb3de2f8b6ad4e44b3aa1` |
| Partial run tree | `e0aea95f9df15e4cc0fb817875d8c887d6b9ece6723b48f029114c18ade169b9` | bound by terminal artifact |

The equivalence receipt records bit-exact tensor values, keys, shapes, and
dtypes; maximum absolute error is zero. AdamW had zero state entries and zero
steps, the sampler had consumed zero batches, and actual T20.43b-schema mirror
dispatch succeeded before update 1.

The terminal artifact binds the complete retained partial tree without copying
its 206 MB checkpoint or multi-megabyte rollout traces into the tracked
closeout. The tree includes checkpoint 500, step-0 and step-500 mirrors, and
step-500 chunk-50/receding-10 rollout evidence.

## Verification

The dedicated verifier reconstructed the three signed artifacts and the local
partial tree, then returned terminal identity `d848a1a8...` with exit code 0:

```text
PYTHONPATH=<pinned Python-3.12 support path>:external/lerobot/src:. \
  external/lerobot/.venv/bin/python \
  scripts/robot_lab/run_t20_43c_act_continuation.py --verify
```

No restart, second continuation, marker rewrite, recipe/gate/data change,
hardware, network, external compute, Brev, physical transfer, or promotion
occurred during closeout. The training lock closes and ACT-on-R0 remains
scientifically unresolved.
