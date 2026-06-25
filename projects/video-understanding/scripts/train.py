"""视频分类训练脚本

支持合成数据和真实数据两种模式。
"""

import argparse
import os
import sys

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_understanding.data.video_dataset import SyntheticVideoDataset
from video_understanding.models.classifier import VideoContentClassifier


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """训练一个 epoch"""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for frames, labels in dataloader:
        frames = frames.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(frames)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * frames.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += frames.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy


def validate(model, dataloader, criterion, device):
    """验证"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for frames, labels in dataloader:
            frames = frames.to(device)
            labels = labels.to(device)

            logits = model(frames)
            loss = criterion(logits, labels)

            total_loss += loss.item() * frames.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += frames.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy


def main():
    parser = argparse.ArgumentParser(description="视频分类训练")
    parser.add_argument("--synthetic", action="store_true", help="使用合成数据")
    parser.add_argument("--epochs", type=int, default=5, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=4, help="批大小")
    parser.add_argument("--lr", type=float, default=0.001, help="学习率")
    parser.add_argument("--num-classes", type=int, default=10, help="类别数")
    parser.add_argument("--num-frames", type=int, default=8, help="帧数")
    parser.add_argument("--feature-dim", type=int, default=256, help="特征维度")
    parser.add_argument("--backbone", type=str, default="resnet18", help="骨干网络")
    parser.add_argument("--save-dir", type=str, default="checkpoints", help="保存目录")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # 创建数据集
    if args.synthetic:
        print("使用合成数据集...")
        train_dataset = SyntheticVideoDataset(
            num_samples=200, num_frames=args.num_frames,
            num_classes=args.num_classes, frame_size=(112, 112)
        )
        val_dataset = SyntheticVideoDataset(
            num_samples=50, num_frames=args.num_frames,
            num_classes=args.num_classes, frame_size=(112, 112), seed=123
        )
    else:
        print("请指定 --synthetic 或提供数据目录")
        return

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    # 创建模型
    model = VideoContentClassifier(
        num_classes=args.num_classes,
        backbone=args.backbone,
        pretrained=False,
        feature_dim=args.feature_dim,
    ).to(device)

    print(f"模型: {model}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # 训练循环
    best_acc = 0.0
    for epoch in range(args.epochs):
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch {epoch + 1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

        if val_acc > best_acc:
            best_acc = val_acc
            os.makedirs(args.save_dir, exist_ok=True)
            save_path = os.path.join(args.save_dir, "best_model.pth")
            torch.save(model.state_dict(), save_path)
            print(f"  -> 保存最佳模型到 {save_path}")

    print(f"\n训练完成! 最佳验证准确率: {best_acc:.4f}")


if __name__ == "__main__":
    main()
