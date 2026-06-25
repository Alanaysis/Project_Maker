"""
简单 GAN 示例
=============

展示 GAN 的基本用法，不依赖真实数据集。

运行方式:
    python examples/simple_example.py

输出:
    - 训练过程日志
    - 生成的随机图像
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import GAN


def create_simple_dataset(n_samples: int = 1000, img_size: int = 28) -> DataLoader:
    """
    创建简单数据集

    生成简单的几何图形（圆形、矩形等）

    参数:
        n_samples: 样本数量
        img_size: 图像尺寸

    返回:
        数据加载器
    """
    images = []

    for _ in range(n_samples):
        img = np.zeros((img_size, img_size), dtype=np.float32)

        # 随机选择图形类型
        shape_type = np.random.randint(0, 3)

        if shape_type == 0:
            # 圆形
            center = np.random.randint(8, img_size - 8, 2)
            radius = np.random.randint(3, 8)
            y, x = np.ogrid[:img_size, :img_size]
            mask = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius ** 2
            img[mask] = 1.0

        elif shape_type == 1:
            # 矩形
            x1 = np.random.randint(4, img_size - 12)
            y1 = np.random.randint(4, img_size - 12)
            w = np.random.randint(4, 12)
            h = np.random.randint(4, 12)
            img[y1:y1 + h, x1:x1 + w] = 1.0

        else:
            # 对角线
            for i in range(img_size):
                j = i + np.random.randint(-2, 3)
                if 0 <= j < img_size:
                    img[i, j] = 1.0

        # 添加噪声
        noise = np.random.normal(0, 0.1, (img_size, img_size))
        img = np.clip(img + noise, 0, 1)

        images.append(img)

    # 转换为张量
    images = torch.FloatTensor(np.array(images)).unsqueeze(1)  # (N, 1, H, W)

    # 创建数据集和加载器
    dataset = TensorDataset(images, torch.zeros(len(images)))
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    return dataloader


def save_images(images: torch.Tensor, path: str, title: str = ""):
    """
    保存图像

    参数:
        images: 图像张量
        path: 保存路径
        title: 图像标题
    """
    images = images.detach().cpu().numpy()
    n_images = min(16, len(images))
    nrow = 4
    ncol = (n_images + nrow - 1) // nrow

    fig, axes = plt.subplots(ncol, nrow, figsize=(nrow * 2, ncol * 2))

    if ncol == 1:
        axes = [axes]
    if nrow == 1:
        axes = [[ax] for ax in axes]

    for i in range(ncol):
        for j in range(nrow):
            idx = i * nrow + j
            if idx < n_images:
                img = images[idx].squeeze()
                axes[i][j].imshow(img, cmap="gray", vmin=0, vmax=1)
            axes[i][j].axis("off")

    if title:
        fig.suptitle(title, fontsize=14)

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    """主函数"""
    print("=" * 50)
    print("简单 GAN 示例")
    print("=" * 50)

    # 创建数据集
    print("\n创建简单数据集...")
    dataloader = create_simple_dataset(n_samples=500, img_size=28)
    print(f"数据集大小: {len(dataloader.dataset)}")

    # 创建 GAN
    print("\n创建 GAN 模型...")
    gan = GAN(
        latent_dim=50,
        img_channels=1,
        img_size=28,
        lr=0.0002,
        beta1=0.5
    )

    # 设置设备
    device = torch.device("cpu")
    print(f"设备: {device}")

    # 训练循环
    n_epochs = 30
    print(f"\n开始训练 ({n_epochs} epochs)...")

    for epoch in range(1, n_epochs + 1):
        epoch_d_loss = 0.0
        epoch_g_loss = 0.0
        n_batches = 0

        for batch_idx, (real_images, _) in enumerate(dataloader):
            batch_size = real_images.size(0)

            # 训练步骤
            stats = gan.train_step(real_images)

            epoch_d_loss += stats["d_loss"]
            epoch_g_loss += stats["g_loss"]
            n_batches += 1

        # 打印进度
        avg_d_loss = epoch_d_loss / n_batches
        avg_g_loss = epoch_g_loss / n_batches

        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch [{epoch}/{n_epochs}] "
                  f"D_loss: {avg_d_loss:.4f} "
                  f"G_loss: {avg_g_loss:.4f}")

            # 生成样本
            if epoch % 10 == 0 or epoch == 1:
                samples = gan.generate_samples(n_samples=16, device=device)
                save_images(
                    samples,
                    f"simple_example_epoch_{epoch:03d}.png",
                    title=f"Epoch {epoch}"
                )

    # 生成最终样本
    print("\n生成最终样本...")
    final_samples = gan.generate_samples(n_samples=16, device=device)
    save_images(final_samples, "simple_example_final.png", title="Final Result")

    print("\n训练完成!")
    print("生成的图像已保存到当前目录")


if __name__ == "__main__":
    main()
