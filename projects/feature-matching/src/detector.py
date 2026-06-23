"""
特征点检测模块

实现SIFT、ORB等特征点检测算法。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureDetector:
    """
    特征点检测器

    支持SIFT和ORB两种检测算法。

    Args:
        method: 检测方法，支持 'sift' 和 'orb'
        **params: 算法特定参数

    Example:
        >>> detector = FeatureDetector(method='sift')
        >>> keypoints = detector.detect(image)
        >>> kp, desc = detector.detect_and_compute(image)
    """

    SUPPORTED_METHODS = ['sift', 'orb']

    def __init__(self, method: str = 'sift', **params):
        """
        初始化特征检测器

        Args:
            method: 检测方法
            **params: 算法参数

        Raises:
            ValueError: 不支持的检测方法
        """
        self.method = method.lower()
        self.params = params

        if self.method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method: {method}. "
                f"Supported methods: {self.SUPPORTED_METHODS}"
            )

        self._detector = self._create_detector()
        logger.info(f"初始化 {self.method.upper()} 检测器")

    def _create_detector(self):
        """
        创建检测器实例

        Returns:
            OpenCV检测器实例
        """
        if self.method == 'sift':
            return cv2.SIFT_create(**self.params)
        elif self.method == 'orb':
            return cv2.ORB_create(**self.params)
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def detect(self, image: np.ndarray) -> List[cv2.KeyPoint]:
        """
        检测图像中的特征点

        Args:
            image: 灰度图像，dtype=np.uint8

        Returns:
            关键点列表

        Raises:
            ValueError: 图像为空或格式不正确
        """
        if image is None:
            raise ValueError("Image cannot be None")

        if len(image.shape) != 2:
            raise ValueError(f"Expected grayscale image, got shape {image.shape}")

        keypoints = self._detector.detect(image)
        logger.info(f"检测到 {len(keypoints)} 个特征点")
        return keypoints

    def detect_and_compute(self, image: np.ndarray) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """
        同时检测关键点和计算描述子

        Args:
            image: 灰度图像，dtype=np.uint8

        Returns:
            (关键点列表, 描述子矩阵)

        Raises:
            ValueError: 图像为空或格式不正确
        """
        if image is None:
            raise ValueError("Image cannot be None")

        if len(image.shape) != 2:
            raise ValueError(f"Expected grayscale image, got shape {image.shape}")

        keypoints, descriptors = self._detector.detectAndCompute(image, None)
        logger.info(f"检测到 {len(keypoints)} 个特征点，描述子形状: {descriptors.shape if descriptors is not None else None}")
        return keypoints, descriptors

    def get_params(self) -> dict:
        """
        获取检测器参数

        Returns:
            参数字典
        """
        return {
            'method': self.method,
            'params': self.params
        }
