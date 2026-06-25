"""评估模块"""

import numpy as np
from typing import List, Dict, Tuple


class OCREvaluator:
    """OCR 评估器"""

    def __init__(self):
        self.results = []

    def add_result(self, pred: str, gt: str):
        """
        添加预测结果

        Args:
            pred: 预测文本
            gt: 真实文本
        """
        self.results.append((pred, gt))

    def reset(self):
        """重置评估器"""
        self.results = []

    def compute_char_accuracy(self) -> float:
        """
        计算字符准确率

        Returns:
            字符准确率
        """
        correct = 0
        total = 0
        for pred, gt in self.results:
            # 使用最长的长度
            max_len = max(len(pred), len(gt))
            for i in range(max_len):
                if i < len(pred) and i < len(gt):
                    if pred[i] == gt[i]:
                        correct += 1
            total += max_len
        return correct / total if total > 0 else 0

    def compute_word_accuracy(self) -> float:
        """
        计算词准确率

        Returns:
            词准确率
        """
        if not self.results:
            return 0
        correct = sum(1 for pred, gt in self.results if pred == gt)
        return correct / len(self.results)

    def compute_edit_distance(self, pred: str, gt: str) -> int:
        """
        计算编辑距离

        Args:
            pred: 预测文本
            gt: 真实文本

        Returns:
            编辑距离
        """
        m, n = len(pred), len(gt)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if pred[i - 1] == gt[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

        return dp[m][n]

    def compute_normalized_edit_distance(self) -> float:
        """
        计算归一化编辑距离

        Returns:
            归一化编辑距离
        """
        total_distance = 0
        total_length = 0
        for pred, gt in self.results:
            total_distance += self.compute_edit_distance(pred, gt)
            total_length += len(gt)
        return total_distance / total_length if total_length > 0 else 0

    def compute_precision_recall_f1(self, pred_boxes: List[np.ndarray],
                                     gt_boxes: List[np.ndarray],
                                     iou_threshold: float = 0.5) -> Dict[str, float]:
        """
        计算检测指标

        Args:
            pred_boxes: 预测框列表
            gt_boxes: 真实框列表
            iou_threshold: IoU 阈值

        Returns:
            包含 precision, recall, f1 的字典
        """
        tp = 0
        fp = 0
        fn = len(gt_boxes)

        for pred_box in pred_boxes:
            matched = False
            for gt_box in gt_boxes:
                iou = self._compute_iou(pred_box, gt_box)
                if iou >= iou_threshold:
                    matched = True
                    break
            if matched:
                tp += 1
                fn -= 1
            else:
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    def _compute_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """
        计算两个多边形的 IoU

        Args:
            box1: 多边形顶点 (N, 2)
            box2: 多边形顶点 (M, 2)

        Returns:
            IoU 值
        """
        # 简化为矩形框 IoU
        x1 = max(box1[:, 0].min(), box2[:, 0].min())
        y1 = max(box1[:, 1].min(), box2[:, 1].min())
        x2 = min(box1[:, 0].max(), box2[:, 0].max())
        y2 = min(box1[:, 1].max(), box2[:, 1].max())

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area1 = self._polygon_area(box1)
        area2 = self._polygon_area(box2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def _polygon_area(self, pts: np.ndarray) -> float:
        """
        计算多边形面积

        Args:
            pts: 多边形顶点 (N, 2)

        Returns:
            面积
        """
        n = len(pts)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return abs(area) / 2

    def summary(self) -> Dict[str, float]:
        """
        生成评估报告

        Returns:
            评估指标字典
        """
        return {
            "char_accuracy": self.compute_char_accuracy(),
            "word_accuracy": self.compute_word_accuracy(),
            "normalized_edit_distance": self.compute_normalized_edit_distance(),
            "num_samples": len(self.results)
        }

    def print_summary(self):
        """打印评估报告"""
        summary = self.summary()
        print("=" * 50)
        print("OCR 评估报告")
        print("=" * 50)
        print(f"样本数量: {summary['num_samples']}")
        print(f"字符准确率: {summary['char_accuracy']:.4f}")
        print(f"词准确率: {summary['word_accuracy']:.4f}")
        print(f"归一化编辑距离: {summary['normalized_edit_distance']:.4f}")
        print("=" * 50)


class DetectionEvaluator:
    """检测评估器"""

    def __init__(self):
        self.results = []

    def add_result(self, pred_boxes: List[np.ndarray],
                   gt_boxes: List[np.ndarray]):
        """添加预测结果"""
        self.results.append((pred_boxes, gt_boxes))

    def compute_metrics(self, iou_threshold: float = 0.5) -> Dict[str, float]:
        """
        计算检测指标

        Args:
            iou_threshold: IoU 阈值

        Returns:
            检测指标
        """
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for pred_boxes, gt_boxes in self.results:
            tp = 0
            fp = 0
            fn = len(gt_boxes)

            for pred_box in pred_boxes:
                matched = False
                for gt_box in gt_boxes:
                    iou = self._compute_iou(pred_box, gt_box)
                    if iou >= iou_threshold:
                        matched = True
                        break
                if matched:
                    tp += 1
                    fn -= 1
                else:
                    fp += 1

            total_tp += tp
            total_fp += fp
            total_fn += fn

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn
        }

    def _compute_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """计算 IoU"""
        x1 = max(box1[:, 0].min(), box2[:, 0].min())
        y1 = max(box1[:, 1].min(), box2[:, 1].min())
        x2 = min(box1[:, 0].max(), box2[:, 0].max())
        y2 = min(box1[:, 1].max(), box2[:, 1].max())

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area1 = self._polygon_area(box1)
        area2 = self._polygon_area(box2)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def _polygon_area(self, pts: np.ndarray) -> float:
        """计算多边形面积"""
        n = len(pts)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return abs(area) / 2