"""
Training Script - 手势分类器训练脚本

使用方法：
    python scripts/train.py --epochs 10 --batch-size 32
    python scripts/train.py --synthetic --epochs 5
"""

import argparse
import sys
import os
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from gesture_recognition.models.gesture_classifier import GestureClassifierNet
from gesture_recognition.data.hand_dataset import HandDataset, create_synthetic_dataset
from gesture_recognition.utils.metrics import MetricTracker


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> dict:
    """
    训练一个epoch

    Args:
        model: 模型
        dataloader: 数据加载器
        criterion: 损失函数
        optimizer: 优化器
        device: 设备

    Returns:
        dict: 训练指标
    """
    model.train()
    tracker = MetricTracker()

    for features, labels in dataloader:
        features = features.to(device)
        labels = labels.to(device)

        # 前向传播
        outputs = model(features)
        loss = criterion(outputs, labels)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 计算准确率
        _, predicted = torch.max(outputs, 1)
        accuracy = (predicted == labels).float().mean()

        tracker.update({"loss": loss.item(), "accuracy": accuracy.item()})

    return tracker.get_metrics()


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> dict:
    """
    验证模型

    Args:
        model: 模型
        dataloader: 数据加载器
        criterion: 损失函数
        device: 设备

    Returns:
        dict: 验证指标
    """
    model.eval()
    tracker = MetricTracker()

    with torch.no_grad():
        for features, labels in dataloader:
            features = features.to(device)
            labels = labels.to(device)

            outputs = model(features)
            loss = criterion(outputs, labels)

            _, predicted = torch.max(outputs, 1)
            accuracy = (predicted == labels).float().mean()

            tracker.update({"loss": loss.item(), "accuracy": accuracy.item()})

    return tracker.get_metrics()


def main(args):
    """主训练函数"""
    # 设备选择
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    print(f"Using device: {device}")

    # 创建数据集
    print("Creating datasets...")
    if args.synthetic:
        train_loader, val_loader = create_synthetic_dataset(
            num_train=args.num_train,
            num_val=args.num_val,
            batch_size=args.batch_size,
        )
    else:
        train_dataset = HandDataset(data_path=args.data_path, mode="train")
        val_dataset = HandDataset(data_path=args.data_path, mode="val")
        train_loader = train_dataset.get_dataloader(batch_size=args.batch_size)
        val_loader = val_dataset.get_dataloader(batch_size=args.batch_size)

    print(f"Train samples: {len(train_loader.dataset)}")
    print(f"Val samples: {len(val_loader.dataset)}")

    # 创建模型
    model = GestureClassifierNet(input_dim=66, num_classes=7).to(device)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    # 创建保存目录
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 训练循环
    best_val_acc = 0.0
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []

    print("\nStarting training...")
    for epoch in range(args.epochs):
        # 训练
        train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # 验证
        val_metrics = validate(model, val_loader, criterion, device)

        # 更新学习率
        scheduler.step()

        # 记录指标
        train_losses.append(train_metrics["loss"])
        val_losses.append(val_metrics["loss"])
        train_accs.append(train_metrics["accuracy"])
        val_accs.append(val_metrics["accuracy"])

        # 打印进度
        print(
            f"Epoch [{epoch+1}/{args.epochs}] "
            f"Train Loss: {train_metrics['loss']:.4f} "
            f"Train Acc: {train_metrics['accuracy']:.4f} "
            f"Val Loss: {val_metrics['loss']:.4f} "
            f"Val Acc: {val_metrics['accuracy']:.4f}"
        )

        # 保存最佳模型
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            torch.save(model.state_dict(), save_dir / "best_model.pth")
            print(f"  -> Saved best model (val_acc: {best_val_acc:.4f})")

    # 保存最终模型
    torch.save(model.state_dict(), save_dir / "final_model.pth")

    # 绘制训练曲线
    try:
        from gesture_recognition.utils.visualization import plot_training_curves

        plot_training_curves(
            train_losses, val_losses, train_accs, val_accs,
            save_path=str(save_dir / "training_curves.png"),
        )
    except Exception as e:
        print(f"Could not plot training curves: {e}")

    print(f"\nTraining completed!")
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Models saved to: {save_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train gesture classifier")

    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--data-path", type=str, default=None, help="Path to data JSON")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--num-train", type=int, default=1000, help="Number of training samples")
    parser.add_argument("--num-val", type=int, default=200, help="Number of validation samples")
    parser.add_argument("--save-dir", type=str, default="checkpoints", help="Save directory")
    parser.add_argument("--no-cuda", action="store_true", help="Disable CUDA")

    args = parser.parse_args()
    main(args)
