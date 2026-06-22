#!/usr/bin/env python3
"""
Evaluation script for trained CARLA RL agents.

Usage:
    # Evaluate with mock environment
    python scripts/evaluate.py --model models/ppo_mock_20240101_120000 --mock

    # Evaluate with CARLA simulator
    python scripts/evaluate.py --model models/ppo_carla_20240101_120000
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

from carla_rl.envs.mock_carla_env import MockCarlaRLEnv


def evaluate_mock(model_path: str, n_episodes: int = 10, render: bool = False):
    """Evaluate with mock environment."""
    print("=" * 60)
    print("Evaluating Model (Mock Environment)")
    print("=" * 60)

    # Create environment
    env = MockCarlaRLEnv(
        target_speed=30.0,
        max_steps=500,
        render_mode="rgb_array" if render else None,
    )

    # Load model
    model = PPO.load(model_path)
    print(f"Loaded model from: {model_path}")

    # Evaluate
    mean_reward, std_reward = evaluate_policy(
        model,
        env,
        n_eval_episodes=n_episodes,
        deterministic=True,
    )

    print(f"\nResults over {n_episodes} episodes:")
    print(f"  Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

    # Run one episode with detailed logging
    print("\nDetailed episode run:")
    obs, info = env.reset()
    total_reward = 0
    steps = 0

    while True:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1

        if steps % 100 == 0:
            print(f"  Step {steps}: speed={info['speed']:.1f} km/h, "
                  f"dist_center={info['dist_to_center']:.2f} m")

        if terminated or truncated:
            break

    print(f"\nEpisode finished:")
    print(f"  Steps: {steps}")
    print(f"  Total reward: {total_reward:.2f}")
    print(f"  Final speed: {info['speed']:.1f} km/h")
    print(f"  Distance traveled: {info['total_distance']:.1f} m")
    print(f"  Collision: {info['collision']}")

    env.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained CARLA RL agent")
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock environment",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=10,
        help="Number of evaluation episodes",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render environment",
    )
    args = parser.parse_args()

    if args.mock:
        evaluate_mock(args.model, args.episodes, args.render)
    else:
        print("CARLA evaluation requires running CARLA simulator.")
        print("Use --mock flag for mock environment evaluation.")


if __name__ == "__main__":
    main()
