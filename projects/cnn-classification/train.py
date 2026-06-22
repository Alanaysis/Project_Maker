"""
CNN训练脚本

使用LeNet-5在MNIST数据集上训练
"""

import argparse
import torch
from pathlib import Path

from src import LeNet5, Trainer, get_mnist_dataloaders
from src.visualization import plot_training_history


def main():
    parser = argparse.ArgumentParser(description='Train CNN on MNIST')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
    parser.add_argument('--epochs', type=int, default=20, help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--optimizer', type=str, default='adam', choices=['adam', 'sgd', 'adamw'],
                        help='Optimizer')
    parser.add_argument('--scheduler', type=str, default=None, choices=['step', 'cosine', 'plateau'],
                        help='Learning rate scheduler')
    parser.add_argument('--save-dir', type=str, default='./checkpoints', help='Save directory')
    parser.add_argument('--data-dir', type=str, default='./data', help='Data directory')
    parser.add_argument('--early-stopping', type=int, default=None, help='Early stopping patience')

    args = parser.parse_args()

    # 创建保存目录
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 加载数据
    print("Loading MNIST dataset...")
    train_loader, val_loader, test_loader = get_mnist_dataloaders(
        data_dir=args.data_dir,
        batch_size=args.batch_size
    )

    print(f"Train samples: {len(train_loader.dataset)}")
    print(f"Val samples: {len(val_loader.dataset)}")
    print(f"Test samples: {len(test_loader.dataset)}")

    # 创建模型
    print("\nCreating LeNet-5 model...")
    model = LeNet5(num_classes=10, in_channels=1)

    # 创建训练器
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader
    )

    # 编译模型
    trainer.compile(
        optimizer=args.optimizer,
        lr=args.lr,
        scheduler=args.scheduler
    )

    # 训练
    print(f"\nStarting training for {args.epochs} epochs...")
    history = trainer.fit(
        epochs=args.epochs,
        save_dir=str(save_dir),
        early_stopping=args.early_stopping
    )

    # 测试
    print("\nEvaluating on test set...")
    test_loss, test_acc = trainer.test()

    # 绘制训练历史
    plot_training_history(history, save_path=str(save_dir / 'training_history.png'))

    # 保存最终结果
    results = {
        'test_loss': test_loss,
        'test_acc': test_acc,
        'best_val_acc': trainer.best_val_acc,
        'epochs_trained': len(history['train_loss'])
    }

    import json
    with open(save_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nTraining completed!")
    print(f"Best validation accuracy: {trainer.best_val_acc:.2f}%")
    print(f"Test accuracy: {test_acc:.2f}%")
    print(f"Results saved to {save_dir}")


if __name__ == '__main__':
    main()
