"""
工具函数模块

提供图像处理和可视化工具。
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2

logger = logging.getLogger(__name__)


def load_image(path: str) -> np.ndarray:
    """
    加载图像

    Args:
        path: 图像路径

    Returns:
        图像数组
    """
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"无法加载图像: {path}")
    return image


def save_image(image: np.ndarray, path: str) -> bool:
    """
    保存图像

    Args:
        image: 图像数组
        path: 保存路径

    Returns:
        是否成功
    """
    return cv2.imwrite(path, image)


def resize_image(
    image: np.ndarray,
    target_size: Optional[Tuple[int, int]] = None,
    max_size: Optional[int] = None,
) -> np.ndarray:
    """
    调整图像大小

    Args:
        image: 输入图像
        target_size: 目标大小 (width, height)
        max_size: 最大尺寸

    Returns:
        调整后的图像
    """
    h, w = image.shape[:2]

    if target_size:
        return cv2.resize(image, target_size)

    if max_size:
        # 等比缩放
        scale = min(max_size / w, max_size / h)
        if scale < 1:
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h))

    return image


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    增强图像质量

    Args:
        image: 输入图像

    Returns:
        增强后的图像
    """
    # 转灰度
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # CLAHE 对比度增强
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 转回原格式
    if len(image.shape) == 3:
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    return enhanced


def binarize_image(
    image: np.ndarray,
    method: str = "otsu",
) -> np.ndarray:
    """
    图像二值化

    Args:
        image: 输入图像
        method: 二值化方法 (otsu/adaptive)

    Returns:
        二值化图像
    """
    # 转灰度
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 去噪
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    if method == "otsu":
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == "adaptive":
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    else:
        raise ValueError(f"未知的二值化方法: {method}")

    return binary


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    去除图像噪声

    Args:
        image: 输入图像

    Returns:
        去噪后的图像
    """
    return cv2.fastNlMeansDenoising(image, h=10)


def draw_bounding_box(
    image: np.ndarray,
    bbox: List[int],
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    label: Optional[str] = None,
) -> np.ndarray:
    """
    绘制边界框

    Args:
        image: 输入图像
        bbox: 边界框 [x1, y1, x2, y2]
        color: 颜色 (BGR)
        thickness: 线条粗细
        label: 标签文本

    Returns:
        绘制后的图像
    """
    vis_image = image.copy()
    x1, y1, x2, y2 = bbox

    # 绘制矩形
    cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, thickness)

    # 添加标签
    if label:
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            vis_image,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            color,
            -1,
        )
        cv2.putText(
            vis_image,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    return vis_image


def draw_text(
    image: np.ndarray,
    text: str,
    position: Tuple[int, int],
    color: Tuple[int, int, int] = (0, 0, 255),
    font_scale: float = 0.5,
    thickness: int = 1,
) -> np.ndarray:
    """
    绘制文字

    Args:
        image: 输入图像
        text: 文字内容
        position: 位置 (x, y)
        color: 颜色 (BGR)
        font_scale: 字体大小
        thickness: 线条粗细

    Returns:
        绘制后的图像
    """
    vis_image = image.copy()

    cv2.putText(
        vis_image,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness,
    )

    return vis_image


def calculate_iou(bbox1: List[int], bbox2: List[int]) -> float:
    """
    计算两个边界框的 IoU

    Args:
        bbox1: 边界框 1 [x1, y1, x2, y2]
        bbox2: 边界框 2 [x1, y1, x2, y2]

    Returns:
        IoU 值
    """
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    # 计算交集面积
    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    # 计算并集面积
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection

    # 计算 IoU
    if union == 0:
        return 0.0

    return intersection / union


def non_max_suppression(
    boxes: List[List[int]],
    scores: List[float],
    threshold: float = 0.5,
) -> List[int]:
    """
    非极大值抑制

    Args:
        boxes: 边界框列表
        scores: 置信度分数
        threshold: IoU 阈值

    Returns:
        保留的边界框索引
    """
    if not boxes:
        return []

    # 按分数排序
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    keep = []
    while indices:
        # 选择分数最高的
        current = indices.pop(0)
        keep.append(current)

        # 过滤与当前框重叠较大的框
        remaining = []
        for idx in indices:
            iou = calculate_iou(boxes[current], boxes[idx])
            if iou <= threshold:
                remaining.append(idx)

        indices = remaining

    return keep


def create_sample_table_image(
    rows: int = 3,
    cols: int = 3,
    cell_width: int = 100,
    cell_height: int = 50,
    border_width: int = 2,
) -> np.ndarray:
    """
    创建示例表格图像

    Args:
        rows: 行数
        cols: 列数
        cell_width: 单元格宽度
        cell_height: 单元格高度
        border_width: 边框宽度

    Returns:
        表格图像
    """
    # 计算图像大小
    width = cols * cell_width + (cols + 1) * border_width
    height = rows * cell_height + (rows + 1) * border_width

    # 创建白色背景
    image = np.ones((height, width, 3), dtype=np.uint8) * 255

    # 绘制边框
    color = (0, 0, 0)

    # 绘制水平线
    for i in range(rows + 1):
        y = i * (cell_height + border_width) + border_width // 2
        cv2.line(image, (0, y), (width, y), color, border_width)

    # 绘制垂直线
    for j in range(cols + 1):
        x = j * (cell_width + border_width) + border_width // 2
        cv2.line(image, (x, 0), (x, height), color, border_width)

    # 添加示例文字
    for i in range(rows):
        for j in range(cols):
            x = j * (cell_width + border_width) + border_width + 10
            y = i * (cell_height + border_width) + border_width + 30
            text = f"R{i}C{j}"
            cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    return image


def create_sample_image_with_tables(
    num_tables: int = 1,
    image_size: Tuple[int, int] = (800, 600),
) -> np.ndarray:
    """
    创建包含表格的示例图像

    Args:
        num_tables: 表格数量
        image_size: 图像大小 (width, height)

    Returns:
        示例图像
    """
    width, height = image_size

    # 创建白色背景
    image = np.ones((height, width, 3), dtype=np.uint8) * 255

    # 添加表格
    for i in range(num_tables):
        # 随机位置和大小
        x = np.random.randint(50, width - 300)
        y = np.random.randint(50, height - 200)
        table_width = np.random.randint(200, 300)
        table_height = np.random.randint(100, 200)

        # 绘制表格边框
        cv2.rectangle(image, (x, y), (x + table_width, y + table_height), (0, 0, 0), 2)

        # 绘制水平线
        num_rows = np.random.randint(2, 5)
        for row in range(1, num_rows):
            line_y = y + row * (table_height // num_rows)
            cv2.line(image, (x, line_y), (x + table_width, line_y), (0, 0, 0), 1)

        # 绘制垂直线
        num_cols = np.random.randint(2, 4)
        for col in range(1, num_cols):
            line_x = x + col * (table_width // num_cols)
            cv2.line(image, (line_x, y), (line_x, y + table_height), (0, 0, 0), 1)

    return image
