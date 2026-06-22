"""
AlexNet 网络实现

经典CNN架构，由Alex Krizhevsky在2012年提出
赢得ImageNet LSVRC-2012比赛

架构：
    输入(3x227x227) -> Conv1(96@11x11) -> Pool1 -> Conv2(256@5x5) -> Pool2 ->
    Conv3(384@3x3) -> Conv4(384@3x3) -> Conv5(256@3x3) -> Pool5 ->
    FC1(4096) -> FC2(4096) -> FC3(1000)

原始论文: https://papers.nips.cc/paper/2012/hash/c399862d3b9d6b76c8436e924a68c45b-Abstract.html
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class AlexNet(nn.Module):
    """
    AlexNet网络结构

    层级结构：
    1. Conv1: 3x227x227 -> 96x55x55 (96个11x11卷积核，步长4)
    2. Pool1: 96x55x55 -> 96x27x27 (3x3最大池化，步长2)
    3. Conv2: 96x27x27 -> 256x27x27 (256个5x5卷积核，填充2)
    4. Pool2: 256x27x27 -> 256x13x13 (3x3最大池化，步长2)
    5. Conv3: 256x13x13 -> 384x13x13 (384个3x3卷积核，填充1)
    6. Conv4: 384x13x13 -> 384x13x13 (384个3x3卷积核，填充1)
    7. Conv5: 384x13x13 -> 256x13x13 (256个3x3卷积核，填充1)
    8. Pool5: 256x13x13 -> 256x6x6 (3x3最大池化，步长2)
    9. Flatten: 256x6x6 -> 9216
    10. FC1: 9216 -> 4096
    11. FC2: 4096 -> 4096
    12. FC3: 4096 -> num_classes
    """

    def __init__(self, num_classes: int = 1000, in_channels: int = 3):
        super().__init__()

        # 特征提取层
        self.features = nn.Sequential(
            # Conv1
            nn.Conv2d(in_channels, 96, kernel_size=11, stride=4, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),

            # Conv2
            nn.Conv2d(96, 256, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),

            # Conv3
            nn.Conv2d(256, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),

            # Conv4
            nn.Conv2d(384, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),

            # Conv5
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )

        # 分类层
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(256 * 6 * 6, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_classes),
        )

        # 权重初始化
        self._initialize_weights()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        参数：
            x: 输入张量，形状 (batch_size, 3, 227, 227)

        返回：
            输出张量，形状 (batch_size, num_classes)
        """
        x = self.features(x)
        x = x.view(x.size(0), 256 * 6 * 6)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        """初始化权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)


class AlexNetCIFAR(nn.Module):
    """
    适用于CIFAR-10的AlexNet变体

    调整后的架构，适用于32x32的输入图像
    """

    def __init__(self, num_classes: int = 10, in_channels: int = 3):
        super().__init__()

        self.features = nn.Sequential(
            # Conv1: 3x32x32 -> 64x16x16
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Conv2: 64x16x16 -> 192x8x8
            nn.Conv2d(64, 192, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Conv3: 192x8x8 -> 384x8x8
            nn.Conv2d(192, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),

            # Conv4: 384x8x8 -> 256x8x8
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),

            # Conv5: 256x8x8 -> 256x4x4
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(256 * 4 * 4, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.5),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_classes),
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
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)


def alexnet(num_classes: int = 1000, in_channels: int = 3) -> AlexNet:
    """创建AlexNet模型"""
    return AlexNet(num_classes=num_classes, in_channels=in_channels)


def alexnet_cifar(num_classes: int = 10, in_channels: int = 3) -> AlexNetCIFAR:
    """创建适用于CIFAR的AlexNet模型"""
    return AlexNetCIFAR(num_classes=num_classes, in_channels=in_channels)
