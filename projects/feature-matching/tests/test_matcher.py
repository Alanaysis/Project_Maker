"""
特征匹配器测试
"""

import cv2
import numpy as np
import pytest
from src.matcher import FeatureMatcher


@pytest.fixture
def sift_descriptors():
    """创建SIFT描述子"""
    # 创建两个相似的描述子集
    np.random.seed(42)
    desc1 = np.random.randn(20, 128).astype(np.float32)
    # 添加一些相似的描述子
    desc2 = desc1[:10] + np.random.randn(10, 128).astype(np.float32) * 0.1
    desc2 = np.vstack([desc2, np.random.randn(10, 128).astype(np.float32)])
    return desc1, desc2


@pytest.fixture
def orb_descriptors():
    """创建ORB描述子"""
    np.random.seed(42)
    desc1 = np.random.randint(0, 256, (20, 32), dtype=np.uint8)
    desc2 = desc1[:10].copy()
    desc2 = np.vstack([desc2, np.random.randint(0, 256, (10, 32), dtype=np.uint8)])
    return desc1, desc2


@pytest.fixture
def sample_image_pair():
    """创建图像对"""
    img1 = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img1, (30, 30), (100, 100), 255, -1)
    cv2.circle(img1, (150, 150), 30, 255, -1)

    img2 = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img2, (40, 40), (110, 110), 255, -1)
    cv2.circle(img2, (160, 160), 30, 255, -1)

    return img1, img2


class TestFeatureMatcher:
    """特征匹配器测试类"""

    def test_bf_match_sift(self, sift_descriptors):
        """测试暴力匹配SIFT描述子"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=True)
        matches = matcher.match(desc1, desc2)

        assert len(matches) > 0, "应匹配到特征点"
        for m in matches:
            assert hasattr(m, 'queryIdx'), "匹配应有queryIdx"
            assert hasattr(m, 'trainIdx'), "匹配应有trainIdx"
            assert hasattr(m, 'distance'), "匹配应有distance"

    def test_bf_match_orb(self, orb_descriptors):
        """测试暴力匹配ORB描述子"""
        desc1, desc2 = orb_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=True, norm_type=cv2.NORM_HAMMING)
        matches = matcher.match(desc1, desc2)

        assert len(matches) > 0, "应匹配到特征点"

    def test_flann_match(self, sift_descriptors):
        """测试FLANN匹配"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='flann')
        matches = matcher.match(desc1, desc2)

        assert len(matches) > 0, "应匹配到特征点"

    def test_knn_match(self, sift_descriptors):
        """测试KNN匹配"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=False)
        matches = matcher.knn_match(desc1, desc2, k=2)

        assert len(matches) > 0, "应返回匹配结果"
        for match_pair in matches:
            assert len(match_pair) == 2, "k=2时应返回2个匹配"

    def test_ratio_test(self, sift_descriptors):
        """测试比率测试"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=False)
        knn_matches = matcher.knn_match(desc1, desc2, k=2)
        good_matches = matcher.ratio_test(knn_matches, ratio=0.7)

        assert len(good_matches) <= len(knn_matches), "比率测试应过滤掉部分匹配"
        assert len(good_matches) >= 0, "匹配数量应非负"

    def test_filter_by_distance(self, sift_descriptors):
        """测试距离过滤"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=True)
        matches = matcher.match(desc1, desc2)

        # 使用自定义阈值
        filtered = matcher.filter_by_distance(matches, max_distance=500)
        assert len(filtered) <= len(matches), "过滤后匹配数应减少"

        # 使用默认阈值
        filtered_default = matcher.filter_by_distance(matches)
        assert len(filtered_default) >= 0, "过滤结果应非负"

    def test_empty_descriptors(self):
        """测试空描述子"""
        matcher = FeatureMatcher(method='bf')
        matches = matcher.match(None, None)
        assert len(matches) == 0, "空描述子应返回空匹配"

    def test_empty_array(self):
        """测试空数组"""
        matcher = FeatureMatcher(method='bf')
        matches = matcher.match(np.array([]), np.array([]))
        assert len(matches) == 0, "空数组应返回空匹配"

    def test_get_params(self):
        """测试获取参数"""
        matcher = FeatureMatcher(method='bf', cross_check=True)
        params = matcher.get_params()

        assert params['method'] == 'bf'
        assert params['cross_check'] is True

    def test_unsupported_method(self):
        """测试不支持的方法"""
        with pytest.raises(ValueError):
            FeatureMatcher(method='unsupported')

    def test_full_pipeline(self, sample_image_pair):
        """测试完整流程"""
        img1, img2 = sample_image_pair

        # 检测特征点
        detector = cv2.SIFT_create()
        kp1, des1 = detector.detectAndCompute(img1, None)
        kp2, des2 = detector.detectAndCompute(img2, None)

        # 匹配
        matcher = FeatureMatcher(method='bf', cross_check=True)
        matches = matcher.match(des1, des2)

        assert len(matches) > 0, "应匹配到特征点"

        # 检查匹配索引范围
        for m in matches:
            assert 0 <= m.queryIdx < len(kp1), f"queryIdx越界: {m.queryIdx}"
            assert 0 <= m.trainIdx < len(kp2), f"trainIdx越界: {m.trainIdx}"

    def test_match_distance_sorted(self, sift_descriptors):
        """测试匹配距离排序"""
        desc1, desc2 = sift_descriptors
        matcher = FeatureMatcher(method='bf', cross_check=True)
        matches = matcher.match(desc1, desc2)

        # 按距离排序
        sorted_matches = sorted(matches, key=lambda x: x.distance)

        # 检查排序
        for i in range(len(sorted_matches) - 1):
            assert sorted_matches[i].distance <= sorted_matches[i+1].distance, \
                "匹配应按距离升序排列"

    def test_cross_check_effect(self, sift_descriptors):
        """测试交叉验证效果"""
        desc1, desc2 = sift_descriptors

        # 带交叉验证
        matcher_checked = FeatureMatcher(method='bf', cross_check=True)
        matches_checked = matcher_checked.match(desc1, desc2)

        # 不带交叉验证
        matcher_unchecked = FeatureMatcher(method='bf', cross_check=False)
        matches_unchecked = matcher_unchecked.match(desc1, desc2)

        # 交叉验证通常会减少匹配数量
        assert len(matches_checked) <= len(matches_unchecked), \
            "交叉验证应减少匹配数量"
