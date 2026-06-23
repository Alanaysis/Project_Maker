"""
描述子提取器测试
"""

import cv2
import numpy as np
import pytest
from src.descriptor import DescriptorExtractor
from src.detector import FeatureDetector


@pytest.fixture
def keypoints_and_image():
    """创建关键点和图像"""
    img = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img, (30, 30), (170, 170), 255, -1)
    cv2.circle(img, (100, 100), 50, 128, -1)

    detector = cv2.SIFT_create()
    keypoints = detector.detect(img)
    return img, keypoints


@pytest.fixture
def sample_image():
    """创建测试图像"""
    img = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(img, (30, 30), (70, 70), 255, -1)
    cv2.circle(img, (150, 150), 30, 255, -1)
    return img


class TestDescriptorExtractor:
    """描述子提取器测试类"""

    def test_sift_descriptor(self, keypoints_and_image):
        """测试SIFT描述子"""
        img, keypoints = keypoints_and_image
        extractor = DescriptorExtractor(method='sift')
        _, descriptors = extractor.compute(img, keypoints)

        assert descriptors is not None, "描述子不为空"
        assert descriptors.shape[1] == 128, "SIFT描述子维度应为128"

    def test_orb_descriptor(self, sample_image):
        """测试ORB描述子"""
        detector = cv2.ORB_create()
        keypoints = detector.detect(sample_image)

        extractor = DescriptorExtractor(method='orb')
        _, descriptors = extractor.compute(sample_image, keypoints)

        assert descriptors is not None, "描述子不为空"
        assert descriptors.shape[1] == 32, "ORB描述子维度应为32"

    def test_empty_keypoints(self):
        """测试空关键点"""
        img = np.zeros((100, 100), dtype=np.uint8)
        extractor = DescriptorExtractor(method='sift')
        _, descriptors = extractor.compute(img, [])
        assert descriptors is None, "空关键点应返回空描述子"

    def test_invalid_image(self):
        """测试无效图像"""
        extractor = DescriptorExtractor(method='sift')
        with pytest.raises(ValueError):
            extractor.compute(None, [])

    def test_color_image(self):
        """测试彩色图像"""
        extractor = DescriptorExtractor(method='sift')
        color_img = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            extractor.compute(color_img, [])

    def test_descriptor_type(self, keypoints_and_image):
        """测试描述子类型"""
        img, keypoints = keypoints_and_image
        extractor = DescriptorExtractor(method='sift')
        _, descriptors = extractor.compute(img, keypoints)

        assert descriptors.dtype == np.float32, "SIFT描述子类型应为float32"

    def test_orb_descriptor_type(self, sample_image):
        """测试ORB描述子类型"""
        detector = cv2.ORB_create()
        keypoints = detector.detect(sample_image)

        extractor = DescriptorExtractor(method='orb')
        _, descriptors = extractor.compute(sample_image, keypoints)

        assert descriptors.dtype == np.uint8, "ORB描述子类型应为uint8"

    def test_get_descriptor_dim(self):
        """测试获取描述子维度"""
        extractor_sift = DescriptorExtractor(method='sift')
        extractor_orb = DescriptorExtractor(method='orb')

        assert extractor_sift.get_descriptor_dim() == 128
        assert extractor_orb.get_descriptor_dim() == 32

    def test_get_params(self):
        """测试获取参数"""
        extractor = DescriptorExtractor(method='sift')
        params = extractor.get_params()

        assert params['method'] == 'sift'
        assert params['descriptor_dim'] == 128

    def test_unsupported_method(self):
        """测试不支持的方法"""
        with pytest.raises(ValueError):
            DescriptorExtractor(method='unsupported')

    def test_descriptor_consistency(self, sample_image):
        """测试描述子一致性"""
        detector = cv2.SIFT_create()
        keypoints = detector.detect(sample_image)

        extractor = DescriptorExtractor(method='sift')

        # 两次计算应该得到相同结果
        _, desc1 = extractor.compute(sample_image, keypoints)
        _, desc2 = extractor.compute(sample_image, keypoints)

        np.testing.assert_array_equal(desc1, desc2, err_msg="两次计算应得到相同描述子")

    def test_different_images_different_descriptors(self):
        """测试不同图像不同描述子"""
        img1 = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(img1, (20, 20), (80, 80), 255, -1)

        img2 = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img2, (50, 50), 30, 255, -1)

        detector = cv2.SIFT_create()
        kp1 = detector.detect(img1)
        kp2 = detector.detect(img2)

        extractor = DescriptorExtractor(method='sift')
        _, desc1 = extractor.compute(img1, kp1)
        _, desc2 = extractor.compute(img2, kp2)

        # 不同图像的描述子应该不同
        if desc1 is not None and desc2 is not None:
            assert not np.array_equal(desc1, desc2), "不同图像的描述子应该不同"
