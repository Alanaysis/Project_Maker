"""OCR 工具函数"""

import cv2
import numpy as np
from typing import List, Tuple


def resize_image(image: np.ndarray, max_size: int = 1024) -> np.ndarray:
    """
    保持宽高比缩放图像

    Args:
        image: 输入图像 (H, W, C)
        max_size: 最大尺寸

    Returns:
        缩放后的图像
    """
    h, w = image.shape[:2]
    scale = min(max_size / max(h, w), 1.0)
    if scale < 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h))
    return image


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    排序四边形顶点：左上、右上、右下、左下

    Args:
        pts: 四边形顶点 (4, 2)

    Returns:
        排序后的顶点
    """
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # 左上
    rect[2] = pts[np.argmax(s)]  # 右下
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 右上
    rect[3] = pts[np.argmax(diff)]  # 左下
    return rect


def crop_text_region(image: np.ndarray, bbox: np.ndarray,
                     target_height: int = 32) -> np.ndarray:
    """
    根据四边形坐标裁剪文字区域

    Args:
        image: 输入图像
        bbox: 四边形坐标 (4, 2)
        target_height: 目标高度

    Returns:
        裁剪后的文字图像
    """
    bbox = order_points(bbox)

    # 计算目标尺寸
    width_a = np.linalg.norm(bbox[1] - bbox[0])
    width_b = np.linalg.norm(bbox[2] - bbox[3])
    max_width = max(int(width_a), int(width_b))

    height_a = np.linalg.norm(bbox[3] - bbox[0])
    height_b = np.linalg.norm(bbox[2] - bbox[1])
    max_height = max(int(height_a), int(height_b))

    # 目标点
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype=np.float32)

    # 透视变换
    M = cv2.getPerspectiveTransform(bbox, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))

    # 调整到目标高度
    if warped.shape[0] != target_height:
        scale = target_height / warped.shape[0]
        new_width = int(warped.shape[1] * scale)
        warped = cv2.resize(warped, (new_width, target_height))

    return warped


def draw_bboxes(image: np.ndarray, bboxes: List[np.ndarray],
                color: Tuple[int, int, int] = (0, 255, 0),
                thickness: int = 2) -> np.ndarray:
    """
    绘制检测框

    Args:
        image: 输入图像
        bboxes: 检测框列表
        color: 颜色 (B, G, R)
        thickness: 线宽

    Returns:
        绘制后的图像
    """
    vis = image.copy()
    for bbox in bboxes:
        pts = bbox.astype(np.int32)
        cv2.polylines(vis, [pts], True, color, thickness)
    return vis


def draw_results(image: np.ndarray, results: List[dict]) -> np.ndarray:
    """
    绘制识别结果

    Args:
        image: 输入图像
        results: 识别结果列表

    Returns:
        绘制后的图像
    """
    vis = image.copy()
    for result in results:
        bbox = result["bbox"].astype(np.int32)
        text = result["text"]
        conf = result["confidence"]

        # 绘制框
        cv2.polylines(vis, [bbox], True, (0, 255, 0), 2)

        # 绘制文本
        x, y = bbox[0]
        label = f"{text} ({conf:.2f})"
        cv2.putText(vis, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return vis


def normalize_image(image: np.ndarray,
                    mean: Tuple[float, ...] = (0.485, 0.456, 0.406),
                    std: Tuple[float, ...] = (0.229, 0.224, 0.225)) -> np.ndarray:
    """
    图像归一化

    Args:
        image: 输入图像 (0-255)
        mean: 均值
        std: 标准差

    Returns:
        归一化后的图像
    """
    image = image.astype(np.float32) / 255.0
    image = (image - mean) / std
    return image


def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """
    计算两个矩形框的 IoU

    Args:
        box1: 矩形框 [x1, y1, x2, y2]
        box2: 矩形框 [x1, y1, x2, y2]

    Returns:
        IoU 值
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0


def nms(boxes: np.ndarray, scores: np.ndarray,
        threshold: float = 0.5) -> List[int]:
    """
    非极大值抑制

    Args:
        boxes: 矩形框数组 (N, 4)
        scores: 置信度数组 (N,)
        threshold: IoU 阈值

    Returns:
        保留的索引列表
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
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        intersection = w * h

        iou = intersection / (areas[i] + areas[order[1:]] - intersection)

        inds = np.where(iou <= threshold)[0]
        order = order[inds + 1]

    return keep


def create_test_image(text: str = "Hello", size: Tuple[int, int] = (200, 600)) -> np.ndarray:
    """
    创建测试图像

    Args:
        text: 文本内容
        size: 图像大小 (height, width)

    Returns:
        测试图像
    """
    h, w = size
    image = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.putText(image, text, (50, h // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    return image