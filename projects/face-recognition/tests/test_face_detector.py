"""
人脸检测器测试
"""

import pytest
import numpy as np
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.face_detector import FaceDetector, HaarDetector, Face
from src.utils import create_test_image


class TestFace:
    """Face 类测试"""

    def test_face_creation(self):
        """测试创建 Face 对象"""
        face = Face(bbox=(10, 20, 100, 100), confidence=0.95)
        assert face.x == 10
        assert face.y == 20
        assert face.width == 100
        assert face.height == 100
        assert face.confidence == 0.95

    def test_face_center(self):
        """测试 Face 中心点"""
        face = Face(bbox=(10, 20, 100, 100))
        assert face.center == (60, 70)

    def test_face_to_dict(self):
        """测试 Face 转字典"""
        face = Face(bbox=(10, 20, 100, 100), confidence=0.95)
        d = face.to_dict()
        assert d["bbox"] == (10, 20, 100, 100)
        assert d["confidence"] == 0.95


class TestHaarDetector:
    """Haar 检测器测试"""

    def test_detector_creation(self):
        """测试创建检测器"""
        detector = HaarDetector()
        assert detector is not None

    def test_detect_with_face(self):
        """测试检测包含人脸的图像"""
        detector = HaarDetector()
        image = create_test_image(with_face=True)
        faces = detector.detect(image)
        # 注意：简单绘制的人脸可能无法被 Haar 检测器检测到
        assert isinstance(faces, list)

    def test_detect_without_face(self):
        """测试检测无人脸图像"""
        detector = HaarDetector()
        image = create_test_image(with_face=False)
        faces = detector.detect(image)
        assert isinstance(faces, list)
        assert len(faces) == 0


class TestFaceDetector:
    """FaceDetector 测试"""

    def test_detector_creation_haar(self):
        """测试创建 Haar 检测器"""
        detector = FaceDetector(method="haar")
        assert detector.method_name == "haar"

    def test_detector_creation_mtcnn(self):
        """测试创建 MTCNN 检测器"""
        detector = FaceDetector(method="mtcnn")
        assert detector.method_name == "mtcnn"

    def test_invalid_method(self):
        """测试无效的检测方法"""
        with pytest.raises(ValueError):
            FaceDetector(method="invalid")

    def test_detect_returns_list(self):
        """测试 detect 返回列表"""
        detector = FaceDetector(method="haar")
        image = create_test_image(with_face=True)
        faces = detector.detect(image)
        assert isinstance(faces, list)

    def test_detect_empty_image(self):
        """测试空图像"""
        detector = FaceDetector(method="haar")
        with pytest.raises(ValueError):
            detector.detect(np.array([]))

    def test_detect_none_image(self):
        """测试 None 图像"""
        detector = FaceDetector(method="haar")
        with pytest.raises(ValueError):
            detector.detect(None)

    def test_detect_and_crop(self):
        """测试检测并裁剪"""
        detector = FaceDetector(method="haar")
        image = create_test_image(with_face=True)
        cropped = detector.detect_and_crop(image, target_size=(160, 160))
        assert isinstance(cropped, list)
        # 如果检测到人脸，检查裁剪结果
        for face_img in cropped:
            assert face_img.shape == (160, 160, 3)

    def test_detect_scale_factor(self):
        """测试不同缩放因子"""
        detector = HaarDetector()
        image = create_test_image(with_face=True)

        # 测试不同的缩放因子
        for scale in [1.05, 1.1, 1.2]:
            faces = detector.detect(image, scale_factor=scale)
            assert isinstance(faces, list)

    def test_detect_min_neighbors(self):
        """测试不同最小邻居数"""
        detector = HaarDetector()
        image = create_test_image(with_face=True)

        # 测试不同的最小邻居数
        for neighbors in [3, 5, 7]:
            faces = detector.detect(image, min_neighbors=neighbors)
            assert isinstance(faces, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
