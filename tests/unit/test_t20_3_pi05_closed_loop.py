import hashlib
import importlib.util
import tempfile
import unittest

from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/robot_lab/run_t20_3_pi05_closed_loop.py"
SPEC = importlib.util.spec_from_file_location("run_t20_3_pi05_closed_loop", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class T20_3PI05ClosedLoopTest(unittest.TestCase):
    def test_training_run_verifier_binds_adapter_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            adapter = Path(directory)
            model = adapter / "adapter_model.safetensors"
            config = adapter / "adapter_config.json"
            model.write_bytes(b"adapter")
            config.write_bytes(b"config")
            digest = hashlib.sha256(b"adapter").hexdigest()
            config_digest = hashlib.sha256(b"config").hexdigest()
            summary = {
                "task_id": "T20.3",
                "simulation_policy_accepted": False,
                "adapter": {
                    "checkpoint_files": {
                        "adapter/adapter_config.json": {"sha256": config_digest},
                        "adapter/adapter_model.safetensors": {"sha256": digest},
                    }
                },
            }
            MODULE._verify_training_run(summary, adapter)
            model.write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "adapter_model.safetensors hash drifted"):
                MODULE._verify_training_run(summary, adapter)

    def test_snapshot_root_is_revision_addressed(self) -> None:
        path = MODULE._snapshot_root("org/model", "abc")
        self.assertTrue(str(path).endswith("models--org--model/snapshots/abc"))


if __name__ == "__main__":
    unittest.main()
