from __future__ import annotations
import copy, unittest
from scenesmith.robot_lab.artifact_contract import load_strict_json, sign_payload
from scenesmith.robot_lab.normalization_bundle import BUNDLE_PATH, CAMERA_ORDER, REPO_ROOT, build_normalization_bundle, verify_normalization_bundle
class NormalizationBundleTests(unittest.TestCase):
 def setUp(self): self.payload=load_strict_json(REPO_ROOT/BUNDLE_PATH)
 def test_checked_bundle_is_deterministic(self):
  verify_normalization_bundle(self.payload,repo_root=REPO_ROOT); self.assertEqual(self.payload,build_normalization_bundle(repo_root=REPO_ROOT)); self.assertFalse(self.payload["production_eligible"]); self.assertFalse(self.payload["simulation_training_ready"])
 def test_feature_and_camera_order_are_pinned(self):
  self.assertEqual(len(self.payload["feature_order"]),6); self.assertEqual(self.payload["preprocessing"]["camera_order"],list(CAMERA_ORDER))
 def test_statistics_are_complete_and_finite(self):
  for values in self.payload["normalization"]["statistics"].values(): self.assertEqual(len(values),6); self.assertTrue(all(isinstance(value,(int,float)) for value in values))
  self.assertTrue(all(value>0 for value in self.payload["normalization"]["statistics"]["std"]))
 def test_actual_processor_parity_is_fixture_scoped(self):
  self.assertTrue(self.payload["actual_cached_processor_executed"]); self.assertFalse(self.payload["model_call_executed"]); self.assertIn("fixture",self.payload["scope"])
 def test_resigned_mode_drift_is_rejected(self):
  value=copy.deepcopy(self.payload); value["normalization"]["mode"]="QUANTILES"; value=sign_payload(value)
  with self.assertRaisesRegex(ValueError,"drifted"): verify_normalization_bundle(value,repo_root=REPO_ROOT)
 def test_resigned_source_drift_is_rejected(self):
  value=copy.deepcopy(self.payload); value["source_refs"]["canonical_processor"]["identity_sha256"]="0"*64; value=sign_payload(value)
  with self.assertRaisesRegex(ValueError,"linkage drifted"): verify_normalization_bundle(value,repo_root=REPO_ROOT)
if __name__=="__main__": unittest.main()
