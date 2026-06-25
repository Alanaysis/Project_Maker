"""Main script demonstrating Q-Learning algorithms.

This script shows how to use different RL algorithms on various environments.
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.grid_world import GridWorld
from src.q_learning import QLearningAgent
from src.sarsa import SarsaAgent, ExpectedSarsaAgent, SarsaConfig
from src.double_q_learning import DoubleQLearningAgent
from src.environments import FrozenLake, Maze
from src.visualization import (
    visualize_training,
    visualize_policy,
    visualize_q_table_heatmap,
    visualize_learning_curves,
    visualize_strategy_comparison,
)


def demo_grid_world():
    """Demonstrate Q-Learning on GridWorld."""
    print("=" * 60)
    print("DEMO: Q-Learning on GridWorld")
    print("=" * 60)
    print()

    # Create environment
    env = GridWorld(
        rows=5,
        cols=5,
        start=(0, 0),
        goal=(4, 4),
        walls=[(1, 1), (2, 2), (3, 1)],
        traps=[(3, 3)],
        seed=42,
    )

    print("Environment:")
    print(env.render())
    print()

    # Create and train agent
    agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        seed=42,
    )

    print("Training Q-Learning agent...")
    result = agent.train(env, n_episodes=500, max_steps=100, verbose=True)
    print()

    # Visualize training
    print(visualize_training(result.episode_rewards, result.episode_steps))

    # Get and visualize policy
    policy = agent.get_policy(env)
    print(visualize_policy(
        env.grid, policy,
        env.start.to_tuple(), env.goal.to_tuple(),
        "Q-Learning Policy"
    ))

    # Evaluate
    metrics = agent.evaluate(env, n_episodes=100)
    print(f"\nEvaluation Results:")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Mean Reward: {metrics['mean_reward']:.1f}")
    print(f"  Mean Steps: {metrics['mean_steps']:.1f}")


def demo_sarsa_comparison():
    """Compare Q-Learning, Sarsa, and Expected Sarsa."""
    print("\n" + "=" * 60)
    print("DEMO: Algorithm Comparison")
    print("=" * 60)
    print()

    # Create environment
    env = GridWorld(
        rows=5,
        cols=5,
        start=(0, 0),
        goal=(4, 4),
        walls=[(1, 1), (2, 2), (3, 1)],
        traps=[(3, 3)],
        seed=42,
    )

    # Q-Learning
    print("Training Q-Learning...")
    q_agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        seed=42,
    )
    q_result = q_agent.train(env, n_episodes=300, max_steps=100)
    q_metrics = q_agent.evaluate(env, n_episodes=50)

    # Sarsa
    print("Training Sarsa...")
    config = SarsaConfig(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        seed=42,
    )
    sarsa_agent = SarsaAgent(config)
    sarsa_result = sarsa_agent.train(env, n_episodes=300, max_steps=100)
    sarsa_metrics = sarsa_agent.evaluate(env, n_episodes=50)

    # Expected Sarsa
    print("Training Expected Sarsa...")
    expected_sarsa = ExpectedSarsaAgent(config)
    es_result = expected_sarsa.train(env, n_episodes=300, max_steps=100)
    es_metrics = expected_sarsa.evaluate(env, n_episodes=50)

    # Compare learning curves
    curves = {
        "Q-Learning": q_result.episode_rewards,
        "Sarsa": sarsa_result.episode_rewards,
        "Expected Sarsa": es_result.episode_rewards,
    }
    print(visualize_learning_curves(curves))

    # Compare strategies
    results = {
        "Q-Learning": q_metrics,
        "Sarsa": sarsa_metrics,
        "Expected Sarsa": es_metrics,
    }
    print(visualize_strategy_comparison(results))


def demo_double_q_learning():
    """Demonstrate Double Q-Learning."""
    print("\n" + "=" * 60)
    print("DEMO: Double Q-Learning")
    print("=" * 60)
    print()

    # Create environment
    env = GridWorld(
        rows=5,
        cols=5,
        start=(0, 0),
        goal=(4, 4),
        walls=[(1, 1), (2, 2), (3, 1)],
        traps=[(3, 3)],
        seed=42,
    )

    # Q-Learning
    print("Training Q-Learning...")
    q_agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        seed=42,
    )
    q_result = q_agent.train(env, n_episodes=300, max_steps=100)
    q_metrics = q_agent.evaluate(env, n_episodes=50)

    # Double Q-Learning
    print("Training Double Q-Learning...")
    double_agent = DoubleQLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        seed=42,
    )
    double_result = double_agent.train(env, n_episodes=300, max_steps=100)
    double_metrics = double_agent.evaluate(env, n_episodes=50)

    # Compare
    curves = {
        "Q-Learning": q_result.episode_rewards,
        "Double Q-Learning": double_result.episode_rewards,
    }
    print(visualize_learning_curves(curves))

    # Show Q-value heatmaps
    print("\nQ-Learning Q-Values:")
    print(visualize_q_table_heatmap(
        q_agent.q_table, env.rows, env.cols,
        "Q-Learning Q-Values"
    ))

    print("\nDouble Q-Learning Q-Values (average):")
    print(visualize_q_table_heatmap(
        double_agent.q_table, env.rows, env.cols,
        "Double Q-Learning Q-Values"
    ))


def demo_frozen_lake():
    """Demonstrate on FrozenLake environment."""
    print("\n" + "=" * 60)
    print("DEMO: FrozenLake Environment")
    print("=" * 60)
    print()

    # Create environment
    env = FrozenLake(map_name="4x4", is_slippery=True, seed=42)

    print("Environment:")
    print(env.render())
    print()

    # Train agent
    print("Training Q-Learning agent...")
    agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        seed=42,
    )

    result = agent.train(env, n_episodes=1000, max_steps=100, verbose=True)
    print()

    # Visualize training
    print(visualize_training(result.episode_rewards, result.episode_steps))

    # Evaluate
    metrics = agent.evaluate(env, n_episodes=100)
    print(f"\nEvaluation Results:")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Mean Reward: {metrics['mean_reward']:.3f}")


def demo_maze():
    """Demonstrate on Maze environment."""
    print("\n" + "=" * 60)
    print("DEMO: Maze Environment")
    print("=" * 60)
    print()

    # Create maze
    env = Maze(seed=42)

    print("Maze:")
    print(env.render())
    print(f"Size: {env.rows}x{env.cols}")
    print(f"Start: {env.start}")
    print(f"Goal: {env.goal}")
    print()

    # Train agent
    print("Training Q-Learning agent...")
    agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        seed=42,
    )

    result = agent.train(env, n_episodes=500, max_steps=500, verbose=True)
    print()

    # Visualize training
    print(visualize_training(result.episode_rewards, result.episode_steps))

    # Evaluate
    metrics = agent.evaluate(env, n_episodes=50)
    print(f"\nEvaluation Results:")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Mean Reward: {metrics['mean_reward']:.1f}")
    print(f"  Mean Steps: {metrics['mean_steps']:.1f}")


def main():
    """Run all demos."""
    print("Q-Learning Algorithms Demonstration")
    print("=" * 60)
    print()

    # Run demos
    demo_grid_world()
    demo_sarsa_comparison()
    demo_double_q_learning()
    demo_frozen_lake()
    demo_maze()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
