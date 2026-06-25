"""文字识别模块 - CRNN 实现"""

import cv2
import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple, Optional


class CRNN(nn.Module):
    """CRNN 文字识别模型

    结构：CNN特征提取 -> RNN序列建模 -> 全连接分类
    """

    def __init__(self, num_classes: int, hidden_size: int = 256):
        """
        Args:
            num_classes: 字符类别数（包含 blank）
            hidden_size: RNN 隐藏层大小
        """
        super().__init__()

        # CNN 特征提取
        self.cnn = nn.Sequential(
            # conv1: 1x32xW -> 64x16xW/2
            nn.Conv2d(1, 64, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),

            # conv2: 64x16xW/2 -> 128x8xW/4
            nn.Conv2d(64, 128, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d(2, 2),

            # conv3: 128x8xW/4 -> 256x8xW/4
            nn.Conv2d(128, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),

            # conv4: 256x8xW/4 -> 256x4xW/4
            nn.Conv2d(256, 256, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),

            # conv5: 256x4xW/4 -> 512x4xW/4
            nn.Conv2d(256, 512, 3, 1, 1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),

            # conv6: 512x4xW/4 -> 512x2xW/4
            nn.Conv2d(512, 512, 3, 1, 1),
            nn.ReLU(True),
            nn.MaxPool2d((2, 1), (2, 1)),

            # conv7: 512x2xW/4 -> 512x1xW/4
            nn.Conv2d(512, 512, 2, 1, 0),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
        )

        # RNN 序列建模
        self.rnn = nn.LSTM(
            input_size=512,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False
        )

        # 全连接层
        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入图像 (B, 1, H, W)

        Returns:
            输出序列 (T, B, num_classes)
        """
        # CNN 特征提取
        conv = self.cnn(x)

        # 转换为序列格式
        b, c, h, w = conv.size()
        assert h == 1, f"Height should be 1, got {h}"
        conv = conv.squeeze(2)  # (B, C, W)
        conv = conv.permute(2, 0, 1)  # (W, B, C) = (T, B, C)

        # RNN 处理
        rnn_out, _ = self.rnn(conv)

        # 全连接
        output = self.fc(rnn_out)

        return output


class CTCDecoder:
    """CTC 解码器"""

    def __init__(self, charset: str, blank_idx: int = 0):
        """
        Args:
            charset: 字符集
            blank_idx: blank 标签索引
        """
        self.charset = charset
        self.blank_idx = blank_idx

    def greedy_decode(self, logits: torch.Tensor) -> str:
        """
        贪心解码

        Args:
            logits: 模型输出 (T, C)

        Returns:
            解码后的文本
        """
        # 获取最大概率的字符
        _, indices = torch.max(logits, dim=1)
        indices = indices.cpu().numpy()

        # 去重和去 blank
        chars = []
        prev_idx = -1
        for idx in indices:
            if idx != self.blank_idx and idx != prev_idx:
                if idx < len(self.charset):
                    chars.append(self.charset[idx])
            prev_idx = idx

        return ''.join(chars)

    def beam_search_decode(self, logits: torch.Tensor,
                           beam_size: int = 10) -> str:
        """
        Beam Search 解码

        Args:
            logits: 模型输出 (T, C)
            beam_size: beam 大小

        Returns:
            解码后的文本
        """
        # 简化实现，使用贪心解码
        return self.greedy_decode(logits)


class TextRecognizer:
    """文字识别器"""

    def __init__(self, model_path: Optional[str] = None,
                 charset: Optional[str] = None,
                 input_height: int = 32,
                 device: str = "cpu"):
        """
        Args:
            model_path: 模型路径
            charset: 字符集
            input_height: 输入图像高度
            device: 设备
        """
        self.input_height = input_height
        self.device = device

        # 默认字符集
        if charset is None:
            charset = "0123456789abcdefghijklmnopqrstuvwxyz"
        self.charset = charset

        # 创建模型
        num_classes = len(charset) + 1  # +1 for blank
        self.model = CRNN(num_classes)

        # 加载模型权重
        if model_path is not None:
            try:
                self.model.load_state_dict(
                    torch.load(model_path, map_location=device)
                )
                print(f"Loaded model from {model_path}")
            except Exception as e:
                print(f"Warning: Failed to load model: {e}")

        self.model.to(device)
        self.model.eval()

        # 创建解码器
        self.decoder = CTCDecoder(charset)

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        预处理图像

        Args:
            image: 输入图像 (H, W, C) 或 (H, W)

        Returns:
            预处理后的张量 (1, 1, H, W)
        """
        # 灰度化
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 调整大小
        h, w = gray.shape
        if h > 0:
            new_w = max(int(w * self.input_height / h), 1)
        else:
            new_w = 100
        resized = cv2.resize(gray, (new_w, self.input_height))

        # 归一化
        normalized = resized.astype(np.float32) / 255.0
        normalized = (normalized - 0.5) / 0.5

        # 转换为张量
        tensor = torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0)
        return tensor.to(self.device)

    def recognize(self, image: np.ndarray) -> Tuple[str, float]:
        """
        识别文字

        Args:
            image: 输入图像

        Returns:
            (识别文本, 置信度)
        """
        # 预处理
        input_tensor = self.preprocess(image)

        # 前向传播
        with torch.no_grad():
            output = self.model(input_tensor)

        # 解码
        text = self.decoder.greedy_decode(output.squeeze(1))

        # 计算置信度
        probs = torch.softmax(output, dim=2)
        confidence = probs.max().item()

        return text, confidence

    def recognize_batch(self, images: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        批量识别

        Args:
            images: 图像列表

        Returns:
            识别结果列表
        """
        results = []
        for image in images:
            text, conf = self.recognize(image)
            results.append((text, conf))
        return results


def create_recognizer(model_path: Optional[str] = None,
                      charset: Optional[str] = None,
                      device: str = "cpu") -> TextRecognizer:
    """
    创建识别器工厂函数

    Args:
        model_path: 模型路径
        charset: 字符集
        device: 设备

    Returns:
        识别器实例
    """
    return TextRecognizer(
        model_path=model_path,
        charset=charset,
        device=device
    )