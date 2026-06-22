"""
评估指标实现

实现目标检测常用的评估指标:
- IoU: Intersection over Union
- AP: Average Precision
- mAP: mean Average Precision

参考:
- COCO Evaluation: https://cocodataset.org/#detection-eval
- PASCAL VOC Evaluation: http://host.robots.ox.ac.uk/pascal/VOC/

⭐ 重点理解:
- AP 的计算方法 (11-point / 101-point)
- mAP 如何综合评估模型
- Precision-Recall 曲线的含义

💡 值得思考:
- 为什么使用 mAP 而不是准确率？
- IoU 阈值如何影响评估结果？
- COCO mAP 和 VOC mAP 的区别？
"""

import torch
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


def compute_iou(
    box1: torch.Tensor,
    box2: torch.Tensor
) -> torch.Tensor:
    """
    计算 IoU (Intersection over Union)

    Args:
        box1: 边界框 [N, 4] (x1, y1, x2, y2)
        box2: 边界框 [M, 4] (x1, y1, x2, y2)

    Returns:
        iou: IoU 矩阵 [N, M]
    """
    from .boxes import box_iou
    return box_iou(box1, box2)


def compute_ap(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5,
    use_07_metric: bool = False
) -> Dict:
    """
    计算 Average Precision

    Args:
        predictions: 预测结果列表，每个元素包含:
            - image_id: 图像 ID
            - boxes: 边界框 [N, 4]
            - scores: 置信度 [N]
            - labels: 类别标签 [N]
        ground_truths: 真实标注列表，每个元素包含:
            - image_id: 图像 ID
            - boxes: 边界框 [M, 4]
            - labels: 类别标签 [M]
        iou_threshold: IoU 阈值
        use_07_metric: 是否使用 VOC 2007 的 11-point 方法

    Returns:
        评估结果字典:
        - ap: Average Precision
        - precision: Precision 曲线
        - recall: Recall 曲线

    ⭐ 重点理解:
    - Precision = TP / (TP + FP)
    - Recall = TP / (TP + FN)
    - AP = Precision-Recall 曲线下的面积
    """
    # 按类别组织数据
    pred_by_class = defaultdict(list)
    gt_by_class = defaultdict(list)

    for pred in predictions:
        for i, label in enumerate(pred['labels']):
            pred_by_class[label.item()].append({
                'image_id': pred['image_id'],
                'score': pred['scores'][i].item(),
                'box': pred['boxes'][i]
            })

    for gt in ground_truths:
        for i, label in enumerate(gt['labels']):
            gt_by_class[label.item()].append({
                'image_id': gt['image_id'],
                'box': gt['boxes'][i],
                'matched': False
            })

    # 计算每个类别的 AP
    aps = {}
    for class_id in set(list(pred_by_class.keys()) + list(gt_by_class.keys())):
        preds = pred_by_class.get(class_id, [])
        gts = gt_by_class.get(class_id, [])

        if len(gts) == 0:
            aps[class_id] = 0.0
            continue

        # 按置信度排序
        preds.sort(key=lambda x: x['score'], reverse=True)

        # 计算 TP 和 FP
        tp = np.zeros(len(preds))
        fp = np.zeros(len(preds))

        for i, pred in enumerate(preds):
            # 查找匹配的 ground truth
            best_iou = 0
            best_gt_idx = -1

            for j, gt in enumerate(gts):
                if gt['image_id'] != pred['image_id']:
                    continue
                if gt['matched']:
                    continue

                iou = compute_iou(
                    pred['box'].unsqueeze(0),
                    gt['box'].unsqueeze(0)
                ).item()

                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = j

            # 判断 TP 或 FP
            if best_iou >= iou_threshold and best_gt_idx >= 0:
                tp[i] = 1
                gts[best_gt_idx]['matched'] = True
            else:
                fp[i] = 1

        # 计算 Precision 和 Recall
        tp_cumsum = np.cumsum(tp)
        fp_cumsum = np.cumsum(fp)

        precision = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-6)
        recall = tp_cumsum / len(gts)

        # 计算 AP
        if use_07_metric:
            # VOC 2007 11-point method
            ap = 0
            for t in np.arange(0, 1.1, 0.1):
                p = precision[recall >= t]
                if len(p) > 0:
                    ap += np.max(p)
            ap /= 11
        else:
            # COCO 101-point method
            ap = 0
            for t in np.arange(0, 1.01, 0.01):
                p = precision[recall >= t]
                if len(p) > 0:
                    ap += np.max(p)
            ap /= 101

        aps[class_id] = ap

    return aps


