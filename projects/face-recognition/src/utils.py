"""
工具函数模块

提供图像处理、可视化和辅助功能。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


def preprocess_image(image: np.ndarray, target_size: Tuple[int, int] = (160, 160),
                     normalize: bool = True) -> np.ndarray:
    """
    图像预处理

    Args:
        image: 输入图像
        target_size: 目标大小
        normalize: 是否归一化

    Returns:
        预处理后的图像
    """
    # 调整大小
    processed = cv2.resize(image, target_size)

    # 归一化
    if normalize:
        processed = processed.astype(np.float32) / 255.0

    return processed


def draw_faces(image: np.ndarray, faces: List, identities: Optional[List[str]] = None,
               color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """
    在图像上绘制人脸框

    Args:
        image: 输入图像
        faces: 人脸列表 (Face 对象或 bbox 元组)
        identities: 身份标签列表
        color: 颜色 (BGR)
        thickness: 线条粗细

    Returns:
        绘制后的图像
    """
    result = image.copy()

    for i, face in enumerate(faces):
        # 获取边界框
        if hasattr(face, "bbox"):
            x, y, w, h = face.bbox
        else:
            x, y, w, h = face

        # 绘制矩形
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)

        # 绘制标签
        if identities and i < len(identities):
            label = identities[i]
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_thickness = 2

            # 计算文本大小
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, text_thickness
            )

            # 绘制背景矩形
            cv2.rectangle(
                result,
                (x, y - text_height - 10),
                (x + text_width, y),
                color,
                cv2.FILLED,
            )

            # 绘制文本
            cv2.putText(
                result,
                label,
                (x, y - 5),
                font,
                font_scale,
                (0, 0, 0),
                text_thickness,
            )

    return result


def cosine_similarity(feature1: np.ndarray, feature2: np.ndarray) -> float:
    """
    计算余弦相似度

    Args:
        feature1: 特征向量 1
        feature2: 特征向量 2

    Returns:
        余弦相似度
    """
    dot_product = np.dot(feature1, feature2)
    norm1 = np.linalg.norm(feature1)
    norm2 = np.linalg.norm(feature2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def euclidean_distance(feature1: np.ndarray, feature2: np.ndarray) -> float:
    """
    计算欧氏距离

    Args:
        feature1: 特征向量 1
        feature2: 特征向量 2

    Returns:
        欧氏距离
    """
    return float(np.linalg.norm(feature1 - feature2))


def normalize_feature(feature: np.ndarray) -> np.ndarray:
    """
    L2 归一化特征向量

    Args:
        feature: 特征向量

    Returns:
        归一化后的特征向量
    """
    norm = np.linalg.norm(feature)
    if norm > 0:
        return feature / norm
    return feature


def crop_face(image: np.ndarray, bbox: Tuple[int, int, int, int],
              margin: float = 0.2) -> np.ndarray:
    """
    裁剪人脸区域

    Args:
        image: 输入图像
        bbox: 边界框 (x, y, w, h)
        margin: 边距比例

    Returns:
        裁剪后的人脸图像
    """
    x, y, w, h = bbox
    img_h, img_w = image.shape[:2]

    # 计算边距
    margin_x = int(w * margin)
    margin_y = int(h * margin)

    # 计算裁剪区域
    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)
    x2 = min(img_w, x + w + margin_x)
    y2 = min(img_h, y + h + margin_y)

    return image[y1:y2, x1:x2].copy()


def align_face(image: np.ndarray, landmarks: dict,
               target_size: Tuple[int, int] = (160, 160)) -> np.ndarray:
    """
    人脸对齐

    Args:
        image: 输入图像
        landmarks: 关键点坐标
        target_size: 目标大小

    Returns:
        对齐后的人脸图像
    """
    # 获取眼睛位置
    left_eye = landmarks.get("left_eye")
    right_eye = landmarks.get("right_eye")

    if left_eye is None or right_eye is None:
        # 如果没有关键点，直接返回调整大小后的图像
        return cv2.resize(image, target_size)

    # 计算旋转角度
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))

    # 计算中心点
    center = (
        (left_eye[0] + right_eye[0]) // 2,
        (left_eye[1] + right_eye[1]) // 2,
    )

    # 计算缩放比例
    desired_left_eye = (0.35, 0.35)
    dist = np.sqrt(dx ** 2 + dy ** 2)
    desired_dist = (1 - 2 * desired_left_eye[0]) * target_size[0]
    scale = desired_dist / dist if dist > 0 else 1.0

    # 仿射变换
    M = cv2.getRotationMatrix2D(center, angle, scale)
    M[0, 2] += target_size[0] * 0.5 - center[0]
    M[1, 2] += target_size[1] * desired_left_eye[1] - center[1]

    aligned = cv2.warpAffine(image, M, target_size)

    return aligned


def create_test_image(width: int = 300, height: int = 300,
                      with_face: bool = True) -> np.ndarray:
    """
    创建测试图像

    Args:
        width: 图像宽度
        height: 图像高度
        with_face: 是否包含人脸

    Returns:
        测试图像
    """
    image = np.ones((height, width, 3), dtype=np.uint8) * 200

    if with_face:
        # 绘制简单的脸部特征
        center_x, center_y = width // 2, height // 2
        face_radius = min(width, height) // 4

        # 脸部
        cv2.circle(image, (center_x, center_y), face_radius, (180, 150, 120), -1)

        # 眼睛
        eye_y = center_y - face_radius // 4
        eye_radius = face_radius // 8
        cv2.circle(image, (center_x - face_radius // 3, eye_y), eye_radius, (50, 50, 50), -1)
        cv2.circle(image, (center_x + face_radius // 3, eye_y), eye_radius, (50, 50, 50), -1)

        # 鼻子
        nose_y = center_y + face_radius // 8
        cv2.line(image, (center_x, nose_y - face_radius // 6),
                 (center_x, nose_y + face_radius // 6), (50, 50, 50), 2)

        # 嘴巴
        mouth_y = center_y + face_radius // 3
        cv2.ellipse(image, (center_x, mouth_y), (face_radius // 4, face_radius // 8),
                    0, 0, 180, (50, 50, 50), 2)

    return image


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
        raise FileNotFoundError(f"无法加载图像: {path}")
    return image


def save_image(path: str, image: np.ndarray) -> bool:
    """
    保存图像

    Args:
        path: 保存路径
        image: 图像数组

    Returns:
        是否成功保存
    """
    return cv2.imwrite(path, image)


def get_image_info(image: np.ndarray) -> dict:
    """
    获取图像信息

    Args:
        image: 图像数组

    Returns:
        图像信息字典
    """
    return {
        "shape": image.shape,
        "dtype": str(image.dtype),
        "min": float(image.min()),
        "max": float(image.max()),
        "mean": float(image.mean()),
    }
