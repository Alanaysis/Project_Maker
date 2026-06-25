#!/usr/bin/env python3
"""
自定义数据集示例

演示如何使用自定义视频数据集进行训练。

数据目录结构:
    data/
        train/
            class1/
                video1.mp4
                video2.mp4
            class2/
                ...
        val/
            class1/
                ...
            class2/
                ...

Usage:
    python examples/custom_dataset.py --data-root /path/to/data
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
from torch.utils.data import DataLoader

from action_recognition.models.action_classifier import ActionClassifier
from action_recognition.data.video_dataset import VideoDataset
from action_recognition.data.frame_sampler import FrameSampler


def main():
    parser = argparse.ArgumentParser(description="自定义数据集示例")
    parser.add_argument("--data-root", type=str, required=True, help="数据根目录")
    parser.add_argument("--num-frames", type=int, default=8, help="每个视频的帧数")
    parser.add_argument("--batch-size", type=int, default=4, help="批大小")
    parser.add_argument("--epochs", type=int, default=5, help="训练轮数")
    parser.add_argument("--lr", type=float, default=1e-3, help="学习率")
    args = parser.parse_args()

    print("=" * 60)
    print("Action Recognition - 自定义数据集示例")
    print("=" * 60)

    # 1. 创建数据集
    print("\n[1] 加载数据集...")
    sampler = FrameSampler(num_frames=args.num_frames, strategy="uniform")

    train_dataset = VideoDataset(
        data_root=f"{args.data_root}/train",
        frame_sampler=sampler,
    )
    val_dataset = VideoDataset(
        data_root=f"{args.data_root}/val",
        frame_sampler=sampler,
        class_to_idx=train_dataset.class_to_idx,
    )

    print(f"  训练集大小: {len(train_dataset)}")
    print(f"  验证集大小: {len(val_dataset)}")
    print(f"  类别数量: {train_dataset.num_classes}")
    print(f"  类别名称: {train_dataset.get_class_names()}")

    # 2. 创建DataLoader
    print("\n[2] 创建DataLoader...")
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    # 3. 创建模型
    print("\n[3] 创建模型...")
    model = ActionClassifier(
        num_classes=train_dataset.num_classes,
        backbone="resnet18",
        temporal_arch="lstm",
        hidden_dim=256,
        pretrained=True,
    )
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 4. 训练设置
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    print(f"  设备: {device}")

    # 5. 训练循环
    print(f"\n[4] 开始训练 ({args.epochs} epochs)...")
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for videos, labels in train_loader:
            videos = videos.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(videos)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * videos.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()
            total += labels.size(0)

        train_loss = total_loss / total
        train_acc = correct / total

        # 验证
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for videos, labels in val_loader:
                videos = videos.to(device)
                labels = labels.to(device)
                outputs = model(videos)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_correct / val_total if val_total > 0 else 0

        print(f"  Epoch {epoch}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Acc: {val_acc:.4f}")

    # 6. 保存模型
    print("\n[5] 保存模型...")
    save_path = "checkpoints/custom_model.pth"
    torch.save(model.state_dict(), save_path)
    print(f"  模型已保存到: {save_path}")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
