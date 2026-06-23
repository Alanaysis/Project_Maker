"""Training script for Actor-Critic agent on CartPole environment."""

import sys
import os
import argparse
import numpy as np
from collections import deque

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gymnasium as gym
from actor_critic import ActorCriticAgent


def train(
    num_episodes: int = 500,
    max_steps: int = 500,
    hidden_dim: int = 128,
    actor_lr: float = 3e-4,
    critic_lr: float = 1e-3,
    gamma: float = 0.99,
    gae_lambda: float = 1.0,
    entropy_coef: float = 0.01,
    print_every: int = 10,
    save_path: str = "checkpoints/actor_critic_cartpole.pt",
) -> None:
    """Train Actor-Critic agent on CartPole-v1.

    Args:
        num_episodes: Number of training episodes.
        max_steps: Maximum steps per episode.
        hidden_dim: Hidden layer dimension.
        actor_lr: Actor learning rate.
        critic_lr: Critic learning rate.
        gamma: Discount factor.
        gae_lambda: GAE lambda parameter.
        entropy_coef: Entropy bonus coefficient.
        print_every: Print stats every N episodes.
        save_path: Path to save model checkpoint.
    """
    # Create environment
    env = gym.make("CartPole-v1")
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    # Create agent
    agent = ActorCriticAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=hidden_dim,
        actor_lr=actor_lr,
        critic_lr=critic_lr,
        gamma=gamma,
        gae_lambda=gae_lambda,
        entropy_coef=entropy_coef,
    )

    # Training loop
    scores = deque(maxlen=100)
    best_avg_score = 0

    for episode in range(1, num_episodes + 1):
        state, _ = env.reset()
        total_reward = 0

        for step in range(max_steps):
            # Select action
            action = agent.select_action(state)

            # Take step
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # Store reward
            agent.store_reward(reward)
            total_reward += reward

            state = next_state

            if done:
                break

        # Update networks
        losses = agent.update()

        # Track progress
        scores.append(total_reward)
        avg_score = np.mean(scores)

        # Print progress
        if episode % print_every == 0:
            print(
                f"Episode {episode:4d} | "
                f"Score: {total_reward:6.1f} | "
                f"Avg Score: {avg_score:6.1f} | "
                f"Actor Loss: {losses['actor_loss']:.4f} | "
                f"Critic Loss: {losses['critic_loss']:.4f} | "
                f"Entropy: {losses['entropy']:.4f}"
            )

        # Save best model
        if avg_score > best_avg_score and len(scores) == 100:
            best_avg_score = avg_score
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            agent.save(save_path)
            print(f"  -> New best model saved! Avg Score: {avg_score:.1f}")

        # Early stopping if solved
        if avg_score >= 475.0 and len(scores) == 100:
            print(f"\nSolved in {episode} episodes! Avg Score: {avg_score:.1f}")
            break

    env.close()
    print(f"\nTraining complete. Best Avg Score: {best_avg_score:.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Actor-Critic on CartPole")
    parser.add_argument("--episodes", type=int, default=500, help="Number of episodes")
    parser.add_argument("--hidden-dim", type=int, default=128, help="Hidden dimension")
    parser.add_argument("--actor-lr", type=float, default=3e-4, help="Actor LR")
    parser.add_argument("--critic-lr", type=float, default=1e-3, help="Critic LR")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--gae-lambda", type=float, default=1.0, help="GAE lambda")
    parser.add_argument("--entropy-coef", type=float, default=0.01, help="Entropy coef")
    args = parser.parse_args()

    train(
        num_episodes=args.episodes,
        hidden_dim=args.hidden_dim,
        actor_lr=args.actor_lr,
        critic_lr=args.critic_lr,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        entropy_coef=args.entropy_coef,
    )
