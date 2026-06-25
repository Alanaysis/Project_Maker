"""
NeRF 训练器 (Trainer)
=====================

将所有组件组合在一起，实现 NeRF 的训练流程。

训练流程:
1. 从数据集中采样光线批次
2. 沿光线采样3D点
3. 位置编码
4. MLP 预测颜色和密度
5. 体渲染得到像素颜色
6. 计算损失（MSE）
7. 反向传播和优化

训练技巧:
- 学习率调度：初始 lr 较大，逐渐衰减
- 批量大小：每批采样若干条光线
- 梯度裁剪：防止梯度爆炸
- 分层采样：先粗采样，再细采样
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Optional, Dict
import time

from .nerf_model import NeRFModel, TinyNeRF
from .positional_encoding import PositionalEncoding
from .volume_renderer import VolumeRenderer
from .ray_utils import sample_points_along_rays


class NeRFTrainer:
    """
    NeRF 训练器

    参数:
        model: NeRF 模型
        pos_encoding: 位置编码器
        dir_encoding: 方向编码器
        renderer: 体渲染器
        learning_rate: 学习率
        device: 计算设备
        near: 近裁剪面
        far: 远裁剪面
        num_samples: 每条光线的采样点数
    """

    def __init__(
        self,
        model: nn.Module,
        pos_encoding: PositionalEncoding,
        dir_encoding: PositionalEncoding,
        renderer: VolumeRenderer,
        learning_rate: float = 5e-4,
        device: str = "cpu",
        near: float = 2.0,
        far: float = 6.0,
        num_samples: int = 64,
    ):
        self.model = model.to(device)
        self.pos_encoding = pos_encoding.to(device)
        self.dir_encoding = dir_encoding.to(device)
        self.renderer = renderer.to(device)
        self.device = device
        self.near = near
        self.far = far
        self.num_samples = num_samples

        # 优化器
        self.optimizer = optim.Adam(
            list(model.parameters())
            + list(pos_encoding.parameters())
            + list(dir_encoding.parameters()),
            lr=learning_rate,
        )

        # 学习率调度器
        self.scheduler = optim.lr_scheduler.ExponentialLR(
            self.optimizer, gamma=0.1 ** (1.0 / 200000)
        )

        # 损失函数
        self.criterion = nn.MSELoss()

        # 训练历史
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "learning_rate": [],
        }

    def train_step(
        self,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor,
        target_colors: torch.Tensor,
    ) -> Dict[str, float]:
        """
        单步训练

        参数:
            rays_o: 光线原点 (num_rays, 3)
            rays_d: 光线方向 (num_rays, 3)
            target_colors: 目标颜色 (num_rays, 3)

        返回:
            metrics: 训练指标
        """
        self.model.train()
        self.pos_encoding.train()
        self.dir_encoding.train()

        # 移动到设备
        rays_o = rays_o.to(self.device)
        rays_d = rays_d.to(self.device)
        target_colors = target_colors.to(self.device)

        # 1. 沿光线采样点
        points, distances = sample_points_along_rays(
            rays_o, rays_d, self.near, self.far, self.num_samples, perturb=True
        )
        # points: (num_rays, num_samples, 3)
        # distances: (num_rays, num_samples)

        # 2. 位置编码
        # 展平处理
        num_rays, num_samples, _ = points.shape
        points_flat = points.reshape(-1, 3)
        directions_flat = rays_d.unsqueeze(1).expand(-1, num_samples, -1).reshape(-1, 3)

        pos_encoded = self.pos_encoding(points_flat)
        dir_encoded = self.dir_encoding(directions_flat)

        # 3. MLP 预测
        densities, colors = self.model(pos_encoded, dir_encoded)

        # 4. 重塑回原来的形状
        densities = densities.reshape(num_rays, num_samples, 1)
        colors = colors.reshape(num_rays, num_samples, 3)

        # 5. 体渲染
        pixel_colors, depth_map, extras = self.renderer(
            colors, densities, distances, rays_d
        )

        # 6. 计算损失
        loss = self.criterion(pixel_colors, target_colors)

        # 7. 反向传播
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        self.optimizer.step()
        self.scheduler.step()

        return {
            "loss": loss.item(),
            "psnr": -10.0 * torch.log10(loss).item(),
        }

    @torch.no_grad()
    def validate(
        self,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor,
        target_colors: torch.Tensor,
    ) -> Dict[str, float]:
        """
        验证

        参数:
            rays_o: 光线原点 (num_rays, 3)
            rays_d: 光线方向 (num_rays, 3)
            target_colors: 目标颜色 (num_rays, 3)

        返回:
            metrics: 验证指标
        """
        self.model.eval()
        self.pos_encoding.eval()
        self.dir_encoding.eval()

        rays_o = rays_o.to(self.device)
        rays_d = rays_d.to(self.device)
        target_colors = target_colors.to(self.device)

        # 采样（不加扰动）
        points, distances = sample_points_along_rays(
            rays_o, rays_d, self.near, self.far, self.num_samples, perturb=False
        )

        num_rays, num_samples, _ = points.shape
        points_flat = points.reshape(-1, 3)
        directions_flat = rays_d.unsqueeze(1).expand(-1, num_samples, -1).reshape(-1, 3)

        pos_encoded = self.pos_encoding(points_flat)
        dir_encoded = self.dir_encoding(directions_flat)

        densities, colors = self.model(pos_encoded, dir_encoded)

        densities = densities.reshape(num_rays, num_samples, 1)
        colors = colors.reshape(num_rays, num_samples, 3)

        pixel_colors, _, _ = self.renderer(colors, densities, distances, rays_d)

        loss = self.criterion(pixel_colors, target_colors)

        return {
            "loss": loss.item(),
            "psnr": -10.0 * torch.log10(loss).item(),
        }

    def render_image(
        self,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor,
        chunk_size: int = 1024,
    ) -> torch.Tensor:
        """
        渲染完整图像

        分块处理以节省内存。

        参数:
            rays_o: 光线原点 (height * width, 3)
            rays_d: 光线方向 (height * width, 3)
            chunk_size: 每次处理的光线数

        返回:
            image: 渲染的图像 (height, width, 3)
        """
        self.model.eval()
        self.pos_encoding.eval()
        self.dir_encoding.eval()

        rays_o = rays_o.to(self.device)
        rays_d = rays_d.to(self.device)

        all_colors = []

        # 分块处理
        for i in range(0, rays_o.shape[0], chunk_size):
            rays_o_chunk = rays_o[i:i + chunk_size]
            rays_d_chunk = rays_d[i:i + chunk_size]

            # 采样
            points, distances = sample_points_along_rays(
                rays_o_chunk, rays_d_chunk, self.near, self.far,
                self.num_samples, perturb=False
            )

            num_rays, num_samples, _ = points.shape
            points_flat = points.reshape(-1, 3)
            directions_flat = (
                rays_d_chunk.unsqueeze(1)
                .expand(-1, num_samples, -1)
                .reshape(-1, 3)
            )

            pos_encoded = self.pos_encoding(points_flat)
            dir_encoded = self.dir_encoding(directions_flat)

            densities, colors = self.model(pos_encoded, dir_encoded)

            densities = densities.reshape(num_rays, num_samples, 1)
            colors = colors.reshape(num_rays, num_samples, 3)

            pixel_colors, _, _ = self.renderer(colors, densities, distances, rays_d_chunk)

            all_colors.append(pixel_colors.cpu())

        return torch.cat(all_colors, dim=0)

    def train(
        self,
        train_rays_o: torch.Tensor,
        train_rays_d: torch.Tensor,
        train_colors: torch.Tensor,
        num_epochs: int = 100,
        batch_size: int = 1024,
        val_rays_o: Optional[torch.Tensor] = None,
        val_rays_d: Optional[torch.Tensor] = None,
        val_colors: Optional[torch.Tensor] = None,
        log_interval: int = 10,
    ):
        """
        完整训练流程

        参数:
            train_rays_o: 训练光线原点 (num_rays, 3)
            train_rays_d: 训练光线方向 (num_rays, 3)
            train_colors: 训练目标颜色 (num_rays, 3)
            num_epochs: 训练轮数
            batch_size: 批量大小
            val_rays_o: 验证光线原点
            val_rays_d: 验证光线方向
            val_colors: 验证目标颜色
            log_interval: 日志打印间隔
        """
        num_rays = train_rays_o.shape[0]

        print(f"开始训练 NeRF...")
        print(f"  训练光线数: {num_rays}")
        print(f"  批量大小: {batch_size}")
        print(f"  训练轮数: {num_epochs}")
        print(f"  设备: {self.device}")
        print()

        for epoch in range(num_epochs):
            epoch_start = time.time()
            epoch_loss = 0.0
            num_batches = 0

            # 随机打乱
            perm = torch.randperm(num_rays)

            for i in range(0, num_rays, batch_size):
                # 获取批次
                indices = perm[i:i + batch_size]
                rays_o = train_rays_o[indices]
                rays_d = train_rays_d[indices]
                target = train_colors[indices]

                # 训练
                metrics = self.train_step(rays_o, rays_d, target)
                epoch_loss += metrics["loss"]
                num_batches += 1

            # 记录历史
            avg_loss = epoch_loss / num_batches
            self.history["train_loss"].append(avg_loss)
            self.history["learning_rate"].append(
                self.optimizer.param_groups[0]["lr"]
            )

            # 验证
            val_metrics = None
            if val_rays_o is not None:
                val_metrics = self.validate(val_rays_o, val_rays_d, val_colors)
                self.history["val_loss"].append(val_metrics["loss"])

            # 日志
            if (epoch + 1) % log_interval == 0:
                elapsed = time.time() - epoch_start
                lr = self.optimizer.param_groups[0]["lr"]
                msg = (
                    f"Epoch {epoch + 1:4d}/{num_epochs} | "
                    f"Loss: {avg_loss:.6f} | "
                    f"PSNR: {-10.0 * torch.log10(torch.tensor(avg_loss)):.2f} | "
                    f"LR: {lr:.2e} | "
                    f"Time: {elapsed:.1f}s"
                )
                if val_metrics:
                    msg += f" | Val Loss: {val_metrics['loss']:.6f}"
                print(msg)

        print("训练完成!")
