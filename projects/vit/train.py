#!/usr/bin/env python3
"""
Vision Transformer 训练脚本

使用 MNIST 或 CIFAR-10 数据集训练 ViT 模型。

用法：
    # 使用 MNIST 数据集（默认）
    python train.py

    # 使用 CIFAR-10 数据集
    python train.py --dataset cifar10

    # 自定义参数
    python train.py --epochs 20 --lr 1e-3 --batch_size 128 --model tiny

    # 快速测试
    python train.py --epochs 1 --dataset mnist --model tiny
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from src.vit import VisionTransformer
from src.trainer import ViTTrainer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Train Vision Transformer')

    # 数据集参数
    parser.add_argument('--dataset', type=str, default='mnist',
                        choices=['mnist', 'cifar10'],
                        help='Dataset to use (default: mnist)')
    parser.add_argument('--data_dir', type=str, default='./data',
                        help='Data directory (default: ./data)')

    # 模型参数
    parser.add_argument('--model', type=str, default='tiny',
                        choices=['tiny', 'small', 'base'],
                        help='Model size (default: tiny)')
    parser.add_argument('--patch_size', type=int, default=None,
                        help='Patch size (auto-selected based on dataset if not set)')

    # 训练参数
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of epochs (default: 10)')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Batch size (default: 64)')
    parser.add_argument('--lr', type=float, default=3e-4,
                        help='Learning rate (default: 3e-4)')
    parser.add_argument('--weight_decay', type=float, default=0.01,
                        help='Weight decay (default: 0.01)')
    parser.add_argument('--label_smoothing', type=float, default=0.1,
                        help='Label smoothing (default: 0.1)')

    # 其他参数
    parser.add_argument('--save_path', type=str, default='best_model.pth',
                        help='Model save path (default: best_model.pth)')
    parser.add_argument('--device', type=str, default=None,
                        help='Device (auto-detected if not set)')

    return parser.parse_args()


def main():
    args = parse_args()

    # 根据数据集确定参数
    if args.dataset == 'mnist':
        img_size = 28
        in_channels = 1
        num_classes = 10
        patch_size = args.patch_size or 7  # 28 / 7 = 4 patches per dim

        print(f"Dataset: MNIST ({img_size}x{img_size}, {in_channels}ch, {num_classes} classes)")
        print(f"Patch size: {patch_size} -> {img_size // patch_size}x{img_size // patch_size} patches")

        train_loader, val_loader = ViTTrainer.create_mnist_loaders(
            batch_size=args.batch_size,
            img_size=img_size,
            data_dir=args.data_dir,
        )

    elif args.dataset == 'cifar10':
        img_size = 32
        in_channels = 3
        num_classes = 10
        patch_size = args.patch_size or 4  # 32 / 4 = 8 patches per dim

        print(f"Dataset: CIFAR-10 ({img_size}x{img_size}, {in_channels}ch, {num_classes} classes)")
        print(f"Patch size: {patch_size} -> {img_size // patch_size}x{img_size // patch_size} patches")

        train_loader, val_loader = ViTTrainer.create_cifar10_loaders(
            batch_size=args.batch_size,
            img_size=img_size,
            data_dir=args.data_dir,
        )

    # 创建模型
    if args.model == 'tiny':
        model = VisionTransformer.vit_tiny(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
        )
    elif args.model == 'small':
        model = VisionTransformer.vit_small(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
        )
    elif args.model == 'base':
        model = VisionTransformer.vit_base(
            img_size=img_size,
            patch_size=patch_size,
            num_classes=num_classes,
        )

    # 打印模型信息
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model: ViT-{args.model.capitalize()}")
    print(f"Parameters: {total_params:,}")
    print()

    # 创建训练器并训练
    trainer = ViTTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        lr=args.lr,
        weight_decay=args.weight_decay,
        epochs=args.epochs,
        label_smoothing=args.label_smoothing,
        device=args.device,
    )

    history = trainer.train(save_path=args.save_path)

    # 打印训练结果
    print()
    print("Training History:")
    print(f"  Best Train Acc: {max(history['train_acc']):.4f}")
    print(f"  Best Val Acc:   {max(history['val_acc']):.4f}")
    print(f"  Final LR:       {history['lr'][-1]:.6f}")


if __name__ == '__main__':
    main()
