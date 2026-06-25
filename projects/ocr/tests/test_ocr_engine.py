"""测试 OCR 引擎"""

import pytest
import numpy as np
import cv2
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ocr_engine import OCREngine, create_ocr_engine


class TestOCREngine:
    """测试 OCR 引擎"""

    @pytest.fixture
    def engine(self):
        return OCREngine()

    @pytest.fixture
    def text_image(self):
        """创建包含文字的测试图像"""
        image = np.zeros((200, 600, 3), dtype=np.uint8)
        cv2.putText(image, "Hello", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(image, "World", (300, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        return image

    def test_process(self, engine, text_image):
        """处理图像"""
        results = engine.process(text_image)
        assert isinstance(results, list)

    def test_result_format(self, engine, text_image):
        """结果格式"""
        results = engine.process(text_image)
        for result in results:
            assert "bbox" in result
            assert "text" in result
            assert "confidence" in result

    def test_process_batch(self, engine):
        """批量处理"""
        images = [
            np.zeros((200, 600, 3), dtype=np.uint8),
            np.zeros((200, 600, 3), dtype=np.uint8)
        ]
        all_results = engine.process_batch(images)
        assert len(all_results) == 2

    def test_detect_only(self, engine, text_image):
        """仅检测"""
        bboxes = engine.detect_only(text_image)
        assert isinstance(bboxes, list)

    def test_recognize_only(self, engine):
        """仅识别"""
        image = np.zeros((32, 100), dtype=np.uint8)
        text, conf = engine.recognize_only(image)
        assert isinstance(text, str)
        assert 0 <= conf <= 1

    def test_visualize(self, engine, text_image):
        """可视化"""
        results = engine.process(text_image)
        vis = engine.visualize(text_image, results)
        assert vis.shape == text_image.shape

    def test_empty_image(self, engine):
        """空图像"""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)

    def test_small_image(self, engine):
        """极小图像"""
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        results = engine.process(image)
        assert isinstance(results, list)


class TestCreateOCREngine:
    """测试 OCR 引擎工厂函数"""

    def test_create_default(self):
        """默认创建"""
        engine = create_ocr_engine()
        assert isinstance(engine, OCREngine)

    def test_create_with_params(self):
        """带参数创建"""
        engine = create_ocr_engine(
            detector_type="simple",
            device="cpu"
        )
        assert isinstance(engine, OCREngine)

    def test_create_detector_type(self):
        """检测器类型"""
        engine = create_ocr_engine(detector_type="simple")
        assert engine.detector.__class__.__name__ == "SimpleTextDetector"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])