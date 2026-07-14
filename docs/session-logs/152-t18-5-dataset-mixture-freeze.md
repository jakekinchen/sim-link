# Executor Session 152 - T18.5 Dataset-Mixture Freeze

T18.5 freezes a reference-only 192-window, zero-correction composition and its
training-input references. The manifests retain the four allowed actor fields
and five named action variants; no observation/action bytes are materialized.
Writer replay, focused tests, and the relevant regression suite passed. Training
lock, model, inference, optimizer, physical, external compute, and Brev remain
closed or false.
