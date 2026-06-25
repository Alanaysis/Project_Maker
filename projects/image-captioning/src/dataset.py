"""
Dataset - 数据集处理

定义图像描述数据集类，负责：
- 加载和预处理图像
- 将描述文本编码为索引序列
- 提供批量数据加载

支持的数据格式：
- 图像文件目录
- 描述文本文件（每行：image_id\tcaption）
"""

import os
from typing import Optional

import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image

from .vocabulary import Vocabulary


class CaptionDataset(Dataset):
    """图像描述数据集。

    管理图像和对应的描述文本，提供统一的数据访问接口。
    """

    def __init__(
        self,
        image_dir: str,
        captions_file: Optional[str] = None,
        captions_list: Optional[list[tuple[str, str]]] = None,
        vocabulary: Optional[Vocabulary] = None,
        transform: Optional[transforms.Compose] = None,
        max_caption_length: int = 100,
        image_size: int = 224,
    ):
        """初始化数据集。

        Args:
            image_dir: 图像文件目录
            captions_file: 描述文件路径（每行：image_filename\tcaption）
            captions_list: 描述列表 [(image_filename, caption), ...]
            vocabulary: 词汇表实例
            transform: 图像预处理变换
            max_caption_length: 最大描述长度
            image_size: 图像尺寸
        """
        self.image_dir = image_dir
        self.max_caption_length = max_caption_length
        self.vocabulary = vocabulary

        # 加载描述数据
        self.captions: list[tuple[str, str]] = []
        if captions_list is not None:
            self.captions = captions_list
        elif captions_file is not None:
            self._load_captions_file(captions_file)

        # 图像预处理
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])
        else:
            self.transform = transform

    def _load_captions_file(self, filepath: str) -> None:
        """从文件加载描述数据。

        文件格式：每行包含 image_filename\\tcaption

        Args:
            filepath: 描述文件路径
        """
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    image_name, caption = parts
                    self.captions.append((image_name.strip(), caption.strip()))

    def __len__(self) -> int:
        return len(self.captions)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, list[int], int]:
        """获取单个样本。

        Args:
            idx: 样本索引

        Returns:
            image: 预处理后的图像张量 (3, H, W)
            caption_indices: 编码后的描述索引列表
            caption_length: 描述长度
        """
        image_name, caption = self.captions[idx]

        # 加载和预处理图像
        image_path = os.path.join(self.image_dir, image_name)
        image = Image.open(image_path).convert("RGB")
        if self.transform:
            image = self.transform(image)

        # 编码描述
        if self.vocabulary is not None:
            caption_indices = self.vocabulary.encode(
                caption, max_length=self.max_caption_length
            )
        else:
            caption_indices = []

        caption_length = len(caption_indices)

        return image, torch.tensor(caption_indices, dtype=torch.long), caption_length


def collate_fn(
    batch: list[tuple[torch.Tensor, torch.Tensor, int]],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """自定义批量整理函数。

    将不同长度的描述序列填充到相同长度，并按长度排序。

    Args:
        batch: 批量数据列表 [(image, caption_indices, length), ...]

    Returns:
        images: 图像张量 (batch_size, 3, H, W)
        captions: 填充后的描述序列 (batch_size, max_length)
        caption_lengths: 描述长度 (batch_size,)
    """
    # 按描述长度降序排序（方便 LSTM 处理）
    batch.sort(key=lambda x: x[2], reverse=True)

    images, captions, lengths = zip(*batch)

    # 堆叠图像
    images = torch.stack(images, dim=0)

    # 填充描述序列
    max_length = max(lengths)
    padded_captions = torch.zeros(len(captions), max_length, dtype=torch.long)
    for i, cap in enumerate(captions):
        end = lengths[i]
        padded_captions[i, :end] = cap[:end]

    caption_lengths = torch.tensor(lengths, dtype=torch.long)

    return images, padded_captions, caption_lengths


class SyntheticCaptionDataset(Dataset):
    """合成数据集，用于测试和演示。

    生成随机图像和简单的模板描述，不需要真实数据。
    """

    def __init__(
        self,
        vocab_size: int = 100,
        num_samples: int = 100,
        image_size: int = 224,
        max_caption_length: int = 10,
    ):
        """初始化合成数据集。

        Args:
            vocab_size: 词汇表大小
            num_samples: 样本数量
            image_size: 图像尺寸
            max_caption_length: 最大描述长度
        """
        self.num_samples = num_samples
        self.image_size = image_size
        self.vocab_size = vocab_size
        self.max_caption_length = max_caption_length

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, int]:
        """获取合成样本。

        Returns:
            随机图像、随机描述序列、描述长度
        """
        # 随机图像
        image = torch.randn(3, self.image_size, self.image_size)

        # 随机描述序列（避免 pad=0, start=1, end=2）
        length = torch.randint(3, self.max_caption_length, (1,)).item()
        caption = torch.randint(4, self.vocab_size, (length,))
        # 在开头加 start，在结尾前加 end
        caption[0] = 1  # <start>
        if length > 2:
            caption[length - 1] = 2  # <end>

        return image, caption, length


def synthetic_collate_fn(
    batch: list[tuple[torch.Tensor, torch.Tensor, int]],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """合成数据集的批量整理函数。"""
    batch.sort(key=lambda x: x[2], reverse=True)
    images, captions, lengths = zip(*batch)

    images = torch.stack(images, dim=0)
    max_length = max(lengths)
    padded_captions = torch.zeros(len(captions), max_length, dtype=torch.long)
    for i, cap in enumerate(captions):
        end = lengths[i]
        padded_captions[i, :end] = cap[:end]

    caption_lengths = torch.tensor(lengths, dtype=torch.long)
    return images, padded_captions, caption_lengths
