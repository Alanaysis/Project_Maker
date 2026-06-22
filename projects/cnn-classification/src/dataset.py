"""
数据集加载和预处理

支持MNIST数据集的下载、预处理和DataLoader创建
"""

import torch
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
from typing import Tuple, Optional


def get_mnist_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """
    获取MNIST数据集的预处理变换

    训练集：随机旋转、平移、归一化
    测试集：仅归一化

    返回：
        (train_transform, test_transform)
    """
    train_transform = transforms.Compose([
        transforms.Resize((32, 32)),  # LeNet-5要求32x32输入
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1)),  # 数据增强
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))  # MNIST均值和标准差
    ])

    test_transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    return train_transform, test_transform


def get_mnist_dataloaders(
    data_dir: str = './data',
    batch_size: int = 64,
    num_workers: int = 4,
    val_split: float = 0.1
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    获取MNIST数据集的DataLoader

    参数：
        data_dir: 数据存储目录
        batch_size: 批次大小
        num_workers: 数据加载线程数
        val_split: 验证集比例

    返回：
        (train_loader, val_loader, test_loader)
    """
    train_transform, test_transform = get_mnist_transforms()

    # 下载并加载训练集
    train_dataset = datasets.MNIST(
        root=data_dir,
        train=True,
        download=True,
        transform=train_transform
    )

    # 下载并加载测试集
    test_dataset = datasets.MNIST(
        root=data_dir,
        train=False,
        download=True,
        transform=test_transform
    )

    # 分割训练集和验证集
    val_size = int(len(train_dataset) * val_split)
    train_size = len(train_dataset) - val_size
    train_dataset, val_dataset = random_split(train_dataset, [train_size, val_size])

    # 创建DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    return train_loader, val_loader, test_loader


def get_cifar10_dataloaders(
    data_dir: str = './data',
    batch_size: int = 128,
    num_workers: int = 4
) -> Tuple[DataLoader, DataLoader]:
    """
    获取CIFAR-10数据集的DataLoader（用于更复杂的模型）

    参数：
        data_dir: 数据存储目录
        batch_size: 批次大小
        num_workers: 数据加载线程数

    返回：
        (train_loader, test_loader)
    """
    train_transform = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])

    train_dataset = datasets.CIFAR10(
        root=data_dir,
        train=True,
        download=True,
        transform=train_transform
    )

    test_dataset = datasets.CIFAR10(
        root=data_dir,
        train=False,
        download=True,
        transform=test_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    return train_loader, test_loader
