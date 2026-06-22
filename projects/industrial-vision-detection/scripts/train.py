"""
训练脚本

使用方法:
    python scripts/train.py --config configs/default.yaml
    python scripts/train.py --epochs 100 --batch-size 16

⭐ 重点理解:
- 命令行参数解析
- 配置文件加载
- 训练流程控制
"""

import argparse
import torch
import yaml
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOv8Tiny
from src.data.dataset import create_dummy_dataset, create_dataloader
from src.data.transforms import get_train_transforms, get_val_transforms


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='工业视觉检测 - 训练脚本')

    # 配置文件
    parser.add_argument('--config', type=str, default='configs/default.yaml',
                        help='配置文件路径')

    # 模型参数
    parser.add_argument('--model', type=str, default='yolov8_tiny',
                        help='模型类型')
    parser.add_argument('--num-classes', type=int, default=5,
                        help='类别数')

    # 训练参数
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='批次大小')
    parser.add_argument('--lr', type=float, default=0.01,
                        help='学习率')
    parser.add_argument('--weight-decay', type=float, default=0.0005,
                        help='权重衰减')

    # 数据参数
    parser.add_argument('--data-dir', type=str, default='data',
                        help='数据目录')
    parser.add_argument('--image-size', type=int, default=640,
                        help='图像尺寸')

    # 其他参数
    parser.add_argument('--device', type=str, default='auto',
                        help='设备 (cpu/cuda/auto)')
    parser.add_argument('--workers', type=int, default=4,
                        help='数据加载器工作进程数')
    parser.add_argument('--save-dir', type=str, default='runs/',
                        help='保存目录')
    parser.add_argument('--resume', type=str, default=None,
                        help='恢复训练的检查点路径')

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def get_device(device_str: str) -> torch.device:
    """获取设备"""
    if device_str == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(device_str)


def train_one_epoch(model, dataloader, optimizer, device):
    """训练一个 epoch"""
    model.train()
    total_loss = 0

    for batch_idx, (images, targets) in enumerate(dataloader):
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


def validate(model, dataloader, device):
    """验证模型"""
    model.eval()
    total_loss = 0

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            outputs = model(images, targets)
            total_loss += outputs['total_loss'].item()

    return total_loss / len(dataloader)


def main():
    """主训练函数"""
    args = parse_args()

    print("=" * 60)
    print("工业视觉检测 - 训练脚本")
    print("=" * 60)

    # 加载配置
    if os.path.exists(args.config):
        config = load_config(args.config)
        print(f"\n加载配置: {args.config}")
    else:
        config = {}
        print("\n使用默认配置")

    # 设备
    device = get_device(args.device)
    print(f"\n设备: {device}")

    # 创建模型
    print("\n创建模型...")
    model = YOLOv8Tiny(num_classes=args.num_classes)
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    # 恢复训练
    if args.resume:
        print(f"\n恢复训练: {args.resume}")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])

    # 创建数据集
    print("\n创建数据集...")
    train_dataset = create_dummy_dataset(num_samples=100, num_classes=args.num_classes)
    val_dataset = create_dummy_dataset(num_samples=20, num_classes=args.num_classes)

    train_loader = create_dataloader(
        train_dataset,
        batch_size=args.batch_size,
        num_workers=args.workers,
        shuffle=True
    )
    val_loader = create_dataloader(
        val_dataset,
        batch_size=args.batch_size,
        num_workers=args.workers,
        shuffle=False
    )

    # 优化器
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay
    )

    # 学习率调度器
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs,
        eta_min=args.lr * 0.01
    )

    # 保存目录
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 训练循环
    print("\n开始训练...")
    best_val_loss = float('inf')

    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        print("-" * 40)

        # 训练
        train_loss = train_one_epoch(model, train_loader, optimizer, device)

        # 验证
        val_loss = validate(model, val_loader, device)

        # 更新学习率
        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]

        # 打印结果
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_loss:.4f}")
        print(f"  Learning Rate: {current_lr:.6f}")

        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_path = save_dir / 'best_model.pth'
            model.save_pretrained(str(save_path))
            print(f"  保存最佳模型: {save_path}")

        # 定期保存检查点
        if (epoch + 1) % 10 == 0:
            save_path = save_dir / f'checkpoint_epoch_{epoch + 1}.pth'
            model.save_pretrained(str(save_path))
            print(f"  保存检查点: {save_path}")

    print("\n" + "=" * 60)
    print("训练完成!")
    print(f"最佳验证损失: {best_val_loss:.4f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
