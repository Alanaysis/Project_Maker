#!/usr/bin/env python3
"""
基础动作识别示例

演示如何使用Action Recognition库进行视频动作识别。

Usage:
    python examples/basic_recognition.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
from action_recognition.models.action_classifier import ActionClassifier
from action_recognition.data.video_dataset import VideoDataset
from action_recognition.data.frame_sampler import FrameSampler


def main():
    print("=" * 60)
    print("Action Recognition - 基础示例")
    print("=" * 60)

    # 1. 创建合成数据集
    print("\n[1] 创建合成数据集...")
    sampler = FrameSampler(num_frames=8, strategy="uniform")
    dataset = VideoDataset(
        synthetic=True,
        num_synthetic_classes=5,
        num_synthetic_samples=20,
        frame_sampler=sampler,
    )
    print(f"  数据集大小: {len(dataset)}")
    print(f"  类别数量: {dataset.num_classes}")
    print(f"  类别名称: {dataset.get_class_names()}")

    # 2. 获取一个样本
    print("\n[2] 获取样本...")
    video, label = dataset[0]
    print(f"  视频张量形状: {video.shape}")  # (T, C, H, W)
    print(f"  标签: {label}")

    # 3. 创建模型
    print("\n[3] 创建动作识别模型...")
    model = ActionClassifier(
        num_classes=5,
        backbone="resnet18",
        temporal_arch="lstm",
        hidden_dim=256,
        pretrained=False,  # 不下载预训练权重
    )
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 4. 前向传播
    print("\n[4] 前向传播...")
    video_batch = video.unsqueeze(0)  # 添加batch维度: (1, T, C, H, W)
    print(f"  输入形状: {video_batch.shape}")

    logits = model(video_batch)
    print(f"  输出形状: {logits.shape}")  # (1, num_classes)
    print(f"  输出logits: {logits.detach().numpy()}")

    # 5. 预测
    print("\n[5] 预测结果...")
    predictions = model.predict(video_batch, top_k=3)
    pred = predictions[0]
    print("  Top-3预测:")
    for class_idx, prob in pred.items():
        class_name = dataset.get_class_names()[class_idx]
        print(f"    {class_name}: {prob:.4f}")

    # 6. 提取特征
    print("\n[6] 提取特征...")
    spatial_features = model.get_spatial_features(video_batch)
    print(f"  空间特征形状: {spatial_features.shape}")  # (1, T, feat_dim)

    temporal_features = model.get_temporal_features(video_batch)
    print(f"  时序特征形状: {temporal_features.shape}")  # (1, hidden_dim)

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
