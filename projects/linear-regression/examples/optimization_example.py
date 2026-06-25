#!/usr/bin/env python3
"""优化算法示例

演示不同梯度下降变体的效果对比：
- 批量梯度下降 (BGD)
- 随机梯度下降 (SGD)
- 小批量梯度下降 (Mini-Batch)
- 学习率调度
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression
from src.optimizers import (
    BatchGradientDescent,
    StochasticGradientDescent,
    MiniBatchGradientDescent,
    LearningRateScheduler,
)
from src.losses import MSELoss
from src.utils import generate_linear_data, train_test_split


def _train_sgd(X, y, learning_rate, n_epochs):
    """手动实现 SGD 训练（用于演示）

    Args:
        X: 特征矩阵
        y: 目标值
        learning_rate: 学习率
        n_epochs: 训练轮数

    Returns:
        (weights, bias, losses)
    """
    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0.0
    losses = []

    for epoch in range(n_epochs):
        # 每个 epoch 打乱数据
        indices = np.random.permutation(n_samples)
        epoch_losses = []

        for i in indices:
            x_i = X[i]
            y_i = y[i]

            # 前向传播
            y_pred_i = x_i @ weights + bias

            # 计算梯度
            error = y_pred_i - y_i
            dw = 2.0 * x_i * error
            db = 2.0 * error

            # 更新参数
            weights -= learning_rate * dw
            bias -= learning_rate * db

            # 记录损失
            y_pred_all = X @ weights + bias
            epoch_losses.append(MSELoss.compute(y, y_pred_all))

        losses.append(np.mean(epoch_losses))

    return weights, bias, losses


def _train_minibatch(X, y, learning_rate, n_epochs, batch_size):
    """手动实现 Mini-Batch 训练

    Args:
        X: 特征矩阵
        y: 目标值
        learning_rate: 学习率
        n_epochs: 训练轮数
        batch_size: 批量大小

    Returns:
        (weights, bias, losses)
    """
    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0.0
    losses = []

    for epoch in range(n_epochs):
        indices = np.random.permutation(n_samples)
        X_shuffled = X[indices]
        y_shuffled = y[indices]

        for start in range(0, n_samples, batch_size):
            end = min(start + batch_size, n_samples)
            X_batch = X_shuffled[start:end]
            y_batch = y_shuffled[start:end]

            # 前向传播
            y_pred_batch = X_batch @ weights + bias

            # 计算梯度
            n_b = len(y_batch)
            error = y_pred_batch - y_batch
            dw = (2.0 / n_b) * (X_batch.T @ error)
            db = (2.0 / n_b) * np.sum(error)

            # 更新参数
            weights -= learning_rate * dw
            bias -= learning_rate * db

        # 每个 epoch 记录损失
        y_pred_all = X @ weights + bias
        losses.append(MSELoss.compute(y, y_pred_all))

    return weights, bias, losses


def _train_with_scheduler(X, y, initial_lr, n_epochs, scheduler):
    """使用学习率调度器训练

    Args:
        X: 特征矩阵
        y: 目标值
        initial_lr: 初始学习率
        n_epochs: 训练轮数
        scheduler: 学习率调度器

    Returns:
        (weights, bias, losses, learning_rates)
    """
    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0.0
    losses = []
    learning_rates = []

    step = 0
    for epoch in range(n_epochs):
        lr = scheduler.get_lr(step, total_steps=n_epochs)
        learning_rates.append(lr)

        # 前向传播
        y_pred = X @ weights + bias
        loss = MSELoss.compute(y, y_pred)
        losses.append(loss)

        # 计算梯度
        error = y_pred - y
        dw = (2.0 / n_samples) * (X.T @ error)
        db = (2.0 / n_samples) * np.sum(error)

        # 更新参数
        weights -= lr * dw
        bias -= lr * db

        step += 1

    return weights, bias, losses, learning_rates


def demo_gradient_descent_comparison():
    """比较不同梯度下降变体"""
    print("=" * 60)
    print("  Demo 1: Gradient Descent Variants Comparison")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=200,
        n_features=3,
        noise=0.5,
        true_weights=np.array([2.0, -1.5, 3.0]),
        true_bias=1.0,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 1. Batch Gradient Descent
    model_bgd = LinearRegression(learning_rate=0.01, n_iterations=500)
    model_bgd.fit(X_train, y_train)
    bgd_final_loss = model_bgd.losses[-1]

    # 2. Stochastic Gradient Descent
    np.random.seed(42)
    sgd_w, sgd_b, sgd_losses = _train_sgd(X_train, y_train, learning_rate=0.001, n_epochs=50)

    # 3. Mini-Batch Gradient Descent
    np.random.seed(42)
    mb_w, mb_b, mb_losses = _train_minibatch(
        X_train, y_train, learning_rate=0.01, n_epochs=50, batch_size=32
    )

    print(f"\n  Data: 200 samples, 3 features")
    print(f"  True weights: [2.0, -1.5, 3.0], bias: 1.0\n")

    print(f"  {'Method':<30} {'Final Loss':<15} {'Test R2':<10}")
    print(f"  {'-'*55}")

    # BGD
    y_pred_bgd = model_bgd.predict(X_test)
    from src.evaluation import r2_score

    print(f"  {'Batch GD (500 iter)':<30} {bgd_final_loss:<15.6f} {r2_score(y_test, y_pred_bgd):<10.4f}")

    # SGD
    y_pred_sgd = X_test @ sgd_w + sgd_b
    print(f"  {'SGD (50 epochs)':<30} {sgd_losses[-1]:<15.6f} {r2_score(y_test, y_pred_sgd):<10.4f}")

    # Mini-Batch
    y_pred_mb = X_test @ mb_w + mb_b
    print(f"  {'Mini-Batch GD (batch=32)':<30} {mb_losses[-1]:<15.6f} {r2_score(y_test, y_pred_mb):<10.4f}")

    print(f"\n  Observation:")
    print(f"  - BGD: Stable convergence, each step uses all data")
    print(f"  - SGD: Noisy but fast per-epoch, may oscillate")
    print(f"  - Mini-Batch: Good balance between BGD and SGD")


def demo_learning_rate_scheduling():
    """演示学习率调度策略"""
    print("\n" + "=" * 60)
    print("  Demo 2: Learning Rate Scheduling")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=2,
        noise=0.5,
        true_weights=np.array([3.0, -2.0]),
        true_bias=1.0,
        random_state=42,
    )

    strategies = ["constant", "step_decay", "exponential_decay", "cosine_annealing"]
    n_epochs = 200

    print(f"\n  Data: 100 samples, 2 features")
    print(f"  Initial LR: 0.1, Epochs: {n_epochs}\n")

    print(f"  {'Strategy':<25} {'Final Loss':<15} {'Final LR':<15}")
    print(f"  {'-'*55}")

    for strategy in strategies:
        scheduler = LearningRateScheduler(
            initial_lr=0.1,
            strategy=strategy,
            decay_rate=0.5,
            decay_steps=50,
            min_lr=1e-4,
        )

        np.random.seed(42)
        w, b, losses, lrs = _train_with_scheduler(X, y, 0.1, n_epochs, scheduler)

        print(f"  {strategy:<25} {losses[-1]:<15.6f} {lrs[-1]:<15.6f}")

    print(f"\n  Observation:")
    print(f"  - Constant: Simple but may not converge optimally")
    print(f"  - Step Decay: Reduces LR at fixed intervals")
    print(f"  - Exponential Decay: Smooth LR reduction")
    print(f"  - Cosine Annealing: LR oscillates, good for escaping local minima")


def demo_learning_rate_impact():
    """演示学习率对训练的影响"""
    print("\n" + "=" * 60)
    print("  Demo 3: Impact of Learning Rate")
    print("=" * 60)

    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=1,
        noise=0.5,
        true_weights=np.array([3.0]),
        true_bias=1.0,
        random_state=42,
    )

    learning_rates = [0.001, 0.01, 0.1, 0.5]
    n_iterations = 300

    print(f"\n  Data: 100 samples, 1 feature")
    print(f"  Iterations: {n_iterations}\n")

    print(f"  {'Learning Rate':<15} {'Final Loss':<15} {'Converged?':<12}")
    print(f"  {'-'*42}")

    for lr in learning_rates:
        model = LinearRegression(learning_rate=lr, n_iterations=n_iterations)
        model.fit(X, y)

        final_loss = model.losses[-1]
        converged = "Yes" if model.losses[-1] < model.losses[0] else "No (diverged)"

        print(f"  {lr:<15.3f} {final_loss:<15.6f} {converged:<12}")

    print(f"\n  Observation:")
    print(f"  - Too small (0.001): Slow convergence")
    print(f"  - Good (0.01-0.1): Fast and stable convergence")
    print(f"  - Too large (0.5): May diverge or oscillate")


def main():
    print("\n" + "#" * 60)
    print("#  Optimization Algorithm Examples")
    print("#" * 60)

    demo_gradient_descent_comparison()
    demo_learning_rate_scheduling()
    demo_learning_rate_impact()

    print("\n" + "#" * 60)
    print("#  All optimization examples completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
