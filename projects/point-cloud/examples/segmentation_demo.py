"""
点云分割演示

展示如何使用 PointNet 进行点云分割。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from src import (
    PointNetSegmentor,
    PointCloudDataset,
    PointCloudTrainer,
    PointCloudVisualizer,
    generate_segmentation_data,
)


def main():
    print("=" * 60)
    print("点云分割演示")
    print("=" * 60)

    # 1. 生成数据
    print("\n[1] 生成分割数据...")
    num_parts = 4
    num_points = 512
    train_points, train_labels = generate_segmentation_data(
        num_points=num_points, num_parts=num_parts, num_samples=500
    )
    val_points, val_labels = generate_segmentation_data(
        num_points=num_points, num_parts=num_parts, num_samples=100
    )

    train_dataset = PointCloudDataset(train_points, train_labels, task="segmentation")
    val_dataset = PointCloudDataset(val_points, val_labels, task="segmentation")

    print(f"  训练集: {len(train_dataset)} 样本")
    print(f"  验证集: {len(val_dataset)} 样本")
    print(f"  部件数: {num_parts}")
    print(f"  点数: {num_points}")

    # 2. 创建模型
    print("\n[2] 创建 PointNet 分割器...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trainer = PointCloudTrainer.create_segmentor(
        num_classes=num_parts, use_tnet=True, device=device
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
        history, save_path="outputs/segmentation_training.png"
    )

    # 5. 测试预测
    print("\n[5] 测试分割预测...")
    test_points, test_labels = generate_segmentation_data(
        num_points=num_points, num_parts=num_parts, num_samples=5
    )
    test_dataset = PointCloudDataset(test_points, test_labels, task="segmentation")

    for i in range(3):
        points, true_labels = test_dataset[i]
        pred_labels = trainer.predict(points)

        # 计算准确率
        acc = (pred_labels == true_labels).float().mean().item()
        print(f"  样本 {i}: 准确率 = {acc:.4f}")

        # 可视化
        points_viz = points.transpose(0, 1).numpy()
        pred_labels_viz = pred_labels.numpy()

        PointCloudVisualizer.visualize_segmentation_result(
            points_viz,
            pred_labels_viz,
            num_parts=num_parts,
            save_path=f"outputs/segmentation_result_{i}.png"
        )

    print("\n" + "=" * 60)
    print("演示完成!")
    print("输出文件保存在 outputs/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
