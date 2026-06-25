"""
超分辨率模型测试

测试 SRCNN、ESPCN 和 EDSR 模型的实现
"""

import pytest
import torch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SRCNN, ESPCN, EDSR, PixelShuffle, get_model


class TestSRCNN:
    """SRCNN 模型测试"""

    def test_init(self):
        """测试模型初始化"""
        model = SRCNN(num_channels=3, num_features=64, hidden_features=32)
        assert model is not None

    def test_forward(self):
        """测试前向传播"""
        model = SRCNN(num_channels=3, num_features=64, hidden_features=32)

        # 创建输入张量（batch_size=2, channels=3, height=64, width=64）
        x = torch.randn(2, 3, 64, 64)

        # 前向传播
        output = model(x)

        # 检查输出形状
        assert output.shape == (2, 3, 64, 64)

    def test_output_range(self):
        """测试输出范围"""
        model = SRCNN(num_channels=3, num_features=64, hidden_features=32)
        model.eval()

        # 创建输入张量
        x = torch.randn(1, 3, 32, 32)

        # 前向传播
        with torch.no_grad():
            output = model(x)

        # 检查输出是有限的
        assert torch.isfinite(output).all()

    def test_different_channels(self):
        """测试不同通道数"""
        # 灰度图像
        model_gray = SRCNN(num_channels=1)
        x_gray = torch.randn(1, 1, 32, 32)
        output_gray = model_gray(x_gray)
        assert output_gray.shape == (1, 1, 32, 32)

        # RGB 图像
        model_rgb = SRCNN(num_channels=3)
        x_rgb = torch.randn(1, 3, 32, 32)
        output_rgb = model_rgb(x_rgb)
        assert output_rgb.shape == (1, 3, 32, 32)

    def test_different_sizes(self):
        """测试不同输入尺寸"""
        model = SRCNN()

        # 小尺寸
        x_small = torch.randn(1, 3, 16, 16)
        output_small = model(x_small)
        assert output_small.shape == (1, 3, 16, 16)

        # 大尺寸
        x_large = torch.randn(1, 3, 128, 128)
        output_large = model(x_large)
        assert output_large.shape == (1, 3, 128, 128)

    def test_gradient_flow(self):
        """测试梯度流动"""
        model = SRCNN()
        x = torch.randn(1, 3, 32, 32, requires_grad=True)

        output = model(x)
        loss = output.mean()
        loss.backward()

        # 检查输入有梯度
        assert x.grad is not None

        # 检查模型参数有梯度
        for param in model.parameters():
            assert param.grad is not None


class TestESPCN:
    """ESPCN 模型测试"""

    def test_init(self):
        """测试模型初始化"""
        model = ESPCN(scale_factor=2, num_channels=3, num_features=64)
        assert model is not None

    def test_forward(self):
        """测试前向传播"""
        model = ESPCN(scale_factor=2, num_channels=3, num_features=64)

        # 创建输入张量
        x = torch.randn(2, 3, 32, 32)

        # 前向传播
        output = model(x)

        # 检查输出形状（上采样 2 倍）
        assert output.shape == (2, 3, 64, 64)

    def test_scale_factor_3(self):
        """测试 3 倍上采样"""
        model = ESPCN(scale_factor=3, num_channels=3, num_features=64)

        x = torch.randn(1, 3, 16, 16)
        output = model(x)

        assert output.shape == (1, 3, 48, 48)

    def test_scale_factor_4(self):
        """测试 4 倍上采样"""
        model = ESPCN(scale_factor=4, num_channels=3, num_features=64)

        x = torch.randn(1, 3, 16, 16)
        output = model(x)

        assert output.shape == (1, 3, 64, 64)

    def test_output_range(self):
        """测试输出范围"""
        model = ESPCN(scale_factor=2, num_channels=3, num_features=64)
        model.eval()

        x = torch.randn(1, 3, 16, 16)

        with torch.no_grad():
            output = model(x)

        assert torch.isfinite(output).all()

    def test_gradient_flow(self):
        """测试梯度流动"""
        model = ESPCN(scale_factor=2)
        x = torch.randn(1, 3, 16, 16, requires_grad=True)

        output = model(x)
        loss = output.mean()
        loss.backward()

        assert x.grad is not None

        for param in model.parameters():
            assert param.grad is not None


class TestPixelShuffle:
    """PixelShuffle 测试"""

    def test_init(self):
        """测试初始化"""
        ps = PixelShuffle(scale_factor=2)
        assert ps.scale_factor == 2

    def test_forward(self):
        """测试前向传播"""
        ps = PixelShuffle(scale_factor=2)

        # 输入：[B, C*r^2, H, W] = [1, 12, 4, 4]
        x = torch.randn(1, 12, 4, 4)

        # 输出：[B, C, H*r, W*r] = [1, 3, 8, 8]
        output = ps(x)

        assert output.shape == (1, 3, 8, 8)

    def test_scale_factor_3(self):
        """测试 3 倍上采样"""
        ps = PixelShuffle(scale_factor=3)

        # 输入：[B, C*r^2, H, W] = [1, 27, 4, 4]
        x = torch.randn(1, 27, 4, 4)

        # 输出：[B, C, H*r, W*r] = [1, 3, 12, 12]
        output = ps(x)

        assert output.shape == (1, 3, 12, 12)


class TestEDSR:
    """EDSR 模型测试"""

    def test_init(self):
        """测试模型初始化"""
        model = EDSR(scale_factor=2, num_channels=3, num_features=64, num_blocks=16)
        assert model is not None

    def test_forward(self):
        """测试前向传播"""
        model = EDSR(scale_factor=2, num_channels=3, num_features=64, num_blocks=4)

        x = torch.randn(1, 3, 16, 16)
        output = model(x)

        assert output.shape == (1, 3, 32, 32)

    def test_different_blocks(self):
        """测试不同残差块数量"""
        # 少量块
        model_small = EDSR(scale_factor=2, num_blocks=2)
        x = torch.randn(1, 3, 16, 16)
        output_small = model_small(x)
        assert output_small.shape == (1, 3, 32, 32)

        # 多量块
        model_large = EDSR(scale_factor=2, num_blocks=8)
        output_large = model_large(x)
        assert output_large.shape == (1, 3, 32, 32)


class TestGetModel:
    """get_model 函数测试"""

    def test_srcnn(self):
        """测试获取 SRCNN 模型"""
        model = get_model('srcnn')
        assert isinstance(model, SRCNN)

    def test_espcn(self):
        """测试获取 ESPCN 模型"""
        model = get_model('espcn', scale_factor=2)
        assert isinstance(model, ESPCN)

    def test_edsr(self):
        """测试获取 EDSR 模型"""
        model = get_model('edsr', scale_factor=2)
        assert isinstance(model, EDSR)

    def test_invalid_model(self):
        """测试无效模型名称"""
        with pytest.raises(ValueError):
            get_model('invalid_model')

    def test_model_parameters(self):
        """测试模型参数传递"""
        model = get_model('srcnn', num_channels=1, num_features=32, hidden_features=16)

        # 检查参数是否正确传递
        assert model.feature_extraction[0].in_channels == 1
        assert model.feature_extraction[0].out_channels == 32


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
