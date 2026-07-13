# Session 114 - Private Current-Frame Retention

**Date:** 2026-07-13

Brief 084 corrects the experiment-derived blocker that the accepted static-pose
session retained camera hashes but discarded the exact current pixel bytes. The
pinned camera now copies each frame into a session-private sink only after its
receive metadata passes. The successful-session boundary emits private-success
v2 only after the complete candidate, camera audits, release, and holder cleanup
pass.

The v2 bundle contains exactly two ordered PNG frames for each of the two exact
stable camera identities. Its verifier requires strict canonical base64, a
finite per-frame byte limit, exact PNG parsing, dimensions, channels, encoding,
frame hashes, aggregate counts, and byte totals against the hash-only candidate
result. Candidate results, receipts, and tracked redacted manifests remain
pixel-free. Legacy v1 success verification and immutable paths are unchanged.

Verification passed 183 focused tests in each pinned runtime and 382 broad
authority/twin tests in 121.863 seconds. Both source verifiers pass in both
runtimes, and the real accepted v1 private success `97eb44b3...` continues to
verify in both. Compilation, workflow, JSON, privacy, and diff checks pass. No
hardware, camera, model, preprocessing, inference, MuJoCo replay, motion,
training, Brev, or paid compute ran in this slice.
