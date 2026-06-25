"""线性回归示例 - 使用不同优化器训练线性回归模型

本示例展示如何使用梯度下降家族的优化器来训练线性回归模型，
并对比不同优化器的收敛速度和性能。
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple

# 添加项目路径
import sys
sys.path.insert(0, '.')

from src.optimizers import BGD, SGD, MiniBatchBGD, Momentum, Adam, AdamW, Nadam


class LinearRegression:
    """线性回归模型

    y = X @ w + b

    使用统一参数向量 theta = [w, b] 进行优化。
    损失函数: L = (1/2N) * ||y - X @ w - b||^2
    """

    def __init__(self, n_features: int):
        """初始化线性回归模型

        Args:
            n_features: 特征数量
        """
        self.n_features = n_features
        # 统一参数: theta = [w_0, w_1, ..., w_{n-1}, b]
        self.theta = np.random.randn(n_features + 1) * 0.01

    @property
    def weights(self) -> np.ndarray:
        """获取权重"""
        return self.theta[:self.n_features]

    @property
    def bias(self) -> float:
        """获取偏置"""
        return self.theta[self.n_features]

    def forward(self, X: np.ndarray) -> np.ndarray:
        """前向传播

        Args:
            X: 输入特征，形状 (n_samples, n_features)

        Returns:
            预测值，形状 (n_samples,)
        """
        # X_aug = [X, 1], theta = [w, b]
        X_aug = np.hstack([X, np.ones((X.shape[0], 1))])
        return X_aug @ self.theta

    def compute_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算损失

        Args:
            X: 输入特征
            y: 真实标签

        Returns:
            均方误差损失
        """
        predictions = self.forward(X)
        return np.mean((predictions - y) ** 2) / 2

    def compute_gradients(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """计算梯度

        Args:
            X: 输入特征
            y: 真实标签

        Returns:
            参数梯度 theta_grad = [dw, db]
        """
        predictions = self.forward(X)
        errors = predictions - y

        # 构造增广特征矩阵
        X_aug = np.hstack([X, np.ones((X.shape[0], 1))])

        # 梯度: (1/N) * X_aug^T @ errors
        grad = X_aug.T @ errors / len(y)

        return grad


def generate_data(n_samples: int = 100, n_features: int = 1, noise: float = 0.1) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """生成线性回归数据

    Args:
        n_samples: 样本数量
        n_features: 特征数量
        noise: 噪声水平

    Returns:
        (X, y, true_weights, true_bias)
    """
    # 生成真实权重
    true_weights = np.random.randn(n_features) * 2
    true_bias = 1.0

    # 生成特征
    X = np.random.randn(n_samples, n_features)

    # 生成带噪声的标签
    y = X @ true_weights + true_bias + np.random.randn(n_samples) * noise

    return X, y, true_weights, true_bias


def train_linear_regression(
    optimizer,
    X: np.ndarray,
    y: np.ndarray,
    n_epochs: int = 100,
    batch_size: int = 32
) -> Dict:
    """训练线性回归模型

    Args:
        optimizer: 优化器实例
        X: 训练特征
        y: 训练标签
        n_epochs: 训练轮数
        batch_size: 批量大小（用于 Mini-Batch）

    Returns:
        训练结果字典
    """
    n_samples, n_features = X.shape
    model = LinearRegression(n_features)

    losses = []
    weight_history = []
    bias_history = []

    for epoch in range(n_epochs):
        # 打乱数据
        indices = np.random.permutation(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        # Mini-Batch 训练
        if hasattr(optimizer, 'batch_size'):
            for i in range(0, n_samples, optimizer.batch_size):
                X_batch = X_shuffled[i:i + optimizer.batch_size]
                y_batch = y_shuffled[i:i + optimizer.batch_size]

                # 计算梯度（统一参数）
                grad = model.compute_gradients(X_batch, y_batch)

                # 更新统一参数
                model.theta = optimizer.step(model.theta, grad)
        else:
            # 全批量或随机梯度下降
            grad = model.compute_gradients(X_shuffled, y_shuffled)
            model.theta = optimizer.step(model.theta, grad)

        # 记录损失
        loss = model.compute_loss(X, y)
        losses.append(loss)
        weight_history.append(model.weights.copy())
        bias_history.append(model.bias)

    return {
        'losses': losses,
        'weight_history': weight_history,
        'bias_history': bias_history,
        'final_weights': model.weights,
        'final_bias': model.bias
    }


def compare_optimizers_linear_regression():
    """对比不同优化器在线性回归上的表现"""
    print("=" * 60)
    print("线性回归优化器对比实验")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X, y, true_weights, true_bias = generate_data(n_samples=200, n_features=5, noise=0.5)

    print(f"\n数据集: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"真实权重: {true_weights}")
    print(f"真实偏置: {true_bias}")

    # 定义优化器（每个优化器独立实例，避免状态冲突）
    optimizers_config = {
        'BGD': lambda: BGD(learning_rate=0.01),
        'SGD': lambda: SGD(learning_rate=0.01),
        'MiniBatch(32)': lambda: MiniBatchBGD(learning_rate=0.01, batch_size=32),
        'Momentum': lambda: Momentum(learning_rate=0.01, momentum=0.9),
        'Adam': lambda: Adam(learning_rate=0.01),
        'AdamW': lambda: AdamW(learning_rate=0.01, weight_decay=0.01),
        'Nadam': lambda: Nadam(learning_rate=0.01),
    }

    # 训练并收集结果
    results = {}
    for name, optimizer_fn in optimizers_config.items():
        print(f"\n训练 {name}...")
        optimizer = optimizer_fn()
        result = train_linear_regression(optimizer, X, y, n_epochs=100)
        results[name] = result
        print(f"  最终损失: {result['losses'][-1]:.6f}")
        print(f"  权重误差: {np.linalg.norm(result['final_weights'] - true_weights):.6f}")

    # 绘制收敛曲线
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 损失曲线
    ax1 = axes[0, 0]
    for name, result in results.items():
        ax1.plot(result['losses'], label=name, alpha=0.7)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # 权重收敛
    ax2 = axes[0, 1]
    for name, result in results.items():
        weight_errors = [np.linalg.norm(w - true_weights) for w in result['weight_history']]
        ax2.plot(weight_errors, label=name, alpha=0.7)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Weight Error (L2 norm)')
    ax2.set_title('Weight Convergence')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    # 偏置收敛
    ax3 = axes[1, 0]
    for name, result in results.items():
        bias_errors = [abs(b - true_bias) for b in result['bias_history']]
        ax3.plot(bias_errors, label=name, alpha=0.7)
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Bias Error (absolute)')
    ax3.set_title('Bias Convergence')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_yscale('log')

    # 最终性能对比
    ax4 = axes[1, 1]
    names = list(results.keys())
    final_losses = [results[name]['losses'][-1] for name in names]
    bars = ax4.bar(names, final_losses, color=plt.cm.Set2(np.arange(len(names))))
    ax4.set_xlabel('Optimizer')
    ax4.set_ylabel('Final Loss')
    ax4.set_title('Final Loss Comparison')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('linear_regression_comparison.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: linear_regression_comparison.png")

    return results


if __name__ == '__main__':
    compare_optimizers_linear_regression()
