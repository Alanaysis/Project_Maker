"""
体渲染测试
==========

测试 VolumeRenderer 模块的功能。
"""

import pytest
import torch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.volume_renderer import VolumeRenderer, VolumeRendererWithEntropy


class TestVolumeRenderer:
    """体渲染测试类"""

    def test_output_shape(self):
        """测试输出形状"""
        renderer = VolumeRenderer(white_background=True)

        num_rays = 10
        num_samples = 64

        colors = torch.randn(num_rays, num_samples, 3)
        densities = torch.randn(num_rays, num_samples, 1).abs()
        distances = torch.linspace(2.0, 6.0, num_samples).expand(num_rays, num_samples)

        pixel_colors, depth_map, extras = renderer(colors, densities, distances)

        assert pixel_colors.shape == (num_rays, 3)
        assert depth_map.shape == (num_rays, 1)

    def test_transparency(self):
        """测试透明区域使用背景颜色"""
        renderer = VolumeRenderer(white_background=True)

        # 零密度 = 完全透明
        colors = torch.randn(10, 32, 3)
        densities = torch.zeros(10, 32, 1)
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, _, _ = renderer(colors, densities, distances)

        # 应该接近白色背景
        assert torch.allclose(pixel_colors, torch.ones_like(pixel_colors), atol=1e-5)

    def test_opaque_object(self):
        """测试不透明物体"""
        renderer = VolumeRenderer(white_background=True)

        # 高密度 = 不透明
        colors = torch.ones(10, 32, 3) * 0.5  # 灰色
        densities = torch.ones(10, 32, 1) * 100.0  # 非常高密度
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, _, _ = renderer(colors, densities, distances)

        # 应该接近第一个采样点的颜色（因为密度很高）
        # 但由于累积效应，会接近第一个点的颜色
        assert pixel_colors.shape == (10, 3)

    def test_accumulation(self):
        """测试累积不透明度"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 32, 3)
        densities = torch.randn(10, 32, 1).abs() * 0.1
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        _, _, extras = renderer(colors, densities, distances)

        # 累积不透明度应该在 [0, 1] 之间
        acc = extras["accumulation"]
        assert (acc >= 0).all()
        assert (acc <= 1).all()

    def test_transmittance(self):
        """测试透射率"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 32, 3)
        densities = torch.randn(10, 32, 1).abs()
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        _, _, extras = renderer(colors, densities, distances)

        # 透射率应该在 [0, 1] 之间
        trans = extras["transmittance"]
        assert (trans >= 0).all()
        assert (trans <= 1).all()

        # 第一个点的透射率应该是 1
        assert torch.allclose(trans[:, 0], torch.ones(10), atol=1e-5)

    def test_weights(self):
        """测试权重"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 32, 3)
        densities = torch.randn(10, 32, 1).abs()
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        _, _, extras = renderer(colors, densities, distances)

        # 权重应该在 [0, 1] 之间
        weights = extras["weights"]
        assert (weights >= 0).all()
        assert (weights <= 1).all()

    def test_black_background(self):
        """测试黑色背景"""
        renderer = VolumeRenderer(white_background=False)

        # 零密度
        colors = torch.randn(10, 32, 3)
        densities = torch.zeros(10, 32, 1)
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, _, _ = renderer(colors, densities, distances)

        # 应该接近黑色
        assert torch.allclose(pixel_colors, torch.zeros_like(pixel_colors), atol=1e-5)

    def test_custom_background(self):
        """测试自定义背景颜色"""
        bg = torch.tensor([0.0, 0.0, 1.0])  # 蓝色背景
        renderer = VolumeRenderer(background_color=bg)

        # 零密度
        colors = torch.randn(10, 32, 3)
        densities = torch.zeros(10, 32, 1)
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, _, _ = renderer(colors, densities, distances)

        # 应该接近蓝色背景
        expected = bg.expand_as(pixel_colors)
        assert torch.allclose(pixel_colors, expected, atol=1e-5)

    def test_gradient_flow(self):
        """测试梯度流"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 32, 3, requires_grad=True)
        densities_raw = torch.randn(10, 32, 1, requires_grad=True)
        densities = densities_raw.abs()
        densities.retain_grad()  # 保留非叶子张量的梯度
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, depth_map, _ = renderer(colors, densities, distances)
        loss = pixel_colors.sum() + depth_map.sum()
        loss.backward()

        assert colors.grad is not None
        assert densities_raw.grad is not None

    def test_single_sample(self):
        """测试单个采样点"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 1, 3)
        densities = torch.randn(10, 1, 1).abs()
        distances = torch.tensor([[3.0]]).expand(10, 1)

        pixel_colors, depth_map, _ = renderer(colors, densities, distances)

        assert pixel_colors.shape == (10, 3)
        assert depth_map.shape == (10, 1)

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            renderer = VolumeRenderer(white_background=True).cuda()

            colors = torch.randn(10, 32, 3).cuda()
            densities = torch.randn(10, 32, 1).abs().cuda()
            distances = torch.linspace(2.0, 6.0, 32).expand(10, 32).cuda()

            pixel_colors, depth_map, _ = renderer(colors, densities, distances)

            assert pixel_colors.is_cuda
            assert depth_map.is_cuda


class TestVolumeRendererWithEntropy:
    """带熵正则化的体渲染测试"""

    def test_output_shape(self):
        """测试输出形状"""
        renderer = VolumeRendererWithEntropy(white_background=True)

        colors = torch.randn(10, 32, 3)
        densities = torch.randn(10, 32, 1).abs()
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, depth_map, extras = renderer(colors, densities, distances)

        assert pixel_colors.shape == (10, 3)
        assert depth_map.shape == (10, 1)
        assert "entropy_loss" in extras

    def test_entropy_loss_calculation(self):
        """测试熵损失计算"""
        renderer = VolumeRendererWithEntropy(
            white_background=True,
            entropy_weight=1e-3,
        )

        colors = torch.randn(10, 32, 3)
        densities = torch.randn(10, 32, 1).abs()
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        _, _, extras = renderer(colors, densities, distances)

        entropy_loss = extras["entropy_loss"]
        assert entropy_loss.dim() == 0  # 标量
        assert entropy_loss >= 0


class TestVolumeRenderingPhysics:
    """体渲染物理原理测试"""

    def test_energy_conservation(self):
        """测试能量守恒"""
        renderer = VolumeRenderer(white_background=False)  # 黑色背景

        # 模拟一条光线穿过均匀介质
        num_samples = 100
        colors = torch.ones(1, num_samples, 3) * 0.5
        densities = torch.ones(1, num_samples, 1) * 0.1
        distances = torch.linspace(0.0, 10.0, num_samples).expand(1, num_samples)

        pixel_colors, _, extras = renderer(colors, densities, distances)

        # 累积不透明度应该小于等于 1
        acc = extras["accumulation"]
        assert acc <= 1.0 + 1e-5

    def test_order_invariance(self):
        """测试顺序不变性（对于均匀介质）"""
        renderer = VolumeRenderer(white_background=False)

        # 均匀介质
        colors = torch.ones(1, 32, 3) * 0.5
        densities = torch.ones(1, 32, 1) * 0.1

        # 正向和反向距离应该产生相同结果
        distances_forward = torch.linspace(2.0, 6.0, 32).expand(1, 32)
        distances_backward = torch.linspace(6.0, 2.0, 32).expand(1, 32)

        # 注意：由于渲染公式，正向和反向应该产生相同结果
        # 因为颜色和密度都相同
        colors_forward, _, _ = renderer(colors, densities, distances_forward)
        colors_backward, _, _ = renderer(colors, densities, distances_backward)

        assert torch.allclose(colors_forward, colors_backward, atol=1e-5)

    def test_front_blocking(self):
        """测试前方物体阻挡后方"""
        renderer = VolumeRenderer(white_background=False)

        num_samples = 32
        # 前半部分高密度，后半部分不同颜色
        densities = torch.zeros(1, num_samples, 1)
        densities[0, :16, 0] = 100.0  # 前面很高密度

        colors = torch.zeros(1, num_samples, 3)
        colors[0, :16, 0] = 1.0   # 前面红色
        colors[0, 16:, 1] = 1.0   # 后面绿色

        distances = torch.linspace(2.0, 6.0, num_samples).expand(1, num_samples)

        pixel_colors, _, _ = renderer(colors, densities, distances)

        # 应该主要显示红色（前面阻挡）
        assert pixel_colors[0, 0] > pixel_colors[0, 1]  # R > G

    def test_empty_scene(self):
        """测试空场景"""
        renderer = VolumeRenderer(white_background=True)

        colors = torch.randn(10, 32, 3)
        densities = torch.zeros(10, 32, 1)
        distances = torch.linspace(2.0, 6.0, 32).expand(10, 32)

        pixel_colors, depth_map, _ = renderer(colors, densities, distances)

        # 应该显示白色背景
        assert torch.allclose(pixel_colors, torch.ones_like(pixel_colors), atol=1e-5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
