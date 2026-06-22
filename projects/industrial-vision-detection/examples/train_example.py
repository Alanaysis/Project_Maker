"""
训练示例

演示如何使用本项目训练 YOLO 模型。

使用方法:
    python examples/train_example.py

⭐ 重点理解:
- 训练流程的完整步骤
- 数据加载和预处理
- 模型训练和评估
"""

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOv8Tiny
from src.data.dataset import create_dummy_dataset, create_dataloader
from src.data.transforms import get_train_transforms


def train_one_epoch(
    model: torch.nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    device: torch.device
) -> float:
    """
    训练一个 epoch

    Args:
        model: 模型
        dataloader: 数据加载器
        optimizer: 优化器
        device: 设备

    Returns:
        平均损失
    """
    model.train()
    total_loss = 0

    for batch_idx, (images, targets) in enumerate(dataloader):
        # 移动到设备
        images = images.to(device)

        # 前向传播
        outputs = model(images, targets)
        loss = outputs['total_loss']

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        # 打印进度
        if (batch_idx + 1) % 10 == 0:
            print(f"  Batch {batch_idx + 1}/{len(dataloader)}, Loss: {loss.item():.4f}")

    return total_loss / len(dataloader)


def evaluate(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device
) -> dict:
    """
    评估模型

    Args:
        model: 模型
        dataloader: 数据加载器
        device: 设备

    Returns:
        评估指标
    """
    model.eval()
    total_loss = 0

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            outputs = model(images, targets)
            total_loss += outputs['total_loss'].item()

    return {'val_loss': total_loss / len(dataloader)}


def main():
    """主训练函数"""
    print("=" * 60)
    print("工业视觉检测 - 训练示例")
    print("=" * 60)

    # 配置
    num_classes = 5
    epochs = 5
    batch_size = 4
    learning_rate = 0.001

    # 设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n使用设备: {device}")

    # 创建模型
    print("\n创建模型...")
    model = YOLOv8Tiny(num_classes=num_classes)
    model = model.to(device)

    # 打印模型参数量
    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    # 创建数据集
    print("\n创建数据集...")
    train_dataset = create_dummy_dataset(num_samples=50, num_classes=num_classes)
    val_dataset = create_dummy_dataset(num_samples=10, num_classes=num_classes)

    # 创建数据加载器
    train_loader = create_dataloader(
        train_dataset,
        batch_size=batch_size,
        num_workers=0,
        shuffle=True
    )
    val_loader = create_dataloader(
        val_dataset,
        batch_size=batch_size,
        num_workers=0,
        shuffle=False
    )

    print(f"训练集大小: {len(train_dataset)}")
    print(f"验证集大小: {len(val_dataset)}")

    # 创建优化器
    optimizer = optim.Adam(
        model.parameters(),
        lr=learning_rate,
        weight_decay=0.0005
    )

    # 创建学习率调度器
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=epochs,
        eta_min=learning_rate * 0.01
    )

    # 训练循环
    print("\n开始训练...")
    history = {
        'train_loss': [],
        'val_loss': [],
        'lr': []
    }

    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")
        print("-" * 40)

        # 训练
        train_loss = train_one_epoch(model, train_loader, optimizer, device)

        # 验证
        val_metrics = evaluate(model, val_loader, device)

        # 更新学习率
        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]

        # 记录历史
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_metrics['val_loss'])
        history['lr'].append(current_lr)

        # 打印结果
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_metrics['val_loss']:.4f}")
        print(f"  Learning Rate: {current_lr:.6f}")

    # 保存模型
    print("\n保存模型...")
    save_path = 'yolov8_tiny_trained.pth'
    model.save_pretrained(save_path)
    print(f"模型已保存到: {save_path}")

    # 打印训练历史
    print("\n训练历史:")
    for key, values in history.items():
        print(f"  {key}: {[f'{v:.4f}' for v in values]}")

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)

    return model, history


if __name__ == '__main__':
    main()
