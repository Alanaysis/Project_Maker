"""视频特征提取器测试"""

import pytest
import torch

from video_understanding.models.feature_extractor import VideoFeatureExtractor


class TestVideoFeatureExtractor:
    """VideoFeatureExtractor 测试类"""

    def test_init_resnet18(self):
        """测试 ResNet18 骨干网络初始化"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        assert extractor.backbone_name == "resnet18"
        assert extractor.feature_dim == 512

    def test_init_resnet50(self):
        """测试 ResNet50 骨干网络初始化"""
        extractor = VideoFeatureExtractor(backbone="resnet50", pretrained=False)
        assert extractor.feature_dim == 512

    def test_invalid_backbone(self):
        """测试无效骨干网络"""
        with pytest.raises(ValueError):
            VideoFeatureExtractor(backbone="invalid_net")

    def test_forward_single_video(self, sample_frames):
        """测试单视频前向传播"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        output = extractor(sample_frames)
        assert output.shape == (512,)

    def test_forward_batch(self, sample_frames_batch):
        """测试 batch 前向传播"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        output = extractor(sample_frames_batch)
        assert output.shape == (2, 512)

    def test_extract_frame_features_single(self, sample_frames):
        """测试单视频帧特征提取"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        features = extractor.extract_frame_features(sample_frames)
        assert features.shape == (8, 512)

    def test_extract_frame_features_batch(self, sample_frames_batch):
        """测试 batch 帧特征提取"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        features = extractor.extract_frame_features(sample_frames_batch)
        assert features.shape == (2, 8, 512)

    def test_temporal_pool_mean(self, sample_frames):
        """测试平均池化"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False, pooling="mean")
        features = extractor.extract_frame_features(sample_frames)
        pooled = extractor.temporal_pool(features)
        assert pooled.shape == (512,)

    def test_temporal_pool_max(self, sample_frames):
        """测试最大池化"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False, pooling="max")
        features = extractor.extract_frame_features(sample_frames)
        pooled = extractor.temporal_pool(features)
        assert pooled.shape == (512,)

    def test_temporal_pool_attention(self, sample_frames):
        """测试注意力池化"""
        extractor = VideoFeatureExtractor(
            backbone="resnet18", pretrained=False, pooling="attention"
        )
        features = extractor.extract_frame_features(sample_frames)
        pooled = extractor.temporal_pool(features)
        assert pooled.shape == (512,)

    def test_custom_feature_dim(self, sample_frames):
        """测试自定义特征维度"""
        extractor = VideoFeatureExtractor(
            backbone="resnet18", pretrained=False, feature_dim=256
        )
        output = extractor(sample_frames)
        assert output.shape == (256,)

    def test_repr(self):
        """测试字符串表示"""
        extractor = VideoFeatureExtractor(backbone="resnet18", pretrained=False)
        repr_str = repr(extractor)
        assert "resnet18" in repr_str
        assert "512" in repr_str
