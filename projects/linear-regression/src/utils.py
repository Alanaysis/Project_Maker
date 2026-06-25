"""工具函数模块

提供数据生成、数据集划分、可视化等辅助功能。
"""

import numpy as np
from typing import Tuple, List, Optional
import matplotlib.pyplot as plt


def generate_linear_data(
    n_samples: int = 100,
    n_features: int = 1,
    noise: float = 0.1,
    true_weights: Optional[np.ndarray] = None,
    true_bias: float = 0.0,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """生成线性回归数据

    生成符合 y = X @ weights + bias + noise 的数据。

    Args:
        n_samples: 样本数量
        n_features: 特征数量
        noise: 噪声标准差
        true_weights: 真实权重，如果为 None 则随机生成
        true_bias: 真实偏置
        random_state: 随机种子

    Returns:
        X: 特征矩阵，形状 (n_samples, n_features)
        y: 目标值，形状 (n_samples,)
    """
    if random_state is not None:
        np.random.seed(random_state)

    # 生成特征
    X = np.random.randn(n_samples, n_features)

    # 生成真实权重
    if true_weights is None:
        true_weights = np.random.randn(n_features)

    # 计算目标值
    y = X @ true_weights + true_bias

    # 添加噪声
    if noise > 0:
        y += noise * np.random.randn(n_samples)

    return X, y


def generate_nonlinear_data(
    n_samples: int = 100,
    noise: float = 0.1,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """生成非线性数据（用于演示多项式回归）

    生成 y = 0.5*x² + x + 2 + noise 的数据。

    Args:
        n_samples: 样本数量
        noise: 噪声标准差
        random_state: 随机种子

    Returns:
        X: 特征矩阵，形状 (n_samples, 1)
        y: 目标值，形状 (n_samples,)
    """
    if random_state is not None:
        np.random.seed(random_state)

    X = np.random.randn(n_samples, 1) * 2
    y = 0.5 * X.flatten() ** 2 + X.flatten() + 2 + noise * np.random.randn(n_samples)

    return X, y


def train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """划分训练集和测试集

    Args:
        X: 特征矩阵
        y: 目标值
        test_size: 测试集比例
        random_state: 随机种子

    Returns:
        X_train, X_test, y_train, y_test
    """
    if random_state is not None:
        np.random.seed(random_state)

    n_samples = len(X)
    n_test = int(n_samples * test_size)

    # 随机打乱索引
    indices = np.random.permutation(n_samples)
    test_indices = indices[:n_test]
    train_indices = indices[n_test:]

    return X[train_indices], X[test_indices], y[train_indices], y[test_indices]


def plot_loss_curve(
    losses: List[float],
    title: str = "Training Loss Curve",
    save_path: Optional[str] = None,
) -> None:
    """绘制损失曲线

    Args:
        losses: 损失值列表
        title: 图表标题
        save_path: 保存路径，如果为 None 则显示图表
    """
    plt.figure(figsize=(10, 6))
    plt.plot(losses, linewidth=2)
    plt.xlabel("Iteration", fontsize=12)
    plt.ylabel("Loss", fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Loss curve saved to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_regression_line(
    X: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    bias: float,
    title: str = "Linear Regression",
    save_path: Optional[str] = None,
) -> None:
    """绘制回归线（仅支持单特征）

    Args:
        X: 特征矩阵，形状 (n_samples, 1)
        y: 目标值
        weights: 权重
        bias: 偏置
        title: 图表标题
        save_path: 保存路径
    """
    X = np.asarray(X).flatten()
    y = np.asarray(y).flatten()

    plt.figure(figsize=(10, 6))

    # 绘制数据点
    plt.scatter(X, y, alpha=0.5, label="Data Points")

    # 绘制回归线
    X_line = np.linspace(X.min(), X.max(), 100)
    y_line = weights[0] * X_line + bias
    plt.plot(X_line, y_line, color="red", linewidth=2, label="Regression Line")

    plt.xlabel("X", fontsize=12)
    plt.ylabel("y", fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Regression plot saved to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_training_process(
    X: np.ndarray,
    y: np.ndarray,
    weight_history: List[np.ndarray],
    bias_history: List[float],
    n_lines: int = 5,
    title: str = "Training Process",
    save_path: Optional[str] = None,
) -> None:
    """展示训练过程中的回归线变化

    Args:
        X: 特征矩阵
        y: 目标值
        weight_history: 权重历史
        bias_history: 偏置历史
        n_lines: 显示的回归线数量
        title: 图表标题
        save_path: 保存路径
    """
    X = np.asarray(X).flatten()
    y = np.asarray(y).flatten()

    plt.figure(figsize=(10, 6))

    # 绘制数据点
    plt.scatter(X, y, alpha=0.3, label="Data Points")

    # 绘制不同时刻的回归线
    n_iterations = len(weight_history)
    step = max(1, n_iterations // n_lines)

    X_line = np.linspace(X.min(), X.max(), 100)

    for i in range(0, n_iterations, step):
        w = weight_history[i][0]
        b = bias_history[i]
        y_line = w * X_line + b
        alpha = 0.3 + 0.7 * (i / n_iterations)
        plt.plot(X_line, y_line, alpha=alpha, label=f"Iteration {i}")

    # 绘制最终回归线
    w_final = weight_history[-1][0]
    b_final = bias_history[-1]
    y_line_final = w_final * X_line + b_final
    plt.plot(X_line, y_line_final, color="red", linewidth=2, label="Final")

    plt.xlabel("X", fontsize=12)
    plt.ylabel("y", fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Training process plot saved to {save_path}")
    else:
        plt.show()

    plt.close()


def plot_regularization_comparison(
    alphas: List[float],
    train_scores: List[float],
    test_scores: List[float],
    title: str = "Regularization Strength vs R2 Score",
    save_path: Optional[str] = None,
) -> None:
    """绘制正则化强度与模型性能的关系

    Args:
        alphas: 正则化强度列表
        train_scores: 训练集 R² 分数
        test_scores: 测试集 R² 分数
        title: 图表标题
        save_path: 保存路径
    """
    plt.figure(figsize=(10, 6))
    plt.semilogx(alphas, train_scores, "b-o", label="Train R²")
    plt.semilogx(alphas, test_scores, "r-o", label="Test R²")
    plt.xlabel("Regularization Strength (alpha)", fontsize=12)
    plt.ylabel("R² Score", fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Regularization comparison plot saved to {save_path}")
    else:
        plt.show()

    plt.close()


def print_evaluation_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    dataset_name: str = "Test",
) -> None:
    """打印模型评估报告

    Args:
        y_true: 真实值
        y_pred: 预测值
        dataset_name: 数据集名称
    """
    from .evaluation import mean_squared_error, root_mean_squared_error
    from .evaluation import mean_absolute_error, r2_score

    mse = mean_squared_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    print(f"\n{'=' * 40}")
    print(f"  {dataset_name} Set Evaluation Report")
    print(f"{'=' * 40}")
    print(f"  MSE  = {mse:.6f}")
    print(f"  RMSE = {rmse:.6f}")
    print(f"  MAE  = {mae:.6f}")
    print(f"  R²   = {r2:.6f}")
    print(f"{'=' * 40}\n")
