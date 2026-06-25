"""
Keypoint Extractor - 手部关键点提取

核心思路：
1. 使用简化的手部关键点模型 (21个关键点)
2. 基于CNN回归关键点坐标
3. 输出归一化的关键点坐标

学习要点:
- 理解关键点检测的回归方法
- 掌握坐标归一化技巧
- 学会处理遮挡和不可见关键点

手部关键点布局 (MediaPipe标准):
        8   12  16  20
        |   |   |   |
    4   7   11  15  19
    |   |   |   |   |
    3   6   10  14  18
    |   |   |   |   |
    2   5   9   13  17
      |   |   |   |
      1
      |
      0 (手腕)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional


class KeypointNet(nn.Module):
    """
    关键点检测网络

    架构设计思路：
    1. 轻量级CNN提取特征
    2. 全连接层回归坐标
    3. 输出21个关键点的(x, y)坐标

    为什么用回归而不是热力图？
    - 回归方法更简单，适合学习
    - 计算量更小
    - 缺点是精度略低，但对学习足够
    """

    def __init__(self, num_keypoints: int = 21):
        super().__init__()
        self.num_keypoints = num_keypoints

        # 特征提取网络
        # 输入: (B, 3, 128, 128)
        self.features = nn.Sequential(
            # 第1层: 3 -> 32 channels
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> (B, 32, 64, 64)

            # 第2层: 32 -> 64 channels
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> (B, 64, 32, 32)

            # 第3层: 64 -> 128 channels
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # -> (B, 128, 16, 16)

            # 第4层: 128 -> 256 channels
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(4),  # -> (B, 256, 4, 4)
        )

        # 回归头
        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, num_keypoints * 2),  # 21个关键点，每个(x, y)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入图像 (B, 3, 128, 128)

        Returns:
            关键点坐标 (B, 42) - 展平的(x, y)坐标
        """
        features = self.features(x)
        keypoints = self.regressor(features)

        # 使用sigmoid将输出限制在[0, 1]范围内（归一化坐标）
        keypoints = torch.sigmoid(keypoints)

        return keypoints


class KeypointExtractor:
    """
    手部关键点提取器

    封装了模型推理和后处理逻辑

    关键点索引定义 (21个):
    0: 手腕 (Wrist)
    1-4: 拇指 (Thumb)
    5-8: 食指 (Index)
    9-12: 中指 (Middle)
    13-16: 无名指 (Ring)
    17-20: 小指 (Pinky)
    """

    # 关键点名称
    KEYPOINT_NAMES = [
        "wrist",
        "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip",
        "index_mcp", "index_pip", "index_dip", "index_tip",
        "middle_mcp", "middle_pip", "middle_dip", "middle_tip",
        "ring_mcp", "ring_pip", "ring_dip", "ring_tip",
        "pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip",
    ]

    # 手指关键点连接关系（用于绘制骨架）
    CONNECTIONS = [
        # 拇指
        (0, 1), (1, 2), (2, 3), (3, 4),
        # 食指
        (0, 5), (5, 6), (6, 7), (7, 8),
        # 中指
        (0, 9), (9, 10), (10, 11), (11, 12),
        # 无名指
        (0, 13), (13, 14), (14, 15), (15, 16),
        # 小指
        (0, 17), (17, 18), (18, 19), (19, 20),
    ]

    def __init__(
        self,
        model_path: Optional[str] = None,
        input_size: Tuple[int, int] = (128, 128),
        device: str = "cpu",
    ):
        """
        初始化关键点提取器

        Args:
            model_path: 预训练模型路径，None则使用随机初始化
            input_size: 输入图像尺寸
            device: 推理设备
        """
        self.input_size = input_size
        self.device = torch.device(device)

        # 创建模型
        self.model = KeypointNet(num_keypoints=21).to(self.device)

        # 加载预训练权重
        if model_path is not None:
            self.model.load_state_dict(
                torch.load(model_path, map_location=self.device)
            )

        self.model.eval()

    def extract(
        self, image: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> dict:
        """
        从图像中提取手部关键点

        Args:
            image: BGR格式的输入图像
            bbox: 手部边界框 (x, y, w, h)，None则处理整张图

        Returns:
            dict: 包含关键点信息
                - keypoints: (21, 2) 归一化坐标
                - keypoints_pixel: (21, 2) 像素坐标
                - confidence: 各关键点置信度
        """
        # 裁剪手部区域
        if bbox is not None:
            x, y, w, h = bbox
            # 添加边距
            margin = int(max(w, h) * 0.1)
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(image.shape[1], x + w + margin)
            y2 = min(image.shape[0], y + h + margin)
            hand_image = image[y1:y2, x1:x2]
            offset = (x1, y1)
        else:
            hand_image = image
            offset = (0, 0)

        # 预处理
        input_tensor = self._preprocess(hand_image)

        # 推理
        with torch.no_grad():
            output = self.model(input_tensor)

        # 后处理
        keypoints = self._postprocess(output, image.shape, bbox, offset)

        return keypoints

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        图像预处理

        步骤：
        1. 调整尺寸到模型输入大小
        2. 归一化到[0, 1]
        3. 转换为tensor并添加batch维度
        """
        # 调整尺寸
        resized = cv2.resize(image, self.input_size)

        # BGR转RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # 归一化
        normalized = rgb.astype(np.float32) / 255.0

        # HWC -> CHW
        tensor = torch.from_numpy(normalized).permute(2, 0, 1)

        # 添加batch维度
        return tensor.unsqueeze(0).to(self.device)

    def _postprocess(
        self,
        output: torch.Tensor,
        image_shape: Tuple[int, int, int],
        bbox: Optional[Tuple[int, int, int, int]],
        offset: Tuple[int, int],
    ) -> dict:
        """
        后处理模型输出

        将归一化坐标转换为像素坐标
        """
        # 获取归一化坐标
        keypoints_norm = output.cpu().numpy().reshape(21, 2)

        # 转换为像素坐标
        h, w = image_shape[:2]

        if bbox is not None:
            bx, by, bw, bh = bbox
            # 在裁剪区域内映射
            keypoints_pixel = np.zeros_like(keypoints_norm)
            keypoints_pixel[:, 0] = offset[0] + keypoints_norm[:, 0] * (w - offset[0])
            keypoints_pixel[:, 1] = offset[1] + keypoints_norm[:, 1] * (h - offset[1])
        else:
            keypoints_pixel = keypoints_norm.copy()
            keypoints_pixel[:, 0] *= w
            keypoints_pixel[:, 1] *= h

        return {
            "keypoints": keypoints_norm,
            "keypoints_pixel": keypoints_pixel.astype(int),
            "confidence": np.ones(21),  # 简化版本，实际模型会输出置信度
        }

    def batch_extract(self, images: list) -> list:
        """
        批量提取关键点

        Args:
            images: 图像列表

        Returns:
            list: 每张图像的关键点结果
        """
        return [self.extract(img) for img in images]


# 需要导入cv2用于resize
import cv2
