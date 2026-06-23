"""
Utility functions for YOLO object detection.

Provides:
- IoU (Intersection over Union) computation
- Bounding box format conversions
- Visualization helpers
"""

import torch
import numpy as np
from typing import Tuple, List, Optional


def compute_iou(
    boxes1: torch.Tensor, boxes2: torch.Tensor, format: str = "xywh"
) -> torch.Tensor:
    """
    Compute IoU (Intersection over Union) between two sets of boxes.

    Args:
        boxes1: Tensor of shape (N, 4) - first set of boxes
        boxes2: Tensor of shape (M, 4) - second set of boxes
        format: Box format - 'xywh' (center x, center y, width, height)
                or 'xyxy' (x1, y1, x2, y2)

    Returns:
        IoU matrix of shape (N, M)
    """
    if format == "xywh":
        boxes1 = xywh_to_xyxy(boxes1)
        boxes2 = xywh_to_xyxy(boxes2)

    # Expand dimensions for broadcasting
    # boxes1: (N, 4) -> (N, 1, 4)
    # boxes2: (M, 4) -> (1, M, 4)
    boxes1 = boxes1.unsqueeze(1)
    boxes2 = boxes2.unsqueeze(0)

    # Compute intersection coordinates
    x1 = torch.max(boxes1[..., 0], boxes2[..., 0])
    y1 = torch.max(boxes1[..., 1], boxes2[..., 1])
    x2 = torch.min(boxes1[..., 2], boxes2[..., 2])
    y2 = torch.min(boxes1[..., 3], boxes2[..., 3])

    # Compute intersection area
    intersection = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)

    # Compute union area
    area1 = (boxes1[..., 2] - boxes1[..., 0]) * (boxes1[..., 3] - boxes1[..., 1])
    area2 = (boxes2[..., 2] - boxes2[..., 0]) * (boxes2[..., 3] - boxes2[..., 1])
    union = area1 + area2 - intersection

    # Compute IoU
    iou = intersection / (union + 1e-6)
    return iou


def xywh_to_xyxy(boxes: torch.Tensor) -> torch.Tensor:
    """
    Convert boxes from (center_x, center_y, width, height) to (x1, y1, x2, y2).

    Args:
        boxes: Tensor of shape (..., 4) in xywh format

    Returns:
        Tensor of shape (..., 4) in xyxy format
    """
    x, y, w, h = boxes[..., 0], boxes[..., 1], boxes[..., 2], boxes[..., 3]
    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2
    return torch.stack([x1, y1, x2, y2], dim=-1)


def xyxy_to_xywh(boxes: torch.Tensor) -> torch.Tensor:
    """
    Convert boxes from (x1, y1, x2, y2) to (center_x, center_y, width, height).

    Args:
        boxes: Tensor of shape (..., 4) in xyxy format

    Returns:
        Tensor of shape (..., 4) in xywh format
    """
    x1, y1, x2, y2 = boxes[..., 0], boxes[..., 1], boxes[..., 2], boxes[..., 3]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1
    return torch.stack([cx, cy, w, h], dim=-1)


def grid_to_absolute(
    predictions: torch.Tensor,
    grid_size: int = 7,
    image_size: int = 448,
) -> torch.Tensor:
    """
    Convert grid-relative predictions to absolute image coordinates.

    In YOLO, each cell predicts coordinates relative to its own position.
    This function converts them to absolute image coordinates.

    Args:
        predictions: Tensor of shape (batch, S, S, B*5+C) or (S, S, B*5+C)
        grid_size: Number of grid cells (S)
        image_size: Input image size in pixels

    Returns:
        Predictions with absolute coordinates (same shape)
    """
    cell_size = image_size / grid_size
    result = predictions.clone()

    # For each bounding box prediction (x, y, w, h, conf, ...)
    B = 2  # Number of boxes per cell
    for b in range(B):
        idx = b * 5
        # Get grid offsets
        grid_y, grid_x = torch.meshgrid(
            torch.arange(grid_size, device=predictions.device),
            torch.arange(grid_size, device=predictions.device),
            indexing="ij",
        )
        # Add grid offset to x, y
        result[..., idx] = (predictions[..., idx] + grid_x) * cell_size
        result[..., idx + 1] = (predictions[..., idx + 1] + grid_y) * cell_size
        # Scale w, h to image size
        result[..., idx + 2] = predictions[..., idx + 2] * image_size
        result[..., idx + 3] = predictions[..., idx + 3] * image_size

    return result


