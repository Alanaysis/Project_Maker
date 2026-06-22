"""
自动驾驶感知系统演示

演示如何使用自动驾驶感知系统进行 3D 目标检测。
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data.point_cloud import PointCloud
from src.models.pointpillars import PointPillars
from src.utils.visualization import Visualizer


def demo_point_cloud():
    """演示点云处理"""
    print("=== 点云处理演示 ===")

    # 创建模拟点云
    points = np.random.rand(1000, 4).astype(np.float32)
    points[:, :3] = points[:, :3] * 80 - 40  # 范围 [-40, 40]
    points[:, 3] = points[:, 3] * 255  # 强度 [0, 255]

    # 创建点云对象
    pc = PointCloud(points)
    print(f"点云数量: {pc.num_points}")
    print(f"特征维度: {pc.num_features}")

    # 范围过滤
    filtered = pc.filter_by_range(
        x_range=(-20, 20),
        y_range=(-20, 20),
        z_range=(-3, 1)
    )
    print(f"过滤后点云数量: {filtered.num_points}")

    # 降采样
    downsampled = pc.downsample(voxel_size=0.5)
    print(f"降采样后点云数量: {downsampled.num_points}")

    # 获取边界框
    min_point, max_point = pc.get_bounding_box()
    print(f"边界框: {min_point} - {max_point}")

    # 获取质心
    centroid = pc.get_centroid()
    print(f"质心: {centroid}")

    print("点云处理演示完成\n")


def demo_model():
    """演示模型"""
    print("=== 模型演示 ===")

    # 创建模型
    model = PointPillars(
        voxel_size=[0.16, 0.16, 4],
        point_cloud_range=[-40, -40, -3, 40, 40, 1],
        num_classes=3,
        num_anchors_per_location=2
    )

    # 打印模型信息
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"总参数数量: {total_params:,}")
    print(f"可训练参数数量: {trainable_params:,}")

    # 创建模拟输入
    batch_size = 2
    num_points = 1000
    points = torch.randn(batch_size, num_points, 4)

    # 前向传播
    import torch
    with torch.no_grad():
        output = model(points)

    # 打印输出形状
    print(f"分类分数形状: {output['cls_score'].shape}")
    print(f"边界框预测形状: {output['bbox_pred'].shape}")
    print(f"方向预测形状: {output['dir_pred'].shape}")

    print("模型演示完成\n")


def demo_visualization():
    """演示可视化"""
    print("=== 可视化演示 ===")

    # 创建模拟点云
    points = np.random.rand(1000, 3).astype(np.float32) * 10 - 5

    # 创建模拟边界框
    boxes = np.array([
        [0, 0, 0, 2, 4, 1.5, 0],      # 一个汽车
        [5, 5, 0, 0.6, 0.8, 1.7, 0.5], # 一个行人
        [-3, -3, 0, 0.6, 1.8, 1.7, 1.0] # 一个骑车人
    ])

    labels = np.array([0, 1, 2])  # Car, Pedestrian, Cyclist
    scores = np.array([0.95, 0.85, 0.90])

    # 创建可视化工具
    visualizer = Visualizer()

    # 创建 3D 边界框可视化
    line_sets = visualizer.visualize_boxes3d(boxes, labels, scores)
    print(f"创建了 {len(line_sets)} 个 3D 边界框")

    # 创建 BEV 可视化
    print("BEV 可视化需要图形界面，跳过演示")

    print("可视化演示完成\n")


def demo_detection_pipeline():
    """演示检测流程"""
    print("=== 检测流程演示 ===")

    import torch

    # 创建模型
    model = PointPillars(
        voxel_size=[0.16, 0.16, 4],
        point_cloud_range=[-40, -40, -3, 40, 40, 1],
        num_classes=3,
        num_anchors_per_location=2
    )
    model.eval()

    # 创建模拟点云
    points = np.random.rand(1000, 4).astype(np.float32)
    points[:, :3] = points[:, :3] * 80 - 40  # 范围 [-40, 40]
    points[:, 3] = points[:, 3] * 255  # 强度 [0, 255]

    # 预处理
    mask = (
        (points[:, 0] >= -40) & (points[:, 0] <= 40) &
        (points[:, 1] >= -40) & (points[:, 1] <= 40) &
        (points[:, 2] >= -3) & (points[:, 2] <= 1)
    )
    filtered_points = points[mask]

    # 转换为 tensor
    points_tensor = torch.from_numpy(filtered_points).float().unsqueeze(0)

    # 推理
    with torch.no_grad():
        predictions = model(points_tensor)

    # 打印预测结果
    print(f"输入点云形状: {filtered_points.shape}")
    print(f"分类分数形状: {predictions['cls_score'].shape}")
    print(f"边界框预测形状: {predictions['bbox_pred'].shape}")
    print(f"方向预测形状: {predictions['dir_pred'].shape}")

    # 后处理 (简化版)
    cls_score = predictions['cls_score']
    bbox_pred = predictions['bbox_pred']

    print(f"最大分类分数: {cls_score.max().item():.4f}")
    print(f"边界框预测范围: [{bbox_pred.min().item():.4f}, {bbox_pred.max().item():.4f}]")

    print("检测流程演示完成\n")


def main():
    """主函数"""
    print("自动驾驶感知系统演示")
    print("=" * 50)

    # 演示点云处理
    demo_point_cloud()

    # 演示模型
    demo_model()

    # 演示可视化
    demo_visualization()

    # 演示检测流程
    demo_detection_pipeline()

    print("=" * 50)
    print("所有演示完成!")


if __name__ == '__main__':
    main()
