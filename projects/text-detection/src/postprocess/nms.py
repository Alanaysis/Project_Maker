"""
Post-processing for Text Detection

Implements NMS and box decoding for EAST-style text detection.
"""

import numpy as np
from typing import List, Tuple


def nms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> List[int]:
    """
    Standard Non-Maximum Suppression for axis-aligned bounding boxes.

    Args:
        boxes: [N, 4] array of [x1, y1, x2, y2]
        scores: [N] array of confidence scores
        threshold: IoU threshold for suppression

    Returns:
        List of kept indices
    """
    if len(boxes) == 0:
        return []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)

        if len(order) == 1:
            break

        # Compute IoU
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)

        # Keep boxes with IoU below threshold
        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]

    return keep


def lanms(boxes: np.ndarray, scores: np.ndarray, threshold: float) -> List[int]:
    """
    Locality-Aware NMS (LANMS) used in EAST.

    Merges overlapping boxes by averaging coordinates before suppression.
    Better suited for text detection where text regions often overlap.

    Args:
        boxes: [N, 4] array of [x1, y1, x2, y2]
        scores: [N] array of confidence scores
        threshold: IoU threshold for suppression

    Returns:
        List of kept indices
    """
    if len(boxes) == 0:
        return [], []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    merged_boxes = []
    merged_scores = []

    while len(order) > 0:
        i = order[0]

        # Find overlapping boxes
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)

        # Find highly overlapping boxes
        merge_inds = np.where(iou > threshold)[0]
        merge_order = np.concatenate([[0], merge_inds + 1])

        # Average coordinates of overlapping boxes
        avg_x1 = np.mean(x1[order[merge_order]])
        avg_y1 = np.mean(y1[order[merge_order]])
        avg_x2 = np.mean(x2[order[merge_order]])
        avg_y2 = np.mean(y2[order[merge_order]])
        avg_score = np.mean(scores[order[merge_order]])

        merged_boxes.append([avg_x1, avg_y1, avg_x2, avg_y2])
        merged_scores.append(avg_score)

        # Remove merged boxes
        keep_inds = np.setdiff1d(np.arange(len(order)), merge_order)
        order = order[keep_inds]

    return merged_boxes, merged_scores


def decode_rbox(score_map: np.ndarray, geo_map: np.ndarray,
                score_thresh: float = 0.5, scale: float = 4.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decode score map and geometry map into bounding boxes.

    Args:
        score_map: [H, W] text probability map
        geo_map: [5, H, W] geometry map (top, right, bottom, left, angle)
        score_thresh: Threshold for text detection
        scale: Scale factor from feature map to input image

    Returns:
        boxes: [N, 4] array of [x1, y1, x2, y2]
        scores: [N] array of confidence scores
    """
    # Find text regions
    mask = score_map > score_thresh
    if not mask.any():
        return np.array([]).reshape(0, 4), np.array([])

    # Get coordinates of text pixels
    ys, xs = np.where(mask)
    scores = score_map[mask]

    # Extract geometry values
    d_top = geo_map[0, mask]    # distance to top
    d_right = geo_map[1, mask]  # distance to right
    d_bottom = geo_map[2, mask] # distance to bottom
    d_left = geo_map[3, mask]   # distance to left
    # angle = geo_map[4, mask]  # rotation angle (unused for axis-aligned boxes)

    # Convert to box coordinates (scale back to original image)
    x1 = (xs - d_left) * scale
    y1 = (ys - d_top) * scale
    x2 = (xs + d_right) * scale
    y2 = (ys + d_bottom) * scale

    boxes = np.stack([x1, y1, x2, y2], axis=1)

    return boxes, scores


def decode_quad(score_map: np.ndarray, geo_map: np.ndarray,
                score_thresh: float = 0.5, scale: float = 4.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decode score map and quad geometry map into quadrilateral boxes.

    Args:
        score_map: [H, W] text probability map
        geo_map: [8, H, W] geometry map (4 corners * 2 offsets)
        score_thresh: Threshold for text detection
        scale: Scale factor from feature map to input image

    Returns:
        quads: [N, 4, 2] array of corner points
        scores: [N] array of confidence scores
    """
    mask = score_map > score_thresh
    if not mask.any():
        return np.array([]).reshape(0, 4, 2), np.array([])

    ys, xs = np.where(mask)
    scores = score_map[mask]

    # Extract corner offsets
    quads = []
    for i in range(4):
        dx = geo_map[i * 2, mask] * scale
        dy = geo_map[i * 2 + 1, mask] * scale
        corner_x = xs * scale + dx
        corner_y = ys * scale + dy
        quads.append(np.stack([corner_x, corner_y], axis=1))

    quads = np.stack(quads, axis=1)  # [N, 4, 2]

    return quads, scores


def boxes_to_quads(boxes: np.ndarray) -> np.ndarray:
    """
    Convert axis-aligned boxes to quadrilateral format.

    Args:
        boxes: [N, 4] array of [x1, y1, x2, y2]

    Returns:
        quads: [N, 4, 2] array of corner points (clockwise from top-left)
    """
    if len(boxes) == 0:
        return np.array([]).reshape(0, 4, 2)

    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]

    # Top-left, top-right, bottom-right, bottom-left
    quads = np.stack([
        np.stack([x1, y1], axis=1),
        np.stack([x2, y1], axis=1),
        np.stack([x2, y2], axis=1),
        np.stack([x1, y2], axis=1),
    ], axis=1)

    return quads


def resize_geometry(geo_map: np.ndarray, target_size: Tuple[int, int],
                    geo_type: str = 'rbox') -> np.ndarray:
    """
    Resize geometry map to target size.

    Args:
        geo_map: Geometry map [C, H, W]
        target_size: (height, width) target size
        geo_type: 'rbox' or 'quad'

    Returns:
        Resized geometry map
    """
    try:
        import cv2
        h, w = target_size
        c = geo_map.shape[0]

        resized = np.zeros((c, h, w), dtype=geo_map.dtype)
        for i in range(c):
            resized[i] = cv2.resize(geo_map[i], (w, h), interpolation=cv2.INTER_LINEAR)

        return resized
    except ImportError:
        # Fallback: nearest neighbor interpolation without cv2
        h_src, w_src = geo_map.shape[1], geo_map.shape[2]
        h_tgt, w_tgt = target_size

        y_idx = (np.arange(h_tgt) * h_src / h_tgt).astype(int)
        x_idx = (np.arange(w_tgt) * w_src / w_tgt).astype(int)
        y_idx = np.clip(y_idx, 0, h_src - 1)
        x_idx = np.clip(x_idx, 0, w_src - 1)

        return geo_map[:, y_idx][:, :, x_idx]
