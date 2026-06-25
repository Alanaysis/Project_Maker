"""
Evaluate Script - 模型评估脚本

使用方法：
    python scripts/evaluate.py --checkpoint checkpoints/best_model.pth
    python scripts/evaluate.py --checkpoint checkpoints/best_model.pth --synthetic
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
import numpy as np
from torch.utils.data import DataLoader

from gesture_recognition.models.gesture_classifier import (
    GestureClassifierNet,
    GESTURE_CLASSES,
)
from gesture_recognition.data.hand_dataset import HandDataset
from gesture_recognition.utils.metrics import (
    calculate_gesture_accuracy,
    calculate_precision_recall_f1,
)


def evaluate_model(
    model: GestureClassifierNet,
    dataloader: DataLoader,
    device: torch.device,
) -> dict:
    """
    评估模型性能

    Args:
        model: 模型
        dataloader: 数据加载器
        device: 设备

    Returns:
        dict: 评估结果
    """
    model.eval()

    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for features, labels in dataloader:
            features = features.to(device)
            labels = labels.to(device)

            outputs = model(features)
            _, predicted = torch.max(outputs, 1)

            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 计算指标
    accuracy_metrics = calculate_gesture_accuracy(
        all_predictions, all_labels, GESTURE_CLASSES
    )

    prf_metrics = calculate_precision_recall_f1(
        all_predictions, all_labels, len(GESTURE_CLASSES), GESTURE_CLASSES
    )

    return {
        "accuracy": accuracy_metrics,
        "precision_recall_f1": prf_metrics,
    }


def main(args):
    """主评估函数"""
    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    print(f"Using device: {device}")

    # 加载模型
    print(f"Loading model from {args.checkpoint}...")
    model = GestureClassifierNet(input_dim=66, num_classes=7).to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device))

    # 创建数据集
    print("Creating dataset...")
    if args.synthetic:
        dataset = HandDataset(num_samples=args.num_samples, mode="val")
    else:
        dataset = HandDataset(data_path=args.data_path, mode="val")

    dataloader = dataset.get_dataloader(batch_size=args.batch_size, shuffle=False)
    print(f"Evaluation samples: {len(dataset)}")

    # 评估
    print("\nEvaluating...")
    results = evaluate_model(model, dataloader, device)

    # 打印结果
    print("\n" + "=" * 50)
    print("Evaluation Results")
    print("=" * 50)

    print(f"\nOverall Accuracy: {results['accuracy']['accuracy']:.4f}")

    print("\nPer-class Accuracy:")
    print("-" * 30)
    for cls_name, acc in results["accuracy"]["per_class_accuracy"].items():
        print(f"  {cls_name:15s}: {acc:.4f}")

    print("\nPrecision / Recall / F1:")
    print("-" * 50)
    print(f"{'Class':15s} {'Precision':10s} {'Recall':10s} {'F1':10s} {'Support':10s}")
    print("-" * 50)

    for cls_name, metrics in results["precision_recall_f1"].items():
        if cls_name == "macro_avg":
            print("-" * 50)
            print(
                f"{'Macro Avg':15s} "
                f"{metrics['precision']:10.4f} "
                f"{metrics['recall']:10.4f} "
                f"{metrics['f1']:10.4f}"
            )
        else:
            print(
                f"{cls_name:15s} "
                f"{metrics['precision']:10.4f} "
                f"{metrics['recall']:10.4f} "
                f"{metrics['f1']:10.4f} "
                f"{metrics['support']:10d}"
            )

    # 打印混淆矩阵
    print("\nConfusion Matrix:")
    print("-" * 50)
    cm = np.array(results["accuracy"]["confusion_matrix"])
    print(cm)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate gesture classifier")

    parser.add_argument("--checkpoint", type=str, required=True, help="Model checkpoint path")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--data-path", type=str, default=None, help="Path to data JSON")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--num-samples", type=int, default=200, help="Number of samples")
    parser.add_argument("--no-cuda", action="store_true", help="Disable CUDA")

    args = parser.parse_args()
    main(args)
