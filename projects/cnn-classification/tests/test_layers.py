"""
CNN层测试

测试自定义层的正确性和形状
"""

import pytest
import torch
import sys
sys.path.insert(0, '.')

from src.layers import Conv2D, MaxPool2D, AvgPool2D, Flatten, AdaptiveAvgPool2D


class TestConv2D:
    """测试Conv2D层"""

    def test_conv2d_output_shape(self):
        """测试卷积层输出形状"""
        batch_size = 4
        in_channels = 3
        height, width = 32, 32
        out_channels = 16
        kernel_size = 3

        x = torch.randn(batch_size, in_channels, height, width)
        conv = Conv2D(in_channels, out_channels, kernel_size)

        output = conv(x)

        assert output.shape == (batch_size, out_channels, height - kernel_size + 1, width - kernel_size + 1)

    def test_conv2d_with_padding(self):
        """测试带填充的卷积层"""
        batch_size = 4
        in_channels = 1
        height, width = 28, 28
        out_channels = 6
        kernel_size = 5
        padding = 2

        x = torch.randn(batch_size, in_channels, height, width)
        conv = Conv2D(in_channels, out_channels, kernel_size, padding=padding)

        output = conv(x)

        assert output.shape == (batch_size, out_channels, height, width)

    def test_conv2d_with_stride(self):
        """测试带步长的卷积层"""
        batch_size = 4
        in_channels = 3
        height, width = 32, 32
        out_channels = 16
        kernel_size = 3
        stride = 2

        x = torch.randn(batch_size, in_channels, height, width)
        conv = Conv2D(in_channels, out_channels, kernel_size, stride=stride)

        output = conv(x)

        expected_height = (height - kernel_size) // stride + 1
        expected_width = (width - kernel_size) // stride + 1

        assert output.shape == (batch_size, out_channels, expected_height, expected_width)

    def test_conv2d_gradient(self):
        """测试卷积层梯度计算"""
        in_channels = 3
        out_channels = 16
        kernel_size = 3

        conv = Conv2D(in_channels, out_channels, kernel_size)
        x = torch.randn(2, in_channels, 10, 10, requires_grad=True)

        output = conv(x)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None
        assert conv.weight.grad is not None
        assert conv.bias.grad is not None


class TestMaxPool2D:
    """测试MaxPool2D层"""

    def test_maxpool2d_output_shape(self):
        """测试最大池化层输出形状"""
        batch_size = 4
        channels = 16
        height, width = 32, 32
        kernel_size = 2

        x = torch.randn(batch_size, channels, height, width)
        pool = MaxPool2D(kernel_size)

        output = pool(x)

        assert output.shape == (batch_size, channels, height // kernel_size, width // kernel_size)

    def test_maxpool2d_with_stride(self):
        """测试带步长的最大池化层"""
        batch_size = 4
        channels = 16
        height, width = 32, 32
        kernel_size = 3
        stride = 2

        x = torch.randn(batch_size, channels, height, width)
        pool = MaxPool2D(kernel_size, stride)

        output = pool(x)

        expected_height = (height - kernel_size) // stride + 1
        expected_width = (width - kernel_size) // stride + 1

        assert output.shape == (batch_size, channels, expected_height, expected_width)

    def test_maxpool2d_preserves_max(self):
        """测试最大池化保留最大值"""
        x = torch.tensor([[[[1, 2], [3, 4]]]], dtype=torch.float32)
        pool = MaxPool2D(2)

        output = pool(x)

        assert output.item() == 4.0


class TestAvgPool2D:
    """测试AvgPool2D层"""

    def test_avgpool2d_output_shape(self):
        """测试平均池化层输出形状"""
        batch_size = 4
        channels = 16
        height, width = 32, 32
        kernel_size = 2

        x = torch.randn(batch_size, channels, height, width)
        pool = AvgPool2D(kernel_size)

        output = pool(x)

        assert output.shape == (batch_size, channels, height // kernel_size, width // kernel_size)

    def test_avgpool2d_computes_average(self):
        """测试平均池化计算平均值"""
        x = torch.tensor([[[[1, 2], [3, 4]]]], dtype=torch.float32)
        pool = AvgPool2D(2)

        output = pool(x)

        assert output.item() == 2.5


class TestFlatten:
    """测试Flatten层"""

    def test_flatten_output_shape(self):
        """测试展平层输出形状"""
        batch_size = 4
        channels = 16
        height, width = 5, 5

        x = torch.randn(batch_size, channels, height, width)
        flatten = Flatten()

        output = flatten(x)

        assert output.shape == (batch_size, channels * height * width)

    def test_flatten_preserves_batch(self):
        """测试展平层保持批次大小"""
        batch_size = 8
        x = torch.randn(batch_size, 3, 10, 10)
        flatten = Flatten()

        output = flatten(x)

        assert output.shape[0] == batch_size


class TestAdaptiveAvgPool2D:
    """测试AdaptiveAvgPool2D层"""

    def test_adaptive_avgpool_output_shape(self):
        """测试自适应平均池化层输出形状"""
        batch_size = 4
        channels = 16
        height, width = 13, 13
        output_size = (1, 1)

        x = torch.randn(batch_size, channels, height, width)
        pool = AdaptiveAvgPool2D(output_size)

        output = pool(x)

        assert output.shape == (batch_size, channels, 1, 1)

    def test_adaptive_avgpool_with_different_sizes(self):
        """测试自适应平均池化层处理不同输入大小"""
        pool = AdaptiveAvgPool2D((1, 1))

        x1 = torch.randn(4, 16, 7, 7)
        x2 = torch.randn(4, 16, 13, 13)

        output1 = pool(x1)
        output2 = pool(x2)

        assert output1.shape == (4, 16, 1, 1)
        assert output2.shape == (4, 16, 1, 1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
