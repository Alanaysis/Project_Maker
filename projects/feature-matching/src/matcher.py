"""
特征匹配模块

实现暴力匹配、FLANN匹配等特征匹配算法。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureMatcher:
    """
    特征匹配器

    支持暴力匹配(Brute-Force)和FLANN两种匹配方法。

    Args:
        method: 匹配方法，支持 'bf' (暴力匹配) 和 'flann'
        cross_check: 是否启用交叉验证（仅bf有效）
        **params: 匹配器特定参数

    Example:
        >>> matcher = FeatureMatcher(method='bf', cross_check=True)
        >>> matches = matcher.match(desc1, desc2)
        >>> good_matches = matcher.ratio_test(knn_matches)
    """

    SUPPORTED_METHODS = ['bf', 'flann']

    def __init__(self, method: str = 'bf', cross_check: bool = True, **params):
        """
        初始化特征匹配器

        Args:
            method: 匹配方法
            cross_check: 是否交叉验证
            **params: 额外参数

        Raises:
            ValueError: 不支持的匹配方法
        """
        self.method = method.lower()
        self.cross_check = cross_check
        self.params = params

        if self.method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method: {method}. "
                f"Supported methods: {self.SUPPORTED_METHODS}"
            )

        self._matcher = self._create_matcher()
        logger.info(f"初始化 {self.method.upper()} 匹配器")

    def _create_matcher(self):
        """
        创建匹配器实例

        Returns:
            OpenCV匹配器实例
        """
        if self.method == 'bf':
            norm_type = self.params.get('norm_type', cv2.NORM_L2)
            return cv2.BFMatcher(norm_type, self.cross_check)
        elif self.method == 'flann':
            # FLANN参数
            index_params = self.params.get('index_params', {
                'algorithm': 1,  # FLANN_INDEX_KDTREE
                'trees': 5
            })
            search_params = self.params.get('search_params', {
                'checks': 50
            })
            return cv2.FlannBasedMatcher(index_params, search_params)
        else:
            raise ValueError(f"Unsupported method: {self.method}")

    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List[cv2.DMatch]:
        """
        匹配两组描述子

        Args:
            desc1: 第一组描述子
            desc2: 第二组描述子

        Returns:
            匹配结果列表
        """
        if desc1 is None or desc2 is None:
            logger.warning("描述子为空，返回空匹配")
            return []

        if len(desc1) == 0 or len(desc2) == 0:
            logger.warning("描述子列表为空，返回空匹配")
            return []

        matches = self._matcher.match(desc1, desc2)
        logger.info(f"匹配到 {len(matches)} 个特征点")
        return matches

    def knn_match(self, desc1: np.ndarray, desc2: np.ndarray, k: int = 2) -> List[List[cv2.DMatch]]:
        """
        K近邻匹配

        Args:
            desc1: 第一组描述子
            desc2: 第二组描述子
            k: 近邻数量

        Returns:
            K近邻匹配结果
        """
        if desc1 is None or desc2 is None:
            logger.warning("描述子为空，返回空匹配")
            return []

        if len(desc1) == 0 or len(desc2) == 0:
            logger.warning("描述子列表为空，返回空匹配")
            return []

        matches = self._matcher.knnMatch(desc1, desc2, k)
        logger.info(f"KNN匹配完成，返回 {len(matches)} 组匹配")
        return matches

    def ratio_test(self, matches: List[List[cv2.DMatch]], ratio: float = 0.7) -> List[cv2.DMatch]:
        """
        Lowe比率测试

        过滤掉距离比率过大的匹配，提高匹配质量。

        Args:
            matches: KNN匹配结果
            ratio: 距离比率阈值，默认0.7

        Returns:
            过滤后的匹配列表
        """
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < ratio * n.distance:
                    good_matches.append(m)

        logger.info(f"比率测试: {len(matches)} -> {len(good_matches)} 个匹配 (ratio={ratio})")
        return good_matches

    def filter_by_distance(self, matches: List[cv2.DMatch],
                           max_distance: float = None) -> List[cv2.DMatch]:
        """
        按距离过滤匹配

        Args:
            matches: 匹配列表
            max_distance: 最大距离阈值

        Returns:
            过滤后的匹配列表
        """
        if max_distance is None:
            # 使用中位数的倍数作为默认阈值
            distances = [m.distance for m in matches]
            if not distances:
                return []
            max_distance = np.median(distances) * 2

        filtered = [m for m in matches if m.distance <= max_distance]
        logger.info(f"距离过滤: {len(matches)} -> {len(filtered)} 个匹配 (max_distance={max_distance:.2f})")
        return filtered

    def get_params(self) -> dict:
        """
        获取匹配器参数

        Returns:
            参数字典
        """
        return {
            'method': self.method,
            'cross_check': self.cross_check,
            'params': self.params
        }
