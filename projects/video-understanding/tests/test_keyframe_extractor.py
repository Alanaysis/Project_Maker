"""关键帧提取器测试"""

import numpy as np
import pytest

from video_understanding.core.keyframe_extractor import KeyframeExtractor


class TestKeyframeExtractor:
    """KeyframeExtractor 测试类"""

    @pytest.fixture
    def color_frames(self):
        """生成不同颜色的帧"""
        frames = []
        colors = [
            (255, 0, 0),    # 红
            (0, 255, 0),    # 绿
            (0, 0, 255),    # 蓝
            (255, 255, 0),  # 黄
            (255, 0, 255),  # 品红
            (0, 255, 255),  # 青
            (128, 128, 128), # 灰
            (255, 255, 255), # 白
        ]
        for color in colors:
            frame = np.full((100, 100, 3), color, dtype=np.uint8)
            frames.append(frame)
        return frames

    def test_init(self):
        """测试初始化"""
        extractor = KeyframeExtractor(method="histogram", threshold=0.5)
        assert extractor.method == "histogram"
        assert extractor.threshold == 0.5

    def test_empty_frames(self):
        """测试空帧列表"""
        extractor = KeyframeExtractor()
        indices, scores = extractor.extract([])
        assert indices == []
        assert scores == []

    def test_single_frame(self, color_frames):
        """测试单帧输入"""
        extractor = KeyframeExtractor(method="histogram")
        indices, scores = extractor.extract([color_frames[0]])
        assert len(indices) == 1
        assert indices[0] == 0

    def test_histogram_extraction(self, color_frames):
        """测试直方图方法提取关键帧"""
        extractor = KeyframeExtractor(method="histogram", max_keyframes=4)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) <= 4
        assert len(indices) == len(scores)
        # 索引应有序
        assert all(indices[i] <= indices[i + 1] for i in range(len(indices) - 1))

    def test_threshold_extraction(self, color_frames):
        """测试阈值方法提取关键帧"""
        extractor = KeyframeExtractor(method="threshold", threshold=0.3, max_keyframes=5)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) >= 1  # 至少第一帧

    def test_optical_flow_extraction(self, color_frames):
        """测试光流方法提取关键帧"""
        extractor = KeyframeExtractor(method="optical_flow", max_keyframes=4)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) >= 1

    def test_clustering_extraction(self, color_frames):
        """测试聚类方法提取关键帧"""
        extractor = KeyframeExtractor(method="clustering", max_keyframes=3)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) <= 3
        assert all(isinstance(i, (int, np.integer)) for i in indices)

    def test_invalid_method(self, color_frames):
        """测试无效方法"""
        extractor = KeyframeExtractor(method="invalid")
        with pytest.raises(ValueError):
            extractor.extract(color_frames)

    def test_max_keyframes_limit(self, color_frames):
        """测试最大关键帧数限制"""
        extractor = KeyframeExtractor(method="histogram", max_keyframes=2)
        indices, scores = extractor.extract(color_frames)
        assert len(indices) <= 2

    def test_similar_frames(self):
        """测试相似帧（应提取较少关键帧）"""
        # 创建非常相似的帧
        frames = [np.full((50, 50, 3), (100, 100, 100), dtype=np.uint8) for _ in range(5)]
        extractor = KeyframeExtractor(method="histogram", max_keyframes=5)
        indices, scores = extractor.extract(frames)
        # 相似帧应产生较少的关键帧（阈值方法）
        assert len(indices) >= 1

    def test_repr(self):
        """测试字符串表示"""
        extractor = KeyframeExtractor(method="histogram", max_keyframes=5)
        repr_str = repr(extractor)
        assert "histogram" in repr_str
        assert "5" in repr_str
