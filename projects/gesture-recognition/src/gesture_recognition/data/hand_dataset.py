"""
Hand Dataset - 手部关键点数据集

支持两种数据模式：
1. 合成数据：用于快速原型验证
2. 真实数据：从标注文件加载

学习要点：
- 理解数据集的抽象设计
- 掌握数据增强技巧
- 学会处理不平衡数据
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Optional, Tuple, List, Dict
import json
from pathlib import Path


class HandDataset(Dataset):
    """
    手部关键点数据集

    数据格式：
    - keypoints: (21, 2) 关键点坐标
    - gesture: 手势类别标签
    - image_size: 图像尺寸（用于坐标归一化）
    """

    def __init__(
        self,
        data_path: Optional[str] = None,
        num_samples: int = 1000,
        num_classes: int = 7,
        transform=None,
        mode: str = "train",
    ):
        """
        初始化数据集

        Args:
            data_path: 数据文件路径（JSON格式）
            num_samples: 合成数据样本数
            num_classes: 手势类别数
            transform: 数据增强变换
            mode: 'train' 或 'val'
        """
        self.transform = transform
        self.mode = mode

        if data_path and Path(data_path).exists():
            # 加载真实数据
            self.data = self._load_data(data_path)
        else:
            # 生成合成数据
            self.data = self._generate_synthetic_data(num_samples, num_classes)

    def _load_data(self, data_path: str) -> List[Dict]:
        """
        加载标注数据

        数据格式 (JSON):
        [
            {
                "keypoints": [[x1, y1], [x2, y2], ...],
                "gesture": 0,
                "image_size": [640, 480]
            },
            ...
        ]
        """
        with open(data_path, "r") as f:
            data = json.load(f)
        return data

    def _generate_synthetic_data(
        self, num_samples: int, num_classes: int
    ) -> List[Dict]:
        """
        生成合成数据

        合成策略：
        1. 为每种手势生成基础关键点模板
        2. 添加随机扰动模拟真实变化
        3. 确保类别平衡

        为什么需要合成数据？
        - 快速验证模型正确性
        - 不需要收集真实数据
        - 可以控制数据分布
        """
        data = []
        samples_per_class = num_samples // num_classes

        for gesture_id in range(num_classes):
            for _ in range(samples_per_class):
                # 生成该手势的基础关键点
                base_keypoints = self._get_base_keypoints(gesture_id)

                # 添加随机扰动
                noise = np.random.normal(0, 0.02, base_keypoints.shape)
                keypoints = base_keypoints + noise

                # 确保坐标在[0, 1]范围内
                keypoints = np.clip(keypoints, 0, 1)

                data.append(
                    {
                        "keypoints": keypoints.tolist(),
                        "gesture": gesture_id,
                        "image_size": [640, 480],
                    }
                )

        # 打乱顺序
        np.random.shuffle(data)
        return data

    def _get_base_keypoints(self, gesture_id: int) -> np.ndarray:
        """
        获取手势的基础关键点模板

        每种手势有独特的手指伸展模式
        """
        # 基础手腕位置
        wrist = np.array([0.5, 0.8])

        # 各手指的关节位置模板
        # 索引: [wrist, thumb, index, middle, ring, pinky]
        # 每个手指: [mcp, pip, dip, tip]

        if gesture_id == 0:  # fist (拳头)
            fingers = self._generate_fist_keypoints(wrist)
        elif gesture_id == 1:  # open_palm (张开手掌)
            fingers = self._generate_open_palm_keypoints(wrist)
        elif gesture_id == 2:  # peace (剪刀手)
            fingers = self._generate_peace_keypoints(wrist)
        elif gesture_id == 3:  # thumbs_up (竖大拇指)
            fingers = self._generate_thumbs_up_keypoints(wrist)
        elif gesture_id == 4:  # pointing (指向)
            fingers = self._generate_pointing_keypoints(wrist)
        elif gesture_id == 5:  # ok (OK手势)
            fingers = self._generate_ok_keypoints(wrist)
        else:  # none (随机)
            fingers = self._generate_random_keypoints(wrist)

        return fingers

    def _generate_fist_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成拳头关键点：所有手指弯曲"""
        keypoints = np.zeros((21, 2))
        keypoints[0] = wrist  # 手腕

        # 拇指弯曲在手掌前
        keypoints[1] = wrist + np.array([-0.1, -0.1])
        keypoints[2] = wrist + np.array([-0.05, -0.15])
        keypoints[3] = wrist + np.array([0.0, -0.12])
        keypoints[4] = wrist + np.array([0.05, -0.08])

        # 其他手指弯曲
        for i, offset_x in enumerate([-0.06, -0.02, 0.02, 0.06]):
            base_idx = 5 + i * 4
            keypoints[base_idx] = wrist + np.array([offset_x, -0.15])
            keypoints[base_idx + 1] = wrist + np.array([offset_x, -0.12])
            keypoints[base_idx + 2] = wrist + np.array([offset_x, -0.08])
            keypoints[base_idx + 3] = wrist + np.array([offset_x, -0.05])

        return keypoints

    def _generate_open_palm_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成张开手掌关键点：所有手指伸展"""
        keypoints = np.zeros((21, 2))
        keypoints[0] = wrist

        # 拇指横向伸展
        keypoints[1] = wrist + np.array([-0.15, -0.1])
        keypoints[2] = wrist + np.array([-0.2, -0.15])
        keypoints[3] = wrist + np.array([-0.25, -0.18])
        keypoints[4] = wrist + np.array([-0.3, -0.2])

        # 其他手指向上伸展
        for i, offset_x in enumerate([-0.1, -0.05, 0.0, 0.05]):
            base_idx = 5 + i * 4
            keypoints[base_idx] = wrist + np.array([offset_x, -0.2])
            keypoints[base_idx + 1] = wrist + np.array([offset_x, -0.35])
            keypoints[base_idx + 2] = wrist + np.array([offset_x, -0.45])
            keypoints[base_idx + 3] = wrist + np.array([offset_x, -0.55])

        return keypoints

    def _generate_peace_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成剪刀手关键点：食指和中指伸展"""
        keypoints = self._generate_fist_keypoints(wrist)

        # 伸展食指
        keypoints[5] = wrist + np.array([-0.05, -0.2])
        keypoints[6] = wrist + np.array([-0.05, -0.35])
        keypoints[7] = wrist + np.array([-0.05, -0.45])
        keypoints[8] = wrist + np.array([-0.05, -0.55])

        # 伸展中指
        keypoints[9] = wrist + np.array([0.0, -0.2])
        keypoints[10] = wrist + np.array([0.0, -0.35])
        keypoints[11] = wrist + np.array([0.0, -0.45])
        keypoints[12] = wrist + np.array([0.0, -0.55])

        return keypoints

    def _generate_thumbs_up_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成竖大拇指关键点：只有拇指伸展"""
        keypoints = self._generate_fist_keypoints(wrist)

        # 伸展拇指
        keypoints[1] = wrist + np.array([-0.05, -0.15])
        keypoints[2] = wrist + np.array([-0.05, -0.3])
        keypoints[3] = wrist + np.array([-0.05, -0.45])
        keypoints[4] = wrist + np.array([-0.05, -0.6])

        return keypoints

    def _generate_pointing_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成指向关键点：只有食指伸展"""
        keypoints = self._generate_fist_keypoints(wrist)

        # 伸展食指
        keypoints[5] = wrist + np.array([-0.05, -0.2])
        keypoints[6] = wrist + np.array([-0.05, -0.35])
        keypoints[7] = wrist + np.array([-0.05, -0.45])
        keypoints[8] = wrist + np.array([-0.05, -0.55])

        return keypoints

    def _generate_ok_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成OK手势关键点：拇指和食指形成圆"""
        keypoints = self._generate_open_palm_keypoints(wrist)

        # 拇指和食指靠近形成圆
        center = wrist + np.array([-0.05, -0.2])
        keypoints[4] = center + np.array([-0.03, 0.0])  # 拇指尖
        keypoints[8] = center + np.array([0.03, 0.0])   # 食指尖

        return keypoints

    def _generate_random_keypoints(self, wrist: np.ndarray) -> np.ndarray:
        """生成随机关键点"""
        keypoints = np.zeros((21, 2))
        keypoints[0] = wrist

        for i in range(1, 21):
            keypoints[i] = wrist + np.array([
                np.random.uniform(-0.3, 0.3),
                np.random.uniform(-0.6, 0.0)
            ])

        return keypoints

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        获取单个样本

        Returns:
            Tuple[torch.Tensor, int]: (关键点特征, 手势标签)
        """
        sample = self.data[idx]

        # 关键点
        keypoints = np.array(sample["keypoints"], dtype=np.float32)

        # 提取特征（使用分类器中的特征提取器）
        from gesture_recognition.models.gesture_classifier import (
            KeypointFeatureExtractor,
        )

        features = KeypointFeatureExtractor.extract_features(keypoints)

        # 转换为tensor
        features_tensor = torch.from_numpy(features)
        label = sample["gesture"]

        # 应用变换
        if self.transform:
            features_tensor = self.transform(features_tensor)

        return features_tensor, label

    def get_dataloader(
        self,
        batch_size: int = 32,
        shuffle: bool = True,
        num_workers: int = 0,
    ) -> DataLoader:
        """
        获取DataLoader

        Args:
            batch_size: 批次大小
            shuffle: 是否打乱
            num_workers: 工作进程数
        """
        return DataLoader(
            self,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
        )


def create_synthetic_dataset(
    num_train: int = 1000,
    num_val: int = 200,
    batch_size: int = 32,
) -> Tuple[DataLoader, DataLoader]:
    """
    创建合成数据集的便捷函数

    Args:
        num_train: 训练样本数
        num_val: 验证样本数
        batch_size: 批次大小

    Returns:
        Tuple[DataLoader, DataLoader]: (训练集, 验证集)
    """
    train_dataset = HandDataset(num_samples=num_train, mode="train")
    val_dataset = HandDataset(num_samples=num_val, mode="val")

    train_loader = train_dataset.get_dataloader(batch_size=batch_size, shuffle=True)
    val_loader = val_dataset.get_dataloader(batch_size=batch_size, shuffle=False)

    return train_loader, val_loader
