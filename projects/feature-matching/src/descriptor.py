"""
描述子提取模块

实现SIFT、ORB等描述子计算算法。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DescriptorExtractor:
    """
    描述子提取器

    支持SIFT和ORB两种描述子算法。

    Args:
        method: 描述子方法，支持 'sift' 和 'orb'

    Example:
        >>> extractor = DescriptorExtractor(method='sift')
        >>> keypoints, descriptors = extractor.compute(image, keypoints)
    """

    SUPPORTED_METHODS = ['sift', 'orb']

    # 描述子维度
    DESCRIPTOR_DIMS = {
        'sift': 128,
        'orb': 32
    }

    def __init__(self, method: str = 'sift'):
        """
        初始化描述子提取器

        Args:
            method: 描述子方法

        Raises:
            ValueError: 不支持的方法
        """
        self.method = method.lower()

        if self.method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method: {method}. "
                f"Supported methods: {self.SUPPORTED_METHODS}"
            )

        self._extractor = self._create_extractor()
        logger.info(f"初始化 {self.method.upper()} 描述子提取器")

    def _create_extractor(self):
        """
        创建描述子提取器实例

        Returns:
            OpenCV特征提取器实例
        """
        if self.method == 'sift':
            return cv2.SIFT_create()
        elif self.method == 'orb':
            return cv2.ORB_create()
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def compute(self, image: np.ndarray, keypoints: List[cv2.KeyPoint]) -> Tuple[List[cv2.KeyPoint], Optional[np.ndarray]]:
        """
        计算描述子

        Args:
            image: 灰度图像，dtype=np.uint8
            keypoints: 关键点列表

        Returns:
            (关键点列表, 描述子矩阵)
            如果关键点为空，返回 ([], None)

        Raises:
            ValueError: 图像为空或格式不正确
        """
        if image is None:
            raise ValueError("Image cannot be None")

        if len(image.shape) != 2:
            raise ValueError(f"Expected grayscale image, got shape {image.shape}")

        if not keypoints:
            logger.warning("关键点列表为空，返回空描述子")
            return [], None

        keypoints, descriptors = self._extractor.compute(image, keypoints)
        logger.info(f"计算了 {len(keypoints)} 个描述子，维度: {descriptors.shape if descriptors is not None else None}")
        return keypoints, descriptors

    def get_descriptor_dim(self) -> int:
        """
        获取描述子维度

        Returns:
            描述子维度
        """
        return self.DESCRIPTOR_DIMS.get(self.method, 0)

    def get_params(self) -> dict:
        """
        获取提取器参数

        Returns:
            参数字典
        """
        return {
            'method': self.method,
            'descriptor_dim': self.get_descriptor_dim()
        }
