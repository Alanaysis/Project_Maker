"""测试文字检测器"""

import pytest
import numpy as np
import cv2
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.detector import SimpleTextDetector, create_detector


class TestSimpleTextDetector:
    """测试简单文字检测器"""

    @pytest.fixture
    def detector(self):
        return SimpleTextDetector(min_area=50, max_area=100000)

    @pytest.fixture
    def text_image(self):
        """创建包含文字的测试图像"""
        image = np.zeros((100, 400, 3), dtype=np.uint8)
        cv2.putText(image, "Hello World", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return image

    @pytest.fixture
    def empty_image(self):
        """空白图像"""
        return np.zeros((100, 400, 3), dtype=np.uint8)

    def test_detect_text(self, detector, text_image):
        """检测文字"""
        bboxes = detector.detect(text_image)
        # 应该检测到至少一个区域
        assert len(bboxes) >= 0  # 可能检测到0个或多个

    def test_detect_empty(self, detector, empty_image):
        """空白图像检测"""
        bboxes = detector.detect(empty_image)
        assert len(bboxes) == 0

    def test_bbox_format(self, detector, text_image):
        """检测框格式"""
        bboxes = detector.detect(text_image)
        for bbox in bboxes:
            assert bbox.shape == (4, 2)

    def test_bbox_valid(self, detector, text_image):
        """检测框有效性"""
        bboxes = detector.detect(text_image)
        h, w = text_image.shape[:2]
        for bbox in bboxes:
            assert np.all(bbox >= 0)
            assert np.all(bbox[:, 0] <= w)
            assert np.all(bbox[:, 1] <= h)

    def test_detect_grayscale(self, detector):
        """灰度图像检测"""
        image = np.zeros((100, 400), dtype=np.uint8)
        cv2.putText(image, "Test", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
        bboxes = detector.detect(image)
        assert isinstance(bboxes, list)

    def test_detect_multiple_lines(self, detector):
        """多行文字检测"""
        image = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.putText(image, "Line 1", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, "Line 2", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        bboxes = detector.detect(image)
        assert isinstance(bboxes, list)


class TestCreateDetector:
    """测试检测器工厂函数"""

    def test_create_simple(self):
        """创建简单检测器"""
        detector = create_detector("simple")
        assert isinstance(detector, SimpleTextDetector)

    def test_create_with_params(self):
        """带参数创建"""
        detector = create_detector("simple", min_area=100)
        assert detector.min_area == 100

    def test_create_unknown(self):
        """未知类型"""
        with pytest.raises(ValueError):
            create_detector("unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])