"""Evaluation script for Actor-Critic agent on CartPole environment."""

import sys
import os
import argparse
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gymnasium as gym
from actor_critic import ActorCriticAgent


def evaluate(
    checkpoint_path: str = "checkpoints/actor_critic_cartpole.pt",
    num_episodes: int = 10,
    hidden_dim: int = 128,
    render: bool = True,
) -> None:
    """Evaluate trained Actor-Critic agent.

    Args:
        checkpoint_path: Path to model checkpoint.
        num_episodes: Number of evaluation episodes.
        hidden_dim: Hidden layer dimension.
        render: Whether to render the environment.
    """
    # Create environment
    render_mode = "human" if render else None
    env = gym.make("CartPole-v1", render_mode=render_mode)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    # Create agent and load checkpoint
    agent = ActorCriticAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=hidden_dim,
    )

    if os.path.exists(checkpoint_path):
        agent.load(checkpoint_path)
        print(f"Loaded checkpoint from {checkpoint_path}")
    else:
        print(f"No checkpoint found at {checkpoint_path}, using random policy")

    # Evaluate
    scores = []

    for episode in range(1, num_episodes + 1):
        state, _ = env.reset()
        total_reward = 0
        done = False

        while not done:
            # Select action (no gradient needed)
            state_tensor = np.array(state)
            action_probs = agent.actor.get_action_probs(
                agent.actor.network[0].weight.new_tensor(state_tensor).unsqueeze(0)
            )
            action = action_probs.argmax(dim=-1).item()

            # Take step
            state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward

        scores.append(total_reward)
        print(f"Episode {episode:2d} | Score: {total_reward:.1f}")

    env.close()

    # Print summary
    print(f"\n{'='*40}")
    print(f"Evaluation Summary ({num_episodes} episodes)")
    print(f"{'='*40}")
    print(f"Mean Score:  {np.mean(scores):.1f}")
    print(f"Std Score:   {np.std(scores):.1f}")
    print(f"Min Score:   {np.min(scores):.1f}")
    print(f"Max Score:   {np.max(scores):.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Actor-Critic on CartPole")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="checkpoints/actor_critic_cartpole.pt",
        help="Path to checkpoint",
    )
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes")
    parser.add_argument("--hidden-dim", type=int, default=128, help="Hidden dimension")
    parser.add_argument("--no-render", action="store_true", help="Disable rendering")
    args = parser.parse_args()

    evaluate(
        checkpoint_path=args.checkpoint,
        num_episodes=args.episodes,
        hidden_dim=args.hidden_dim,
        render=not args.no_render,
    )
