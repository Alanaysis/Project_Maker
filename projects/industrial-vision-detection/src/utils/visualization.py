"""
可视化工具实现

实现检测结果和训练过程的可视化。

核心功能:
- plot_detections: 绘制检测结果
- plot_training_curves: 绘制训练曲线
- plot_confusion_matrix: 绘制混淆矩阵

⭐ 重点理解:
- 可视化对调试和理解模型很重要
- 颜色编码可以帮助区分不同类别
- 训练曲线可以诊断训练问题

💡 值得思考:
- 如何选择合适的可视化方式？
- 如何处理大量检测结果的可视化？
- 如何可视化模型的注意力区域？
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Optional, Tuple
from pathlib import Path


def plot_detections(
    image: np.ndarray,
    detections: Dict,
    class_names: Optional[List[str]] = None,
    score_threshold: float = 0.5,
    save_path: Optional[str] = None,
    show: bool = True
) -> np.ndarray:
    """
    绘制检测结果

    Args:
        image: 输入图像 [H, W, 3] (RGB 格式)
        detections: 检测结果字典，包含:
            - boxes: 边界框 [N, 4] (x1, y1, x2, y2)
            - scores: 置信度 [N]
            - labels: 类别标签 [N]
        class_names: 类别名称列表
        score_threshold: 置信度阈值
        save_path: 保存路径
        show: 是否显示图像

    Returns:
        绘制了检测结果的图像

    使用示例:
        result = model.predict(image)
        plot_detections(image, result, class_names=['cat', 'dog'])
    """
    # 创建图像副本
    img = image.copy()

    # 获取检测结果
    boxes = detections.get('boxes', torch.zeros((0, 4)))
    scores = detections.get('scores', torch.zeros(0))
    labels = detections.get('labels', torch.zeros(0, dtype=torch.long))

    # 转换为 numpy
    if isinstance(boxes, torch.Tensor):
        boxes = boxes.numpy()
    if isinstance(scores, torch.Tensor):
        scores = scores.numpy()
    if isinstance(labels, torch.Tensor):
        labels = labels.numpy()

    # 创建图形
    fig, ax = plt.subplots(1, figsize=(12, 8))
    ax.imshow(img)

    # 预定义颜色
    colors = plt.cm.hsv(np.linspace(0, 1, 20))

    # 绘制每个检测框
    for i in range(len(boxes)):
        score = scores[i]
        if score < score_threshold:
            continue

        x1, y1, x2, y2 = boxes[i]
        label = labels[i]

        # 获取颜色
        color = colors[label % len(colors)]

        # 绘制边界框
        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=2,
            edgecolor=color,
            facecolor='none'
        )
        ax.add_patch(rect)

        # 绘制标签
        if class_names and label < len(class_names):
            class_name = class_names[label]
        else:
            class_name = f'Class {label}'

        text = f'{class_name}: {score:.2f}'
        ax.text(
            x1, y1 - 5,
            text,
            color='white',
            fontsize=10,
            bbox=dict(facecolor=color, alpha=0.7)
        )

    ax.set_axis_off()
    plt.tight_layout()

    # 保存图像
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图像已保存到: {save_path}")

    # 显示图像
    if show:
        plt.show()

    plt.close()

    return img


def plot_training_curves(
    history: Dict[str, List[float]],
    save_path: Optional[str] = None,
    show: bool = True
):
    """
    绘制训练曲线

    Args:
        history: 训练历史字典，包含:
            - train_loss: 训练损失列表
            - val_loss: 验证损失列表
            - mAP: mAP 列表
            - lr: 学习率列表
        save_path: 保存路径
        show: 是否显示图像

    使用示例:
        history = trainer.train(epochs=100)
        plot_training_curves(history)
    """
    # 确定子图数量
    num_plots = len(history)
    fig, axes = plt.subplots(num_plots, 1, figsize=(10, 4 * num_plots))

    if num_plots == 1:
        axes = [axes]

    # 绘制每个指标
    for ax, (name, values) in zip(axes, history.items()):
        ax.plot(values, label=name, linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel(name)
        ax.set_title(f'{name} over epochs')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存图像
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"训练曲线已保存到: {save_path}")

    # 显示图像
    if show:
        plt.show()

    plt.close()


def plot_confusion_matrix(
    confusion_matrix: np.ndarray,
    class_names: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    show: bool = True
):
    """
    绘制混淆矩阵

    Args:
        confusion_matrix: 混淆矩阵 [num_classes, num_classes]
        class_names: 类别名称列表
        save_path: 保存路径
        show: 是否显示图像
    """
    num_classes = confusion_matrix.shape[0]

    if class_names is None:
        class_names = [f'Class {i}' for i in range(num_classes)]

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 8))

    # 绘制混淆矩阵
    im = ax.imshow(confusion_matrix, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    # 设置标签
    ax.set(
        xticks=np.arange(num_classes),
        yticks=np.arange(num_classes),
        xticklabels=class_names,
        yticklabels=class_names,
        title='Confusion Matrix',
        ylabel='True label',
        xlabel='Predicted label'
    )

    # 旋转标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

    # 添加数值
    for i in range(num_classes):
        for j in range(num_classes):
            ax.text(
                j, i, str(confusion_matrix[i, j]),
                ha='center', va='center',
                color='white' if confusion_matrix[i, j] > confusion_matrix.max() / 2 else 'black'
            )

    plt.tight_layout()

    # 保存图像
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"混淆矩阵已保存到: {save_path}")

    # 显示图像
    if show:
        plt.show()

    plt.close()


def plot_feature_maps(
    feature_maps: torch.Tensor,
    num_channels: int = 16,
    save_path: Optional[str] = None,
    show: bool = True
):
    """
    可视化特征图

    Args:
        feature_maps: 特征图 [C, H, W]
        num_channels: 显示的通道数
        save_path: 保存路径
        show: 是否显示图像
    """
    # 选择前 num_channels 个通道
    if feature_maps.shape[0] > num_channels:
        feature_maps = feature_maps[:num_channels]

    num_channels = feature_maps.shape[0]
    cols = min(8, num_channels)
    rows = (num_channels + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))

    if rows == 1:
        axes = axes.reshape(1, -1)

    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if idx < num_channels:
                axes[i, j].imshow(feature_maps[idx].numpy(), cmap='viridis')
            axes[i, j].axis('off')

    plt.suptitle('Feature Maps')
    plt.tight_layout()

    # 保存图像
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"特征图已保存到: {save_path}")

    # 显示图像
    if show:
        plt.show()

    plt.close()


def create_visualization_grid(
    images: List[np.ndarray],
    detections: List[Dict],
    class_names: Optional[List[str]] = None,
    score_threshold: float = 0.5,
    grid_size: Tuple[int, int] = (2, 2)
) -> np.ndarray:
    """
    创建可视化网格

    Args:
        images: 图像列表
        detections: 检测结果列表
        class_names: 类别名称
        score_threshold: 置信度阈值
        grid_size: 网格大小 (rows, cols)

    Returns:
        网格图像
    """
    rows, cols = grid_size
    num_images = min(len(images), rows * cols)

    # 计算网格图像大小
    h, w = images[0].shape[:2]
    grid_h = h * rows
    grid_w = w * cols

    # 创建网格图像
    grid = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)

    # 预定义颜色
    colors = plt.cm.hsv(np.linspace(0, 1, 20))

    for idx in range(num_images):
        row = idx // cols
        col = idx % cols

        # 放置图像
        img = images[idx].copy()
        y1 = row * h
        y2 = (row + 1) * h
        x1 = col * w
        x2 = (col + 1) * w

        grid[y1:y2, x1:x2] = img

        # 绘制检测框
        if idx < len(detections):
            det = detections[idx]
            boxes = det.get('boxes', torch.zeros((0, 4)))
            scores = det.get('scores', torch.zeros(0))
            labels = det.get('labels', torch.zeros(0, dtype=torch.long))

            for i in range(len(boxes)):
                score = scores[i]
                if score < score_threshold:
                    continue

                bx1, by1, bx2, by2 = boxes[i].numpy()
                label = labels[i].item()

                # 调整到网格坐标
                bx1 = bx1 + x1
                by1 = by1 + y1
                bx2 = bx2 + x1
                by2 = by2 + y1

                # 使用 OpenCV 绘制
                import cv2
                color = (colors[label % len(colors)] * 255).astype(int)[:3]
                cv2.rectangle(grid, (int(bx1), int(by1)), (int(bx2), int(by2)), color, 2)

    return grid


def test_visualization():
    """
    测试可视化工具

    验证:
    1. 检测结果可视化正常
    2. 训练曲线绘制正常
    3. 混淆矩阵绘制正常
    """
    print("=" * 50)
    print("测试可视化工具")
    print("=" * 50)

    # 测试检测结果可视化
    print("\n1. 测试检测结果可视化")
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    detections = {
        'boxes': torch.tensor([[100, 100, 200, 200], [300, 300, 400, 400]]),
        'scores': torch.tensor([0.9, 0.8]),
        'labels': torch.tensor([0, 1])
    }
    class_names = ['defect_A', 'defect_B']

    # 绘制 (不显示)
    plot_detections(
        image, detections,
        class_names=class_names,
        score_threshold=0.5,
        show=False
    )
    print("   检测结果可视化完成")

    # 测试训练曲线
    print("\n2. 测试训练曲线")
    history = {
        'train_loss': [0.5, 0.4, 0.35, 0.3, 0.28],
        'val_loss': [0.55, 0.45, 0.4, 0.38, 0.36],
        'mAP': [0.3, 0.4, 0.5, 0.55, 0.58]
    }
    plot_training_curves(history, show=False)
    print("   训练曲线绘制完成")

    # 测试混淆矩阵
    print("\n3. 测试混淆矩阵")
    cm = np.array([[50, 5, 2], [3, 45, 4], [1, 2, 48]])
    plot_confusion_matrix(cm, class_names=['A', 'B', 'C'], show=False)
    print("   混淆矩阵绘制完成")

    print("\n✓ 可视化工具测试通过!")
    return True


if __name__ == '__main__':
    test_visualization()