def decode_predictions(
    predictions: torch.Tensor,
    grid_size: int = 7,
    num_boxes: int = 2,
    num_classes: int = 20,
    confidence_threshold: float = 0.1,
    image_size: int = 448,
) -> List[dict]:
    """
    Decode raw YOLO predictions into usable detections.

    Args:
        predictions: Raw output from YOLO network, shape (batch, S, S, B*5+C)
        grid_size: Grid size S
        num_boxes: Number of boxes per cell B
        num_classes: Number of classes C
        confidence_threshold: Minimum confidence to keep a detection
        image_size: Input image size

    Returns:
        List of detection dictionaries with keys:
        - 'boxes': Tensor of shape (N, 4) in xyxy format
        - 'scores': Tensor of shape (N,) confidence scores
        - 'labels': Tensor of shape (N,) class indices
    """
    batch_size = predictions.shape[0]
    cell_size = image_size / grid_size

    results = []

    for b in range(batch_size):
        pred = predictions[b]

        # Get grid offsets
        grid_y, grid_x = torch.meshgrid(
            torch.arange(grid_size, device=predictions.device),
            torch.arange(grid_size, device=predictions.device),
            indexing="ij",
        )

        all_boxes = []
        all_scores = []
        all_labels = []

        for box_idx in range(num_boxes):
            idx = box_idx * 5
            # Get box predictions
            x = (pred[..., idx] + grid_x) * cell_size
            y = (pred[..., idx + 1] + grid_y) * cell_size
            w = pred[..., idx + 2] * image_size
            h = pred[..., idx + 3] * image_size
            conf = pred[..., idx + 4]

            # Get class predictions
            class_start = num_boxes * 5
            class_scores = pred[..., class_start : class_start + num_classes]
            class_probs = torch.softmax(class_scores, dim=-1)

            # Convert to xyxy format
            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2

            # Flatten
            boxes = torch.stack([x1, y1, x2, y2], dim=-1).reshape(-1, 4)
            conf_flat = conf.reshape(-1)
            class_probs_flat = class_probs.reshape(-1, num_classes)

            # Final confidence = objectness * class probability
            final_scores = conf_flat.unsqueeze(-1) * class_probs_flat

            # Filter by threshold
            mask = conf_flat > confidence_threshold
            if mask.any():
                boxes_filtered = boxes[mask]
                scores_filtered = final_scores[mask]
                labels_filtered = scores_filtered.argmax(dim=-1)
                max_scores = scores_filtered.max(dim=-1).values

                all_boxes.append(boxes_filtered)
                all_scores.append(max_scores)
                all_labels.append(labels_filtered)

        if all_boxes:
            results.append({
                "boxes": torch.cat(all_boxes, dim=0),
                "scores": torch.cat(all_scores, dim=0),
                "labels": torch.cat(all_labels, dim=0),
            })
        else:
            results.append({
                "boxes": torch.zeros(0, 4),
                "scores": torch.zeros(0),
                "labels": torch.zeros(0, dtype=torch.long),
            })

    return results


def draw_boxes(
    image: np.ndarray,
    boxes: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    class_names: Optional[List[str]] = None,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw bounding boxes on an image.

    Args:
        image: Input image as numpy array (H, W, 3)
        boxes: Array of shape (N, 4) in xyxy format
        scores: Array of shape (N,) confidence scores
        labels: Array of shape (N,) class indices
        class_names: Optional list of class name strings
        color: Box color as (R, G, B) tuple
        thickness: Box line thickness

    Returns:
        Image with drawn boxes
    """
    import cv2

    img = image.copy()
    for i in range(len(boxes)):
        x1, y1, x2, y2 = boxes[i].astype(int)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

        # Prepare label text
        if class_names is not None:
            label = f"{class_names[labels[i]]}: {scores[i]:.2f}"
        else:
            label = f"Class {labels[i]}: {scores[i]:.2f}"

        # Draw label background
        (text_w, text_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        cv2.rectangle(
            img, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1
        )
        cv2.putText(
            img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
        )

    return img


# VOC class names
VOC_CLASSES = [
    "aeroplane", "bicycle", "bird", "boat", "bottle",
    "bus", "car", "cat", "chair", "cow",
    "diningtable", "dog", "horse", "motorbike", "person",
    "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]
