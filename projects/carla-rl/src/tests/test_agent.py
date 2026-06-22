"""
Tests for the PPO Agent.
"""

import sys
import numpy as np
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv
from carla_rl.agents.ppo_agent import PPOTrainer


class TestPPOTrainer:
    """Test suite for PPOTrainer."""

    def test_init(self):
        """Test trainer initialization."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_steps=32,
            batch_size=16,
            verbose=0,
            seed=42,
        )

        assert trainer.model is not None
        assert trainer.env is not None
        assert trainer.eval_env is not None

        trainer.close()

    def test_hyperparameters(self):
        """Test hyperparameter storage."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            learning_rate=1e-4,
            n_steps=128,
            batch_size=32,
            n_epochs=5,
            gamma=0.95,
            verbose=0,
            seed=42,
        )

        params = trainer.get_hyperparameters()

        assert params["learning_rate"] == 1e-4
        assert params["n_steps"] == 128
        assert params["batch_size"] == 32
        assert params["n_epochs"] == 5
        assert params["gamma"] == 0.95

        trainer.close()

    def test_train_short(self):
        """Test short training run."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_steps=32,
            batch_size=16,
            n_epochs=2,
            verbose=0,
            seed=42,
        )

        result = trainer.train(total_timesteps=64)

        assert "total_timesteps" in result
        assert "model" in result
        assert result["total_timesteps"] == 64

        trainer.close()

    def test_predict(self):
        """Test action prediction."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_steps=32,
            batch_size=16,
            verbose=0,
            seed=42,
        )

        # Get initial observation
        obs, _ = trainer.env.reset()

        # Predict action
        action = trainer.predict(obs)

        assert isinstance(action, np.ndarray)
        assert action.shape == (2,)
        assert -1.0 <= action[0] <= 1.0
        assert -1.0 <= action[1] <= 1.0

        trainer.close()

    def test_save_load(self, tmp_path):
        """Test model save and load."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_steps=32,
            batch_size=16,
            verbose=0,
            seed=42,
        )

        # Train a bit
        trainer.train(total_timesteps=64)

        # Save
        save_path = str(tmp_path / "test_model")
        trainer.save(save_path)

        # Verify files exist
        assert Path(save_path + ".zip").exists()

        # Load
        trainer.load(save_path)

        trainer.close()

    def test_evaluate(self):
        """Test evaluation."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_steps=32,
            batch_size=16,
            verbose=0,
            seed=42,
        )

        # Train a bit first
        trainer.train(total_timesteps=64)

        # Evaluate
        results = trainer.evaluate(n_episodes=2)

        assert "mean_reward" in results
        assert "std_reward" in results
        assert isinstance(results["mean_reward"], float)
        assert isinstance(results["std_reward"], float)

        trainer.close()


class TestPPOTrainerIntegration:
    """Integration tests for PPO trainer."""

    def test_full_training_loop(self):
        """Test a complete training loop."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 100, "seed": 42},
            policy="MlpPolicy",
            learning_rate=3e-4,
            n_steps=64,
            batch_size=32,
            n_epochs=2,
            gamma=0.99,
            verbose=0,
            seed=42,
        )

        # Train
        result = trainer.train(total_timesteps=128)

        # Evaluate
        eval_results = trainer.evaluate(n_episodes=2)

        # Predict
        obs, _ = trainer.env.reset()
        action = trainer.predict(obs)

        assert action.shape == (2,)

        trainer.close()

    def test_multiple_envs(self):
        """Test with multiple environments."""
        trainer = PPOTrainer(
            env_class=MockCarlaRLEnv,
            env_kwargs={"max_steps": 50, "seed": 42},
            n_envs=2,
            n_steps=32,
            batch_size=16,
            verbose=0,
            seed=42,
        )

        # Train
        trainer.train(total_timesteps=64)

        trainer.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
