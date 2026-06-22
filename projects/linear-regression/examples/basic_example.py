#!/usr/bin/env python3
"""线性回归基础示例

演示如何使用线性回归模型进行训练和预测。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression
from src.losses import MSELoss
from src.utils import (
    generate_linear_data,
    train_test_split,
    compute_r2_score,
    plot_loss_curve,
    plot_regression_line,
)


def main():
    """主函数"""
    print("=" * 60)
    print("线性回归基础示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n[1] 生成数据...")
    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=1,
        noise=0.5,
        true_weights=np.array([3.0]),
        true_bias=4.0,
        random_state=42,
    )
    print(f"  数据形状: X={X.shape}, y={y.shape}")
    print(f"  真实权重: 3.0")
    print(f"  真实偏置: 4.0")

    # 2. 划分数据集
    print("\n[2] 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  训练集大小: {len(X_train)}")
    print(f"  测试集大小: {len(X_test)}")

    # 3. 创建并训练模型
    print("\n[3] 训练模型...")
    model = LinearRegression(learning_rate=0.1, n_iterations=500, verbose=True)
    model.fit(X_train, y_train)

    # 4. 评估模型
    print("\n[4] 评估模型...")
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    train_loss = MSELoss.compute(y_train, y_train_pred)
    test_loss = MSELoss.compute(y_test, y_test_pred)

    train_r2 = compute_r2_score(y_train, y_train_pred)
    test_r2 = compute_r2_score(y_test, y_test_pred)

    print(f"  训练集 MSE: {train_loss:.4f}")
    print(f"  测试集 MSE: {test_loss:.4f}")
    print(f"  训练集 R²: {train_r2:.4f}")
    print(f"  测试集 R²: {test_r2:.4f}")

    # 5. 查看学习到的参数
    print("\n[5] 学习到的参数...")
    print(f"  权重: {model.weights[0]:.4f} (真实: 3.0)")
    print(f"  偏置: {model.bias:.4f} (真实: 4.0)")

    # 6. 预测新数据
    print("\n[6] 预测新数据...")
    X_new = np.array([[1.0], [2.0], [3.0]])
    y_new_pred = model.predict(X_new)
    for x, y_pred in zip(X_new.flatten(), y_new_pred):
        print(f"  X={x:.1f} -> y_pred={y_pred:.4f}")

    # 7. 可视化
    print("\n[7] 生成可视化图表...")

    # 损失曲线
    plot_loss_curve(
        model.losses,
        title="Training Loss Curve",
        save_path="examples/loss_curve.png",
    )

    # 回归线
    plot_regression_line(
        X_train,
        y_train,
        model.weights,
        model.bias,
        title="Linear Regression Result",
        save_path="examples/regression_line.png",
    )

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
