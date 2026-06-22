"""
推理示例

演示如何使用训练好的模型进行推理。

使用方法:
    python examples/inference_example.py

⭐ 重点理解:
- 推理流程
- 后处理 (NMS)
- 结果可视化
"""

import torch
import numpy as np
import cv2
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOv8Tiny
from src.utils.visualization import plot_detections


def create_test_image(
    width: int = 640,
    height: int = 640,
    num_objects: int = 3
) -> tuple:
    """
    创建测试图像和标注

    Args:
        width: 图像宽度
        height: 图像高度
        num_objects: 目标数量

    Returns:
        image: 测试图像
        ground_truth: 真实标注
    """
    # 创建背景图像
    image = np.random.randint(100, 200, (height, width, 3), dtype=np.uint8)

    # 类别颜色
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]

    boxes = []
    labels = []

    for i in range(num_objects):
        # 随机位置和大小
        x1 = np.random.randint(50, width - 150)
        y1 = np.random.randint(50, height - 150)
        w = np.random.randint(50, 150)
        h = np.random.randint(50, 150)
        x2 = x1 + w
        y2 = y1 + h

        # 随机类别
        label = np.random.randint(0, 5)
        color = colors[label]

        # 绘制矩形
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

        # 添加标签
        cv2.putText(
            image,
            f'Class {label}',
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

        # 保存标注
        boxes.append([x1 / width, y1 / height, x2 / width, y2 / height])
        labels.append(label)

    ground_truth = {
        'boxes': torch.tensor(boxes, dtype=torch.float32),
        'labels': torch.tensor(labels, dtype=torch.long)
    }

    return image, ground_truth


def main():
    """主推理函数"""
    print("=" * 60)
    print("工业视觉检测 - 推理示例")
    print("=" * 60)

    # 配置
    num_classes = 5
    conf_threshold = 0.3
    iou_threshold = 0.5

    # 创建模型
    print("\n创建模型...")
    model = YOLOv8Tiny(num_classes=num_classes)
    model.eval()

    print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 创建测试图像
    print("\n创建测试图像...")
    image, ground_truth = create_test_image(
        width=640,
        height=640,
        num_objects=3
    )

    print(f"图像形状: {image.shape}")
    print(f"真实标注: {len(ground_truth['boxes'])} 个目标")

    # 推理
    print("\n执行推理...")
    result = model.predict(
        image,
        conf_threshold=conf_threshold,
        iou_threshold=iou_threshold
    )

    print(f"检测结果:")
    print(f"  检测到 {len(result['boxes'])} 个目标")
    print(f"  边界框形状: {result['boxes'].shape}")
    print(f"  置信度: {result['scores']}")
    print(f"  类别标签: {result['labels']}")

    # 可视化
    print("\n可视化结果...")
    class_names = [f'Defect_{i}' for i in range(num_classes)]

    # 绘制检测结果
    plot_detections(
        image,
        result,
        class_names=class_names,
        score_threshold=conf_threshold,
        save_path='detection_result.png',
        show=False
    )

    print("\n检测结果已保存到: detection_result.png")

    # 打印详细结果
    print("\n详细检测结果:")
    for i in range(len(result['boxes'])):
        box = result['boxes'][i]
        score = result['scores'][i]
        label = result['labels'][i]

        if score >= conf_threshold:
            print(f"  目标 {i + 1}:")
            print(f"    类别: {class_names[label]}")
            print(f"    置信度: {score:.4f}")
            print(f"    边界框: [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")

    print("\n" + "=" * 60)
    print("推理完成!")
    print("=" * 60)

    return result


if __name__ == '__main__':
    main()
