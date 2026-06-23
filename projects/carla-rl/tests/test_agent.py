"""
Tests for PPOTrainer.

Focuses on initialization, hyperparameters, training, prediction,
save/load, and evaluation using the MockCarlaRLEnv (no CARLA needed).
"""

import numpy as np
import pytest
from pathlib import Path

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv
from carla_rl.agents.ppo_agent import PPOTrainer


def _make_trainer(**kwargs):
    """Helper to create a PPOTrainer with sensible test defaults."""
    defaults = dict(
        env_class=MockCarlaRLEnv,
        env_kwargs={"max_steps": 50, "seed": 42},
        policy="MultiInputPolicy",
        n_steps=32,
        batch_size=16,
        n_epochs=2,
        verbose=0,
        seed=42,
    )
    defaults.update(kwargs)
    return PPOTrainer(**defaults)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestPPOTrainerInit:
    """Trainer construction tests."""

    def test_model_created(self):
        trainer = _make_trainer()
        assert trainer.model is not None
        trainer.close()

    def test_envs_created(self):
        trainer = _make_trainer()
        assert trainer.env is not None
        assert trainer.eval_env is not None
        trainer.close()

    def test_default_hyperparameters(self):
        trainer = _make_trainer()
        params = trainer.get_hyperparameters()
        assert params["learning_rate"] == pytest.approx(3e-4)
        assert params["gamma"] == pytest.approx(0.99)
        assert params["gae_lambda"] == pytest.approx(0.95)
        assert params["clip_range"] == pytest.approx(0.2)
        trainer.close()

    def test_custom_hyperparameters(self):
        trainer = _make_trainer(
            learning_rate=1e-4,
            gamma=0.95,
            ent_coef=0.01,
            vf_coef=0.3,
        )
        params = trainer.get_hyperparameters()
        assert params["learning_rate"] == pytest.approx(1e-4)
        assert params["gamma"] == pytest.approx(0.95)
        assert params["ent_coef"] == pytest.approx(0.01)
        assert params["vf_coef"] == pytest.approx(0.3)
        trainer.close()

    def test_policy_stored(self):
        trainer = _make_trainer(policy="MultiInputPolicy")
        assert trainer.policy == "MultiInputPolicy"
        trainer.close()

    def test_n_envs_stored(self):
        trainer = _make_trainer(n_envs=1)
        assert trainer.n_envs == 1
        trainer.close()


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


class TestPPOTrainerTraining:
    """Training loop tests."""

    def test_train_returns_dict(self):
        trainer = _make_trainer()
        result = trainer.train(total_timesteps=64)
        assert isinstance(result, dict)
        assert "total_timesteps" in result
        assert "model" in result
        trainer.close()

    def test_train_timesteps_match(self):
        trainer = _make_trainer()
        result = trainer.train(total_timesteps=128)
        assert result["total_timesteps"] == 128
        trainer.close()

    def test_train_with_checkpoint(self, tmp_path):
        trainer = _make_trainer()
        save_dir = str(tmp_path / "ckpts")
        trainer.train(total_timesteps=64, save_freq=32, save_path=save_dir)
        # Checkpoint files should exist
        ckpt_dir = Path(save_dir)
        assert ckpt_dir.exists()
        trainer.close()

    def test_train_minimum_steps(self):
        """Should be able to train with very few timesteps."""
        trainer = _make_trainer()
        result = trainer.train(total_timesteps=32)
        assert result["total_timesteps"] == 32
        trainer.close()


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


class TestPPOTrainerPredict:
    """Action prediction tests."""

    def test_predict_shape(self):
        trainer = _make_trainer()
        obs = trainer.env.reset()  # VecEnv reset returns obs only
        action = trainer.predict(obs)
        assert action.shape == (1, 2) or action.shape == (2,)
        trainer.close()

    def test_predict_bounds(self):
        trainer = _make_trainer()
        obs = trainer.env.reset()
        action = trainer.predict(obs)
        flat = action.flatten()
        assert np.all(flat >= -1.0 - 1e-5)
        assert np.all(flat <= 1.0 + 1e-5)
        trainer.close()

    def test_predict_deterministic_consistent(self):
        """Same observation + deterministic should give same action."""
        trainer = _make_trainer()
        obs = trainer.env.reset()
        a1 = trainer.predict(obs, deterministic=True)
        a2 = trainer.predict(obs, deterministic=True)
        np.testing.assert_array_almost_equal(a1, a2)
        trainer.close()

    def test_predict_after_training(self):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        obs = trainer.env.reset()
        action = trainer.predict(obs)
        assert action is not None
        trainer.close()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class TestPPOTrainerEvaluate:
    """Evaluation tests."""

    def test_evaluate_returns_metrics(self):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        results = trainer.evaluate(n_episodes=2)
        assert "mean_reward" in results
        assert "std_reward" in results
        assert isinstance(results["mean_reward"], float)
        assert isinstance(results["std_reward"], float)
        trainer.close()

    def test_evaluate_std_non_negative(self):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        results = trainer.evaluate(n_episodes=2)
        assert results["std_reward"] >= 0.0
        trainer.close()


# ---------------------------------------------------------------------------
# Save / Load
# ---------------------------------------------------------------------------


class TestPPOTrainerSaveLoad:
    """Model persistence tests."""

    def test_save_creates_file(self, tmp_path):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        path = str(tmp_path / "model")
        trainer.save(path)
        assert Path(path + ".zip").exists()
        trainer.close()

    def test_load_restores_model(self, tmp_path):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        path = str(tmp_path / "model")
        trainer.save(path)
        trainer.load(path)
        assert trainer.model is not None
        trainer.close()

    def test_save_creates_directory(self, tmp_path):
        trainer = _make_trainer()
        trainer.train(total_timesteps=64)
        path = str(tmp_path / "subdir" / "deep" / "model")
        trainer.save(path)
        assert Path(path + ".zip").exists()
        trainer.close()


# ---------------------------------------------------------------------------
# Multi-env
# ---------------------------------------------------------------------------


class TestPPOTrainerMultiEnv:
    """Tests with multiple parallel environments."""

    def test_two_envs(self):
        try:
            trainer = _make_trainer(n_envs=2)
        except (TypeError, RuntimeError):
            pytest.skip("SubprocVecEnv not supported in this environment")
        trainer.train(total_timesteps=64)
        trainer.close()

    def test_two_envs_predict(self):
        try:
            trainer = _make_trainer(n_envs=2)
        except (TypeError, RuntimeError):
            pytest.skip("SubprocVecEnv not supported in this environment")
        trainer.train(total_timesteps=64)
        obs = trainer.env.reset()
        action = trainer.predict(obs)
        assert action is not None
        trainer.close()


# ---------------------------------------------------------------------------
# Integration: full loop
# ---------------------------------------------------------------------------


class TestPPOTrainerIntegration:
    """End-to-end integration tests."""

    def test_full_loop(self, tmp_path):
        trainer = _make_trainer(
            env_kwargs={"max_steps": 30, "seed": 42},
            n_steps=32,
            batch_size=16,
            n_epochs=2,
        )

        # Train
        train_result = trainer.train(total_timesteps=64)
        assert train_result["total_timesteps"] == 64

        # Evaluate
        eval_result = trainer.evaluate(n_episodes=2)
        assert "mean_reward" in eval_result

        # Save & load
        path = str(tmp_path / "final_model")
        trainer.save(path)
        trainer.load(path)

        # Predict
        obs = trainer.env.reset()
        action = trainer.predict(obs)
        assert action is not None

        trainer.close()
