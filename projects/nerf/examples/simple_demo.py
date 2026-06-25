"""
简单 NeRF 演示
===============

演示 NeRF 的基本用法:
1. 创建简单场景
2. 生成训练数据
3. 训练 NeRF 模型
4. 渲染新视角

运行方式:
    python examples/simple_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
import numpy as np

from src import (
    PositionalEncoding,
    NeRFModel,
    VolumeRenderer,
    RayGenerator,
    sample_points_along_rays,
    SphereScene,
    NeRFTrainer,
)


def main():
    print("=" * 60)
    print("NeRF 简单演示")
    print("=" * 60)

    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ===== 1. 创建场景 =====
    print("\n1. 创建简单球体场景...")
    scene = SphereScene(
        radius=1.0,
        color=(1.0, 0.0, 0.0),  # 红色球
        density=10.0,
    )

    # ===== 2. 生成训练数据 =====
    print("2. 生成训练数据...")

    height, width = 64, 64
    focal_length = 32.0
    near, far = 2.0, 6.0

    generator = RayGenerator(height, width, focal_length, near, far)

    # 生成多个视角
    num_views = 50
    all_rays_o = []
    all_rays_d = []
    all_colors = []

    for i in range(num_views):
        # 均匀分布的视角
        azimuth = 2 * np.pi * i / num_views
        elevation = np.pi / 6  # 30度仰角

        # 生成相机位姿
        c2w = generator.generate_camera_pose(azimuth, elevation, radius=4.0)

        # 生成光线
        rays_o, rays_d = generator.get_rays(c2w)

        # 展平
        rays_o_flat = rays_o.reshape(-1, 3)
        rays_d_flat = rays_d.reshape(-1, 3)

        # 渲染 ground truth
        colors, _ = scene.render_rays(rays_o_flat, rays_d_flat, near, far, 64)

        all_rays_o.append(rays_o_flat)
        all_rays_d.append(rays_d_flat)
        all_colors.append(colors)

    # 合并数据
    train_rays_o = torch.cat(all_rays_o, dim=0)
    train_rays_d = torch.cat(all_rays_d, dim=0)
    train_colors = torch.cat(all_colors, dim=0)

    print(f"   训练光线数: {train_rays_o.shape[0]}")

    # ===== 3. 创建模型 =====
    print("3. 创建 NeRF 模型...")

    pos_encoding = PositionalEncoding(input_dim=3, num_freqs=10)
    dir_encoding = PositionalEncoding(input_dim=3, num_freqs=6)

    model = NeRFModel(
        pos_encoding_dim=pos_encoding.output_dim,
        dir_encoding_dim=dir_encoding.output_dim,
        hidden_dim=128,
        num_layers=6,
    )

    renderer = VolumeRenderer(white_background=True)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"   模型参数量: {total_params:,}")

    # ===== 4. 训练 =====
    print("4. 开始训练...")

    trainer = NeRFTrainer(
        model=model,
        pos_encoding=pos_encoding,
        dir_encoding=dir_encoding,
        renderer=renderer,
        learning_rate=5e-4,
        device=device,
        near=near,
        far=far,
        num_samples=64,
    )

    # 简化训练（只训练几个 epoch）
    trainer.train(
        train_rays_o=train_rays_o,
        train_rays_d=train_rays_d,
        train_colors=train_colors,
        num_epochs=5,
        batch_size=1024,
        log_interval=1,
    )

    # ===== 5. 渲染新视角 =====
    print("\n5. 渲染新视角...")

    # 生成新视角
    c2w_new = generator.generate_camera_pose(
        azimuth=np.pi / 4,  # 45度
        elevation=np.pi / 4,
        radius=4.0,
    )

    rays_o_new, rays_d_new = generator.get_rays(c2w_new)
    rays_o_new = rays_o_new.reshape(-1, 3)
    rays_d_new = rays_d_new.reshape(-1, 3)

    # 渲染
    rendered = trainer.render_image(rays_o_new, rays_d_new, chunk_size=1024)
    rendered_image = rendered.reshape(height, width, 3)

    print(f"   渲染图像形状: {rendered_image.shape}")
    print(f"   像素值范围: [{rendered_image.min():.3f}, {rendered_image.max():.3f}]")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
