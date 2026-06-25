"""
PSO 用于神经网络训练

使用粒子群优化算法训练神经网络权重，替代传统的梯度下降方法。

特点：
- 全局优化：避免梯度下降陷入局部最优
- 无需梯度：适用于不可微的激活函数
- 并行评估：可以同时评估多个网络
"""

import numpy as np
from typing import Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NeuralNetworkConfig:
    """神经网络配置"""

    # 网络结构
    layer_sizes: list[int]  # 各层神经元数量，如 [2, 10, 1]

    # 激活函数
    hidden_activation: str = "relu"  # "relu", "sigmoid", "tanh"
    output_activation: str = "sigmoid"  # "sigmoid", "linear"

    # PSO 参数
    n_particles: int = 30
    max_iterations: int = 100
    w: float = 0.7
    c1: float = 1.5
    c2: float = 1.5
    random_seed: Optional[int] = None


class NeuralNetwork:
    """
    简单的前馈神经网络

    支持任意层数和神经元数量的网络结构。
    """

    def __init__(self, config: NeuralNetworkConfig):
        """
        初始化神经网络

        参数:
            config: 网络配置
        """
        self.config = config
        self.layer_sizes = config.layer_sizes
        self.n_layers = len(self.layer_sizes) - 1

        # 计算权重总数
        self.n_weights = 0
        for i in range(self.n_layers):
            # 权重矩阵 + 偏置向量
            self.n_weights += (self.layer_sizes[i] + 1) * self.layer_sizes[i + 1]

        # 激活函数
        self.activations = {
            "relu": self._relu,
            "sigmoid": self._sigmoid,
            "tanh": np.tanh,
            "linear": lambda x: x,
        }

        self.hidden_activation = self.activations[config.hidden_activation]
        self.output_activation = self.activations[config.output_activation]

    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU 激活函数"""
        return np.maximum(0, x)

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid 激活函数"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def _unpack_weights(self, weights: np.ndarray) -> list[Tuple[np.ndarray, np.ndarray]]:
        """
        将权重向量解包为各层的权重矩阵和偏置向量

        参数:
            weights: 一维权重向量

        返回:
            [(W1, b1), (W2, b2), ...] 列表
        """
        layers = []
        idx = 0

        for i in range(self.n_layers):
            n_in = self.layer_sizes[i]
            n_out = self.layer_sizes[i + 1]

            # 权重矩阵
            W_size = n_in * n_out
            W = weights[idx:idx + W_size].reshape(n_in, n_out)
            idx += W_size

            # 偏置向量
            b = weights[idx:idx + n_out]
            idx += n_out

            layers.append((W, b))

        return layers

    def forward(self, X: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """
        前向传播

        参数:
            X: 输入数据，形状 (n_samples, n_features)
            weights: 网络权重向量

        返回:
            网络输出，形状 (n_samples, n_outputs)
        """
        layers = self._unpack_weights(weights)
        output = X

        for i, (W, b) in enumerate(layers):
            output = output @ W + b

            # 应用激活函数
            if i < self.n_layers - 1:
                output = self.hidden_activation(output)
            else:
                output = self.output_activation(output)

        return output


class NeuralNetworkTrainer:
    """
    使用 PSO 训练神经网络

    将网络权重视为粒子位置，使用 PSO 搜索最优权重。
    """

    def __init__(self, config: NeuralNetworkConfig):
        """
        初始化训练器

        参数:
            config: 神经网络配置
        """
        self.config = config
        self.network = NeuralNetwork(config)
        self._rng = np.random.default_rng(config.random_seed)

    def _create_fitness_function(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        loss_type: str = "mse",
    ) -> Callable:
        """
        创建适应度函数

        参数:
            X_train: 训练数据
            y_train: 训练标签
            loss_type: 损失类型 ("mse", "binary_crossentropy")

        返回:
            适应度函数
        """
        def fitness_function(weights: np.ndarray) -> float:
            # 前向传播
            predictions = self.network.forward(X_train, weights)

            # 计算损失
            if loss_type == "mse":
                loss = np.mean((predictions - y_train) ** 2)
            elif loss_type == "binary_crossentropy":
                predictions = np.clip(predictions, 1e-7, 1 - 1e-7)
                loss = -np.mean(
                    y_train * np.log(predictions) +
                    (1 - y_train) * np.log(1 - predictions)
                )
            else:
                raise ValueError(f"未知的损失类型: {loss_type}")

            return float(loss)

        return fitness_function

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        loss_type: str = "mse",
        verbose: bool = False,
    ) -> dict:
        """
        训练神经网络

        参数:
            X_train: 训练数据，形状 (n_samples, n_features)
            y_train: 训练标签，形状 (n_samples, n_outputs)
            loss_type: 损失类型
            verbose: 是否打印进度

        返回:
            训练结果字典
        """
        # 导入 PSO
        from .swarm import Swarm, PSOConfig

        # 创建适应度函数
        fitness_function = self._create_fitness_function(X_train, y_train, loss_type)

        # 配置 PSO
        # 搜索范围根据网络结构设置
        bound = 1.0 / np.sqrt(self.network.layer_sizes[0])
        config = PSOConfig(
            n_particles=self.config.n_particles,
            dimensions=self.network.n_weights,
            bounds=(-bound, bound),
            w=self.config.w,
            c1=self.config.c1,
            c2=self.config.c2,
            max_iterations=self.config.max_iterations,
            random_seed=self.config.random_seed,
        )

        # 运行 PSO
        swarm = Swarm(config)
        result = swarm.optimize(fitness_function, verbose=verbose)

        # 计算训练准确率
        best_weights = result.best_position
        predictions = self.network.forward(X_train, best_weights)

        if loss_type == "binary_crossentropy":
            accuracy = np.mean((predictions > 0.5) == y_train)
        else:
            accuracy = None

        return {
            "best_weights": best_weights,
            "best_loss": result.best_fitness,
            "iterations": result.iterations,
            "convergence_history": result.convergence_history,
            "accuracy": accuracy,
        }

    def predict(self, X: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """
        使用训练好的网络进行预测

        参数:
            X: 输入数据
            weights: 网络权重

        返回:
            预测结果
        """
        return self.network.forward(X, weights)


def create_xor_dataset() -> Tuple[np.ndarray, np.ndarray]:
    """
    创建 XOR 数据集

    返回:
        (X, y) 元组
    """
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = np.array([[0], [1], [1], [0]])
    return X, y


def create_spiral_dataset(n_points: int = 100, noise: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """
    创建螺旋数据集

    参数:
        n_points: 每类样本数
        noise: 噪声水平

    返回:
        (X, y) 元组
    """
    np.random.seed(42)

    # 生成螺旋数据
    theta = np.linspace(0, 4 * np.pi, n_points)
    r = np.linspace(0.5, 2, n_points)

    # 类别 0
    x1 = r * np.cos(theta) + np.random.randn(n_points) * noise
    y1 = r * np.sin(theta) + np.random.randn(n_points) * noise

    # 类别 1
    x2 = r * np.cos(theta + np.pi) + np.random.randn(n_points) * noise
    y2 = r * np.sin(theta + np.pi) + np.random.randn(n_points) * noise

    X = np.vstack([np.column_stack([x1, y1]), np.column_stack([x2, y2])])
    y = np.vstack([np.zeros((n_points, 1)), np.ones((n_points, 1))])

    return X, y
