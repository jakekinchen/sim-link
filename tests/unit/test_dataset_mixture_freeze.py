"""Tests for deterministic, reference-only T18.5 manifests."""
from __future__ import annotations
import copy, subprocess, unittest
from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.dataset_mixture_freeze import REPO_ROOT, build_manifests, verify_manifests
class DatasetMixtureFreezeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.mixture,cls.inputs=build_manifests()
 def test_deterministic_frozen_reference_only_manifests(self):
  verify_manifests(self.mixture,self.inputs);self.assertEqual(self.mixture['window_count'],192);self.assertEqual(self.mixture['correction_window_count'],0);self.assertTrue(self.mixture['dataset_mixture_frozen']);self.assertFalse(self.inputs['training_eligible'])
 def test_drift_privilege_and_authority_are_rejected(self):
  for field,value,message in [('dataset_mixture_frozen',False,'not frozen'),('optimizer_training',True,'authority flag'),('correction_window_count',1,'correction accounting')]:
   bad=copy.deepcopy(self.mixture);bad[field]=value
   with self.assertRaisesRegex(ValueError,message):verify_manifests(sign_payload(bad),self.inputs)
  leak=copy.deepcopy(self.inputs);leak['privileged_fields_available_to_actor']=True
  with self.assertRaisesRegex(ValueError,'exposes privileged'):verify_manifests(self.mixture,sign_payload(leak))
  absent=copy.deepcopy(self.mixture);absent['mixture_rows'][0]['window_id']='0'*64
  with self.assertRaisesRegex(ValueError,'drifted'):verify_manifests(sign_payload(absent),self.inputs)
 def test_rewrite_is_refused(self):
  r=subprocess.run([str(REPO_ROOT/'.mujoco_venv/bin/python'),str(REPO_ROOT/'scripts/robot_lab/write_dataset_mixture_freeze.py'),'--rewrite'],cwd=REPO_ROOT,capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('immutable',r.stderr)
if __name__=='__main__':unittest.main()
