"""
Tests for Gesture Classifier

测试覆盖：
1. 特征提取测试
2. 分类网络测试
3. 规则分类测试
4. 边界情况测试
"""

import pytest
import torch
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gesture_recognition.models.gesture_classifier import (
    KeypointFeatureExtractor,
    GestureClassifierNet,
    GestureClassifier,
    GESTURE_CLASSES,
    GESTURE_NAMES_ZH,
)


class TestKeypointFeatureExtractor:
    """关键点特征提取器测试"""

    def test_extract_features(self, sample_keypoints):
        """测试特征提取"""
        features = KeypointFeatureExtractor.extract_features(sample_keypoints)

        assert isinstance(features, np.ndarray)
        assert features.dtype == np.float32
        assert len(features) > 0

    def test_finger_states_open_palm(self, sample_keypoints):
        """测试张开手掌的手指状态"""
        states = KeypointFeatureExtractor._get_finger_states(sample_keypoints)

        assert len(states) == 5
        # 所有手指应该伸展
        assert all(s > 0 for s in states)

    def test_finger_states_fist(self, fist_keypoints):
        """测试拳头的手指状态"""
        states = KeypointFeatureExtractor._get_finger_states(fist_keypoints)

        assert len(states) == 5
        # 大部分手指应该弯曲
        assert sum(states) <= 2

    def test_tip_distances(self, sample_keypoints):
        """测试指尖距离计算"""
        distances = KeypointFeatureExtractor._get_tip_distances(sample_keypoints)

        assert len(distances) == 10  # C(5,2) = 10
        assert all(d >= 0 for d in distances)

    def test_finger_angles(self, sample_keypoints):
        """测试手指角度计算"""
        angles = KeypointFeatureExtractor._get_finger_angles(sample_keypoints)

        assert len(angles) == 4
        # 角度应该在[0, pi]范围内
        assert all(0 <= a <= np.pi for a in angles)

    def test_palm_distances(self, sample_keypoints):
        """测试手掌到指尖距离"""
        distances = KeypointFeatureExtractor._get_palm_to_tip_distances(sample_keypoints)

        assert len(distances) == 5
        assert all(d >= 0 for d in distances)

    def test_normalize_keypoints(self, sample_keypoints):
        """测试关键点归一化"""
        normalized = KeypointFeatureExtractor._normalize_keypoints(sample_keypoints)

        assert normalized.shape == (21, 2)
        # 手腕应该在原点
        np.testing.assert_array_almost_equal(normalized[0], [0, 0])


class TestGestureClassifierNet:
    """分类网络测试"""

    def test_model_structure(self):
        """测试模型结构"""
        model = GestureClassifierNet(input_dim=66, num_classes=7)
        assert model is not None

    def test_forward_pass(self):
        """测试前向传播"""
        model = GestureClassifierNet(input_dim=66, num_classes=7)
        x = torch.randn(4, 66)

        output = model(x)
        assert output.shape == (4, 7)

    def test_output_logits(self):
        """测试输出是logits"""
        model = GestureClassifierNet(input_dim=66, num_classes=7)
        model.eval()  # eval模式下BatchNorm不需要batch>1
        x = torch.randn(2, 66)

        output = model(x)
        # 输出应该是实数
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()


class TestGestureClassifier:
    """手势分类器测试"""

    def test_init(self):
        """测试初始化"""
        classifier = GestureClassifier()
        assert classifier.device == torch.device("cpu")
        assert len(classifier.classes) == 7

    def test_classify_rule_based_open_palm(self, sample_keypoints):
        """测试规则分类：张开手掌"""
        classifier = GestureClassifier()
        result = classifier.classify_rule_based(sample_keypoints)

        assert "gesture" in result
        assert "gesture_zh" in result
        assert "confidence" in result
        assert result["gesture"] == "open_palm"

    def test_classify_rule_based_fist(self, fist_keypoints):
        """测试规则分类：拳头"""
        classifier = GestureClassifier()
        result = classifier.classify_rule_based(fist_keypoints)

        assert result["gesture"] == "fist"

    def test_classify_neural(self, sample_keypoints):
        """测试神经网络分类"""
        classifier = GestureClassifier()
        result = classifier.classify(sample_keypoints)

        assert "gesture" in result
        assert "probabilities" in result
        assert len(result["probabilities"]) == 7

    def test_gesture_classes(self):
        """测试手势类别定义"""
        assert len(GESTURE_CLASSES) == 7
        assert 0 in GESTURE_CLASSES
        assert GESTURE_CLASSES[0] == "fist"

    def test_gesture_names_zh(self):
        """测试中文名称"""
        assert len(GESTURE_NAMES_ZH) == 7
        assert "fist" in GESTURE_NAMES_ZH
        assert GESTURE_NAMES_ZH["fist"] == "拳头"

    def test_batch_classify(self, sample_keypoints):
        """测试批量分类"""
        classifier = GestureClassifier()

        # 创建多个关键点
        keypoints_list = [sample_keypoints] * 3
        results = classifier.batch_classify(keypoints_list)

        assert len(results) == 3
        for result in results:
            assert "gesture" in result
