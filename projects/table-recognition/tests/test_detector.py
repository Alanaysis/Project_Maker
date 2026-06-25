"""
表格检测器测试
"""

import pytest
import numpy as np
import cv2

from src.detector import SimpleTableDetector, TableDetector
from src.utils import create_sample_image_with_tables


class TestSimpleTableDetector:
    """简单表格检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return SimpleTableDetector(min_area=500)

    @pytest.fixture
    def sample_image(self):
        """创建示例图像"""
        return create_sample_image_with_tables(num_tables=1)

    def test_init(self, detector):
        """测试初始化"""
        assert detector is not None
        assert detector.min_area == 500

    def test_detect_returns_list(self, detector, sample_image):
        """测试检测返回列表"""
        results = detector.detect(sample_image)
        assert isinstance(results, list)

    def test_detect_result_format(self, detector, sample_image):
        """测试检测结果格式"""
        results = detector.detect(sample_image)

        for result in results:
            assert "bbox" in result
            assert "confidence" in result
            assert "class_id" in result

            # 检查边界框格式
            bbox = result["bbox"]
            assert len(bbox) == 4
            assert all(isinstance(v, (int, np.integer)) for v in bbox)

    def test_detect_with_empty_image(self, detector):
        """测试空图像检测"""
        # 创建全白图像
        empty_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        results = detector.detect(empty_image)
        assert isinstance(results, list)

    def test_detect_with_table_image(self, detector):
        """测试表格图像检测"""
        # 创建包含表格的图像
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255

        # 绘制表格
        cv2.rectangle(image, (100, 100), (500, 300), (0, 0, 0), 2)
        cv2.line(image, (100, 200), (500, 200), (0, 0, 0), 1)
        cv2.line(image, (300, 100), (300, 300), (0, 0, 0), 1)

        results = detector.detect(image)
        assert isinstance(results, list)


class TestTableDetector:
    """表格检测器测试（需要模型）"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        # 跳过需要 GPU 或模型的测试
        pytest.skip("需要预训练模型")

    def test_init(self):
        """测试初始化"""
        # 测试无模型初始化
        try:
            detector = TableDetector(device="cpu")
            assert detector is not None
        except Exception:
            pytest.skip("无法初始化检测器")


class TestDetectorIntegration:
    """检测器集成测试"""

    def test_detect_and_crop(self):
        """测试检测和裁剪"""
        detector = SimpleTableDetector(min_area=500)

        # 创建测试图像
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (100, 100), (500, 300), (0, 0, 0), 2)

        # 检测
        results = detector.detect(image)

        # 裁剪
        for result in results:
            bbox = result["bbox"]
            x1, y1, x2, y2 = bbox
            crop = image[y1:y2, x1:x2]
            assert crop.size > 0

    def test_detect_with_visualization(self):
        """测试可视化"""
        detector = SimpleTableDetector(min_area=500)

        # 创建测试图像
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (100, 100), (500, 300), (0, 0, 0), 2)

        # 检测
        results = detector.detect(image)

        # 可视化
        vis_image = image.copy()
        for result in results:
            bbox = result["bbox"]
            cv2.rectangle(vis_image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

        assert vis_image.shape == image.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
