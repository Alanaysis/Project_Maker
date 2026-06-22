"""
REINFORCE 算法模块

实现经典的 REINFORCE（Monte Carlo Policy Gradient）算法。
REINFORCE 是最基础的策略梯度算法，使用蒙特卡洛采样估计梯度。

核心思想：
1. 采集完整的轨迹（episode）
2. 计算每个时间步的回报（return）
3. 使用策略梯度定理更新策略参数

策略梯度定理：
    ∇J(θ) = E[∑_t ∇log π(a_t|s_t; θ) * G_t]

其中 G_t 是从时间步 t 开始的累积回报。
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .policy_network import PolicyNetwork
from .baseline import Baseline, NoBaseline, MovingAverageBaseline


@dataclass
class TrajectoryStep:
    """轨迹中的单步数据"""
    state: np.ndarray
    action: int
    reward: float
    log_prob: torch.Tensor


@dataclass
class EpisodeResult:
    """单个 episode 的结果"""
    steps: List[TrajectoryStep]
    total_reward: float
    length: int


class REINFORCE:
    """
    REINFORCE 算法

    Monte Carlo Policy Gradient 方法。
    每个 episode 结束后，使用完整的轨迹更新策略。

    Args:
        policy: 策略网络
        optimizer: 优化器
        gamma: 折扣因子
        baseline: 基线方法
        entropy_coef: 熵正则化系数
        max_grad_norm: 最大梯度范数（用于梯度裁剪）
    """

    def __init__(
        self,
        policy: PolicyNetwork,
        optimizer: torch.optim.Optimizer,
        gamma: float = 0.99,
        baseline: Optional[Baseline] = None,
        entropy_coef: float = 0.0,
        max_grad_norm: Optional[float] = None,
    ):
        self.policy = policy
        self.optimizer = optimizer
        self.gamma = gamma
        self.baseline = baseline or NoBaseline()
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm

    def compute_returns(self, rewards: List[float]) -> torch.Tensor:
        """
        计算折扣回报（discounted returns）

        G_t = r_t + γ * r_{t+1} + γ² * r_{t+2} + ...

        Args:
            rewards: 奖励列表

        Returns:
            折扣回报张量
        """
        returns = []
        G = 0

        # 从后往前计算，利用递推关系：G_t = r_t + γ * G_{t+1}
        for reward in reversed(rewards):
            G = reward + self.gamma * G
            returns.insert(0, G)

        return torch.tensor(returns, dtype=torch.float32)

    def select_action(self, state: np.ndarray) -> Tuple[int, torch.Tensor]:
        """
        根据策略选择动作

        Args:
            state: 环境状态

        Returns:
            (action, log_prob): 动作和对数概率
        """
        state_tensor = torch.FloatTensor(state)
        log_probs = self.policy(state_tensor.unsqueeze(0))

        # 从分布中采样动作
        dist = torch.distributions.Categorical(logits=log_probs)
        action = dist.sample()

        return action.item(), log_probs[0, action]

    def collect_episode(self, env) -> EpisodeResult:
        """
        收集一个完整的 episode

        Args:
            env: Gym 环境

        Returns:
            EpisodeResult 对象
        """
        steps = []
        state, _ = env.reset()
        done = False

        while not done:
            action, log_prob = self.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            steps.append(
                TrajectoryStep(
                    state=state,
                    action=action,
                    reward=reward,
                    log_prob=log_prob,
                )
            )
            state = next_state

        total_reward = sum(step.reward for step in steps)
        return EpisodeResult(
            steps=steps, total_reward=total_reward, length=len(steps)
        )

    def update(self, episode: EpisodeResult) -> Dict[str, float]:
        """
        使用一个 episode 的数据更新策略

        Args:
            episode: EpisodeResult 对象

        Returns:
            包含训练指标的字典
        """
        # 提取奖励和对数概率
        rewards = [step.reward for step in episode.steps]
        log_probs = torch.stack([step.log_prob for step in episode.steps])

        # 计算折扣回报
        returns = self.compute_returns(rewards)

        # 应用基线
        advantages = self.baseline.compute_advantage(returns)

        # 归一化优势（可选，通常有助于训练稳定性）
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (
                advantages.std() + 1e-8
            )

        # 计算策略损失
        # 策略梯度定理：∇J(θ) = E[∑_t ∇log π(a_t|s_t; θ) * A_t]
        # 最大化 J 等价于最小化 -J
        policy_loss = -(log_probs * advantages.detach()).mean()

        # 计算熵正则化（鼓励探索）
        entropy_loss = 0.0
        if self.entropy_coef > 0:
            states = torch.FloatTensor(
                np.array([step.state for step in episode.steps])
            )
            entropy = self.policy.get_entropy(states).mean()
            entropy_loss = -self.entropy_coef * entropy

        # 总损失
        loss = policy_loss + entropy_loss

        # 反向传播和优化
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        if self.max_grad_norm is not None:
            torch.nn.utils.clip_grad_norm_(
                self.policy.parameters(), self.max_grad_norm
            )

        self.optimizer.step()

        return {
            "policy_loss": policy_loss.item(),
            "entropy_loss": (
                entropy_loss.item()
                if isinstance(entropy_loss, torch.Tensor)
                else entropy_loss
            ),
            "total_loss": loss.item(),
            "mean_return": returns.mean().item(),
            "episode_reward": episode.total_reward,
            "episode_length": episode.length,
        }

    def train(
        self,
        env,
        num_episodes: int,
        eval_env=None,
        eval_interval: int = 50,
        eval_episodes: int = 10,
        verbose: bool = True,
    ) -> Dict[str, List[float]]:
        """
        训练 REINFORCE 算法

        Args:
            env: 训练环境
            num_episodes: 训练 episode 数量
            eval_env: 评估环境（可选）
            eval_interval: 评估间隔
            eval_episodes: 每次评估的 episode 数量
            verbose: 是否打印训练信息

        Returns:
            包含训练历史的字典
        """
        history = {
            "episode_rewards": [],
            "episode_lengths": [],
            "policy_losses": [],
            "eval_rewards": [],
        }

        for episode_idx in range(num_episodes):
            # 收集 episode
            episode = self.collect_episode(env)

            # 更新策略
            metrics = self.update(episode)

            # 记录历史
            history["episode_rewards"].append(episode.total_reward)
            history["episode_lengths"].append(episode.length)
            history["policy_losses"].append(metrics["policy_loss"])

            # 打印训练信息
            if verbose and (episode_idx + 1) % 10 == 0:
                recent_rewards = history["episode_rewards"][-10:]
                avg_reward = np.mean(recent_rewards)
                print(
                    f"Episode {episode_idx + 1}/{num_episodes} | "
                    f"Avg Reward (last 10): {avg_reward:.2f} | "
                    f"Episode Reward: {episode.total_reward:.2f} | "
                    f"Length: {episode.length}"
                )

            # 评估
            if eval_env is not None and (episode_idx + 1) % eval_interval == 0:
                eval_reward = self.evaluate(eval_env, eval_episodes)
                history["eval_rewards"].append(eval_reward)
                if verbose:
                    print(
                        f"  [Eval] Avg Reward ({eval_episodes} episodes): "
                        f"{eval_reward:.2f}"
                    )

        return history

    def evaluate(self, env, num_episodes: int = 10) -> float:
        """
        评估策略性能

        Args:
            env: 评估环境
            num_episodes: 评估 episode 数量

        Returns:
            平均回报
        """
        total_rewards = []

        for _ in range(num_episodes):
            state, _ = env.reset()
            episode_reward = 0
            done = False

            while not done:
                action, _ = self.select_action(state)
                state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward

            total_rewards.append(episode_reward)

        return np.mean(total_rewards)

    def save(self, path: str):
        """保存模型"""
        torch.save(
            {
                "policy_state_dict": self.policy.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            path,
        )

    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path)
        self.policy.load_state_dict(checkpoint["policy_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])


class REINFORCEWithBaseline(REINFORCE):
    """
    带基线的 REINFORCE

    使用价值网络作为基线，减少梯度方差。
    这是 REINFORCE 的改进版本。

    Args:
        policy: 策略网络
        value_network: 价值网络
        policy_optimizer: 策略优化器
        value_optimizer: 价值网络优化器
        gamma: 折扣因子
        entropy_coef: 熵正则化系数
        value_coef: 价值损失系数
        max_grad_norm: 最大梯度范数
    """

    def __init__(
        self,
        policy: PolicyNetwork,
        value_network: nn.Module,
        policy_optimizer: torch.optim.Optimizer,
        value_optimizer: torch.optim.Optimizer,
        gamma: float = 0.99,
        entropy_coef: float = 0.0,
        value_coef: float = 0.5,
        max_grad_norm: Optional[float] = None,
    ):
        super().__init__(
            policy=policy,
            optimizer=policy_optimizer,
            gamma=gamma,
            entropy_coef=entropy_coef,
            max_grad_norm=max_grad_norm,
        )
        self.value_network = value_network
        self.value_optimizer = value_optimizer
        self.value_coef = value_coef

    def update(self, episode: EpisodeResult) -> Dict[str, float]:
        """
        使用一个 episode 的数据更新策略和价值网络

        Args:
            episode: EpisodeResult 对象

        Returns:
            包含训练指标的字典
        """
        # 提取数据
        states = torch.FloatTensor(
            np.array([step.state for step in episode.steps])
        )
        rewards = [step.reward for step in episode.steps]
        log_probs = torch.stack([step.log_prob for step in episode.steps])

        # 计算折扣回报
        returns = self.compute_returns(rewards)

        # 计算价值估计
        values = self.value_network(states).squeeze(-1)

        # 计算优势函数：A(s,a) = G_t - V(s_t)
        advantages = returns - values.detach()

        # 归一化优势
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (
                advantages.std() + 1e-8
            )

        # 策略损失
        policy_loss = -(log_probs * advantages).mean()

        # 价值损失
        value_loss = nn.functional.mse_loss(values, returns.detach())

        # 熵正则化
        entropy_loss = 0.0
        if self.entropy_coef > 0:
            entropy = self.policy.get_entropy(states).mean()
            entropy_loss = -self.entropy_coef * entropy

        # 总策略损失
        total_policy_loss = policy_loss + entropy_loss

        # 更新价值网络
        self.value_optimizer.zero_grad()
        value_loss.backward(retain_graph=True)
        if self.max_grad_norm is not None:
            torch.nn.utils.clip_grad_norm_(
                self.value_network.parameters(), self.max_grad_norm
            )
        self.value_optimizer.step()

        # 更新策略网络
        self.optimizer.zero_grad()
        total_policy_loss.backward()
        if self.max_grad_norm is not None:
            torch.nn.utils.clip_grad_norm_(
                self.policy.parameters(), self.max_grad_norm
            )
        self.optimizer.step()

        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy_loss": (
                entropy_loss.item()
                if isinstance(entropy_loss, torch.Tensor)
                else entropy_loss
            ),
            "total_loss": total_policy_loss.item(),
            "mean_return": returns.mean().item(),
            "episode_reward": episode.total_reward,
            "episode_length": episode.length,
        }
