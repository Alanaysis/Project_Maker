"""
特征提取模块

实现人脸特征向量的提取功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Tuple


class FaceEmbeddingNet(nn.Module):
    """
    人脸特征提取网络

    使用卷积神经网络提取人脸特征，输出 L2 归一化的特征向量。
    """

    def __init__(self, embedding_size: int = 128):
        """
        初始化网络

        Args:
            embedding_size: 特征向量维度
        """
        super().__init__()

        self.embedding_size = embedding_size

        # 卷积层
        self.conv_layers = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),

            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        # 全连接层
        self.fc_layers = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, embedding_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量 (batch_size, 3, 160, 160)

        Returns:
            特征向量 (batch_size, embedding_size)
        """
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        x = self.fc_layers(x)
        # L2 归一化
        x = F.normalize(x, p=2, dim=1)
        return x


class ResidualBlock(nn.Module):
    """残差块"""

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()

        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, stride, 1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, 1, 1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        out = F.relu(out)
        return out


class ResNetEmbedding(nn.Module):
    """
    基于 ResNet 的特征提取网络

    使用残差块构建更深的网络。
    """

    def __init__(self, embedding_size: int = 128):
        super().__init__()

        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 64, 7, 2, 3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(3, 2, 1),
        )

        self.layer1 = self._make_layer(64, 64, 2, stride=1)
        self.layer2 = self._make_layer(64, 128, 2, stride=2)
        self.layer3 = self._make_layer(128, 256, 2, stride=2)

        self.avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(256, embedding_size)

    def _make_layer(self, in_channels: int, out_channels: int,
                    num_blocks: int, stride: int) -> nn.Sequential:
        layers = [ResidualBlock(in_channels, out_channels, stride)]
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.avg_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        x = F.normalize(x, p=2, dim=1)
        return x


class FeatureExtractor:
    """
    特征提取器

    将人脸图像转换为特征向量。
    """

    def __init__(self, model_type: str = "custom", embedding_size: int = 128,
                 device: Optional[str] = None):
        """
        初始化特征提取器

        Args:
            model_type: 模型类型 ("custom" 或 "resnet")
            embedding_size: 特征向量维度
            device: 计算设备 (cpu 或 cuda)
        """
        self.model_type = model_type
        self.embedding_size = embedding_size

        # 设置设备
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # 构建模型
        self.model = self._build_model()
        self.model.to(self.device)
        self.model.eval()

    def _build_model(self) -> nn.Module:
        """构建特征提取网络"""
        if self.model_type == "custom":
            return FaceEmbeddingNet(self.embedding_size)
        elif self.model_type == "resnet":
            return ResNetEmbedding(self.embedding_size)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def _preprocess(self, face_image: np.ndarray) -> torch.Tensor:
        """
        预处理人脸图像

        Args:
            face_image: 人脸图像 (H, W, C) BGR 格式

        Returns:
            预处理后的张量
        """
        # 确保图像是 RGB 格式
        if len(face_image.shape) == 3 and face_image.shape[2] == 3:
            face_image = face_image[:, :, ::-1].copy()

        # 调整大小
        face_image = np.resize(face_image, (160, 160, 3))

        # 转换为浮点数并归一化
        face_image = face_image.astype(np.float32) / 255.0

        # 标准化
        mean = np.array([0.5, 0.5, 0.5])
        std = np.array([0.5, 0.5, 0.5])
        face_image = (face_image - mean) / std

        # 转换为张量 (C, H, W)
        tensor = torch.from_numpy(face_image.transpose(2, 0, 1)).float()

        return tensor

    def extract(self, face_image: np.ndarray) -> np.ndarray:
        """
        提取人脸特征

        Args:
            face_image: 人脸图像 (H, W, C)

        Returns:
            特征向量 (embedding_size,)
        """
        # 预处理
        tensor = self._preprocess(face_image)
        tensor = tensor.unsqueeze(0).to(self.device)

        # 提取特征
        with torch.no_grad():
            feature = self.model(tensor)

        # 转换为 numpy 数组
        feature = feature.cpu().numpy().flatten()

        return feature

    def extract_batch(self, face_images: List[np.ndarray],
                      batch_size: int = 32) -> np.ndarray:
        """
        批量提取特征

        Args:
            face_images: 人脸图像列表
            batch_size: 批处理大小

        Returns:
            特征向量矩阵 (N, embedding_size)
        """
        all_features = []

        for i in range(0, len(face_images), batch_size):
            batch = face_images[i:i + batch_size]

            # 预处理批次
            tensors = [self._preprocess(img) for img in batch]
            batch_tensor = torch.stack(tensors).to(self.device)

            # 提取特征
            with torch.no_grad():
                features = self.model(batch_tensor)

            all_features.append(features.cpu().numpy())

        return np.vstack(all_features)

    def get_embedding_size(self) -> int:
        """返回特征向量维度"""
        return self.embedding_size

    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            "model_type": self.model_type,
            "embedding_size": self.embedding_size,
            "model_state_dict": self.model.state_dict(),
        }, path)

    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model_type = checkpoint["model_type"]
        self.embedding_size = checkpoint["embedding_size"]
        self.model = self._build_model()
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
