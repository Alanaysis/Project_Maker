"""
特征提取器测试
"""

import pytest
import numpy as np
import torch
import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.feature_extractor import FeatureExtractor, FaceEmbeddingNet, ResNetEmbedding


class TestFaceEmbeddingNet:
    """FaceEmbeddingNet 测试"""

    def test_network_creation(self):
        """测试创建网络"""
        net = FaceEmbeddingNet(embedding_size=128)
        assert net.embedding_size == 128

    def test_forward_pass(self):
        """测试前向传播"""
        net = FaceEmbeddingNet(embedding_size=128)
        x = torch.randn(2, 3, 160, 160)
        output = net(x)
        assert output.shape == (2, 128)

    def test_output_normalized(self):
        """测试输出是否归一化"""
        net = FaceEmbeddingNet(embedding_size=128)
        net.eval()
        x = torch.randn(4, 3, 160, 160)
        with torch.no_grad():
            output = net(x)
        # 检查 L2 范数
        norms = torch.norm(output, p=2, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_different_embedding_sizes(self):
        """测试不同的嵌入维度"""
        for size in [64, 128, 256, 512]:
            net = FaceEmbeddingNet(embedding_size=size)
            x = torch.randn(1, 3, 160, 160)
            output = net(x)
            assert output.shape == (1, size)


class TestResNetEmbedding:
    """ResNetEmbedding 测试"""

    def test_network_creation(self):
        """测试创建网络"""
        net = ResNetEmbedding(embedding_size=128)
        assert net is not None

    def test_forward_pass(self):
        """测试前向传播"""
        net = ResNetEmbedding(embedding_size=128)
        x = torch.randn(2, 3, 160, 160)
        output = net(x)
        assert output.shape == (2, 128)

    def test_output_normalized(self):
        """测试输出是否归一化"""
        net = ResNetEmbedding(embedding_size=128)
        net.eval()
        x = torch.randn(4, 3, 160, 160)
        with torch.no_grad():
            output = net(x)
        norms = torch.norm(output, p=2, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)


class TestFeatureExtractor:
    """FeatureExtractor 测试"""

    def test_extractor_creation_custom(self):
        """测试创建自定义特征提取器"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        assert extractor.embedding_size == 128
        assert extractor.model_type == "custom"

    def test_extractor_creation_resnet(self):
        """测试创建 ResNet 特征提取器"""
        extractor = FeatureExtractor(model_type="resnet", embedding_size=128)
        assert extractor.embedding_size == 128
        assert extractor.model_type == "resnet"

    def test_invalid_model_type(self):
        """测试无效的模型类型"""
        with pytest.raises(ValueError):
            FeatureExtractor(model_type="invalid")

    def test_extract_feature_shape(self):
        """测试特征提取形状"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        feature = extractor.extract(face)
        assert feature.shape == (128,)

    def test_extract_feature_normalized(self):
        """测试特征是否归一化"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        feature = extractor.extract(face)
        norm = np.linalg.norm(feature)
        assert abs(norm - 1.0) < 1e-5

    def test_extract_batch(self):
        """测试批量提取"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        faces = [
            np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
            for _ in range(4)
        ]
        features = extractor.extract_batch(faces)
        assert features.shape == (4, 128)

    def test_same_input_same_output(self):
        """测试相同输入产生相同输出"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        extractor.model.eval()

        face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        feature1 = extractor.extract(face)
        feature2 = extractor.extract(face)
        assert np.allclose(feature1, feature2, atol=1e-5)

    def test_get_embedding_size(self):
        """测试获取嵌入维度"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=256)
        assert extractor.get_embedding_size() == 256

    def test_save_load_model(self, tmp_path):
        """测试保存和加载模型"""
        extractor = FeatureExtractor(model_type="custom", embedding_size=128)

        # 保存模型
        save_path = str(tmp_path / "model.pth")
        extractor.save_model(save_path)
        assert os.path.exists(save_path)

        # 加载模型
        new_extractor = FeatureExtractor(model_type="custom", embedding_size=128)
        new_extractor.load_model(save_path)

        # 验证两个模型产生相同的输出
        face = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)
        feature1 = extractor.extract(face)
        feature2 = new_extractor.extract(face)
        assert np.allclose(feature1, feature2, atol=1e-5)

    def test_device_selection(self):
        """测试设备选择"""
        # CPU
        extractor_cpu = FeatureExtractor(model_type="custom", device="cpu")
        assert extractor_cpu.device == torch.device("cpu")

        # 自动选择
        extractor_auto = FeatureExtractor(model_type="custom")
        assert extractor_auto.device in [torch.device("cpu"), torch.device("cuda")]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
