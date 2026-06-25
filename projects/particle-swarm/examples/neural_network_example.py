"""
神经网络训练示例

演示使用 PSO 训练神经网络。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import NeuralNetworkTrainer, NeuralNetworkConfig
from src.neural_network import create_xor_dataset, create_spiral_dataset


def main():
    print("=" * 60)
    print("PSO 训练神经网络示例")
    print("=" * 60)

    # 示例 1: XOR 问题
    print("\n[示例 1] XOR 问题")
    print("-" * 40)

    X_xor, y_xor = create_xor_dataset()
    print(f"数据集: {X_xor.shape[0]} 样本, {X_xor.shape[1]} 特征")
    print(f"输入:\n{X_xor}")
    print(f"标签:\n{y_xor}")

    config = NeuralNetworkConfig(
        layer_sizes=[2, 10, 1],
        hidden_activation="sigmoid",
        output_activation="sigmoid",
        n_particles=30,
        max_iterations=100,
        random_seed=42,
    )

    trainer = NeuralNetworkTrainer(config)
    result = trainer.train(X_xor, y_xor, loss_type="binary_crossentropy", verbose=False)

    print(f"\n训练结果:")
    print(f"  最终损失: {result['best_loss']:.6f}")
    print(f"  迭代次数: {result['iterations']}")

    # 预测
    predictions = trainer.predict(X_xor, result['best_weights'])
    print(f"\n预测结果:")
    for i in range(len(X_xor)):
        print(f"  输入: {X_xor[i]}, 标签: {y_xor[i][0]}, 预测: {predictions[i][0]:.4f}")

    # 示例 2: 螺旋数据集
    print("\n[示例 2] 螺旋数据集")
    print("-" * 40)

    X_spiral, y_spiral = create_spiral_dataset(n_points=50)
    print(f"数据集: {X_spiral.shape[0]} 样本, {X_spiral.shape[1]} 特征")

    config = NeuralNetworkConfig(
        layer_sizes=[2, 20, 10, 1],
        hidden_activation="tanh",
        output_activation="sigmoid",
        n_particles=50,
        max_iterations=200,
        random_seed=42,
    )

    trainer = NeuralNetworkTrainer(config)
    result = trainer.train(X_spiral, y_spiral, loss_type="binary_crossentropy", verbose=False)

    print(f"\n训练结果:")
    print(f"  最终损失: {result['best_loss']:.6f}")
    print(f"  迭代次数: {result['iterations']}")

    # 计算准确率
    predictions = trainer.predict(X_spiral, result['best_weights'])
    accuracy = np.mean((predictions > 0.5) == y_spiral)
    print(f"  训练准确率: {accuracy:.2%}")

    # 示例 3: 回归问题
    print("\n[示例 3] 回归问题")
    print("-" * 40)

    # 创建简单的回归数据
    np.random.seed(42)
    X_reg = np.random.randn(100, 2)
    y_reg = (X_reg[:, 0] ** 2 + X_reg[:, 1] ** 2).reshape(-1, 1)

    # 归一化
    y_reg = (y_reg - y_reg.mean()) / y_reg.std()

    config = NeuralNetworkConfig(
        layer_sizes=[2, 10, 5, 1],
        hidden_activation="relu",
        output_activation="linear",
        n_particles=30,
        max_iterations=100,
        random_seed=42,
    )

    trainer = NeuralNetworkTrainer(config)
    result = trainer.train(X_reg, y_reg, loss_type="mse", verbose=False)

    print(f"\n训练结果:")
    print(f"  最终 MSE: {result['best_loss']:.6f}")
    print(f"  迭代次数: {result['iterations']}")


if __name__ == "__main__":
    main()
