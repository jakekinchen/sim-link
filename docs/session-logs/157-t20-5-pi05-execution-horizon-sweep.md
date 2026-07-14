# Executor Session 157 - T20.5 PI0.5 Execution-Horizon Sweep

T20.5 parameterized only PI0.5's executed action horizon while fixing the
T20.4 500-update adapter, held-out and inference seeds, ten denoising steps,
prompt, processor, coordinates, scene, and strict proof gates.

Fresh horizon-5, horizon-10, and horizon-15 rollouts recorded one initial reset
and 49, 25, and 17 queue refills. Their action-sequence hashes are distinct.
Every 244-frame rollout nevertheless made zero strict-v2 contacts and lifted
only 0.00000030070669393422733 m against the 0.025 m threshold. Every artifact
contains five 256 px keyframes, measured gate margins, zero assist frames, and
zero action projections.

Thirty relevant horizon, evidence, authority, coordinate, and strict-grasp
tests passed. No optimizer, hardware, network, external compute, or Brev was
used. T20.5 closes as a verified negative: queue duration does not explain the
low-loss policy's failure to reach contact.
