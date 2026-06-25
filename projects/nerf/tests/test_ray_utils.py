"""
光线工具测试
============

测试 RayGenerator 和 sample_points_along_rays 模块。
"""

import pytest
import torch
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.ray_utils import RayGenerator, sample_points_along_rays


class TestRayGenerator:
    """光线生成器测试类"""

    def test_initialization(self):
        """测试初始化"""
        gen = RayGenerator(height=100, width=100, focal_length=50.0)

        assert gen.height == 100
        assert gen.width == 100
        assert gen.focal_length == 50.0

    def test_directions_shape(self):
        """测试方向形状"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        assert gen.directions.shape == (64, 64, 3)

    def test_directions_center(self):
        """测试中心像素方向"""
        gen = RayGenerator(height=100, width=100, focal_length=50.0)

        # 中心像素应该指向 -z 方向
        center_dir = gen.directions[50, 50]
        assert center_dir[0].abs() < 0.01  # x 接近 0
        assert center_dir[1].abs() < 0.01  # y 接近 0
        assert center_dir[2] < 0  # z 应该是负的

    def test_get_rays_simple(self):
        """测试简化版光线生成"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        rays_o, rays_d = gen.get_rays_simple()

        assert rays_o.shape == (64, 64, 3)
        assert rays_d.shape == (64, 64, 3)

        # 光线原点应该都是 0
        assert torch.allclose(rays_o, torch.zeros_like(rays_o), atol=1e-6)

    def test_rays_normalized(self):
        """测试光线方向归一化"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        _, rays_d = gen.get_rays_simple()

        # 方向应该是单位向量
        norms = torch.norm(rays_d, dim=-1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_get_rays_with_pose(self):
        """测试带位姿的光线生成"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        # 单位矩阵（相机在原点，看向 -z）
        c2w = torch.eye(4)
        rays_o, rays_d = gen.get_rays(c2w)

        assert rays_o.shape == (64, 64, 3)
        assert rays_d.shape == (64, 64, 3)

    def test_camera_pose_generation(self):
        """测试相机位姿生成"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        c2w = gen.generate_camera_pose(
            azimuth=0.0,
            elevation=0.0,
            radius=4.0,
        )

        assert c2w.shape == (4, 4)

        # 验证是刚体变换（旋转矩阵行列式为 1）
        R = c2w[:3, :3]
        det = torch.det(R)
        assert torch.allclose(det, torch.tensor(1.0), atol=1e-5)

    def test_different_azimuths(self):
        """测试不同方位角"""
        gen = RayGenerator(height=64, width=64, focal_length=50.0)

        poses = []
        for azimuth in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
            c2w = gen.generate_camera_pose(azimuth=azimuth, elevation=0.0)
            poses.append(c2w)

        # 不同方位角应该产生不同的位姿
        for i in range(len(poses)):
            for j in range(i + 1, len(poses)):
                assert not torch.allclose(poses[i], poses[j], atol=1e-3)

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            gen = RayGenerator(height=64, width=64, focal_length=50.0)
            c2w = torch.eye(4).cuda()
            rays_o, rays_d = gen.get_rays(c2w)

            assert rays_o.is_cuda
            assert rays_d.is_cuda


class TestSamplePointsAlongRays:
    """沿光线采样测试"""

    def test_output_shape(self):
        """测试输出形状"""
        num_rays = 10
        num_samples = 64

        rays_o = torch.zeros(num_rays, 3)
        rays_d = torch.tensor([[0, 0, -1]]).expand(num_rays, 3).float()

        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=num_samples
        )

        assert points.shape == (num_rays, num_samples, 3)
        assert distances.shape == (num_rays, num_samples)

    def test_points_on_ray(self):
        """测试点在光线上"""
        rays_o = torch.tensor([[0, 0, 0]]).float()
        rays_d = torch.tensor([[0, 0, -1]]).float()

        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=False
        )

        # 点应该在 z 轴负方向上
        assert torch.allclose(points[0, :, 0], torch.zeros(32), atol=1e-5)
        assert torch.allclose(points[0, :, 1], torch.zeros(32), atol=1e-5)
        assert (points[0, :, 2] < 0).all()  # z 应该是负的

    def test_distance_range(self):
        """测试距离范围"""
        near, far = 2.0, 6.0
        num_samples = 64

        rays_o = torch.zeros(5, 3)
        rays_d = torch.randn(5, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        _, distances = sample_points_along_rays(
            rays_o, rays_d, near=near, far=far, num_samples=num_samples, perturb=False
        )

        # 距离应该在 [near, far] 范围内
        assert (distances >= near - 1e-5).all()
        assert (distances <= far + 1e-5).all()

    def test_perturbation(self):
        """测试扰动"""
        rays_o = torch.zeros(10, 3)
        rays_d = torch.randn(10, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        # 无扰动
        _, dist_no_perturb = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=False
        )

        # 有扰动
        _, dist_perturb = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=True
        )

        # 扰动后距离应该不同
        assert not torch.allclose(dist_no_perturb, dist_perturb, atol=1e-3)

    def test_lindisp(self):
        """测试视差空间采样"""
        rays_o = torch.zeros(5, 3)
        rays_d = torch.randn(5, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        _, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32,
            perturb=False, lindisp=True
        )

        # 距离应该在 [near, far] 范围内
        assert (distances >= 2.0 - 1e-5).all()
        assert (distances <= 6.0 + 1e-5).all()

        # 近处应该更密集
        near_diff = distances[:, 1] - distances[:, 0]
        far_diff = distances[:, -1] - distances[:, -2]
        assert (near_diff < far_diff).all()

    def test_batch_processing(self):
        """测试批量处理"""
        for num_rays in [1, 10, 100]:
            rays_o = torch.randn(num_rays, 3)
            rays_d = torch.randn(num_rays, 3)
            rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

            points, distances = sample_points_along_rays(
                rays_o, rays_d, near=2.0, far=6.0, num_samples=32
            )

            assert points.shape == (num_rays, 32, 3)
            assert distances.shape == (num_rays, 32)

    def test_gradient_flow(self):
        """测试梯度流"""
        rays_o = torch.zeros(5, 3, requires_grad=True)
        rays_d = torch.randn(5, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32
        )

        loss = points.sum()
        loss.backward()

        assert rays_o.grad is not None

    def test_device_compatibility(self):
        """测试设备兼容性"""
        if torch.cuda.is_available():
            rays_o = torch.zeros(5, 3).cuda()
            rays_d = torch.randn(5, 3).cuda()
            rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

            points, distances = sample_points_along_rays(
                rays_o, rays_d, near=2.0, far=6.0, num_samples=32
            )

            assert points.is_cuda
            assert distances.is_cuda


class TestRaySamplingIntegration:
    """光线采样集成测试"""

    def test_with_ray_generator(self):
        """测试与光线生成器的集成"""
        gen = RayGenerator(height=32, width=32, focal_length=50.0)
        rays_o, rays_d = gen.get_rays_simple()

        # 展平
        rays_o = rays_o.reshape(-1, 3)
        rays_d = rays_d.reshape(-1, 3)

        points, distances = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=64
        )

        num_rays = 32 * 32
        assert points.shape == (num_rays, 64, 3)
        assert distances.shape == (num_rays, 64)

    def test_consistency(self):
        """测试一致性"""
        rays_o = torch.zeros(5, 3)
        rays_d = torch.randn(5, 3)
        rays_d = rays_d / torch.norm(rays_d, dim=-1, keepdim=True)

        # 多次采样（无扰动）应该得到相同结果
        points1, dist1 = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=False
        )
        points2, dist2 = sample_points_along_rays(
            rays_o, rays_d, near=2.0, far=6.0, num_samples=32, perturb=False
        )

        assert torch.allclose(points1, points2, atol=1e-6)
        assert torch.allclose(dist1, dist2, atol=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
