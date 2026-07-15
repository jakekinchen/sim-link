from __future__ import annotations

import copy
import hashlib
import unittest

from scenesmith.robot_lab.artifact_contract import sign_payload
from scenesmith.robot_lab.t20_35k_sampler_noise_distribution_audit import (
    build_sampler_noise_distribution_audit,
    extract_sampler_contract,
    verify_sampler_noise_distribution_audit,
)


MODEL_SOURCE = """
class PI05Pytorch:
    def __init__(self, config):
        self.config = config
        self.action_in_proj = nn.Linear(config.max_action_dim, 1024)
        self.action_out_proj = nn.Linear(1024, config.max_action_dim)

    def sample_noise(self, shape, device):
        return torch.normal(mean=0.0, std=1.0, size=shape, dtype=torch.float32, device=device)

    def sample_time(self, bsize, device):
        time_beta = sample_beta(
            self.config.time_sampling_beta_alpha,
            self.config.time_sampling_beta_beta,
            bsize,
            device,
        )
        time = time_beta * self.config.time_sampling_scale + self.config.time_sampling_offset
        return time

    def embed_suffix(self, noisy_actions, timestep):
        action_emb = self.action_in_proj(noisy_actions)
        return action_emb

    def forward(self, images, img_masks, tokens, masks, actions, noise, time):
        time_expanded = time[:, None, None]
        x_t = time_expanded * noise + (1 - time_expanded) * actions
        u_t = noise - actions
        return x_t, u_t

    def sample_actions(self, tokens, noise=None, num_steps=None):
        if num_steps is None:
            num_steps = self.config.num_inference_steps
        bsize = tokens.shape[0]
        device = tokens.device
        if noise is None:
            actions_shape = (bsize, self.config.chunk_size, self.config.max_action_dim)
            noise = self.sample_noise(actions_shape, device)
        dt = -1.0 / num_steps
        x_t = noise
        for step in range(num_steps):
            time = 1.0 + step * dt
            v_t = self.denoise_step(x_t=x_t, timestep=time)
            x_t = x_t + dt * v_t
        return x_t

class PI05Policy:
    def prepare_action(self, batch):
        actions = pad_vector(batch[ACTION], self.config.max_action_dim)
        return actions

    def predict_action_chunk(self, batch):
        actions = self.model.sample_actions([], [], [], [])
        original_action_dim = self.config.output_features[ACTION].shape[0]
        actions = actions[:, :, :original_action_dim]
        return actions

    def forward(self, batch):
        actions = self.prepare_action(batch)
        noise = self.model.sample_noise(actions.shape, actions.device)
        time = self.model.sample_time(actions.shape[0], actions.device)
        losses = self.model.forward([], [], [], [], actions, noise, time)
        original_action_dim = self.config.output_features[ACTION].shape[0]
        losses = losses[:, :, :original_action_dim]
        return losses
"""

CONFIG_SOURCE = """
class PI05Config:
    chunk_size: int = 50
    max_action_dim: int = 32
    num_inference_steps: int = 10
    time_sampling_beta_alpha: float = 1.5
    time_sampling_beta_beta: float = 1.0
    time_sampling_scale: float = 0.999
    time_sampling_offset: float = 0.001
"""


