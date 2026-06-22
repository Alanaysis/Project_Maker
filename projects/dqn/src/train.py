"""
DQN 训练脚本

在 CartPole-v1 环境中训练 DQN 代理。
"""

import argparse
import os
from collections import deque

import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt

from .agent import DQNAgent


def train(
    num_episodes: int = 500,
    max_steps: int = 500,
    hidden_dim: int = 128,
    learning_rate: float = 1e-3,
    gamma: float = 0.99,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.01,
    epsilon_decay: float = 0.995,
    buffer_size: int = 10000,
    batch_size: int = 64,
    target_update_freq: int = 10,
    save_dir: str = "checkpoints",
    render: bool = False,
) -> list:
    """
    训练 DQN 代理

    Args:
        num_episodes: 训练轮数
        max_steps: 每轮最大步数
        hidden_dim: 隐藏层维度
        learning_rate: 学习率
        gamma: 折扣因子
        epsilon_start: 初始探索率
        epsilon_end: 最终探索率
        epsilon_decay: 探索率衰减
        buffer_size: 经验回放缓冲区大小
        batch_size: 训练批次大小
        target_update_freq: 目标网络更新频率
        save_dir: 模型保存目录
        render: 是否渲染环境

    Returns:
        每轮的奖励列表
    """
    # 创建环境
    env = gym.make("CartPole-v1", render_mode="human" if render else None)

    # 获取状态和动作维度
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n

    # 创建代理
    agent = DQNAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=hidden_dim,
        learning_rate=learning_rate,
        gamma=gamma,
        epsilon_start=epsilon_start,
        epsilon_end=epsilon_end,
        epsilon_decay=epsilon_decay,
        buffer_size=buffer_size,
        batch_size=batch_size,
        target_update_freq=target_update_freq,
    )

    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)

    # 记录训练过程
    episode_rewards = []
    reward_window = deque(maxlen=100)
    best_reward = 0

    print("开始训练 DQN...")
    print(f"状态维度: {state_dim}, 动作维度: {action_dim}")
    print("-" * 50)

    for episode in range(num_episodes):
        state, _ = env.reset()
        episode_reward = 0

        for step in range(max_steps):
            # 选择动作
            action = agent.select_action(state, training=True)

            # 执行动作
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # 存储经验
            agent.store_experience(state, action, reward, next_state, done)

            # 训练
            loss = agent.train()

            # 更新状态
            state = next_state
            episode_reward += reward

            if done:
                break

        # 记录奖励
        episode_rewards.append(episode_reward)
        reward_window.append(episode_reward)
        avg_reward = np.mean(reward_window)

        # 打印进度
        if (episode + 1) % 10 == 0:
            print(
                f"Episode {episode + 1}/{num_episodes} | "
                f"Reward: {episode_reward:.1f} | "
                f"Avg Reward: {avg_reward:.1f} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )

        # 保存最佳模型
        if avg_reward > best_reward and len(reward_window) >= 100:
            best_reward = avg_reward
            agent.save(os.path.join(save_dir, "best_model.pth"))
            print(f"保存最佳模型，平均奖励: {best_reward:.1f}")

        # 检查是否解决环境
        if avg_reward >= 475 and len(reward_window) >= 100:
            print(f"\n环境已解决！平均奖励: {avg_reward:.1f}")
            agent.save(os.path.join(save_dir, "solved_model.pth"))
            break

    env.close()
    print("训练完成！")

    return episode_rewards


def plot_rewards(rewards: list, save_path: str = "training_rewards.png") -> None:
    """
    绘制训练奖励曲线

    Args:
        rewards: 奖励列表
        save_path: 保存路径
    """
    plt.figure(figsize=(10, 6))
    plt.plot(rewards, alpha=0.6, label="Episode Reward")

    # 计算移动平均
    window_size = 100
    if len(rewards) >= window_size:
        moving_avg = np.convolve(rewards, np.ones(window_size) / window_size, mode="valid")
        plt.plot(
            range(window_size - 1, len(rewards)),
            moving_avg,
            color="red",
            label=f"{window_size}-Episode Moving Avg",
        )

    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.title("DQN Training on CartPole-v1")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"奖励曲线已保存到: {save_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="DQN 训练脚本")
    parser.add_argument("--episodes", type=int, default=500, help="训练轮数")
    parser.add_argument("--max-steps", type=int, default=500, help="每轮最大步数")
    parser.add_argument("--hidden-dim", type=int, default=128, help="隐藏层维度")
    parser.add_argument("--lr", type=float, default=1e-3, help="学习率")
    parser.add_argument("--gamma", type=float, default=0.99, help="折扣因子")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="初始探索率")
    parser.add_argument("--epsilon-end", type=float, default=0.01, help="最终探索率")
    parser.add_argument("--epsilon-decay", type=float, default=0.995, help="探索率衰减")
    parser.add_argument("--buffer-size", type=int, default=10000, help="缓冲区大小")
    parser.add_argument("--batch-size", type=int, default=64, help="批次大小")
    parser.add_argument("--target-update", type=int, default=10, help="目标网络更新频率")
    parser.add_argument("--save-dir", type=str, default="checkpoints", help="保存目录")
    parser.add_argument("--render", action="store_true", help="渲染环境")

    args = parser.parse_args()

    # 训练
    rewards = train(
        num_episodes=args.episodes,
        max_steps=args.max_steps,
        hidden_dim=args.hidden_dim,
        learning_rate=args.lr,
        gamma=args.gamma,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay,
        buffer_size=args.buffer_size,
        batch_size=args.batch_size,
        target_update_freq=args.target_update,
        save_dir=args.save_dir,
        render=args.render,
    )

    # 绘制奖励曲线
    plot_rewards(rewards, os.path.join(args.save_dir, "training_rewards.png"))


if __name__ == "__main__":
    main()
