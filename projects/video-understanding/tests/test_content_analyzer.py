"""内容分析器测试"""

import pytest
import torch

from video_understanding.core.content_analyzer import ContentAnalyzer


class TestContentAnalyzer:
    """ContentAnalyzer 测试类"""

    def test_init(self):
        """测试初始化"""
        analyzer = ContentAnalyzer(num_classes=10, num_frames=8)
        assert analyzer.num_frames == 8
        assert analyzer.num_keyframes == 5

    def test_analyze_frames(self, sample_frames):
        """测试帧分析"""
        analyzer = ContentAnalyzer(num_classes=10, num_frames=8)
        results = analyzer.analyze_frames(sample_frames)

        assert "video_feature" in results
        assert "frame_features" in results
        assert "predictions" in results
        assert "importance_scores" in results
        assert "keyframe_indices" in results
        assert "num_frames" in results
        assert results["num_frames"] == 8

    def test_analyze_frames_predictions(self, sample_frames):
        """测试分析结果包含预测"""
        analyzer = ContentAnalyzer(num_classes=5)
        results = analyzer.analyze_frames(sample_frames)
        pred = results["predictions"]
        assert "predicted_class" in pred
        assert "confidence" in pred
        assert 0 <= pred["confidence"] <= 1

    def test_compute_frame_similarity(self, sample_frames):
        """测试帧间相似度计算"""
        analyzer = ContentAnalyzer()
        similarity = analyzer.compute_frame_similarity(sample_frames)
        assert similarity.shape == (8, 8)
        # 对角线应接近 1
        for i in range(8):
            assert abs(similarity[i, i] - 1.0) < 0.01

    def test_detect_segments(self, sample_frames):
        """测试片段检测"""
        analyzer = ContentAnalyzer()
        segments = analyzer.detect_segments(sample_frames)
        assert len(segments) >= 1
        for start, end in segments:
            assert start <= end

    def test_analyze_numpy_frames(self, sample_numpy_frames):
        """测试 numpy 帧分析"""
        analyzer = ContentAnalyzer(num_classes=10)
        results = analyzer.analyze_numpy_frames(sample_numpy_frames)
        assert "video_feature" in results

    def test_repr(self):
        """测试字符串表示"""
        analyzer = ContentAnalyzer(num_frames=16, num_keyframes=5)
        repr_str = repr(analyzer)
        assert "16" in repr_str
        assert "5" in repr_str
