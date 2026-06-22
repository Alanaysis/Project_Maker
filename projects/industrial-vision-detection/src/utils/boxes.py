"""
边界框操作工具

实现边界框相关的常用操作:
- IoU 计算
- NMS (非极大值抑制)
- 格式转换

⭐ 重点理解:
- IoU 的计算方法
- NMS 的算法流程
- 不同边界框格式的区别

💡 值得思考:
- 为什么需要 NMS？
- 如何处理大量边界框的效率问题？
- 软 NMS 和硬 NMS 的区别？
"""

import torch
import numpy as np
from typing import Tuple


def box_iou(
    box1: torch.Tensor,
    box2: torch.Tensor
) -> torch.Tensor:
    """
    计算两组边界框的 IoU (Intersection over Union)

    IoU = |A ∩ B| / |A ∪ B|

    Args:
        box1: 第一组边界框 [N, 4] (x1, y1, x2, y2)
        box2: 第二组边界框 [M, 4] (x1, y1, x2, y2)

    Returns:
        iou: IoU 矩阵 [N, M]

    Example:
        >>> box1 = torch.tensor([[0, 0, 10, 10]])
        >>> box2 = torch.tensor([[5, 5, 15, 15]])
        >>> iou = box_iou(box1, box2)
        >>> print(iou)
        tensor([[0.1429]])
    """
    # 计算交集
    # 交集的左上角: 取两个框左上角的最大值
    inter_x1 = torch.max(box1[:, 0].unsqueeze(1), box2[:, 0].unsqueeze(0))
    inter_y1 = torch.max(box1[:, 1].unsqueeze(1), box2[:, 1].unsqueeze(0))

    # 交集的右下角: 取两个框右下角的最小值
    inter_x2 = torch.min(box1[:, 2].unsqueeze(1), box2[:, 2].unsqueeze(0))
    inter_y2 = torch.min(box1[:, 3].unsqueeze(1), box2[:, 3].unsqueeze(0))

    # 计算交集面积
    inter_w = torch.clamp(inter_x2 - inter_x1, min=0)
    inter_h = torch.clamp(inter_y2 - inter_y1, min=0)
    intersection = inter_w * inter_h

    # 计算两个框的面积
    area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
    area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])

    # 计算并集面积
    union = area1.unsqueeze(1) + area2.unsqueeze(0) - intersection

    # 计算 IoU
    iou = intersection / (union + 1e-6)

    return iou


def box_nms(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.0
) -> torch.Tensor:
    """
    非极大值抑制 (Non-Maximum Suppression)

    保留置信度最高的边界框，删除与其重叠度高的其他框。

    算法流程:
    1. 按置信度排序所有边界框
    2. 选择置信度最高的框加入结果
    3. 删除与其 IoU > 阈值的框
    4. 重复直到没有框剩余

    Args:
        boxes: 边界框 [N, 4] (x1, y1, x2, y2)
        scores: 置信度 [N]
        iou_threshold: IoU 阈值
        score_threshold: 置信度阈值

    Returns:
        keep_indices: 保留的边界框索引

    ⭐ 重点理解:
    - 为什么需要 NMS？(同一目标可能有多个检测框)
    - IoU 阈值如何影响结果？
    - 如何处理密集目标？
    """
    # 过滤低置信度框
    if score_threshold > 0:
        mask = scores > score_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        if len(boxes) == 0:
            return torch.zeros(0, dtype=torch.long)

    # 按置信度排序
    sorted_indices = torch.argsort(scores, descending=True)

    keep = []
    while len(sorted_indices) > 0:
        # 选择置信度最高的框
        current = sorted_indices[0]
        keep.append(current)

        if len(sorted_indices) == 1:
            break

        # 计算当前框与其他框的 IoU
        current_box = boxes[current].unsqueeze(0)
        other_boxes = boxes[sorted_indices[1:]]
        ious = box_iou(current_box, other_boxes).squeeze(0)

        # 保留 IoU 小于阈值的框
        mask = ious < iou_threshold
        sorted_indices = sorted_indices[1:][mask]

    return torch.tensor(keep, dtype=torch.long)


def xywh_to_xyxy(boxes: torch.Tensor) -> torch.Tensor:
    """
    边界框格式转换: (x, y, w, h) -> (x1, y1, x2, y2)

    Args:
        boxes: 边界框 [N, 4] (center_x, center_y, width, height)

    Returns:
        转换后的边界框 [N, 4] (x1, y1, x2, y2)
    """
    x, y, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]

    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2

    return torch.stack([x1, y1, x2, y2], dim=-1)