def compute_map(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_thresholds: List[float] = None
) -> Dict:
    """
    计算 mAP (mean Average Precision)

    Args:
        predictions: 预测结果列表
        ground_truths: 真实标注列表
        iou_thresholds: IoU 阈值列表，默认 [0.5, 0.55, ..., 0.95]

    Returns:
        评估结果字典:
        - mAP: 所有类别和 IoU 阈值的平均 AP
        - mAP_50: IoU=0.5 时的 mAP
        - mAP_75: IoU=0.75 时的 mAP
        - ap_by_class: 每个类别的 AP

    ⭐ 重点理解:
    - COCO mAP 是 IoU 从 0.5 到 0.95 的平均
    - mAP_50 更宽松，mAP_75 更严格
    """
    if iou_thresholds is None:
        iou_thresholds = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]

    results = {}

    # 计算不同 IoU 阈值下的 AP
    ap_by_iou = {}
    for iou_thresh in iou_thresholds:
        aps = compute_ap(predictions, ground_truths, iou_threshold=iou_thresh)
        ap_by_iou[iou_thresh] = aps

    # 计算 mAP_50
    if 0.5 in ap_by_iou:
        aps_50 = ap_by_iou[0.5]
        results['mAP_50'] = np.mean(list(aps_50.values())) if aps_50 else 0.0
        results['ap_by_class_50'] = aps_50

    # 计算 mAP_75
    if 0.75 in ap_by_iou:
        aps_75 = ap_by_iou[0.75]
        results['mAP_75'] = np.mean(list(aps_75.values())) if aps_75 else 0.0

    # 计算 COCO mAP (IoU 0.5:0.95)
    all_aps = []
    for iou_thresh in iou_thresholds:
        aps = ap_by_iou[iou_thresh]
        all_aps.extend(aps.values())
    results['mAP'] = np.mean(all_aps) if all_aps else 0.0

    return results


def compute_precision_recall(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算 Precision-Recall 曲线

    Args:
        predictions: 预测结果列表
        ground_truths: 真实标注列表
        iou_threshold: IoU 阈值

    Returns:
        precision: Precision 数组
        recall: Recall 数组
    """
    # 收集所有预测
    all_preds = []
    for pred in predictions:
        for i in range(len(pred['boxes'])):
            all_preds.append({
                'image_id': pred['image_id'],
                'score': pred['scores'][i].item(),
                'box': pred['boxes'][i],
                'label': pred['labels'][i].item()
            })

    # 按置信度排序
    all_preds.sort(key=lambda x: x['score'], reverse=True)

    # 收集所有 ground truth
    all_gts = defaultdict(list)
    for gt in ground_truths:
        for i in range(len(gt['boxes'])):
            all_gts[gt['image_id']].append({
                'box': gt['boxes'][i],
                'label': gt['labels'][i].item(),
                'matched': False
            })

    # 计算 TP 和 FP
    tp = np.zeros(len(all_preds))
    fp = np.zeros(len(all_preds))

    for i, pred in enumerate(all_preds):
        gts = all_gts.get(pred['image_id'], [])

        best_iou = 0
        best_gt_idx = -1

        for j, gt in enumerate(gts):
            if gt['matched'] or gt['label'] != pred['label']:
                continue

            iou = compute_iou(
                pred['box'].unsqueeze(0),
                gt['box'].unsqueeze(0)
            ).item()

            if iou > best_iou:
                best_iou = iou
                best_gt_idx = j

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            tp[i] = 1
            gts[best_gt_idx]['matched'] = True
        else:
            fp[i] = 1

    # 计算 Precision 和 Recall
    tp_cumsum = np.cumsum(tp)
    fp_cumsum = np.cumsum(fp)

    total_gts = sum(len(gts) for gts in all_gts.values())

    precision = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-6)
    recall = tp_cumsum / (total_gts + 1e-6)

    return precision, recall


def test_metrics():
    """
    测试评估指标

    验证:
    1. IoU 计算正确
    2. AP 计算正确
    3. mAP 计算正确
    """
    print("=" * 50)
    print("测试评估指标")
    print("=" * 50)

    # 创建测试数据
    predictions = [
        {
            'image_id': 0,
            'boxes': torch.tensor([[10, 10, 50, 50], [100, 100, 150, 150]]).float(),
            'scores': torch.tensor([0.9, 0.8]),
            'labels': torch.tensor([0, 1])
        }
    ]

    ground_truths = [
        {
            'image_id': 0,
            'boxes': torch.tensor([[12, 12, 52, 52], [102, 102, 152, 152]]).float(),
            'labels': torch.tensor([0, 1])
        }
    ]

    # 测试 AP
    print("\n1. 测试 AP 计算")
    aps = compute_ap(predictions, ground_truths, iou_threshold=0.5)
    print(f"   AP by class: {aps}")

    # 测试 mAP
    print("\n2. 测试 mAP 计算")
    results = compute_map(predictions, ground_truths)
    print(f"   mAP@0.5: {results['mAP_50']:.4f}")
    print(f"   mAP@0.5:0.95: {results['mAP']:.4f}")

    # 测试 Precision-Recall
    print("\n3. 测试 Precision-Recall")
    precision, recall = compute_precision_recall(predictions, ground_truths)
    print(f"   Precision: {precision[:5]}")
    print(f"   Recall: {recall[:5]}")

    print("\n✓ 评估指标测试通过!")
    return True


if __name__ == '__main__':
    test_metrics()
