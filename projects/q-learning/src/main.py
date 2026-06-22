"""Main example demonstrating Q-Learning on a Grid World.

This script shows how to:
1. Create a grid world environment
2. Train a Q-Learning agent
3. Evaluate the learned policy
4. Visualize results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grid_world import GridWorld
from q_learning import QLearningAgent
from visualization import (
    visualize_training,
    visualize_policy,
    visualize_q_values,
)


def main():
    """Run the Q-Learning example."""
    print("=" * 60)
    print("Q-Learning Grid World Example")
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

    # Create agent
    agent = QLearningAgent(
        n_states=env.n_states,
        n_actions=env.n_actions,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
        seed=42,
    )

    # Train
    print("Training...")
    result = agent.train(
        env,
        n_episodes=1000,
        max_steps=200,
        convergence_window=100,
        verbose=True,
    )
    print()

    # Training visualization
    print(visualize_training(result.episode_rewards, result.episode_steps))
    print()

    # Evaluate
    print("Evaluating policy...")
    metrics = agent.evaluate(env, n_episodes=100)
    print(f"  Mean Reward: {metrics['mean_reward']:.1f}")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    print(f"  Mean Steps: {metrics['mean_steps']:.1f}")
    print()

    # Policy visualization
    policy = agent.get_policy(env)
    print(visualize_policy(
        env.grid,
        policy,
        env.start.to_tuple(),
        env.goal.to_tuple(),
        "Learned Policy",
    ))
    print()

    # Q-value visualization
    value_map = agent.get_value_map(env)
    print(visualize_q_values(
        env.grid,
        value_map,
        env.start.to_tuple(),
        env.goal.to_tuple(),
        "Q-Value Map",
    ))
    print()

    # Show a sample episode
    print("Sample Episode:")
    print("-" * 40)
    state = env.reset()
    path = [state]
    total_reward = 0

    for step in range(100):
        action = agent.choose_action(state, env)
        action_names = {0: "UP", 1: "RIGHT", 2: "DOWN", 3: "LEFT"}
        print(f"  Step {step + 1}: State {state} -> Action {action_names[action]}")

        next_state, reward, done, info = env.step(action)
        path.append(next_state)
        total_reward += reward
        state = next_state

        if done:
            if info.get("reached_goal"):
                print(f"  Reached goal! Total reward: {total_reward:.1f}")
            elif info.get("fell_in_trap"):
                print(f"  Fell in trap! Total reward: {total_reward:.1f}")
            break

    print()
    print("Path visualization:")
    from visualization import visualize_episode_path
    print(visualize_episode_path(
        env.grid,
        path,
        env.start.to_tuple(),
        env.goal.to_tuple(),
        "Agent Path",
    ))

    print()
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
