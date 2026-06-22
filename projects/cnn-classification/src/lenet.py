"""
LeNet-5 网络实现

经典CNN架构，由Yann LeCun在1998年提出
用于手写数字识别（MNIST）

架构：
    输入(1x32x32) -> Conv1(6@5x5) -> Pool1 -> Conv2(16@5x5) -> Pool2 -> FC1 -> FC2 -> FC3

原始论文: http://yann.lecun.com/exdb/publis/pdf/lecun-98.pdf
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

from .layers import Conv2D, MaxPool2D, Flatten


class LeNet5(nn.Module):
    """
    LeNet-5 网络结构

    层级结构：
    1. Conv1: 1x32x32 -> 6x28x28 (6个5x5卷积核)
    2. Pool1: 6x28x28 -> 6x14x14 (2x2最大池化)
    3. Conv2: 6x14x14 -> 16x10x10 (16个5x5卷积核)
    4. Pool2: 16x10x10 -> 16x5x5 (2x2最大池化)
    5. Flatten: 16x5x5 -> 400
    6. FC1: 400 -> 120
    7. FC2: 120 -> 84
    8. FC3: 84 -> 10 (输出10个类别)
    """

    def __init__(self, num_classes: int = 10, in_channels: int = 1):
        super().__init__()

        # 第一个卷积块
        # 输入: 1x32x32, 输出: 6x28x28
        self.conv1 = nn.Conv2d(in_channels, 6, kernel_size=5)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        # 池化后: 6x14x14

        # 第二个卷积块
        # 输入: 6x14x14, 输出: 16x10x10
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        # 池化后: 16x5x5

        # 展平层
        self.flatten = Flatten()

        # 全连接层
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数：
            x: 输入张量，形状 (batch_size, 1, 32, 32)

        返回：
            输出张量，形状 (batch_size, num_classes)
        """
        # 第一个卷积块
        x = self.conv1(x)          # (batch, 6, 28, 28)
        x = F.relu(x)              # 激活函数
        x = self.pool1(x)          # (batch, 6, 14, 14)

        # 第二个卷积块
        x = self.conv2(x)          # (batch, 16, 10, 10)
        x = F.relu(x)
        x = self.pool2(x)          # (batch, 16, 5, 5)

        # 展平
        x = self.flatten(x)        # (batch, 400)

        # 全连接层
        x = F.relu(self.fc1(x))    # (batch, 120)
        x = F.relu(self.fc2(x))    # (batch, 84)
        x = self.fc3(x)            # (batch, 10)

        return x

    def get_feature_maps(self, x: torch.Tensor) -> dict:
        """
        获取各层特征图（用于可视化）

        参数：
            x: 输入张量

        返回：
            包含各层特征图的字典
        """
        features = {}

        # 第一个卷积块
        x = self.conv1(x)
        features['conv1'] = x
        x = F.relu(x)
        x = self.pool1(x)
        features['pool1'] = x

        # 第二个卷积块
        x = self.conv2(x)
        features['conv2'] = x
        x = F.relu(x)
        x = self.pool2(x)
        features['pool2'] = x

        return features


class LeNet5Custom(nn.Module):
    """
    使用自定义层实现的LeNet-5

    用于学习目的，展示CNN层的实现原理
    """

    def __init__(self, num_classes: int = 10, in_channels: int = 1):
        super().__init__()

        # 使用自定义Conv2D层
        self.conv1 = Conv2D(in_channels, 6, kernel_size=5)
        self.pool1 = MaxPool2D(kernel_size=2, stride=2)

        self.conv2 = Conv2D(6, 16, kernel_size=5)
        self.pool2 = MaxPool2D(kernel_size=2, stride=2)

        self.flatten = Flatten()

        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)
        x = self.flatten(x)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def lenet5(num_classes: int = 10, in_channels: int = 1) -> LeNet5:
    """
    创建LeNet-5模型的工厂函数

    参数：
        num_classes: 分类数量
        in_channels: 输入通道数

    返回：
        LeNet-5模型实例
    """
    return LeNet5(num_classes=num_classes, in_channels=in_channels)
