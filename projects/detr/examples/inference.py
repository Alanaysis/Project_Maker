"""
DETR 推理示例
"""

import torch
import torch.nn.functional as F
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.detr import build_detr
from src.matcher import box_cxcywh_to_xyxy


def post_process(outputs, target_sizes):
    """
    后处理：将模型输出转换为检测结果

    Args:
        outputs: 模型输出
        target_sizes: 目标图像尺寸 (batch_size, 2)

    Returns:
        results: 检测结果列表
    """
    out_logits, out_bbox = outputs['pred_logits'], outputs['pred_boxes']

    assert len(out_logits) == len(target_sizes)
    assert target_sizes.shape[1] == 2

    prob = F.softmax(out_logits, -1)
    scores, labels = prob[..., :-1].max(-1)

    # 将边界框转换为xyxy格式
    boxes = box_cxcywh_to_xyxy(out_bbox)

    # 缩放到目标尺寸
    img_h, img_w = target_sizes.unbind(1)
    scale_fct = torch.stack([img_w, img_h, img_w, img_h], dim=1)
    boxes = boxes * scale_fct[:, None, :]

    results = [{'scores': s, 'labels': l, 'boxes': b} for s, l, b in zip(scores, labels, boxes)]

    return results


def filter_predictions(results, threshold=0.5):
    """
    过滤低置信度的预测

    Args:
        results: 检测结果
        threshold: 置信度阈值

    Returns:
        filtered_results: 过滤后的结果
    """
    filtered_results = []
    for result in results:
        scores = result['scores']
        mask = scores > threshold

        filtered_results.append({
            'scores': scores[mask],
            'labels': result['labels'][mask],
            'boxes': result['boxes'][mask]
        })

    return filtered_results


def visualize_predictions(image, result, class_names=None):
    """
    可视化预测结果（打印到控制台）

    Args:
        image: 输入图像 (3, H, W)
        result: 检测结果
        class_names: 类别名称列表
    """
    print("\n" + "=" * 50)
    print("Detection Results")
    print("=" * 50)

    num_detections = len(result['scores'])
    print(f"Number of detections: {num_detections}")

    if num_detections == 0:
        print("No objects detected")
        return

    for i in range(num_detections):
        score = result['scores'][i].item()
        label = result['labels'][i].item()
        box = result['boxes'][i].tolist()

        if class_names and label < len(class_names):
            class_name = class_names[label]
        else:
            class_name = f"Class {label}"

        print(f"\nDetection {i + 1}:")
        print(f"  Class: {class_name}")
        print(f"  Confidence: {score:.4f}")
        print(f"  Box (x1, y1, x2, y2): [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")


def main():
    """
    主推理函数
    """
    # 模型参数
    num_classes = 5
    num_queries = 100
    hidden_dim = 256
    nhead = 8
    num_encoder_layers = 6
    num_decoder_layers = 6
    image_size = 320

    # 设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # 创建模型
    print("Building model...")
    model = build_detr(
        num_classes=num_classes,
        num_queries=num_queries,
        backbone_model='resnet18',
        hidden_dim=hidden_dim,
        nhead=nhead,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers
    )
    model = model.to(device)
    model.eval()

    # 类别名称（示例）
    class_names = ['person', 'car', 'dog', 'cat', 'bird']

    # 创建测试图像
    print("Creating test images...")
    test_images = torch.randn(2, 3, image_size, image_size).to(device)
    target_sizes = torch.tensor([[image_size, image_size], [image_size, image_size]]).to(device)

    # 推理
    print("Running inference...")
    with torch.no_grad():
        outputs = model(test_images)

    # 后处理
    results = post_process(outputs, target_sizes)

    # 过滤低置信度预测
    filtered_results = filter_predictions(results, threshold=0.3)

    # 可视化结果
    for i, result in enumerate(filtered_results):
        print(f"\n{'=' * 60}")
        print(f"Image {i + 1}")
        print(f"{'=' * 60}")
        visualize_predictions(test_images[i], result, class_names)

    # 统计信息
    print("\n" + "=" * 50)
    print("Statistics")
    print("=" * 50)
    for i, result in enumerate(filtered_results):
        num_det = len(result['scores'])
        avg_score = result['scores'].mean().item() if num_det > 0 else 0
        print(f"Image {i + 1}: {num_det} detections, avg confidence: {avg_score:.4f}")


if __name__ == '__main__':
    main()
