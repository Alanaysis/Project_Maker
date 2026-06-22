"""
可视化工具

用于可视化训练过程、模型结构、特征图等
"""

import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json


def plot_training_history(history: Dict[str, List[float]], save_path: Optional[str] = None):
    """
    绘制训练历史

    参数：
        history: 训练历史字典
        save_path: 保存路径
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # 损失曲线
    axes[0].plot(history['train_loss'], label='Train Loss')
    axes[0].plot(history['val_loss'], label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True)

    # 准确率曲线
    axes[1].plot(history['train_acc'], label='Train Acc')
    axes[1].plot(history['val_acc'], label='Val Acc')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy (%)')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_confusion_matrix(confusion: torch.Tensor, class_names: List[str], save_path: Optional[str] = None):
    """
    绘制混淆矩阵

    参数：
        confusion: 混淆矩阵
        class_names: 类别名称
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # 归一化
    confusion_normalized = confusion / confusion.sum(dim=1, keepdim=True)

    im = ax.imshow(confusion_normalized.numpy(), cmap='Blues')

    # 添加数值
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            text = ax.text(j, i, f'{confusion[i][j]:.0f}',
                          ha="center", va="center", color="black", fontsize=10)

    ax.set_xticks(np.arange(len(class_names)))
    ax.set_yticks(np.arange(len(class_names)))
    ax.set_xticklabels(class_names)
    ax.set_yticklabels(class_names)

    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    ax.set_title('Confusion Matrix')

    plt.colorbar(im)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def visualize_feature_maps(model: nn.Module, image: torch.Tensor, save_path: Optional[str] = None):
    """
    可视化特征图

    参数：
        model: CNN模型
        image: 输入图像
        save_path: 保存路径
    """
    model.eval()

    # 获取特征图
    with torch.no_grad():
        features = model.get_feature_maps(image.unsqueeze(0))

    # 绘制每层特征图
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    for idx, (name, feat) in enumerate(features.items()):
        ax = axes[idx // 2][idx % 2]

        # 取前16个特征图
        feat = feat.squeeze(0)[:16]
        grid_size = int(np.ceil(np.sqrt(len(feat))))

        # 创建网格
        grid = torch.zeros(grid_size * feat.shape[1], grid_size * feat.shape[2])
        for i in range(len(feat)):
            row = i // grid_size
            col = i % grid_size
            grid[row * feat.shape[1]:(row + 1) * feat.shape[1],
                 col * feat.shape[2]:(col + 1) * feat.shape[2]] = feat[i]

        ax.imshow(grid.numpy(), cmap='viridis')
        ax.set_title(f'{name} ({len(feat)} channels)')
        ax.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def visualize_predictions(
    model: nn.Module,
    test_loader: torch.utils.data.DataLoader,
    device: torch.device,
    num_samples: int = 16,
    save_path: Optional[str] = None
):
    """
    可视化预测结果

    参数：
        model: 模型
        test_loader: 测试数据加载器
        device: 计算设备
        num_samples: 样本数量
        save_path: 保存路径
    """
    model.eval()

    # 获取一批数据
    data, target = next(iter(test_loader))
    data, target = data[:num_samples].to(device), target[:num_samples]

    # 预测
    with torch.no_grad():
        output = model(data)
        _, predicted = output.max(1)

    # 绘制
    grid_size = int(np.ceil(np.sqrt(num_samples)))
    fig, axes = plt.subplots(grid_size, grid_size, figsize=(10, 10))

    for i in range(num_samples):
        ax = axes[i // grid_size][i % grid_size]
        img = data[i].cpu().squeeze()
        ax.imshow(img, cmap='gray')

        color = 'green' if predicted[i] == target[i] else 'red'
        ax.set_title(f'Pred: {predicted[i]}\nTrue: {target[i]}', color=color)
        ax.axis('off')

    # 隐藏多余的子图
    for i in range(num_samples, grid_size * grid_size):
        axes[i // grid_size][i % grid_size].axis('off')

    plt.suptitle('Model Predictions', fontsize=16)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def visualize_filters(model: nn.Module, save_path: Optional[str] = None):
    """
    可视化卷积核

    参数：
        model: CNN模型
        save_path: 保存路径
    """
    # 获取第一个卷积层的权重
    first_conv = None
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            first_conv = module
            break

    if first_conv is None:
        print("No Conv2d layer found")
        return

    weights = first_conv.weight.data.cpu()

    # 归一化到[0, 1]
    weights = (weights - weights.min()) / (weights.max() - weights.min())

    # 绘制
    num_filters = weights.shape[0]
    grid_size = int(np.ceil(np.sqrt(num_filters)))

    fig, axes = plt.subplots(grid_size, grid_size, figsize=(10, 10))

    for i in range(num_filters):
        ax = axes[i // grid_size][i % grid_size]
        if weights.shape[1] == 1:
            ax.imshow(weights[i].squeeze(), cmap='gray')
        else:
            ax.imshow(weights[i].permute(1, 2, 0))
        ax.axis('off')
        ax.set_title(f'Filter {i + 1}')

    for i in range(num_filters, grid_size * grid_size):
        axes[i // grid_size][i % grid_size].axis('off')

    plt.suptitle('First Conv Layer Filters', fontsize=16)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def load_history(history_path: str) -> Dict[str, List[float]]:
    """
    加载训练历史

    参数：
        history_path: 历史文件路径

    返回：
        训练历史字典
    """
    with open(history_path, 'r') as f:
        return json.load(f)
