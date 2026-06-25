"""
环境封装器

提供 CartPole 和 Atari 游戏的标准化接口。
"""

import gymnasium as gym
import numpy as np
from typing import Tuple, Optional


class CartPoleWrapper:
    """
    CartPole 环境封装器

    封装 CartPole-v1 环境，提供统一接口。

    Args:
        render_mode: 渲染模式，None 或 "human"
    """

    def __init__(self, render_mode: Optional[str] = None):
        self.env = gym.make("CartPole-v1", render_mode=render_mode)
        self.state_dim = self.env.observation_space.shape[0]
        self.action_dim = self.env.action_space.n

    def reset(self) -> Tuple[np.ndarray, dict]:
        """重置环境"""
        state, info = self.env.reset()
        return state, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        执行动作

        Args:
            action: 动作索引

        Returns:
            (next_state, reward, terminated, truncated, info)
        """
        return self.env.step(action)

    def close(self) -> None:
        """关闭环境"""
        self.env.close()


class AtariWrapper:
    """
    Atari 游戏封装器

    封装 Atari 环境，进行预处理：
    - 灰度化
    - 下采样 (84x84)
    - 帧堆叠 (4 帧)

    Args:
        game: 游戏名称 (例如 "Pong", "Breakout")
        render_mode: 渲染模式
        frame_stack: 堆叠帧数
    """

    def __init__(
        self,
        game: str = "Pong",
        render_mode: Optional[str] = None,
        frame_stack: int = 4,
    ):
        self.frame_stack = frame_stack

        # 创建环境
        env_name = f"ALE/{game}-v5"
        self.env = gym.make(
            env_name,
            render_mode=render_mode,
            frameskip=4,
            repeat_action_probability=0.25,
        )

        # 预处理维度
        self.state_dim = (frame_stack, 84, 84)
        self.action_dim = self.env.action_space.n

        # 帧缓冲区
        self.frames = np.zeros((frame_stack, 84, 84), dtype=np.uint8)

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        预处理帧

        Args:
            frame: 原始帧，形状 (210, 160, 3)

        Returns:
            预处理后的帧，形状 (84, 84)
        """
        # 转换为灰度
        gray = np.mean(frame, axis=2).astype(np.uint8)

        # 下采样到 84x84
        # 使用简单的平均池化
        height, width = gray.shape
        new_height, new_width = 84, 84
        block_h = height // new_height
        block_w = width // new_width

        resized = np.zeros((new_height, new_width), dtype=np.uint8)
        for i in range(new_height):
            for j in range(new_width):
                block = gray[
                    i * block_h : (i + 1) * block_h,
                    j * block_w : (j + 1) * block_w,
                ]
                resized[i, j] = np.mean(block)

        return resized

    def reset(self) -> Tuple[np.ndarray, dict]:
        """重置环境"""
        state, info = self.env.reset()
        processed = self._preprocess_frame(state)

        # 填充帧缓冲区
        for i in range(self.frame_stack):
            self.frames[i] = processed

        return self.frames.copy(), info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        执行动作

        Args:
            action: 动作索引

        Returns:
            (next_state, reward, terminated, truncated, info)
        """
        next_state, reward, terminated, truncated, info = self.env.step(action)
        processed = self._preprocess_frame(next_state)

        # 更新帧缓冲区（移位）
        self.frames = np.roll(self.frames, shift=-1, axis=0)
        self.frames[-1] = processed

        return self.frames.copy(), reward, terminated, truncated, info

    def close(self) -> None:
        """关闭环境"""
        self.env.close()


class SimpleAtariWrapper:
    """
    简化版 Atari 封装器

    用于测试，不依赖 ALE，使用简单的数值状态。

    Args:
        state_dim: 状态维度
        action_dim: 动作维度
    """

    def __init__(self, state_dim: int = 4, action_dim: int = 2):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.state = None
        self.step_count = 0
        self.max_steps = 200

    def reset(self) -> Tuple[np.ndarray, dict]:
        """重置环境"""
        self.state = np.random.randn(self.state_dim).astype(np.float32)
        self.step_count = 0
        return self.state, {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        执行动作

        Args:
            action: 动作索引

        Returns:
            (next_state, reward, terminated, truncated, info)
        """
        # 简单的状态转移
        noise = np.random.randn(self.state_dim).astype(np.float32) * 0.1
        self.state = self.state + noise

        # 简单的奖励函数
        reward = 1.0 if np.sum(self.state) > 0 else -1.0

        self.step_count += 1
        terminated = abs(np.sum(self.state)) > 5.0  # 超出范围结束
        truncated = self.step_count >= self.max_steps

        return self.state, reward, terminated, truncated, {}

    def close(self) -> None:
        """关闭环境"""
        pass


def create_env(
    env_name: str = "cartpole",
    render_mode: Optional[str] = None,
    **kwargs,
):
    """
    创建环境

    Args:
        env_name: 环境名称 ("cartpole", "atari", "simple")
        render_mode: 渲染模式
        **kwargs: 额外参数

    Returns:
        环境实例
    """
    if env_name == "cartpole":
        return CartPoleWrapper(render_mode=render_mode)
    elif env_name == "atari":
        game = kwargs.get("game", "Pong")
        return AtariWrapper(game=game, render_mode=render_mode)
    elif env_name == "simple":
        return SimpleAtariWrapper(**kwargs)
    else:
        raise ValueError(f"未知环境: {env_name}")
