"""视频内容分类器测试"""

import pytest
import torch

from video_understanding.models.classifier import VideoContentClassifier


class TestVideoContentClassifier:
    """VideoContentClassifier 测试类"""

    def test_init(self):
        """测试初始化"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        assert classifier.num_classes == 10

    def test_forward(self, sample_frames_batch):
        """测试前向传播"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        logits = classifier(sample_frames_batch)
        assert logits.shape == (2, 10)

    def test_predict(self, sample_frames):
        """测试预测"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        results = classifier.predict(sample_frames, top_k=5)
        assert len(results) == 1
        assert "predicted_class" in results[0]
        assert "confidence" in results[0]
        assert len(results[0]["top_classes"]) == 5

    def test_predict_batch(self, sample_frames_batch):
        """测试 batch 预测"""
        classifier = VideoContentClassifier(num_classes=5, pretrained=False)
        results = classifier.predict(sample_frames_batch, top_k=3)
        assert len(results) == 2
        for r in results:
            assert len(r["top_classes"]) == 3

    def test_get_features(self, sample_frames):
        """测试特征提取"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        features = classifier.get_features(sample_frames)
        assert features.shape == (512,)

    def test_logits_not_normalized(self, sample_frames_batch):
        """测试 logits 未归一化"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        logits = classifier(sample_frames_batch)
        # logits 不应在 [0, 1] 范围内
        assert logits.min() < 0 or logits.max() > 1

    def test_predict_probabilities_sum_to_one(self, sample_frames):
        """测试预测概率和为 1"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        results = classifier.predict(sample_frames, top_k=10)
        prob_sum = sum(results[0]["top_probs"])
        assert abs(prob_sum - 1.0) < 0.01

    def test_repr(self):
        """测试字符串表示"""
        classifier = VideoContentClassifier(num_classes=10, pretrained=False)
        repr_str = repr(classifier)
        assert "10" in repr_str
