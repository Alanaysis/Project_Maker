"""
Visualization Utilities for Text Detection

Provides functions to visualize detection results.
"""

import numpy as np
from typing import List, Optional, Tuple


def draw_boxes(image: np.ndarray, boxes: np.ndarray,
               scores: Optional[np.ndarray] = None,
               color: Tuple[int, int, int] = (0, 255, 0),
               thickness: int = 2) -> np.ndarray:
    """
    Draw bounding boxes on image.

    Args:
        image: [H, W, 3] RGB image
        boxes: [N, 4] array of [x1, y1, x2, y2]
        scores: [N] optional confidence scores
        color: Box color (R, G, B)
        thickness: Line thickness

    Returns:
        Image with drawn boxes
    """
    try:
        import cv2
        img = image.copy()

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

            if scores is not None:
                label = f"{scores[i]:.2f}"
                cv2.putText(img, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return img
    except ImportError:
        # Fallback without cv2
        img = image.copy()
        for box in boxes:
            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
            img[y1:y1+2, x1:x2] = color  # Top
            img[y2-2:y2, x1:x2] = color  # Bottom
            img[y1:y2, x1:x1+2] = color  # Left
            img[y1:y2, x2-2:x2] = color  # Right
        return img


def draw_quads(image: np.ndarray, quads: np.ndarray,
               scores: Optional[np.ndarray] = None,
               color: Tuple[int, int, int] = (0, 255, 0),
               thickness: int = 2) -> np.ndarray:
    """
    Draw quadrilateral boxes on image.

    Args:
        image: [H, W, 3] RGB image
        quads: [N, 4, 2] array of corner points
        scores: [N] optional confidence scores
        color: Box color (R, G, B)
        thickness: Line thickness

    Returns:
        Image with drawn quads
    """
    try:
        import cv2
        img = image.copy()

        for i, quad in enumerate(quads):
            pts = quad.astype(int).reshape((-1, 1, 2))
            cv2.polylines(img, [pts], True, color, thickness)

            if scores is not None:
                label = f"{scores[i]:.2f}"
                cv2.putText(img, label, tuple(quad[0].astype(int)),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return img
    except ImportError:
        return draw_boxes(image, quads_to_boxes(quads), scores, color, thickness)


def quads_to_boxes(quads: np.ndarray) -> np.ndarray:
    """
    Convert quadrilateral boxes to axis-aligned boxes.

    Args:
        quads: [N, 4, 2] array of corner points

    Returns:
        boxes: [N, 4] array of [x1, y1, x2, y2]
    """
    if len(quads) == 0:
        return np.array([]).reshape(0, 4)

    x1 = quads[:, :, 0].min(axis=1)
    y1 = quads[:, :, 1].min(axis=1)
    x2 = quads[:, :, 0].max(axis=1)
    y2 = quads[:, :, 1].max(axis=1)

    return np.stack([x1, y1, x2, y2], axis=1)


def visualize_score_map(score_map: np.ndarray,
                        colormap: str = 'jet') -> np.ndarray:
    """
    Visualize score map as colored image.

    Args:
        score_map: [H, W] score map
        colormap: Colormap name

    Returns:
        Colored visualization [H, W, 3]
    """
    try:
        import cv2
        # Normalize to 0-255
        normalized = (score_map * 255).astype(np.uint8)

        # Apply colormap
        colormap_id = getattr(cv2, f'COLORMAP_{colormap.upper()}', cv2.COLORMAP_JET)
        colored = cv2.applyColorMap(normalized, colormap_id)
        return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    except ImportError:
        # Simple grayscale visualization
        normalized = (score_map * 255).astype(np.uint8)
        return np.stack([normalized, normalized, normalized], axis=2)


def visualize_geometry_map(geo_map: np.ndarray) -> np.ndarray:
    """
    Visualize geometry map channels.

    Args:
        geo_map: [5, H, W] geometry map

    Returns:
        Visualization [H, W*5, 3]
    """
    try:
        import cv2
        channels = []
        for i in range(5):
            ch = geo_map[i]
            ch_norm = ((ch - ch.min()) / (ch.max() - ch.min() + 1e-6) * 255).astype(np.uint8)
            channels.append(cv2.applyColorMap(ch_norm, cv2.COLORMAP_VIRIDIS))

        return np.concatenate(channels, axis=1)
    except ImportError:
        # Simple grayscale concatenation
        channels = []
        for i in range(5):
            ch = geo_map[i]
            ch_norm = ((ch - ch.min()) / (ch.max() - ch.min() + 1e-6) * 255).astype(np.uint8)
            channels.append(np.stack([ch_norm, ch_norm, ch_norm], axis=2))
        return np.concatenate(channels, axis=1)


def create_detection_overlay(image: np.ndarray, boxes: np.ndarray,
                             scores: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """
    Create detection overlay with colored regions.

    Args:
        image: [H, W, 3] RGB image
        boxes: [N, 4] array of [x1, y1, x2, y2]
        scores: [N] confidence scores
        alpha: Overlay transparency

    Returns:
        Image with overlay
    """
    overlay = image.copy()

    for box, score in zip(boxes, scores):
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)

        # Color based on score (red for low, green for high)
        r = int(255 * (1 - score))
        g = int(255 * score)
        color = (r, g, 0)

        # Fill with semi-transparent color
        overlay[y1:y2, x1:x2] = (
            overlay[y1:y2, x1:x2] * (1 - alpha) +
            np.array(color) * alpha
        ).astype(np.uint8)

    return overlay
