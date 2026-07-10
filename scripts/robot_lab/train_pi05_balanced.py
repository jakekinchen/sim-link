#!/usr/bin/env python3
"""Run LeRobot training with a finite, audited SceneSmith replay plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--replay-plan", type=Path, required=True)
    parser.add_argument("--replay-audit", type=Path, required=True)
    args, remaining = parser.parse_known_args()

    from scenesmith.robot_lab.balanced_replay import AuditedReplaySampler

    plan = json.loads(args.replay_plan.read_text(encoding="utf-8"))
    expected_frames = int(plan["dataset_total_frames"])
    dataset_root = _dataset_root(remaining)
    contract_path = dataset_root / "scenesmith_pi05_dataset_contract.json"
    contract_sha256 = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    if contract_sha256 != plan["dataset_contract_sha256"]:
        raise ValueError("Replay plan dataset contract does not match training dataset")
    if any(not 0 <= int(index) < expected_frames for index in plan["sample_indices"]):
        raise ValueError("Replay plan contains an out-of-range sample index")
    import torch

    original_dataloader = torch.utils.data.DataLoader
    state = {"replaced": False}

    class BalancedDataLoader(original_dataloader):
        def __init__(self, dataset, *loader_args, **loader_kwargs):
            sampler = loader_kwargs.get("sampler")
            if not state["replaced"] and sampler is not None and len(dataset) == expected_frames:
                loader_kwargs["sampler"] = AuditedReplaySampler(plan, args.replay_audit)
                loader_kwargs["shuffle"] = False
                state["replaced"] = True
            super().__init__(dataset, *loader_args, **loader_kwargs)

    torch.utils.data.DataLoader = BalancedDataLoader
    sys.argv = [sys.argv[0], *remaining]
    from lerobot.scripts.lerobot_train import train

    train()
    if not state["replaced"]:
        raise RuntimeError("Balanced replay sampler was not installed")
    realized_draws = len(args.replay_audit.read_text(encoding="utf-8").splitlines())
    if realized_draws != len(plan["sample_indices"]):
        raise RuntimeError(
            f"Replay audit recorded {realized_draws} draws; expected {len(plan['sample_indices'])}"
        )
    return 0


def _dataset_root(argv: list[str]) -> Path:
    prefix = "--dataset.root="
    values = [argument[len(prefix) :] for argument in argv if argument.startswith(prefix)]
    if len(values) != 1:
        raise ValueError("Balanced training requires exactly one --dataset.root argument")
    return Path(values[0])


if __name__ == "__main__":
    raise SystemExit(main())
