# Executor Session 168 - T20.15 State/Action Normalizer Ablation

T20.15 loaded the T20.14 checkpoint and exact seed-2 source frame zero on local
MPS, then crossed checkpoint/dataset state preprocessing with
checkpoint/dataset action postprocessing. The checkpoint's serialized pipeline
was deep-copied and only the targeted state or action statistics entry was
replaced. All other processor statistics remained identical.

Four common-seed calls produced byte-identical normalized output within each
repeated state condition. The dataset/dataset cell reproduced T20.14 exactly.
Checkpoint state plus checkpoint action scaling retained 0.03088 rad arm MAE
but 0.75430 rad gripper error. Changing only action postprocessing raised arm
MAE to 0.96656 rad while reducing gripper error to 0.12015 rad. Changing only
state preprocessing raised arm MAE to 0.22802 rad and gripper error to 0.84713
rad.

Action postprocessing contributed 0.95872 rad mean absolute arm displacement,
versus 0.23586 for state preprocessing and 0.26037 interaction, a 3.682x
dominance ratio. This selects a no-training hybrid hypothesis: checkpoint state
and arm scaling with dataset-derived gripper-only unnormalization.

The signed identity is `5c618860...`, file hash `34c6da7c...`, and 42 focused
tests pass. There were four model calls, zero optimizer steps, zero simulator
steps, and no hardware, external compute, or Brev.
