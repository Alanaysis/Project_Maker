"""
点云分类演示

展示如何使用 PointNet 进行点云分类。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from src import (
    PointNetClassifier,
    PointCloudDataset,
    PointCloudTrainer,
    PointCloudVisualizer,
    generate_random_pointcloud,
)


def main():
    print("=" * 60)
    print("点云分类演示")
    print("=" * 60)

    # 1. 生成数据
    print("\n[1] 生成训练数据...")
    num_classes = 5
    num_points = 512
    train_points, train_labels = generate_random_pointcloud(
        num_points=num_points, num_classes=num_classes, num_samples=500
    )
    val_points, val_labels = generate_random_pointcloud(
        num_points=num_points, num_classes=num_classes, num_samples=100
    )

    train_dataset = PointCloudDataset(train_points, train_labels, task="classification")
    val_dataset = PointCloudDataset(val_points, val_labels, task="classification")

    print(f"  训练集: {len(train_dataset)} 样本")
    print(f"  验证集: {len(val_dataset)} 样本")
    print(f"  类别数: {num_classes}")
    print(f"  点数: {num_points}")

    # 2. 创建模型
    print("\n[2] 创建 PointNet 分类器...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trainer = PointCloudTrainer.create_classifier(
        num_classes=num_classes, use_tnet=True, device=device
    )

    param_count = sum(p.numel() for p in trainer.model.parameters())
    print(f"  模型参数: {param_count:,}")
    print(f"  设备: {device}")

    # 3. 训练模型
    print("\n[3] 训练模型...")
    history = trainer.train(
        train_dataset, val_dataset,
        epochs=20, lr=0.001, batch_size=32
    )

    # 4. 可视化训练历史
    print("\n[4] 可视化训练历史...")
    os.makedirs("outputs", exist_ok=True)
    PointCloudVisualizer.plot_training_history(
        history, save_path="outputs/classification_training.png"
    )

    # 5. 测试预测
    print("\n[5] 测试预测...")
    test_points, test_labels = generate_random_pointcloud(
        num_points=num_points, num_classes=num_classes, num_samples=10
    )
    test_dataset = PointCloudDataset(test_points, test_labels, task="classification")

    predictions = []
    for i in range(5):
        points, true_label = test_dataset[i]
        pred = trainer.predict(points)
        predictions.append(pred.item())
        print(f"  样本 {i}: 真实={true_label.item()}, 预测={pred.item()}")

    # 6. 可视化预测结果
    print("\n[6] 可视化预测结果...")
    class_names = [f"Class_{i}" for i in range(num_classes)]

    for i in range(min(3, len(test_dataset))):
        points, true_label = test_dataset[i]
        # 转置回 (N, 3) 用于可视化
        points_viz = points.transpose(0, 1).numpy()

        PointCloudVisualizer.visualize_classification_result(
            points_viz,
            true_label.item(),
            predictions[i],
            class_names=class_names,
            save_path=f"outputs/classification_result_{i}.png"
        )

    print("\n" + "=" * 60)
    print("演示完成!")
    print("输出文件保存在 outputs/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