class T2035kSamplerNoiseDistributionAuditTests(unittest.TestCase):
    def test_exact_contract_routes_padded_noise_mask_discriminator(self) -> None:
        contract = extract_sampler_contract(
            model_source=MODEL_SOURCE,
            config_source=CONFIG_SOURCE,
            action_dimension_count=6,
        )
        audit = self._audit(contract)
        verify_sampler_noise_distribution_audit(audit)
        self.assertTrue(audit["default_train_inference_noise_distribution_match"])
        self.assertEqual(audit["supervised_action_dimension_count"], 6)
        self.assertEqual(audit["padded_action_dimension_count"], 26)
        self.assertTrue(audit["stochastic_padded_dimensions_enter_action_projection"])
        self.assertFalse(audit["padded_dimensions_receive_direct_loss"])
        self.assertEqual(
            audit["sampler_classification"],
            "matched_standard_normal_sampler_with_unsupervised_padded_noise_exposure",
        )
        self.assertEqual(
            audit["selected_next_hypothesis"],
            "run_separately_reviewed_active_vs_padded_noise_mask_discriminator",
        )

    def test_mismatch_and_no_padded_exposure_route_fail_closed(self) -> None:
        contract = extract_sampler_contract(
            model_source=MODEL_SOURCE,
            config_source=CONFIG_SOURCE,
            action_dimension_count=6,
        )
        mismatch = copy.deepcopy(contract)
        mismatch["training_uses_same_standard_normal_sampler"] = False
        mismatch_audit = self._audit(mismatch)
        self.assertEqual(
            mismatch_audit["selected_next_hypothesis"],
            "correct_train_inference_noise_distribution_mismatch",
        )
        no_padding = copy.deepcopy(contract)
        no_padding["training_action_padded_to_max_action_dim"] = False
        no_padding["stochastic_padded_dimensions_enter_action_projection"] = False
        no_padding_audit = self._audit(no_padding)
        self.assertEqual(
            no_padding_audit["selected_next_hypothesis"],
            "audit_model_flow_consistency_along_integration_path",
        )

    def test_source_semantic_drift_fails_extraction(self) -> None:
        cases = [
            MODEL_SOURCE.replace("std=1.0", "std=0.5"),
            MODEL_SOURCE.replace("x_t = noise", "x_t = noise * 0.5"),
            MODEL_SOURCE.replace(
                "losses = losses[:, :, :original_action_dim]",
                "losses = losses[:, :, :]",
            ),
            MODEL_SOURCE.replace(
                "actions_shape = (bsize, self.config.chunk_size, self.config.max_action_dim)",
                "actions_shape = (bsize, self.config.chunk_size, 6)",
            ),
        ]
        for source in cases:
            with self.subTest(source_sha=hashlib.sha256(source.encode()).hexdigest()):
                with self.assertRaises(ValueError):
                    extract_sampler_contract(
                        model_source=source,
                        config_source=CONFIG_SOURCE,
                        action_dimension_count=6,
                    )

    def test_invalid_dimensions_lineage_and_result_route_fail(self) -> None:
        with self.assertRaises(ValueError):
            extract_sampler_contract(
                model_source=MODEL_SOURCE,
                config_source=CONFIG_SOURCE,
                action_dimension_count=33,
            )
        contract = extract_sampler_contract(
            model_source=MODEL_SOURCE,
            config_source=CONFIG_SOURCE,
            action_dimension_count=6,
        )
        with self.assertRaises(ValueError):
            build_sampler_noise_distribution_audit(
                t20_35j_result_identity="bad",
                model_source_sha256="2" * 64,
                config_source_sha256="3" * 64,
                contract=contract,
                initial_noise_scale_effect_positive=True,
                gate_b_passed=False,
                selected_initial_noise_scale=0.0,
            )
        nonfinite = copy.deepcopy(contract)
        nonfinite["training_time_scale"] = float("nan")
        with self.assertRaises(ValueError):
            self._audit(nonfinite)
        with self.assertRaises(ValueError):
            build_sampler_noise_distribution_audit(
                t20_35j_result_identity="1" * 64,
                model_source_sha256="2" * 64,
                config_source_sha256="3" * 64,
                contract=contract,
                initial_noise_scale_effect_positive=False,
                gate_b_passed=False,
                selected_initial_noise_scale=0.0,
            )

    def test_signed_derived_and_authority_mutation_fails(self) -> None:
        contract = extract_sampler_contract(
            model_source=MODEL_SOURCE,
            config_source=CONFIG_SOURCE,
            action_dimension_count=6,
        )
        audit = self._audit(contract)
        for field, value in (
            ("padded_action_dimension_count", 0),
            ("gate_b_passed", True),
            ("model_loaded", True),
            ("optimizer_training", True),
        ):
            drift = copy.deepcopy(audit)
            drift[field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    verify_sampler_noise_distribution_audit(sign_payload(drift))

    @staticmethod
    def _audit(contract: dict) -> dict:
        return build_sampler_noise_distribution_audit(
            t20_35j_result_identity="1" * 64,
            model_source_sha256="2" * 64,
            config_source_sha256="3" * 64,
            contract=contract,
            initial_noise_scale_effect_positive=True,
            gate_b_passed=False,
            selected_initial_noise_scale=0.0,
        )


if __name__ == "__main__":
    unittest.main()
