"""
人体姿态估计演示脚本。

演示完整的姿态估计流程:
1. 创建合成数据集
2. 构建模型
3. 训练模型
4. 推理和可视化
"""

import torch
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model import SimplePoseNet, PoseEstimationNet
from src.dataset import SyntheticPoseDataset, create_dataloader
from src.heatmap import generate_heatmaps, heatmaps_to_keypoints
from src.loss import KeypointMSELoss
from src.keypoints import extract_keypoints, KEYPOINT_NAMES
from src.utils import visualize_pose


def demo_heatmap_generation():
    """演示热力图生成。"""
    print("=" * 60)
    print("演示 1: 高斯热力图生成")
    print("=" * 60)

    # 创建关键点 (归一化坐标)
    keypoints = torch.tensor([[
        [0.3, 0.2],  # 鼻子
        [0.25, 0.15],  # 左眼
        [0.35, 0.15],  # 右眼
    ]])  # (1, 3, 2)
    weights = torch.ones(1, 3)

    # 生成热力图
    heatmap_size = (64, 64)
    heatmaps = generate_heatmaps(keypoints, weights, heatmap_size, sigma=2.0)

    print(f"关键点形状: {keypoints.shape}")
    print(f"热力图形状: {heatmaps.shape}")
    print(f"热力图值范围: [{heatmaps.min():.4f}, {heatmaps.max():.4f}]")
    print(f"热力图峰值位置:")

    for i in range(3):
        flat = heatmaps[0, i].view(-1)
        _, max_idx = flat.max(dim=0)
        y = max_idx.item() // heatmap_size[1]
        x = max_idx.item() % heatmap_size[1]
        print(f"  {KEYPOINT_NAMES[i]}: ({x}, {y}), "
              f"期望: ({keypoints[0, i, 0] * (heatmap_size[1]-1):.1f}, "
              f"{keypoints[0, i, 1] * (heatmap_size[0]-1):.1f})")


def demo_keypoint_extraction():
    """演示关键点提取。"""
    print("\n" + "=" * 60)
    print("演示 2: 关键点提取")
    print("=" * 60)

    # 创建已知关键点
    original_kp = torch.tensor([[
        [0.3, 0.4],
        [0.6, 0.7],
    ]])
    weights = torch.ones(1, 2)

    # 生成热力图
    heatmaps = generate_heatmaps(original_kp, weights, (64, 64), sigma=3.0)

    # 提取关键点
    extracted_kp, confidence = extract_keypoints(heatmaps, threshold=0.1)

    print(f"原始关键点: {original_kp[0].tolist()}")
    print(f"提取关键点: {extracted_kp[0].tolist()}")
    print(f"置信度: {confidence[0].tolist()}")

    # 计算误差
    error = (original_kp - extracted_kp).abs()
    print(f"误差: {error[0].tolist()}")
    print(f"平均误差: {error.mean():.4f}")


def demo_model_forward():
    """演示模型前向传播。"""
    print("\n" + "=" * 60)
    print("演示 3: 模型前向传播")
    print("=" * 60)

    # 创建模型
    model = SimplePoseNet(num_keypoints=17, input_size=128)

    # 计算参数量
    num_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {num_params:,}")

    # 前向传播
    x = torch.randn(2, 3, 128, 128)
    heatmaps = model(x)

    print(f"输入形状: {x.shape}")
    print(f"输出热力图形状: {heatmaps.shape}")

    # 提取关键点
    keypoints, confidence = extract_keypoints(heatmaps)
    print(f"关键点形状: {keypoints.shape}")
    print(f"置信度形状: {confidence.shape}")
    print(f"关键点坐标范围: [{keypoints.min():.4f}, {keypoints.max():.4f}]")


def demo_training_loop():
    """演示训练循环。"""
    print("\n" + "=" * 60)
    print("演示 4: 训练循环 (简化)")
    print("=" * 60)

    # 创建数据集
    dataset = SyntheticPoseDataset(
        num_samples=32,
        image_size=(128, 128),
        heatmap_size=(64, 64),
        num_keypoints=17,
    )
    loader = create_dataloader(dataset, batch_size=8)

    # 创建模型和损失
    model = SimplePoseNet(num_keypoints=17, input_size=128)
    criterion = KeypointMSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    # 训练几个 epoch
    for epoch in range(3):
        model.train()
        total_loss = 0.0

        for batch in loader:
            images = batch["image"]
            target_hm = batch["heatmaps"]
            target_w = batch["weights"]

            # 前向传播
            pred_hm = model(images)

            # 计算损失
            loss_dict = criterion(pred_hm, target_hm, target_w)
            loss = loss_dict["loss"]

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch + 1}/3, Loss: {avg_loss:.4f}")


def demo_visualization():
    """演示可视化。"""
    print("\n" + "=" * 60)
    print("演示 5: 可视化")
    print("=" * 60)

    # 创建一个简单的图像
    img = np.random.randint(50, 200, (256, 256, 3), dtype=np.uint8)

    # 创建关键点 (像素坐标)
    keypoints = np.array([
        [128, 50],   # 鼻子
        [115, 40],   # 左眼
        [141, 40],   # 右眼
        [100, 45],   # 左耳
        [156, 45],   # 右耳
        [90, 90],    # 左肩
        [166, 90],   # 右肩
        [70, 140],   # 左肘
        [186, 140],  # 右肘
        [60, 190],   # 左腕
        [196, 190],  # 右腕
        [105, 180],  # 左髋
        [151, 180],  # 右髋
        [100, 230],  # 左膝
        [156, 230],  # 右膝
        [95, 255],   # 左踝
        [161, 255],  # 右踝
    ], dtype=np.float32)

    confidence = np.ones(17)

    # 可视化
    result = visualize_pose(
        torch.from_numpy(img).permute(2, 0, 1),
        torch.from_numpy(keypoints),
        torch.from_numpy(confidence),
    )

    print(f"输入图像形状: {img.shape}")
    print(f"关键点数量: {len(keypoints)}")
    print(f"输出图像形状: {result.shape}")
    print("可视化完成 (图像已生成，可使用 cv2.imshow 或 matplotlib 显示)")


def demo_full_pipeline():
    """演示完整流程。"""
    print("=" * 60)
    print("人体姿态估计 - 完整流程演示")
    print("=" * 60)

    demo_heatmap_generation()
    demo_keypoint_extraction()
    demo_model_forward()
    demo_training_loop()
    demo_visualization()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo_full_pipeline()
