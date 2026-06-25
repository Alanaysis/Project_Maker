"""
Metrics - 评估指标

功能：
1. 关键点检测准确率
2. 手势分类准确率
3. 混淆矩阵
4. 各类别准确率

学习要点：
- 理解评估指标的含义
- 掌握多分类评估方法
- 学会分析模型性能
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


def calculate_keypoint_accuracy(
    predicted: np.ndarray,
    ground_truth: np.ndarray,
    threshold: float = 0.05,
) -> dict:
    """
    计算关键点检测准确率

    使用归一化欧氏距离 (NED) 作为评估指标

    Args:
        predicted: (N, 21, 2) 预测关键点
        ground_truth: (N, 21, 2) 真实关键点
        threshold: 距离阈值（归一化坐标）

    Returns:
        dict: 包含各项指标
    """
    # 计算每个关键点的欧氏距离
    distances = np.sqrt(np.sum((predicted - ground_truth) ** 2, axis=2))

    # 整体准确率（距离小于阈值的比例）
    accuracy = np.mean(distances < threshold)

    # 每个关键点的平均距离
    mean_distance_per_keypoint = np.mean(distances, axis=0)

    # 每个关键点的准确率
    accuracy_per_keypoint = np.mean(distances < threshold, axis=0)

    return {
        "accuracy": float(accuracy),
        "mean_distance": float(np.mean(distances)),
        "mean_distance_per_keypoint": mean_distance_per_keypoint.tolist(),
        "accuracy_per_keypoint": accuracy_per_keypoint.tolist(),
    }


def calculate_gesture_accuracy(
    predicted: List[int],
    ground_truth: List[int],
    class_names: Optional[Dict[int, str]] = None,
) -> dict:
    """
    计算手势分类准确率

    Args:
        predicted: 预测类别列表
        ground_truth: 真实类别列表
        class_names: 类别名称映射

    Returns:
        dict: 包含各项指标
    """
    predicted = np.array(predicted)
    ground_truth = np.array(ground_truth)

    # 整体准确率
    accuracy = np.mean(predicted == ground_truth)

    # 各类别准确率
    unique_classes = np.unique(ground_truth)
    per_class_accuracy = {}

    for cls in unique_classes:
        mask = ground_truth == cls
        if mask.sum() > 0:
            cls_acc = np.mean(predicted[mask] == cls)
            cls_name = class_names.get(cls, str(cls)) if class_names else str(cls)
            per_class_accuracy[cls_name] = float(cls_acc)

    # 混淆矩阵
    num_classes = max(predicted.max(), ground_truth.max()) + 1
    confusion_matrix = np.zeros((num_classes, num_classes), dtype=int)
    for pred, gt in zip(predicted, ground_truth):
        confusion_matrix[gt, pred] += 1

    return {
        "accuracy": float(accuracy),
        "per_class_accuracy": per_class_accuracy,
        "confusion_matrix": confusion_matrix.tolist(),
    }


def calculate_precision_recall_f1(
    predicted: List[int],
    ground_truth: List[int],
    num_classes: int,
    class_names: Optional[Dict[int, str]] = None,
) -> dict:
    """
    计算精确率、召回率、F1分数

    Args:
        predicted: 预测类别列表
        ground_truth: 真实类别列表
        num_classes: 类别数量
        class_names: 类别名称映射

    Returns:
        dict: 包含各项指标
    """
    predicted = np.array(predicted)
    ground_truth = np.array(ground_truth)

    results = {}
    macro_precision = 0
    macro_recall = 0
    macro_f1 = 0
    valid_classes = 0

    for cls in range(num_classes):
        # True Positive, False Positive, False Negative
        tp = np.sum((predicted == cls) & (ground_truth == cls))
        fp = np.sum((predicted == cls) & (ground_truth != cls))
        fn = np.sum((predicted != cls) & (ground_truth == cls))

        # 计算指标
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        cls_name = class_names.get(cls, str(cls)) if class_names else str(cls)
        results[cls_name] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "support": int(np.sum(ground_truth == cls)),
        }

        if np.sum(ground_truth == cls) > 0:
            macro_precision += precision
            macro_recall += recall
            macro_f1 += f1
            valid_classes += 1

    # 宏平均
    if valid_classes > 0:
        results["macro_avg"] = {
            "precision": float(macro_precision / valid_classes),
            "recall": float(macro_recall / valid_classes),
            "f1": float(macro_f1 / valid_classes),
        }

    return results


class MetricTracker:
    """
    指标追踪器

    用于训练过程中的指标记录和计算

    使用示例：
        tracker = MetricTracker()
        for batch in dataloader:
            loss, acc = train_step(batch)
            tracker.update({"loss": loss, "acc": acc})
        metrics = tracker.get_metrics()
    """

    def __init__(self):
        self.metrics = defaultdict(list)

    def update(self, metrics: Dict[str, float]):
        """
        更新指标

        Args:
            metrics: 指标字典
        """
        for key, value in metrics.items():
            self.metrics[key].append(value)

    def get_metrics(self) -> Dict[str, float]:
        """
        获取平均指标

        Returns:
            dict: 平均指标
        """
        return {
            key: float(np.mean(values))
            for key, values in self.metrics.items()
        }

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()

    def get_history(self) -> Dict[str, List[float]]:
        """获取指标历史"""
        return dict(self.metrics)
