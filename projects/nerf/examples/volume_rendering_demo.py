"""
体渲染演示
==========

演示体渲染的原理:
1. 采样点的颜色和密度
2. 计算 alpha 不透明度
3. 计算累积透射率
4. 合成最终颜色

运行方式:
    python examples/volume_rendering_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import numpy as np

from src import VolumeRenderer, sample_points_along_rays


def main():
    print("=" * 60)
    print("体渲染演示")
    print("=" * 60)

    # ===== 1. 创建渲染器 =====
    print("\n1. 创建体渲染器")
    print("-" * 40)

    renderer = VolumeRenderer(white_background=True)

    print("渲染器参数:")
    print("  背景颜色: 白色 (1, 1, 1)")
    print("  渲染公式: C = Σ T_i * α_i * c_i")

    # ===== 2. 模拟单条光线 =====
    print("\n2. 模拟单条光线渲染")
    print("-" * 40)

    # 光线参数
    rays_o = torch.tensor([[0.0, 0.0, 0.0]])  # 原点
    rays_d = torch.tensor([[0.0, 0.0, -1.0]])  # 看向 -z

    # 采样点
    num_samples = 32
    points, distances = sample_points_along_rays(
        rays_o, rays_d, near=2.0, far=6.0, num_samples=num_samples, perturb=False
    )

    print(f"采样点数: {num_samples}")
    print(f"采样范围: [2.0, 6.0]")
    print(f"采样点形状: {points.shape}")

    # ===== 3. 场景 1: 空场景 =====
    print("\n3. 场景 1: 空场景（零密度）")
    print("-" * 40)

    colors_empty = torch.randn(1, num_samples, 3)
    densities_empty = torch.zeros(1, num_samples, 1)

    pixel_colors, depth_map, extras = renderer(
        colors_empty, densities_empty, distances, rays_d
    )

    print(f"渲染颜色: {pixel_colors[0]}")
    print(f"累积不透明度: {extras['accumulation'][0].item():.4f}")
    print("-> 应该接近白色背景")

    # ===== 4. 场景 2: 不透明物体 =====
    print("\n4. 场景 2: 不透明物体（高密度）")
    print("-" * 40)

    # 前半部分红色，后半部分绿色
    colors_opaque = torch.zeros(1, num_samples, 3)
    colors_opaque[0, :16, 0] = 1.0  # 红色
    colors_opaque[0, 16:, 1] = 1.0  # 绿色

    # 高密度
    densities_opaque = torch.ones(1, num_samples, 1) * 10.0

    pixel_colors, depth_map, extras = renderer(
        colors_opaque, densities_opaque, distances, rays_d
    )

    print(f"渲染颜色: {pixel_colors[0]}")
    print(f"累积不透明度: {extras['accumulation'][0].item():.4f}")
    print("-> 应该主要显示红色（前面阻挡）")

    # ===== 5. 场景 3: 半透明物体 =====
    print("\n5. 场景 3: 半透明物体（低密度）")
    print("-" * 40)

    # 蓝色半透明
    colors_semi = torch.zeros(1, num_samples, 3)
    colors_semi[0, :, 2] = 1.0  # 蓝色

    # 低密度
    densities_semi = torch.ones(1, num_samples, 1) * 0.5

    pixel_colors, depth_map, extras = renderer(
        colors_semi, densities_semi, distances, rays_d
    )

    print(f"渲染颜色: {pixel_colors[0]}")
    print(f"累积不透明度: {extras['accumulation'][0].item():.4f}")
    print("-> 应该是蓝色和白色的混合")

    # ===== 6. 展示渲染过程 =====
    print("\n6. 展示渲染过程（单条光线）")
    print("-" * 40)

    # 简单场景：3个采样点
    num_samples_simple = 3
    points_simple = torch.tensor([[[0, 0, -2], [0, 0, -3], [0, 0, -4]]]).float()
    distances_simple = torch.tensor([[2.0, 3.0, 4.0]])

    colors_simple = torch.tensor([[[1.0, 0.0, 0.0],   # 红色
                                   [0.0, 1.0, 0.0],   # 绿色
                                   [0.0, 0.0, 1.0]]])  # 蓝色

    densities_simple = torch.tensor([[[2.0],   # 高密度
                                      [1.0],   # 中密度
                                      [0.5]]])  # 低密度

    pixel_colors, depth_map, extras = renderer(
        colors_simple, densities_simple, distances_simple
    )

    print("采样点:")
    print("  点1: 红色, 密度=2.0")
    print("  点2: 绿色, 密度=1.0")
    print("  点3: 蓝色, 密度=0.5")

    print(f"\nAlpha 不透明度: {extras['alpha'][0].numpy()}")
    print(f"透射率: {extras['transmittance'][0].numpy()}")
    print(f"权重: {extras['weights'][0].numpy()}")
    print(f"最终颜色: {pixel_colors[0].numpy()}")

    # ===== 7. 渲染公式解释 =====
    print("\n7. 渲染公式解释")
    print("-" * 40)

    print("""
    体渲染公式:
    C(r) = Σ T_i * α_i * c_i

    其中:
    - T_i = exp(-Σ_{j<i} σ_j * δ_j)  累积透射率
    - α_i = 1 - exp(-σ_i * δ_i)       alpha 不透明度
    - σ_i                              体积密度
    - δ_i                              采样点间距
    - c_i                              采样点颜色

    直觉理解:
    - T_i: 光线到达第 i 个点的概率
    - α_i: 光线在第 i 个点被阻挡的概率
    - T_i * α_i: 第 i 个点对最终颜色的贡献权重
    """)

    # ===== 8. 背景颜色的影响 =====
    print("8. 背景颜色的影响")
    print("-" * 40)

    # 零密度场景
    densities_zero = torch.zeros(1, num_samples, 1)
    colors_random = torch.randn(1, num_samples, 3)

    # 白色背景
    renderer_white = VolumeRenderer(white_background=True)
    white_result, _, _ = renderer_white(colors_random, densities_zero, distances, rays_d)

    # 黑色背景
    renderer_black = VolumeRenderer(white_background=False)
    black_result, _, _ = renderer_black(colors_random, densities_zero, distances, rays_d)

    # 自定义背景
    bg = torch.tensor([0.5, 0.5, 0.5])  # 灰色
    renderer_custom = VolumeRenderer(background_color=bg)
    custom_result, _, _ = renderer_custom(colors_random, densities_zero, distances, rays_d)

    print(f"白色背景: {white_result[0].numpy()}")
    print(f"黑色背景: {black_result[0].numpy()}")
    print(f"灰色背景: {custom_result[0].numpy()}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
