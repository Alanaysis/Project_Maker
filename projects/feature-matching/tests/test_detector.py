"""
特征检测器测试
"""

import cv2
import numpy as np
import pytest
from src.detector import FeatureDetector


@pytest.fixture
def sample_image():
    """创建测试图像"""
    img = np.zeros((200, 200), dtype=np.uint8)
    # 添加几何图形作为特征
    cv2.rectangle(img, (30, 30), (70, 70), 255, -1)
    cv2.circle(img, (150, 150), 30, 255, -1)
    cv2.line(img, (20, 180), (180, 20), 255, 3)
    return img


@pytest.fixture
def texture_image():
    """创建有纹理的测试图像"""
    img = np.zeros((200, 200), dtype=np.uint8)
    # 添加多个小特征
    for i in range(10):
        for j in range(10):
            x = 20 + i * 18
            y = 20 + j * 18
            cv2.rectangle(img, (x, y), (x+8, y+8), 255, -1)
    return img


class TestFeatureDetector:
    """特征检测器测试类"""

    def test_sift_detection(self, sample_image):
        """测试SIFT检测"""
        detector = FeatureDetector(method='sift')
        keypoints = detector.detect(sample_image)
        assert len(keypoints) > 0, "SIFT应该检测到特征点"

    def test_orb_detection(self, sample_image):
        """测试ORB检测"""
        detector = FeatureDetector(method='orb')
        keypoints = detector.detect(sample_image)
        assert len(keypoints) > 0, "ORB应该检测到特征点"

    def test_sift_detect_and_compute(self, sample_image):
        """测试SIFT同时检测和计算"""
        detector = FeatureDetector(method='sift')
        keypoints, descriptors = detector.detect_and_compute(sample_image)
        assert len(keypoints) > 0, "应该检测到特征点"
        assert descriptors is not None, "描述子不为空"
        assert descriptors.shape[0] == len(keypoints), "描述子数量应与关键点数量一致"
        assert descriptors.shape[1] == 128, "SIFT描述子维度应为128"

    def test_orb_detect_and_compute(self, sample_image):
        """测试ORB同时检测和计算"""
        detector = FeatureDetector(method='orb')
        keypoints, descriptors = detector.detect_and_compute(sample_image)
        assert len(keypoints) > 0, "应该检测到特征点"
        assert descriptors is not None, "描述子不为空"
        assert descriptors.shape[0] == len(keypoints), "描述子数量应与关键点数量一致"
        assert descriptors.shape[1] == 32, "ORB描述子维度应为32"

    def test_invalid_image(self):
        """测试无效图像"""
        detector = FeatureDetector(method='sift')
        with pytest.raises(ValueError):
            detector.detect(None)

    def test_color_image(self):
        """测试彩色图像（应该报错）"""
        detector = FeatureDetector(method='sift')
        color_img = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            detector.detect(color_img)

    def test_texture_detection(self, texture_image):
        """测试纹理图像检测"""
        detector_sift = FeatureDetector(method='sift')
        detector_orb = FeatureDetector(method='orb')

        kp_sift = detector_sift.detect(texture_image)
        kp_orb = detector_orb.detect(texture_image)

        # 纹理图像应该检测到很多特征点
        assert len(kp_sift) > 50, "纹理图像应该检测到大量SIFT特征点"
        assert len(kp_orb) > 50, "纹理图像应该检测到大量ORB特征点"

    def test_custom_params(self, sample_image):
        """测试自定义参数"""
        # SIFT自定义参数
        detector = FeatureDetector(method='sift', nfeatures=50)
        kp, desc = detector.detect_and_compute(sample_image)
        assert len(kp) <= 50, "特征点数量应受限制"

    def test_get_params(self):
        """测试获取参数"""
        detector = FeatureDetector(method='sift', nfeatures=100)
        params = detector.get_params()
        assert params['method'] == 'sift'
        assert 'nfeatures' in params['params']

    def test_unsupported_method(self):
        """测试不支持的方法"""
        with pytest.raises(ValueError):
            FeatureDetector(method='unsupported')

    def test_keypoint_properties(self, sample_image):
        """测试关键点属性"""
        detector = FeatureDetector(method='sift')
        keypoints = detector.detect(sample_image)

        # 检查关键点属性
        kp = keypoints[0]
        assert hasattr(kp, 'pt'), "关键点应有位置属性"
        assert hasattr(kp, 'size'), "关键点应有尺度属性"
        assert hasattr(kp, 'angle'), "关键点应有方向属性"
        assert hasattr(kp, 'response'), "关键点应有响应属性"

        # 检查坐标范围
        for kp in keypoints:
            x, y = kp.pt
            assert 0 <= x < 200, f"x坐标越界: {x}"
            assert 0 <= y < 200, f"y坐标越界: {y}"

    def test_empty_image(self):
        """测试空图像（全黑）"""
        empty_img = np.zeros((100, 100), dtype=np.uint8)
        detector = FeatureDetector(method='sift')
        keypoints = detector.detect(empty_img)
        # 空图像可能检测到很少或没有特征点
        # OpenCV返回的是tuple，需要检查是否可迭代
        assert hasattr(keypoints, '__len__'), "应返回可迭代对象"