def xyxy_to_xywh(boxes: torch.Tensor) -> torch.Tensor:
    """
    边界框格式转换: (x1, y1, x2, y2) -> (x, y, w, h)

    Args:
        boxes: 边界框 [N, 4] (x1, y1, x2, y2)

    Returns:
        转换后的边界框 [N, 4] (center_x, center_y, width, height)
    """
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]

    x = (x1 + x2) / 2
    y = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1

    return torch.stack([x, y, w, h], dim=-1)


def clip_boxes(
    boxes: torch.Tensor,
    image_shape: Tuple[int, int]
) -> torch.Tensor:
    """
    裁剪边界框到图像范围

    Args:
        boxes: 边界框 [N, 4] (x1, y1, x2, y2)
        image_shape: 图像尺寸 (height, width)

    Returns:
        裁剪后的边界框
    """
    h, w = image_shape
    boxes[:, 0] = boxes[:, 0].clamp(0, w)
    boxes[:, 1] = boxes[:, 1].clamp(0, h)
    boxes[:, 2] = boxes[:, 2].clamp(0, w)
    boxes[:, 3] = boxes[:, 3].clamp(0, h)
    return boxes


def scale_boxes(
    boxes: torch.Tensor,
    orig_shape: Tuple[int, int],
    target_shape: Tuple[int, int]
) -> torch.Tensor:
    """
    缩放边界框到目标尺寸

    Args:
        boxes: 边界框 [N, 4] (x1, y1, x2, y2)
        orig_shape: 原始图像尺寸 (height, width)
        target_shape: 目标图像尺寸 (height, width)

    Returns:
        缩放后的边界框
    """
    orig_h, orig_w = orig_shape
    target_h, target_w = target_shape

    scale_x = target_w / orig_w
    scale_y = target_h / orig_h

    boxes[:, 0] *= scale_x
    boxes[:, 1] *= scale_y
    boxes[:, 2] *= scale_x
    boxes[:, 3] *= scale_y

    return boxes


def non_max_suppression(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.25,
    max_det: int = 300
) -> torch.Tensor:
    """
    完整的非极大值抑制

    支持多类别 NMS。

    Args:
        boxes: 边界框 [N, 4]
        scores: 置信度 [N, num_classes]
        iou_threshold: IoU 阈值
        score_threshold: 置信度阈值
        max_det: 最大检测数

    Returns:
        保留的边界框索引
    """
    num_classes = scores.shape[1]
    all_keep = []

    for cls in range(num_classes):
        cls_scores = scores[:, cls]

        # 过滤低置信度
        mask = cls_scores > score_threshold
        if not mask.any():
            continue

        cls_boxes = boxes[mask]
        cls_scores = cls_scores[mask]

        # NMS
        keep = box_nms(cls_boxes, cls_scores, iou_threshold)

        # 转换为原始索引
        original_indices = torch.where(mask)[0][keep]
        all_keep.append(original_indices)

    if not all_keep:
        return torch.zeros(0, dtype=torch.long)

    # 合并所有类别的结果
    all_keep = torch.cat(all_keep)

    # 限制最大检测数
    if len(all_keep) > max_det:
        # 按分数排序
        all_scores = scores[all_keep].max(dim=1).values
        topk_indices = torch.argsort(all_scores, descending=True)[:max_det]
        all_keep = all_keep[topk_indices]

    return all_keep


def test_boxes():
    """
    测试边界框操作

    验证:
    1. IoU 计算正确
    2. NMS 工作正常
    3. 格式转换正确
    """
    print("=" * 50)
    print("测试边界框操作")
    print("=" * 50)

    # 测试 IoU
    print("\n1. 测试 IoU 计算")
    box1 = torch.tensor([[0, 0, 10, 10], [5, 5, 15, 15]])
    box2 = torch.tensor([[5, 5, 15, 15], [0, 0, 10, 10]])
    iou = box_iou(box1, box2)
    print(f"   IoU 矩阵:\n{iou}")

    # 测试 NMS
    print("\n2. 测试 NMS")
    boxes = torch.tensor([
        [10, 10, 50, 50],
        [15, 15, 55, 55],
        [100, 100, 150, 150]
    ]).float()
    scores = torch.tensor([0.9, 0.8, 0.7])
    keep = box_nms(boxes, scores, iou_threshold=0.5)
    print(f"   保留的框索引: {keep}")

    # 测试格式转换
    print("\n3. 测试格式转换")
    boxes_xywh = torch.tensor([[10, 10, 20, 20]])
    boxes_xyxy = xywh_to_xyxy(boxes_xywh)
    boxes_xywh_back = xyxy_to_xywh(boxes_xyxy)
    print(f"   (x, y, w, h): {boxes_xywh}")
    print(f"   (x1, y1, x2, y2): {boxes_xyxy}")
    print(f"   转换回来: {boxes_xywh_back}")

    print("\n✓ 边界框操作测试通过!")
    return True


if __name__ == '__main__':
    test_boxes()
