"""
CNN演示脚本

展示CNN的基本功能和可视化
"""

import torch
import matplotlib.pyplot as plt
from pathlib import Path

from src import LeNet5, get_mnist_dataloaders
from src.visualization import (
    plot_training_history,
    visualize_feature_maps,
    visualize_predictions,
    visualize_filters,
    load_history
)


def demo_model_structure():
    """演示模型结构"""
    print("=" * 60)
    print("LeNet-5 Model Structure")
    print("=" * 60)

    model = LeNet5(num_classes=10, in_channels=1)

    # 打印模型结构
    print(model)

    # 计算参数数量
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"\nTotal parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    # 测试前向传播
    x = torch.randn(1, 1, 32, 32)
    output = model(x)
    print(f"\nInput shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output probabilities: {torch.softmax(output, dim=1)}")


def demo_feature_extraction():
    """演示特征提取"""
    print("\n" + "=" * 60)
    print("Feature Extraction Demo")
    print("=" * 60)

    model = LeNet5(num_classes=10, in_channels=1)
    x = torch.randn(1, 1, 32, 32)

    features = model.get_feature_maps(x)

    print("\nFeature map shapes:")
    for name, feat in features.items():
        print(f"  {name}: {feat.shape}")


def demo_different_models():
    """演示不同模型"""
    print("\n" + "=" * 60)
    print("Different CNN Models")
    print("=" * 60)

    from src import AlexNetCIFAR, vgg_cifar

    models = {
        'LeNet-5': LeNet5(10, 1),
        'AlexNet': AlexNetCIFAR(10, 3),
        'VGG-11': vgg_cifar('vgg11', 10, 3)
    }

    print("\nModel comparison:")
    print("-" * 50)
    print(f"{'Model':<15} {'Parameters':<15} {'Input Shape':<15}")
    print("-" * 50)

    for name, model in models.items():
        params = sum(p.numel() for p in model.parameters())
        if name == 'LeNet-5':
            input_shape = '(1, 32, 32)'
        else:
            input_shape = '(3, 32, 32)'
        print(f"{name:<15} {params:<15,} {input_shape:<15}")


def demo_training_visualization():
    """演示训练可视化"""
    print("\n" + "=" * 60)
    print("Training Visualization Demo")
    print("=" * 60)

    # 模拟训练历史
    import numpy as np

    epochs = 20
    history = {
        'train_loss': [2.3 - 0.1 * i + 0.02 * np.random.randn() for i in range(epochs)],
        'val_loss': [2.3 - 0.08 * i + 0.03 * np.random.randn() for i in range(epochs)],
        'train_acc': [10 + 4 * i + 0.5 * np.random.randn() for i in range(epochs)],
        'val_acc': [10 + 3.5 * i + 0.8 * np.random.randn() for i in range(epochs)],
        'lr': [0.001] * epochs
    }

    # 限制准确率在合理范围内
    history['train_acc'] = [min(100, max(0, acc)) for acc in history['train_acc']]
    history['val_acc'] = [min(100, max(0, acc)) for acc in history['val_acc']]

    print("\nSimulated training history (last 5 epochs):")
    for i in range(-5, 0):
        print(f"  Epoch {epochs + i + 1}: "
              f"Train Loss={history['train_loss'][i]:.4f}, "
              f"Train Acc={history['train_acc'][i]:.2f}%, "
              f"Val Loss={history['val_loss'][i]:.4f}, "
              f"Val Acc={history['val_acc'][i]:.2f}%")


def demo_data_loading():
    """演示数据加载"""
    print("\n" + "=" * 60)
    print("Data Loading Demo")
    print("=" * 60)

    print("\nLoading MNIST dataset...")
    train_loader, val_loader, test_loader = get_mnist_dataloaders(
        batch_size=32,
        num_workers=0  # 演示时使用单线程
    )

    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")

    # 获取一个批次的数据
    data, target = next(iter(train_loader))
    print(f"\nBatch data shape: {data.shape}")
    print(f"Batch target shape: {target.shape}")
    print(f"Target labels: {target[:10].tolist()}")


def main():
    """主函数"""
    print("CNN Classification Demo")
    print("=" * 60)

    # 演示模型结构
    demo_model_structure()

    # 演示特征提取
    demo_feature_extraction()

    # 演示不同模型
    demo_different_models()

    # 演示训练可视化
    demo_training_visualization()

    # 演示数据加载（需要网络连接下载数据）
    try:
        demo_data_loading()
    except Exception as e:
        print(f"\nData loading demo skipped: {e}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
