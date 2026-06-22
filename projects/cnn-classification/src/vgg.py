"""
VGG 网络实现

经典CNN架构，由Karen Simonyan和Andrew Zisserman在2014年提出
使用多个3x3卷积核堆叠来增加网络深度

架构变体：
    VGG-11: 8个卷积层 + 3个全连接层
    VGG-13: 10个卷积层 + 3个全连接层
    VGG-16: 13个卷积层 + 3个全连接层
    VGG-19: 16个卷积层 + 3个全连接层

原始论文: https://arxiv.org/abs/1409.1556
"""

import torch
import torch.nn as nn
from typing import List, Dict


# VGG网络配置
# 'M' 表示最大池化层，数字表示卷积层的输出通道数
VGG_CONFIGS = {
    'vgg11': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg13': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'vgg16': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'vgg19': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}


def make_layers(config: List, batch_norm: bool = False) -> nn.Sequential:
    """
    根据配置创建卷积层

    参数：
        config: 网络配置列表
        batch_norm: 是否使用批归一化

    返回：
        nn.Sequential 包含的层
    """
    layers = []
    in_channels = 3

    for v in config:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v

    return nn.Sequential(*layers)


class VGG(nn.Module):
    """
    VGG网络结构

    特点：
    - 使用3x3小卷积核堆叠
    - 网络深度可配置
    - 支持批归一化
    """

    def __init__(
        self,
        config: List,
        num_classes: int = 1000,
        in_channels: int = 3,
        batch_norm: bool = False,
        init_weights: bool = True
    ):
        super().__init__()

        # 特征提取层
        self.features = make_layers(config, batch_norm)

        # 分类层
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, num_classes),
        )

        if init_weights:
            self._initialize_weights()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数：
            x: 输入张量，形状 (batch_size, 3, 224, 224)

        返回：
            输出张量，形状 (batch_size, num_classes)
        """
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)


class VGGCIFAR(nn.Module):
    """
    适用于CIFAR-10的VGG变体

    调整后的架构，适用于32x32的输入图像
    """

    def __init__(
        self,
        config: List,
        num_classes: int = 10,
        in_channels: int = 3,
        batch_norm: bool = True
    ):
        super().__init__()

        self.features = make_layers(config, batch_norm)

        # CIFAR-10输入为32x32，经过5次池化后为1x1
        self.classifier = nn.Sequential(
            nn.Linear(512, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(512, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(512, num_classes),
        )

        self._initialize_weights()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)


# 工厂函数
def vgg11(num_classes: int = 1000, in_channels: int = 3, batch_norm: bool = False) -> VGG:
    """创建VGG-11模型"""
    return VGG(VGG_CONFIGS['vgg11'], num_classes, in_channels, batch_norm)


def vgg13(num_classes: int = 1000, in_channels: int = 3, batch_norm: bool = False) -> VGG:
    """创建VGG-13模型"""
    return VGG(VGG_CONFIGS['vgg13'], num_classes, in_channels, batch_norm)


def vgg16(num_classes: int = 1000, in_channels: int = 3, batch_norm: bool = False) -> VGG:
    """创建VGG-16模型"""
    return VGG(VGG_CONFIGS['vgg16'], num_classes, in_channels, batch_norm)


def vgg19(num_classes: int = 1000, in_channels: int = 3, batch_norm: bool = False) -> VGG:
    """创建VGG-19模型"""
    return VGG(VGG_CONFIGS['vgg19'], num_classes, in_channels, batch_norm)


def vgg_cifar(
    model_name: str = 'vgg16',
    num_classes: int = 10,
    in_channels: int = 3,
    batch_norm: bool = True
) -> VGGCIFAR:
    """创建适用于CIFAR的VGG模型"""
    if model_name not in VGG_CONFIGS:
        raise ValueError(f"Unknown VGG model: {model_name}")
    return VGGCIFAR(VGG_CONFIGS[model_name], num_classes, in_channels, batch_norm)
