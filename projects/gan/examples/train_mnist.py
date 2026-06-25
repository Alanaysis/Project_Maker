"""
MNIST GAN 训练示例
==================

使用 GAN 在 MNIST 数据集上训练图像生成模型。

运行方式:
    python examples/train_mnist.py

输出:
    - 训练过程日志
    - 生成的图像样本
    - 训练损失曲线
    - 保存的模型检查点
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import GAN, GANTrainer


def create_mnist_dataloader(batch_size: int = 64, img_size: int = 28) -> DataLoader:
    """
    创建 MNIST 数据加载器

    参数:
        batch_size: 批次大小
        img_size: 图像尺寸

    返回:
        数据加载器
    """
    # 数据预处理
    transform = transforms.Compose([
        transforms.Resize(img_size),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5])  # 归一化到 [-1, 1]
    ])

    # 加载 MNIST 数据集
    dataset = datasets.MNIST(
        root="./data",
        train=True,
        download=True,
        transform=transform
    )

    # 创建数据加载器
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2
    )

    return dataloader


def save_images(images: torch.Tensor, path: str, nrow: int = 8):
    """
    保存图像网格

    参数:
        images: 图像张量，形状为 (n, c, h, w)
        path: 保存路径
        nrow: 每行图像数量
    """
    # 反归一化
    images = images * 0.5 + 0.5

    # 转换为 numpy
    images = images.cpu().numpy()

    # 创建网格
    n_images = images.shape[0]
    ncol = min(nrow, n_images)
    nrow_actual = (n_images + ncol - 1) // ncol

    fig, axes = plt.subplots(nrow_actual, ncol, figsize=(ncol * 2, nrow_actual * 2))

    if nrow_actual == 1:
        axes = [axes]
    if ncol == 1:
        axes = [[ax] for ax in axes]

    for i in range(nrow_actual):
        for j in range(ncol):
            idx = i * ncol + j
            if idx < n_images:
                img = images[idx].squeeze()
                axes[i][j].imshow(img, cmap="gray")
            axes[i][j].axis("off")

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_training_history(history: dict, save_path: str):
    """
    绘制训练历史

    参数:
        history: 训练历史字典
        save_path: 保存路径
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 判别器损失
    axes[0, 0].plot(history["d_loss"], label="D Loss", color="blue")
    axes[0, 0].set_title("Discriminator Loss")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("Loss")
    axes[0, 0].legend()
    axes[0, 0].grid(True)

    # 生成器损失
    axes[0, 1].plot(history["g_loss"], label="G Loss", color="red")
    axes[0, 1].set_title("Generator Loss")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Loss")
    axes[0, 1].legend()
    axes[0, 1].grid(True)

    # 判别器准确率
    axes[1, 0].plot(history["d_real_acc"], label="Real Acc", color="green")
    axes[1, 0].plot(history["d_fake_acc"], label="Fake Acc", color="orange")
    axes[1, 0].set_title("Discriminator Accuracy")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("Accuracy")
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # 训练时间
    axes[1, 1].plot(history["epoch_time"], label="Time", color="purple")
    axes[1, 1].set_title("Training Time per Epoch")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].set_ylabel("Time (s)")
    axes[1, 1].legend()
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    """主训练函数"""
    # 配置参数
    config = {
        "latent_dim": 100,
        "img_channels": 1,
        "img_size": 28,
        "batch_size": 64,
        "lr": 0.0002,
        "beta1": 0.5,
        "n_epochs": 50,
        "save_interval": 10,
        "sample_interval": 5,
        "save_dir": "checkpoints_mnist",
        "sample_dir": "samples_mnist"
    }

    # 创建目录
    os.makedirs(config["save_dir"], exist_ok=True)
    os.makedirs(config["sample_dir"], exist_ok=True)

    # 设置设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # 创建数据加载器
    print("加载 MNIST 数据集...")
    dataloader = create_mnist_dataloader(
        batch_size=config["batch_size"],
        img_size=config["img_size"]
    )
    print(f"数据集大小: {len(dataloader.dataset)}")

    # 创建 GAN
    print("创建 GAN 模型...")
    gan = GAN(
        latent_dim=config["latent_dim"],
        img_channels=config["img_channels"],
        img_size=config["img_size"],
        lr=config["lr"],
        beta1=config["beta1"]
    ).to(device)

    print(f"生成器参数数量: {sum(p.numel() for p in gan.generator.parameters()):,}")
    print(f"判别器参数数量: {sum(p.numel() for p in gan.discriminator.parameters()):,}")

    # 创建训练器
    trainer = GANTrainer(
        gan=gan,
        device=device,
        label_smoothing=0.1,
        noisy_labels=False,
        n_critic=1
    )

    # 定义回调函数
    def sample_callback(epoch, stats):
        """生成样本回调"""
        if epoch % config["sample_interval"] == 0 or epoch == 1:
            samples = gan.generate_samples(n_samples=16, device=device)
            save_images(
                samples,
                os.path.join(config["sample_dir"], f"epoch_{epoch:04d}.png")
            )

    # 开始训练
    print("\n开始训练...")
    history = trainer.train(
        dataloader=dataloader,
        n_epochs=config["n_epochs"],
        save_interval=config["save_interval"],
        sample_interval=config["sample_interval"],
        save_dir=config["save_dir"],
        callbacks=[sample_callback]
    )

    # 保存训练历史图
    plot_training_history(history, os.path.join(config["save_dir"], "training_history.png"))

    # 生成最终样本
    print("\n生成最终样本...")
    final_samples = gan.generate_samples(n_samples=64, device=device)
    save_images(final_samples, os.path.join(config["sample_dir"], "final_samples.png"), nrow=8)

    print(f"\n训练完成!")
    print(f"模型检查点保存在: {config['save_dir']}")
    print(f"生成样本保存在: {config['sample_dir']}")


if __name__ == "__main__":
    main()
