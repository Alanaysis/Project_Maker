"""
评估脚本

使用方法:
    python scripts/evaluate.py --model runs/best_model.pth
    python scripts/evaluate.py --model runs/best_model.pth --data-dir data/val

⭐ 重点理解:
- 模型评估流程
- 评估指标计算
- 结果分析
"""

import argparse
import torch
import yaml
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import YOLOModel
from src.data.dataset import create_dummy_dataset, create_dataloader
from src.data.transforms import get_val_transforms
from src.utils.metrics import compute_map


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='工业视觉检测 - 评估脚本')

    # 模型参数
    parser.add_argument('--model', type=str, required=True,
                        help='模型检查点路径')
    parser.add_argument('--num-classes', type=int, default=5,
                        help='类别数')

    # 数据参数
    parser.add_argument('--data-dir', type=str, default='data',
                        help='数据目录')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='批次大小')
    parser.add_argument('--image-size', type=int, default=640,
                        help='图像尺寸')

    # 评估参数
    parser.add_argument('--iou-threshold', type=float, default=0.5,
                        help='IoU 阈值')
    parser.add_argument('--conf-threshold', type=float, default=0.25,
                        help='置信度阈值')

    # 其他参数
    parser.add_argument('--device', type=str, default='auto',
                        help='设备')
    parser.add_argument('--workers', type=int, default=4,
                        help='数据加载器工作进程数')

    return parser.parse_args()


def get_device(device_str: str) -> torch.device:
    """获取设备"""
    if device_str == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(device_str)


def evaluate(model, dataloader, device, conf_threshold=0.25):
    """评估模型"""
    model.eval()

    all_predictions = []
    all_ground_truths = []

    with torch.no_grad():
        for batch_idx, (images, targets) in enumerate(dataloader):
            images = images.to(device)

            # 推理
            outputs = model(images)

            # 处理每个样本
            for i in range(len(images)):
                # 预测结果
                pred = {
                    'image_id': batch_idx * dataloader.batch_size + i,
                    'boxes': outputs['boxes'][i].cpu(),
                    'scores': outputs['scores'][i].cpu(),
                    'labels': outputs['labels'][i].cpu()
                }
                all_predictions.append(pred)

                # 真实标注
                gt = {
                    'image_id': batch_idx * dataloader.batch_size + i,
                    'boxes': targets[i]['boxes'],
                    'labels': targets[i]['labels']
                }
                all_ground_truths.append(gt)

            if (batch_idx + 1) % 10 == 0:
                print(f"  处理批次 {batch_idx + 1}/{len(dataloader)}")

    return all_predictions, all_ground_truths


def main():
    """主评估函数"""
    args = parse_args()

    print("=" * 60)
    print("工业视觉检测 - 评估脚本")
    print("=" * 60)

    # 设备
    device = get_device(args.device)
    print(f"\n设备: {device}")

    # 加载模型
    print(f"\n加载模型: {args.model}")
    model = YOLOModel.load_pretrained(args.model)
    model = model.to(device)
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    # 创建数据集
    print("\n创建数据集...")
    val_dataset = create_dummy_dataset(num_samples=50, num_classes=args.num_classes)

    val_loader = create_dataloader(
        val_dataset,
        batch_size=args.batch_size,
        num_workers=args.workers,
        shuffle=False
    )

    print(f"验证集大小: {len(val_dataset)}")

    # 评估
    print("\n开始评估...")
    predictions, ground_truths = evaluate(
        model, val_loader, device,
        conf_threshold=args.conf_threshold
    )

    # 计算指标
    print("\n计算评估指标...")
    results = compute_map(
        predictions, ground_truths,
        iou_thresholds=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    )

    # 打印结果
    print("\n评估结果:")
    print("-" * 40)
    print(f"  mAP@0.5:      {results.get('mAP_50', 0):.4f}")
    print(f"  mAP@0.75:     {results.get('mAP_75', 0):.4f}")
    print(f"  mAP@0.5:0.95: {results.get('mAP', 0):.4f}")

    # 按类别结果
    if 'ap_by_class_50' in results:
        print("\n按类别 AP@0.5:")
        for class_id, ap in results['ap_by_class_50'].items():
            print(f"  Class {class_id}: {ap:.4f}")

    print("\n" + "=" * 60)
    print("评估完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
