"""
超分辨率模型训练脚本

使用方法：
    python train.py --model srcnn --epochs 100 --scale_factor 2
    python train.py --model espcn --epochs 100 --scale_factor 2
"""

import argparse
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.trainer import SRTrainer
from src.dataset import create_synthetic_dataset
from src.utils import set_seed, plot_training_history


def main():
    parser = argparse.ArgumentParser(description='Train Super Resolution Model')

    # 模型参数
    parser.add_argument('--model', type=str, default='srcnn',
                        choices=['srcnn', 'espcn', 'edsr'],
                        help='Model name (default: srcnn)')
    parser.add_argument('--scale_factor', type=int, default=2,
                        help='Scale factor (default: 2)')
    parser.add_argument('--num_features', type=int, default=64,
                        help='Number of features (default: 64)')

    # 训练参数
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs (default: 100)')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size (default: 16)')
    parser.add_argument('--learning_rate', type=float, default=1e-4,
                        help='Learning rate (default: 1e-4)')
    parser.add_argument('--patch_size', type=int, default=96,
                        help='Training patch size (default: 96)')

    # 数据参数
    parser.add_argument('--train_dir', type=str, default='data/train',
                        help='Training data directory')
    parser.add_argument('--val_dir', type=str, default='data/val',
                        help='Validation data directory')

    # 其他参数
    parser.add_argument('--checkpoint_dir', type=str, default='checkpoints',
                        help='Checkpoint directory')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='Number of data loading workers')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--create_synthetic', action='store_true',
                        help='Create synthetic dataset for testing')

    args = parser.parse_args()

    # 设置随机种子
    set_seed(args.seed)

    # 创建合成数据集（用于测试）
    if args.create_synthetic:
        print("Creating synthetic dataset...")
        create_synthetic_dataset(args.train_dir, num_images=100, image_size=256)
        create_synthetic_dataset(args.val_dir, num_images=20, image_size=256)

    # 检查数据目录
    if not os.path.exists(args.train_dir):
        print(f"Error: Training directory {args.train_dir} does not exist")
        print("Use --create_synthetic to create a synthetic dataset")
        sys.exit(1)

    # 创建训练器
    trainer = SRTrainer(
        model_name=args.model,
        scale_factor=args.scale_factor,
        learning_rate=args.learning_rate,
        checkpoint_dir=args.checkpoint_dir
    )

    # 打印模型摘要
    print("\n" + "="*50)
    print("Model Summary")
    print("="*50)
    print(trainer.get_model_summary())

    # 训练模型
    print("\n" + "="*50)
    print("Training")
    print("="*50)

    history = trainer.train(
        train_dir=args.train_dir,
        val_dir=args.val_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        patch_size=args.patch_size,
        num_workers=args.num_workers
    )

    # 绘制训练历史
    plot_training_history(history, save_path=os.path.join(args.checkpoint_dir, 'training_history.png'))

    print("\n" + "="*50)
    print("Training Complete!")
    print("="*50)
    print(f"Checkpoints saved to: {args.checkpoint_dir}")
    print(f"Best model: {os.path.join(args.checkpoint_dir, 'best.pth')}")


if __name__ == '__main__':
    main()
