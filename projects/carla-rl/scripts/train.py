#!/usr/bin/env python3
"""
Training script for CARLA RL.

Usage:
    # Train with mock environment (no CARLA needed)
    python scripts/train.py --mock

    # Train with CARLA simulator
    python scripts/train.py --host localhost --port 2000

    # Train with custom config
    python scripts/train.py --config configs/mock.yaml
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
import numpy as np
from datetime import datetime

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv
from carla_rl.agents.ppo_agent import PPOTrainer


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def train_mock(config: dict, args):
    """Train with mock environment."""
    print("=" * 60)
    print("CARLA RL Training (Mock Environment)")
    print("=" * 60)

    # Environment kwargs
    env_kwargs = {
        "target_speed": config["env"]["target_speed"],
        "max_steps": config["env"]["max_steps"],
        "road_width": config["env"].get("road_width", 8.0),
        "use_camera": config["env"]["use_camera"],
        "image_size": tuple(config["env"]["image_size"]),
        "reward_weights": config["reward"],
        "seed": args.seed,
    }

    # Create trainer
    trainer = PPOTrainer(
        env_class=MockCarlaRLEnv,
        env_kwargs=env_kwargs,
        policy=config["ppo"]["policy"],
        learning_rate=config["ppo"]["learning_rate"],
        n_steps=config["ppo"]["n_steps"],
        batch_size=config["ppo"]["batch_size"],
        n_epochs=config["ppo"]["n_epochs"],
        gamma=config["ppo"]["gamma"],
        gae_lambda=config["ppo"]["gae_lambda"],
        clip_range=config["ppo"]["clip_range"],
        ent_coef=config["ppo"]["ent_coef"],
        vf_coef=config["ppo"]["vf_coef"],
        max_grad_norm=config["ppo"]["max_grad_norm"],
        n_envs=config["ppo"]["n_envs"],
        seed=args.seed,
        device=config["ppo"]["device"],
        tensorboard_log=config["training"]["tensorboard_log"],
        verbose=config["logging"]["verbose"],
    )

    # Train
    total_timesteps = args.timesteps or config["training"]["total_timesteps"]
    print(f"\nTraining for {total_timesteps} timesteps...")

    result = trainer.train(
        total_timesteps=total_timesteps,
        eval_freq=config["training"]["eval_freq"],
        n_eval_episodes=config["training"]["n_eval_episodes"],
        save_freq=config["training"]["save_freq"],
        save_path=config["training"]["save_path"],
    )

    # Evaluate
    print("\nEvaluating trained agent...")
    eval_results = trainer.evaluate(n_episodes=10)

    # Save final model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"models/ppo_mock_{timestamp}"
    trainer.save(save_path)

    print(f"\nFinal model saved to: {save_path}")
    print(f"Evaluation results: {eval_results}")

    # Cleanup
    trainer.close()

    return eval_results


def train_carla(config: dict, args):
    """Train with CARLA simulator."""
    print("=" * 60)
    print("CARLA RL Training (CARLA Simulator)")
    print("=" * 60)

    try:
        from carla_rl.envs.carla_env import CarlaRLEnv
    except ImportError:
        print("ERROR: CARLA Python API not available.")
        print("Please ensure CARLA simulator is installed and running.")
        print("Use --mock flag to train with mock environment instead.")
        sys.exit(1)

    # Environment kwargs
    env_kwargs = {
        "host": args.host,
        "port": args.port,
        "town": config["env"]["town"],
        "vehicle_model": config["env"]["vehicle_model"],
        "target_speed": config["env"]["target_speed"],
        "max_steps": config["env"]["max_steps"],
        "use_camera": config["env"]["use_camera"],
        "image_size": tuple(config["env"]["image_size"]),
        "reward_weights": config["reward"],
        "seed": args.seed,
    }

    # Create trainer
    trainer = PPOTrainer(
        env_class=CarlaRLEnv,
        env_kwargs=env_kwargs,
        policy=config["ppo"]["policy"],
        learning_rate=config["ppo"]["learning_rate"],
        n_steps=config["ppo"]["n_steps"],
        batch_size=config["ppo"]["batch_size"],
        n_epochs=config["ppo"]["n_epochs"],
        gamma=config["ppo"]["gamma"],
        gae_lambda=config["ppo"]["gae_lambda"],
        clip_range=config["ppo"]["clip_range"],
        ent_coef=config["ppo"]["ent_coef"],
        vf_coef=config["ppo"]["vf_coef"],
        max_grad_norm=config["ppo"]["max_grad_norm"],
        n_envs=config["ppo"]["n_envs"],
        seed=args.seed,
        device=config["ppo"]["device"],
        tensorboard_log=config["training"]["tensorboard_log"],
        verbose=config["logging"]["verbose"],
    )

    # Train
    total_timesteps = args.timesteps or config["training"]["total_timesteps"]
    print(f"\nTraining for {total_timesteps} timesteps...")

    result = trainer.train(
        total_timesteps=total_timesteps,
        eval_freq=config["training"]["eval_freq"],
        n_eval_episodes=config["training"]["n_eval_episodes"],
        save_freq=config["training"]["save_freq"],
        save_path=config["training"]["save_path"],
    )

    # Evaluate
    print("\nEvaluating trained agent...")
    eval_results = trainer.evaluate(n_episodes=10)

    # Save final model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"models/ppo_carla_{timestamp}"
    trainer.save(save_path)

    print(f"\nFinal model saved to: {save_path}")
    print(f"Evaluation results: {eval_results}")

    # Cleanup
    trainer.close()

    return eval_results


def main():
    parser = argparse.ArgumentParser(description="Train CARLA RL agent")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock environment (no CARLA needed)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML file",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="CARLA server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=2000,
        help="CARLA server port",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=None,
        help="Total training timesteps (overrides config)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    args = parser.parse_args()

    # Load config
    if args.config:
        config = load_config(args.config)
    elif args.mock:
        config_path = Path(__file__).parent.parent / "configs" / "mock.yaml"
        config = load_config(str(config_path))
    else:
        config_path = Path(__file__).parent.parent / "configs" / "default.yaml"
        config = load_config(str(config_path))

    # Create output directories
    os.makedirs("models", exist_ok=True)
    os.makedirs(config["training"]["save_path"], exist_ok=True)
    os.makedirs(config["training"]["tensorboard_log"], exist_ok=True)

    # Run training
    if args.mock:
        results = train_mock(config, args)
    else:
        results = train_carla(config, args)

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
