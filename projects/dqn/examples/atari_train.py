"""
Atari 游戏训练示例

演示如何使用 DQN 训练 Atari 游戏环境。
"""

import argparse
import os
import sys
from collections import deque

import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import DQNAgent
from src.env_wrapper import SimpleAtariWrapper
from src.visualization import TrainingVisualizer


def train_atari(
    game: str = "simple",
    algorithm: str = "dqn",
    num_episodes: int = 1000,
    max_steps: int = 1000,
    hidden_dim: int = 256,
    learning_rate: float = 1e-4,
    gamma: float = 0.99,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.01,
    epsilon_decay: float = 0.999,
    buffer_size: int = 50000,
    batch_size: int = 32,
    target_update_freq: int = 100,
    save_dir: str = "checkpoints",
    plot_dir: str = "plots",
):
    """
    训练 Atari 游戏

    Args:
        game: 游戏名称 ("simple", "Pong", "Breakout")
        algorithm: 算法类型
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
        plot_dir: 图表保存目录
    """
    # 创建环境
    if game == "simple":
        env = SimpleAtariWrapper(state_dim=4, action_dim=2)
        state_dim = 4
        action_dim = 2
    else:
        # 真实 Atari 环境需要安装 ALE
        try:
            from src.env_wrapper import AtariWrapper
            env = AtariWrapper(game=game)
            state_dim = env.state_dim
            action_dim = env.action_dim
        except Exception as e:
            print(f"无法创建 Atari 环境: {e}")
            print("使用简化环境代替...")
            env = SimpleAtariWrapper(state_dim=4, action_dim=2)
            state_dim = 4
            action_dim = 2

    # 创建代理
    agent = DQNAgent(
        state_dim=state_dim if isinstance(state_dim, int) else state_dim[0],
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

    # 创建可视化器
    visualizer = TrainingVisualizer(save_dir=plot_dir)

    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)

    # 记录训练过程
    episode_rewards = []
    reward_window = deque(maxlen=100)
    best_reward = -float("inf")

    print(f"开始训练 {algorithm.upper()} on {game}...")
    print(f"状态维度: {state_dim}, 动作维度: {action_dim}")
    print("-" * 50)

    for episode in range(num_episodes):
        state, _ = env.reset()

        # 处理状态维度
        if isinstance(state, np.ndarray) and state.ndim > 1:
            state = state.flatten()

        episode_reward = 0

        for step in range(max_steps):
            # 选择动作
            action = agent.select_action(state, training=True)

            # 执行动作
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # 处理下一个状态维度
            if isinstance(next_state, np.ndarray) and next_state.ndim > 1:
                next_state = next_state.flatten()

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

        # 记录指标
        visualizer.record(
            reward=episode_reward,
            epsilon=agent.epsilon,
        )

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
            agent.save(os.path.join(save_dir, f"{algorithm}_{game}_best.pth"))
            print(f"保存最佳模型，平均奖励: {best_reward:.1f}")

    env.close()
    print("训练完成！")

    # 绘制图表
    visualizer.plot_rewards(
        rewards=episode_rewards,
        save_path=os.path.join(plot_dir, f"{algorithm}_{game}_rewards.png"),
    )
    visualizer.plot_epsilon(
        save_path=os.path.join(plot_dir, f"{algorithm}_{game}_epsilon.png"),
    )

    return episode_rewards


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Atari DQN 训练")
    parser.add_argument(
        "--game",
        type=str,
        default="simple",
        choices=["simple", "Pong", "Breakout", "SpaceInvaders"],
        help="游戏名称",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="dqn",
        choices=["dqn", "double_dqn", "dueling_dqn"],
        help="算法类型",
    )
    parser.add_argument("--episodes", type=int, default=1000, help="训练轮数")
    parser.add_argument("--max-steps", type=int, default=1000, help="每轮最大步数")
    parser.add_argument("--hidden-dim", type=int, default=256, help="隐藏层维度")
    parser.add_argument("--lr", type=float, default=1e-4, help="学习率")
    parser.add_argument("--gamma", type=float, default=0.99, help="折扣因子")
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="初始探索率")
    parser.add_argument("--epsilon-end", type=float, default=0.01, help="最终探索率")
    parser.add_argument("--epsilon-decay", type=float, default=0.999, help="探索率衰减")
    parser.add_argument("--buffer-size", type=int, default=50000, help="缓冲区大小")
    parser.add_argument("--batch-size", type=int, default=32, help="批次大小")
    parser.add_argument("--target-update", type=int, default=100, help="目标网络更新频率")
    parser.add_argument("--save-dir", type=str, default="checkpoints", help="保存目录")

    args = parser.parse_args()

    train_atari(
        game=args.game,
        algorithm=args.algorithm,
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
    )


if __name__ == "__main__":
    main()
