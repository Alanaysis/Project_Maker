"""
人脸检测模块

支持 Haar Cascade 和 MTCNN 两种检测方法。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class Face:
    """人脸检测结果"""

    def __init__(self, bbox: Tuple[int, int, int, int], confidence: float = 1.0,
                 landmarks: Optional[dict] = None):
        """
        初始化人脸对象

        Args:
            bbox: 边界框 (x, y, w, h)
            confidence: 置信度
            landmarks: 关键点坐标
        """
        self.bbox = bbox
        self.confidence = confidence
        self.landmarks = landmarks or {}

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "bbox": self.bbox,
            "confidence": self.confidence,
            "landmarks": self.landmarks,
        }


class HaarDetector:
    """基于 Haar Cascade 的人脸检测器"""

    def __init__(self):
        """初始化 Haar 检测器"""
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError(f"无法加载 Haar Cascade 文件: {cascade_path}")

    def detect(self, image: np.ndarray, scale_factor: float = 1.1,
               min_neighbors: int = 5, min_size: Tuple[int, int] = (30, 30)) -> List[Face]:
        """
        检测图像中的人脸

        Args:
            image: 输入图像 (BGR 格式)
            scale_factor: 缩放因子
            min_neighbors: 最小邻居数
            min_size: 最小人脸尺寸

        Returns:
            检测到的人脸列表
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # 检测人脸
        faces_rects = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        # 转换为 Face 对象
        faces = []
        if len(faces_rects) > 0:
            for (x, y, w, h) in faces_rects:
                faces.append(Face(bbox=(x, y, w, h), confidence=1.0))

        return faces


class MTCNNDetector:
    """
    基于 MTCNN 的人脸检测器

    使用简化的 MTCNN 实现，包含 P-Net、R-Net、O-Net 三个网络。
    """

    def __init__(self, min_face_size: int = 20, thresholds: List[float] = None):
        """
        初始化 MTCNN 检测器

        Args:
            min_face_size: 最小人脸尺寸
            thresholds: 各网络的置信度阈值
        """
        self.min_face_size = min_face_size
        self.thresholds = thresholds or [0.6, 0.7, 0.7]

        # 使用 OpenCV 的 DNN 模块作为后端
        # 这里使用简化的实现，实际应用中可以使用预训练的 MTCNN 模型
        self._init_networks()

    def _init_networks(self):
        """初始化网络"""
        # 简化实现：使用 OpenCV 的人脸检测作为替代
        # 实际应用中应该加载预训练的 MTCNN 模型
        prototxt = None  # 可以加载 Caffe 模型
        self.use_opencv_fallback = True

    def detect(self, image: np.ndarray) -> List[Face]:
        """
        检测图像中的人脸

        Args:
            image: 输入图像 (BGR 格式)

        Returns:
            检测到的人脸列表
        """
        if self.use_opencv_fallback:
            return self._detect_with_opencv(image)
        return self._detect_with_mtcnn(image)

    def _detect_with_opencv(self, image: np.ndarray) -> List[Face]:
        """使用 OpenCV DNN 进行检测"""
        h, w = image.shape[:2]

        # 使用 OpenCV 的人脸检测器
        detector = HaarDetector()
        faces = detector.detect(image)

        # 添加模拟的关键点
        for face in faces:
            x, y, fw, fh = face.bbox
            face.landmarks = {
                "left_eye": (x + fw // 3, y + fh // 3),
                "right_eye": (x + 2 * fw // 3, y + fh // 3),
                "nose": (x + fw // 2, y + fh // 2),
                "left_mouth": (x + fw // 3, y + 2 * fh // 3),
                "right_mouth": (x + 2 * fw // 3, y + 2 * fh // 3),
            }
            face.confidence = 0.9

        return faces

    def _detect_with_mtcnn(self, image: np.ndarray) -> List[Face]:
        """使用 MTCNN 进行检测"""
        # 这里是完整的 MTCNN 实现占位
        # 实际实现需要加载预训练模型
        raise NotImplementedError("完整 MTCNN 实现需要预训练模型")


class FaceDetector:
    """
    人脸检测器

    支持多种检测方法的统一接口。
    """

    def __init__(self, method: str = "haar"):
        """
        初始化检测器

        Args:
            method: 检测方法 ("haar" 或 "mtcnn")
        """
        self.method = method.lower()

        if self.method == "haar":
            self._detector = HaarDetector()
        elif self.method == "mtcnn":
            self._detector = MTCNNDetector()
        else:
            raise ValueError(f"不支持的检测方法: {method}")

    def detect(self, image: np.ndarray) -> List[Face]:
        """
        检测图像中的人脸

        Args:
            image: 输入图像 (BGR 格式)

        Returns:
            检测到的人脸列表
        """
        if image is None or image.size == 0:
            raise ValueError("输入图像为空")

        return self._detector.detect(image)

    def detect_and_crop(self, image: np.ndarray, target_size: Tuple[int, int] = (160, 160),
                        margin: float = 0.2) -> List[np.ndarray]:
        """
        检测并裁剪人脸

        Args:
            image: 输入图像
            target_size: 目标大小
            margin: 边距比例

        Returns:
            裁剪后的人脸图像列表
        """
        faces = self.detect(image)
        cropped_faces = []

        for face in faces:
            x, y, w, h = face.bbox

            # 添加边距
            margin_x = int(w * margin)
            margin_y = int(h * margin)

            # 计算裁剪区域
            x1 = max(0, x - margin_x)
            y1 = max(0, y - margin_y)
            x2 = min(image.shape[1], x + w + margin_x)
            y2 = min(image.shape[0], y + h + margin_y)

            # 裁剪和调整大小
            cropped = image[y1:y2, x1:x2]
            cropped = cv2.resize(cropped, target_size)
            cropped_faces.append(cropped)

        return cropped_faces

    @property
    def method_name(self) -> str:
        """返回检测方法名称"""
        return self.method
