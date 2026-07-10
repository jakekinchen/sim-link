# PI0.5 autolearn ledger

This directory tracks small, reviewable facts about each simulation-learning
cycle. Generated observations, LeRobot datasets, policy-server logs, and model
weights live under ignored `outputs/robot_lab/autolearn/`; they are never added
to Git.

Each real cycle follows the same bounded sequence:

1. evaluate the accepted checkpoint on fixed held-out seeds without task-space
   transfer or recovery;
2. collect controller corrections on a disjoint randomized training seed set;
3. export only expert corrections from policy-visited states;
4. merge corrections with the original causal demonstrations;
5. run a finite fine-tune;
6. evaluate the candidate on the same held-out seeds; and
7. promote only if the candidate meets the pure-policy gate without regression.

The runner refuses dirty learning-loop paths before a real cycle. It commits the
manifest after every stage and commits the accepted-checkpoint pointer only when
the held-out gate passes. A failed or rejected candidate remains in the cycle
manifest but cannot replace the accepted checkpoint.

Validate the full command plan without starting inference or training:

```bash
./.mujoco_venv/bin/python scripts/robot_lab/run_pi05_autolearn_cycle.py \
  --config configurations/robot_lab/pi05_autolearn.example.json \
  --dry-run
```

Remove `--dry-run` only after the configuration, source commit, free disk space,
and expected output paths have been reviewed. The example runs locally on Apple
MPS and does not instantiate or command a physical SO-101 follower.
