# sim-link Closure Note (2026-07-17)

Recorded by Claude at the owner's instruction during the final hour before
full transfer to the sim2claw fork. This note makes the repository safe to
leave: the arc is resolved, evidence is preserved in-repo, open threads are
named, and the only remaining owner decisions are listed.

## The arc, resolved

The question this repository carried from T20.2 (first zero-contact rollout)
through 236+ briefs: **can a learned policy complete the strict unassisted
grasp cycle?** Answer: yes — F0c, executed in the sim2claw fork from the R2
checkpoint this repo produced and diagnosed, passed strict Gate C in 500
updates (~400 s). Checkpoint `8ecf7bb9...`, receipt `9e957708...`, fork main
`f17ba6a`. The closing ledger entry records this; sim-link's own history no
longer ends on "packaged, unresolved."

## Evidence preserved in this final hour

- **F1 Brev workspace archive** (`docs/autonomous-workflow/
  f1-brev-workspace-archive/`, 2.7 MB): the receipt/evaluation/config/script
  bytes whose identities the F1 evidence fold binds previously lived only in
  a Codex scratch workspace. Now in-repo. The selected F1 model artifact
  (step-1000, SHA `75554495...`) remains on the external volume at
  `/Volumes/cerebro/CodexOffload/f1-pi05-r0-20260717/` — external-drive
  location is acceptable; it is a closed negative's checkpoint.

## Open threads that transfer with the team (not with this repo's authority)

- **T19.2c physical calibration**: WCW-1A print package released
  (`release/`), fixture harness verified; a physically printed Actual-Size
  target, fresh permits, and owner presence are still required before any
  motion. All historical permits/markers are consumed and inert.
- **Robo Scan**: first real metric bundle still pending; producer/consumer
  boundary unchanged.
- **Studio track**: separate worktree `../sim-link-studio` (branch
  `studio/app-shell`) remains independent. The live :8790 server audited at
  closure belongs to `/Users/kelly/Developer/so-101-sim`; installed Studio
  app/backend processes point at `sim-link-studio` build products. Both are
  untouched by this repository closure.

## Local state noted at closure

- Deliberately dirty/untracked and left as-is: `.codex/config.toml`
  (owner's agent config), `external/` pinned checkouts (acquisition is
  scripted in the kit), `tmp/` scratch, and one stale Claude worktree
  (`.claude/worktrees/keen-clarke-401502`, detached).
- **Disk cleanup completed and reconciled.** The tier-1 and tier-2 deletion
  had already run under the owner's earlier exact-path authorization before
  this closure note was written. Its preserved audit recorded
  `DELETE_TOTAL_KiB 96967592`: `outputs/` fell from 113 G to 21 G. The targets
  were `so101_desk_cube_sort/{evals,train,datasets,models}`, the generated
  `autolearn/` bulk, closed-negative tensor trees
  `t20_35c_expert_only_run_001`, `t20_35p_terminal_flow_run_001`,
  `t20_35r_full_path_run_001`,
  `t20_35t_time_normalized_standard_replay_run_001`,
  `t20_36_bounded_corrected_coverage_run_001`,
  `t20_36o_bounded_optimizer_run_001`, and
  `t20_44_r2_smolvla_run_001/checkpoints`, all under
  `outputs/robot_lab/`. One tracked `autolearn` receipt was restored after the
  bulk deletion and remains in Git.
- The owner's new go-ahead was audited against the filesystem rather than
  applied to different surviving paths: every tier-1/tier-2 bulk target was
  already absent, so no second destructive operation occurred. Current audit:
  `outputs/` 21 G and 146 GiB filesystem free. Tier 3
  `t20_35x_physical_gate_joint_weighted_run_001` remains deliberately retained
  at 2.6 G. Also retained: `t20_42_r0_generation_run_001`,
  `t20_43c_r2_act_replacement_run_001` (F0c's source checkpoint),
  `t17_5b_raw_store`, SmolVLA `mirrors/` and `rollouts/`, small
  dataset/receipt directories, and `weights/`.

## Remaining owner decision

- **Branch disposition**: `codex/pi05-autolearn-loop` holds the complete
   record and is fully pushed. Recommendation: leave unmerged and archive
   the repository as-is — the fork is the successor; a merge to `main`
   would add nothing but noise. If a single-branch archive is wanted later,
   fast-forward `main` in a quiet moment.

Nothing else remains here. Authorities are consumed or closed, a fresh Brev
inventory is zero, no sim-link-owned cron or background training run exists,
and the fork carries the live doctrine. Two unrelated user crons and the
separately owned Studio surfaces were observed and deliberately left alone.

Future work happens in `/Users/kelly/Developer/sim2claw`.
