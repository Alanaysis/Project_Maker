"""视频摘要生成器测试"""

import pytest
import torch

from video_understanding.models.summarizer import VideoSummarizer


class TestVideoSummarizer:
    """VideoSummarizer 测试类"""

    def test_init(self):
        """测试初始化"""
        summarizer = VideoSummarizer(num_keyframes=5)
        assert summarizer.num_keyframes == 5

    def test_compute_importance_scores(self, sample_frames):
        """测试重要性分数计算"""
        summarizer = VideoSummarizer(num_keyframes=3)
        scores = summarizer.compute_importance_scores(sample_frames)
        assert scores.shape == (8,)
        assert (scores >= 0).all()
        assert (scores <= 1).all()

    def test_detect_scene_changes(self, sample_frames):
        """测试场景变化检测"""
        summarizer = VideoSummarizer()
        changes = summarizer.detect_scene_changes(sample_frames)
        assert isinstance(changes, list)

    def test_extract_keyframes(self, sample_frames):
        """测试关键帧提取"""
        summarizer = VideoSummarizer(num_keyframes=3)
        indices, scores = summarizer.extract_keyframes(sample_frames)
        assert len(indices) == 3
        assert len(scores) == 3
        # 索引应有序
        assert all(indices[i] <= indices[i + 1] for i in range(len(indices) - 1))

    def test_generate_summary(self, sample_frames):
        """测试摘要生成"""
        summarizer = VideoSummarizer(num_keyframes=3)
        summary = summarizer.generate_summary(sample_frames)
        assert "num_frames" in summary
        assert "num_keyframes" in summary
        assert "keyframe_indices" in summary
        assert "keyframe_scores" in summary
        assert "scene_changes" in summary
        assert "video_feature" in summary
        assert summary["num_frames"] == 8

    def test_forward(self, sample_frames):
        """测试前向传播"""
        summarizer = VideoSummarizer()
        output = summarizer(sample_frames)
        assert output.shape == (512,)

    def test_keyframes_less_than_total(self, small_frames):
        """测试关键帧数小于总帧数"""
        summarizer = VideoSummarizer(num_keyframes=10)
        indices, scores = summarizer.extract_keyframes(small_frames)
        # 应不超过总帧数
        assert len(indices) <= 4

    def test_repr(self):
        """测试字符串表示"""
        summarizer = VideoSummarizer(num_keyframes=5)
        repr_str = repr(summarizer)
        assert "5" in repr_str
