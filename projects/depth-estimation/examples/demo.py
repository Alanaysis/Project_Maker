"""
深度估计演示脚本

演示完整流程:
1. 创建模型
2. 生成合成数据
3. 训练模型
4. 评估模型
5. 可视化结果
"""

import torch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import SimpleDepthNet, DepthEstimationNet, model_summary
from src.loss import CombinedDepthLoss
from src.dataset import SyntheticDepthDataset, create_dataloader
from src.train import DepthTrainer
from src.utils import (
    compute_depth_metrics,
    print_metrics,
    colorize_depth,
    visualize_depth,
    normalize_depth,
    depth_stats,
)

import numpy as np


def demo_model():
    """演示模型创建和前向传播"""
    print("=" * 60)
    print("演示 1: 模型创建和前向传播")
    print("=" * 60)

    # 创建简单模型
    model = SimpleDepthNet()
    print("\nSimpleDepthNet:")
    print(model_summary(model, input_size=(1, 3, 128, 128)))

    # 创建完整模型
    model_full = DepthEstimationNet(base_channels=32)
    print("\nDepthEstimationNet:")
    print(model_summary(model_full, input_size=(1, 3, 128, 128)))

    # 前向传播
    x = torch.randn(2, 3, 128, 128)
    with torch.no_grad():
        depth = model(x)

    print(f"\n输入形状: {x.shape}")
    print(f"输出形状: {depth.shape}")
    print(f"深度范围: [{depth.min():.4f}, {depth.max():.4f}]")


def demo_dataset():
    """演示数据集"""
    print("\n" + "=" * 60)
    print("演示 2: 合成数据集")
    print("=" * 60)

    # 创建数据集
    dataset = SyntheticDepthDataset(
        num_samples=20,
        image_size=(128, 128),
    )

    # 获取样本
    image, depth, mask = dataset[0]

    print(f"\n图像形状: {image.shape}")
    print(f"深度形状: {depth.shape}")
    print(f"掩码形状: {mask.shape}")

    # 深度统计
    stats = depth_stats(depth)
    print(f"\n深度统计:")
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")

    # 测试不同场景
    print("\n不同场景类型:")
    for scene in ["plane", "slope", "stairs", "sphere"]:
        ds = SyntheticDepthDataset(num_samples=1, scene_types=[scene])
        _, d, _ = ds[0]
        print(f"  {scene}: 深度范围 [{d.min():.2f}, {d.max():.2f}]")


def demo_loss():
    """演示损失函数"""
    print("\n" + "=" * 60)
    print("演示 3: 损失函数")
    print("=" * 60)

    criterion = CombinedDepthLoss()

    # 模拟预测和目标
    pred = torch.rand(2, 1, 32, 32) * 10 + 0.1
    target = torch.rand(2, 1, 32, 32) * 10 + 0.1

    loss_dict = criterion(pred, target)

    print("\n组合损失:")
    for key, value in loss_dict.items():
        print(f"  {key}: {value.item():.4f}")


def demo_training():
    """演示训练过程"""
    print("\n" + "=" * 60)
    print("演示 4: 模型训练")
    print("=" * 60)

    # 创建数据集
    train_dataset = SyntheticDepthDataset(num_samples=50, image_size=(64, 64))
    val_dataset = SyntheticDepthDataset(num_samples=20, image_size=(64, 64))

    train_loader = create_dataloader(train_dataset, batch_size=8)
    val_loader = create_dataloader(val_dataset, batch_size=8, shuffle=False)

    # 创建模型
    model = SimpleDepthNet()
    criterion = CombinedDepthLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)

    # 训练
    trainer = DepthTrainer(
        model=model,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
    )

    print("\n开始训练 (10 epochs)...")
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=10,
        print_every=2,
    )

    # 打印训练历史
    print("\n训练历史:")
    print(f"  最终训练损失: {history['train_loss'][-1]:.4f}")
    if history['val_abs_rel']:
        print(f"  最终验证 Abs Rel: {history['val_abs_rel'][-1]:.4f}")
        print(f"  最终验证 RMSE: {history['val_rmse'][-1]:.4f}")

    return model


def demo_evaluation(model):
    """演示评估"""
    print("\n" + "=" * 60)
    print("演示 5: 模型评估")
    print("=" * 60)

    # 创建测试数据
    test_dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
    test_loader = create_dataloader(test_dataset, batch_size=10, shuffle=False)

    device = next(model.parameters()).device
    model.eval()
    with torch.no_grad():
        for images, depths, masks in test_loader:
            images = images.to(device)
            depths = depths.to(device)
            masks = masks.to(device)
            pred_depths = model(images)
            metrics = compute_depth_metrics(pred_depths, depths, masks)
            break

    print("\n评估结果:")
    print_metrics(metrics)


def demo_visualization():
    """演示可视化"""
    print("\n" + "=" * 60)
    print("演示 6: 可视化")
    print("=" * 60)

    # 创建深度图
    depth = torch.rand(64, 64)

    # 归一化
    depth_norm = normalize_depth(depth)
    print(f"\n归一化深度范围: [{depth_norm.min():.4f}, {depth_norm.max():.4f}]")

    # 着色
    colored = colorize_depth(depth, colormap="jet")
    print(f"着色后形状: {colored.shape}")

    # 可视化
    image = torch.rand(3, 64, 64)
    pred_depth = torch.rand(1, 64, 64)
    target_depth = torch.rand(1, 64, 64)

    result = visualize_depth(image, pred_depth, target_depth)
    print(f"可视化结果形状: {result.shape}")


def demo_depth_disparity():
    """演示深度-视差转换"""
    print("\n" + "=" * 60)
    print("演示 7: 深度-视差转换")
    print("=" * 60)

    from src.utils import depth_to_disparity, disparity_to_depth

    # 创建深度图
    depth = torch.rand(1, 1, 32, 32) * 10 + 0.1

    # 转换为视差
    baseline = 0.1  # 10cm 基线
    focal = 500.0   # 500 像素焦距

    disparity = depth_to_disparity(depth, baseline, focal)
    depth_recovered = disparity_to_depth(disparity, baseline, focal)

    print(f"\n深度范围: [{depth.min():.4f}, {depth.max():.4f}]")
    print(f"视差范围: [{disparity.min():.4f}, {disparity.max():.4f}]")
    print(f"恢复深度误差: {(depth - depth_recovered).abs().max():.6f}")


def main():
    """主函数"""
    print("深度估计演示")
    print("=" * 60)

    # 1. 模型演示
    demo_model()

    # 2. 数据集演示
    demo_dataset()

    # 3. 损失函数演示
    demo_loss()

    # 4. 训练演示
    model = demo_training()

    # 5. 评估演示
    demo_evaluation(model)

    # 6. 可视化演示
    demo_visualization()

    # 7. 深度-视差转换演示
    demo_depth_disparity()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
