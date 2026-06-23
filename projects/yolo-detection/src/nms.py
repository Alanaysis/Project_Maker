"""
Non-Maximum Suppression (NMS) for object detection.

NMS is a post-processing technique used to:
1. Filter out low-confidence detections
2. Remove duplicate detections (overlapping boxes)
3. Keep only the best detection for each object

Algorithm:
1. Sort detections by confidence score (descending)
2. Pick the detection with highest confidence
3. Remove all detections with IoU > threshold with this detection
4. Repeat until no detections remain
"""

import torch
from typing import List, Tuple


def compute_iou_matrix(boxes: torch.Tensor) -> torch.Tensor:
    """
    Compute pairwise IoU matrix for a set of boxes.

    Args:
        boxes: Tensor of shape (N, 4) in xyxy format (x1, y1, x2, y2)

    Returns:
        IoU matrix of shape (N, N)
    """
    # Compute areas
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

    # Compute intersection coordinates
    # boxes[:, None] -> (N, 1, 4), boxes[None] -> (1, N, 4)
    inter_x1 = torch.max(boxes[:, None, 0], boxes[None, :, 0])
    inter_y1 = torch.max(boxes[:, None, 1], boxes[None, :, 1])
    inter_x2 = torch.min(boxes[:, None, 2], boxes[None, :, 2])
    inter_y2 = torch.min(boxes[:, None, 3], boxes[None, :, 3])

    # Compute intersection area
    inter_w = torch.clamp(inter_x2 - inter_x1, min=0)
    inter_h = torch.clamp(inter_y2 - inter_y1, min=0)
    intersection = inter_w * inter_h

    # Compute union
    union = areas[:, None] + areas[None, :] - intersection

    # Compute IoU
    iou = intersection / (union + 1e-6)
    return iou


def non_max_suppression(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.1,
    max_detections: int = 100,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Apply Non-Maximum Suppression to a set of detections.

    Args:
        boxes: Tensor of shape (N, 4) in xyxy format
        scores: Tensor of shape (N,) confidence scores
        iou_threshold: IoU threshold for suppression. Default: 0.5
        score_threshold: Minimum confidence to keep. Default: 0.1
        max_detections: Maximum number of detections to return. Default: 100

    Returns:
        keep_boxes: Tensor of shape (M, 4) kept boxes
        keep_scores: Tensor of shape (M,) kept scores

    Example:
        >>> boxes = torch.tensor([[10, 10, 50, 50], [12, 12, 52, 52], [100, 100, 150, 150]])
        >>> scores = torch.tensor([0.9, 0.8, 0.7])
        >>> keep_boxes, keep_scores = non_max_suppression(boxes, scores, iou_threshold=0.5)
    """
    if boxes.numel() == 0:
        return torch.zeros(0, 4), torch.zeros(0)

    # Filter by score threshold
    mask = scores > score_threshold
    boxes = boxes[mask]
    scores = scores[mask]

    if boxes.numel() == 0:
        return torch.zeros(0, 4), torch.zeros(0)

    # Sort by score (descending)
    sorted_indices = torch.argsort(scores, descending=True)
    boxes = boxes[sorted_indices]
    scores = scores[sorted_indices]

    # Compute pairwise IoU
    iou_matrix = compute_iou_matrix(boxes)

    # Greedy NMS
    keep = []
    suppressed = torch.zeros(len(boxes), dtype=torch.bool, device=boxes.device)

    for i in range(len(boxes)):
        if suppressed[i]:
            continue

        keep.append(i)

        # Suppress boxes with high IoU
        if len(keep) >= max_detections:
            break

        # Find boxes with IoU > threshold
        high_iou = iou_matrix[i] > iou_threshold
        suppressed = suppressed | high_iou

    if len(keep) == 0:
        return torch.zeros(0, 4), torch.zeros(0)

    keep = torch.tensor(keep, dtype=torch.long, device=boxes.device)
    return boxes[keep], scores[keep]


def batched_nms(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    labels: torch.Tensor,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.1,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Apply NMS separately for each class.

    This is the standard approach for multi-class detection:
    NMS is applied independently per class to avoid suppressing
    detections of different classes that overlap.

    Args:
        boxes: Tensor of shape (N, 4) in xyxy format
        scores: Tensor of shape (N,) confidence scores
        labels: Tensor of shape (N,) class indices
        iou_threshold: IoU threshold for suppression
        score_threshold: Minimum confidence to keep

    Returns:
        keep_boxes: Tensor of shape (M, 4) kept boxes
        keep_scores: Tensor of shape (M,) kept scores
        keep_labels: Tensor of shape (M,) kept labels
    """
    if boxes.numel() == 0:
        return torch.zeros(0, 4), torch.zeros(0), torch.zeros(0, dtype=torch.long)

    all_keep_boxes = []
    all_keep_scores = []
    all_keep_labels = []

    # Apply NMS per class
    unique_labels = labels.unique()
    for cls in unique_labels:
        cls_mask = labels == cls
        cls_boxes = boxes[cls_mask]
        cls_scores = scores[cls_mask]

        kept_boxes, kept_scores = non_max_suppression(
            cls_boxes, cls_scores, iou_threshold, score_threshold
        )

        if len(kept_boxes) > 0:
            all_keep_boxes.append(kept_boxes)
            all_keep_scores.append(kept_scores)
            all_keep_labels.append(
                torch.full((len(kept_boxes),), cls, dtype=torch.long, device=boxes.device)
            )

    if not all_keep_boxes:
        return torch.zeros(0, 4), torch.zeros(0), torch.zeros(0, dtype=torch.long)

    return (
        torch.cat(all_keep_boxes, dim=0),
        torch.cat(all_keep_scores, dim=0),
        torch.cat(all_keep_labels, dim=0),
    )


def soft_nms(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float = 0.5,
    sigma: float = 0.5,
    score_threshold: float = 0.01,
    method: str = "gaussian",
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Apply Soft-NMS to detections.

    Instead of removing overlapping detections, Soft-NMS decays their
    scores based on IoU with higher-scoring detections.

    Args:
        boxes: Tensor of shape (N, 4) in xyxy format
        scores: Tensor of shape (N,) confidence scores
        iou_threshold: IoU threshold for suppression (for linear method)
        sigma: Gaussian sigma for score decay
        score_threshold: Minimum score to keep
        method: 'linear' or 'gaussian' decay method

    Returns:
        keep_boxes: Tensor of shape (M, 4) kept boxes
        keep_scores: Tensor of shape (M,) kept scores
    """
    if boxes.numel() == 0:
        return torch.zeros(0, 4), torch.zeros(0)

    # Sort by score
    sorted_indices = torch.argsort(scores, descending=True)
    boxes = boxes[sorted_indices].clone()
    scores = scores[sorted_indices].clone()

    keep = []
    iou_matrix = compute_iou_matrix(boxes)

    for i in range(len(boxes)):
        # Find the box with highest score
        max_idx = scores.argmax()
        if scores[max_idx] < score_threshold:
            break

        keep.append(max_idx)

        # Decay scores of overlapping boxes
        ious = iou_matrix[max_idx]
        if method == "linear":
            weight = torch.where(
                ious > iou_threshold, 1.0 - ious, torch.ones_like(ious)
            )
        else:  # gaussian
            weight = torch.exp(-(ious ** 2) / sigma)

        scores = scores * weight

        # Set processed box score to 0
        scores[max_idx] = 0

    if len(keep) == 0:
        return torch.zeros(0, 4), torch.zeros(0)

    keep = torch.tensor(keep, dtype=torch.long, device=boxes.device)
    return boxes[keep], scores[keep]
