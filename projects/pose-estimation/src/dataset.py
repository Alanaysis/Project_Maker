"""
数据集处理 (Dataset Handling).

提供合成数据集用于测试和开发，以及真实数据集的加载接口。

数据格式:
- 图像: (3, H, W) 张量
- 关键点: (K, 2) 归一化坐标
- 关键点权重: (K,) 可见性标记
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, Optional, List

from .keypoints import KEYPOINT_NAMES


class SyntheticPoseDataset(Dataset):
    """
    合成姿态估计数据集。

    生成带有随机姿态的合成数据，用于测试和快速原型。
    每个样本包含:
    - 随机颜色背景上的简笔画人形
    - 对应的关键点坐标和可见性

    Args:
        num_samples: 样本数量
        image_size: 图像尺寸 (H, W)
        heatmap_size: 热力图尺寸 (H, W)
        num_keypoints: 关键点数量
        sigma: 高斯热力图标准差
        transform: 数据增强变换
    """

    def __init__(
        self,
        num_samples: int = 100,
        image_size: Tuple[int, int] = (256, 256),
        heatmap_size: Tuple[int, int] = (64, 64),
        num_keypoints: int = 17,
        sigma: float = 2.0,
        transform=None,
    ):
        super().__init__()
        self.num_samples = num_samples
        self.image_size = image_size
        self.heatmap_size = heatmap_size
        self.num_keypoints = num_keypoints
        self.sigma = sigma
        self.transform = transform

        # 预生成所有样本
        self.data = self._generate_samples()

    def _generate_samples(self) -> list:
        """预生成所有合成样本。"""
        samples = []
        for _ in range(self.num_samples):
            sample = self._generate_single_pose()
            samples.append(sample)
        return samples

    def _generate_single_pose(self) -> dict:
        """
        生成单个合成姿态。

        创建一个简化的"火柴人"姿态:
        - 躯干为中心区域
        - 四肢从躯干延伸
        - 头部在顶部
        """
        h, w = self.image_size

        # 随机人体中心和尺寸
        center_x = np.random.uniform(0.3, 0.7)
        center_y = np.random.uniform(0.3, 0.6)
        body_scale = np.random.uniform(0.15, 0.3)  # 躯干长度比例

        # 生成关键点 (归一化坐标)
        keypoints = np.zeros((self.num_keypoints, 2), dtype=np.float32)
        weights = np.ones(self.num_keypoints, dtype=np.float32)

        if self.num_keypoints >= 17:
            # COCO 17 关键点
            # 头部
            keypoints[0] = [center_x, center_y - body_scale * 1.5]  # 鼻子
            keypoints[1] = [center_x - body_scale * 0.15, center_y - body_scale * 1.6]  # 左眼
            keypoints[2] = [center_x + body_scale * 0.15, center_y - body_scale * 1.6]  # 右眼
            keypoints[3] = [center_x - body_scale * 0.25, center_y - body_scale * 1.55]  # 左耳
            keypoints[4] = [center_x + body_scale * 0.25, center_y - body_scale * 1.55]  # 右耳

            # 肩膀
            shoulder_y = center_y - body_scale * 1.0
            keypoints[5] = [center_x - body_scale * 0.6, shoulder_y]  # 左肩
            keypoints[6] = [center_x + body_scale * 0.6, shoulder_y]  # 右肩

            # 肘部 (随机角度)
            l_elbow_angle = np.random.uniform(-0.3, 0.3)
            r_elbow_angle = np.random.uniform(-0.3, 0.3)
            keypoints[7] = [  # 左肘
                center_x - body_scale * 0.8 + l_elbow_angle * body_scale,
                shoulder_y + body_scale * 0.5,
            ]
            keypoints[8] = [  # 右肘
                center_x + body_scale * 0.8 + r_elbow_angle * body_scale,
                shoulder_y + body_scale * 0.5,
            ]

            # 手腕
            l_wrist_angle = np.random.uniform(-0.3, 0.3)
            r_wrist_angle = np.random.uniform(-0.3, 0.3)
            keypoints[9] = [  # 左腕
                keypoints[7, 0] + l_wrist_angle * body_scale,
                keypoints[7, 1] + body_scale * 0.4,
            ]
            keypoints[10] = [  # 右腕
                keypoints[8, 0] + r_wrist_angle * body_scale,
                keypoints[8, 1] + body_scale * 0.4,
            ]

            # 髋部
            hip_y = center_y + body_scale * 0.2
            keypoints[11] = [center_x - body_scale * 0.3, hip_y]  # 左髋
            keypoints[12] = [center_x + body_scale * 0.3, hip_y]  # 右髋

            # 膝盖
            l_knee_angle = np.random.uniform(-0.1, 0.1)
            r_knee_angle = np.random.uniform(-0.1, 0.1)
            keypoints[13] = [  # 左膝
                center_x - body_scale * 0.3 + l_knee_angle * body_scale,
                hip_y + body_scale * 0.6,
            ]
            keypoints[14] = [  # 右膝
                center_x + body_scale * 0.3 + r_knee_angle * body_scale,
                hip_y + body_scale * 0.6,
            ]

            # 脚踝
            l_ankle_angle = np.random.uniform(-0.1, 0.1)
            r_ankle_angle = np.random.uniform(-0.1, 0.1)
            keypoints[15] = [  # 左踝
                keypoints[13, 0] + l_ankle_angle * body_scale,
                keypoints[13, 1] + body_scale * 0.6,
            ]
            keypoints[16] = [  # 右踝
                keypoints[14, 0] + r_ankle_angle * body_scale,
                keypoints[14, 1] + body_scale * 0.6,
            ]

        # 随机遮挡部分关键点
        num_occluded = np.random.randint(0, 5)
        occluded_indices = np.random.choice(self.num_keypoints, num_occluded, replace=False)
        weights[occluded_indices] = 0.0

        # 裁剪到 [0, 1] 范围
        keypoints = np.clip(keypoints, 0.0, 1.0)

        return {
            "keypoints": keypoints,
            "weights": weights,
        }

    def _draw_person(self, keypoints: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """
        在图像上绘制简笔画人形。

        Args:
            keypoints: (K, 2) 归一化坐标
            weights: (K,) 可见性

        Returns:
            图像 (H, W, 3) uint8
        """
        h, w = self.image_size
        img = np.random.randint(20, 60, (h, w, 3), dtype=np.uint8)

        # 随机背景颜色
        bg_color = np.random.randint(0, 100, 3)
        img[:, :] = bg_color

        # 绘制关键点
        kp_color = (0, 255, 0)  # 绿色
        for k in range(self.num_keypoints):
            if weights[k] > 0:
                px = int(keypoints[k, 0] * (w - 1))
                py = int(keypoints[k, 1] * (h - 1))
                px = max(0, min(w - 1, px))
                py = max(0, min(h - 1, py))
                # 画圆点
                cv2_available = False
                try:
                    import cv2
                    cv2.circle(img, (px, py), 3, kp_color, -1)
                    cv2_available = True
                except ImportError:
                    pass

                if not cv2_available:
                    # 纯 numpy 绘制
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            ny, nx = py + dy, px + dx
                            if 0 <= ny < h and 0 <= nx < w:
                                img[ny, nx] = kp_color

        # 绘制骨骼连线
        from .keypoints import SKELETON_CONNECTIONS
        line_color = (255, 200, 0)  # 黄色
        for (i, j) in SKELETON_CONNECTIONS:
            if i < self.num_keypoints and j < self.num_keypoints:
                if weights[i] > 0 and weights[j] > 0:
                    x1 = int(keypoints[i, 0] * (w - 1))
                    y1 = int(keypoints[i, 1] * (h - 1))
                    x2 = int(keypoints[j, 0] * (w - 1))
                    y2 = int(keypoints[j, 1] * (h - 1))

                    try:
                        import cv2
                        cv2.line(img, (x1, y1), (x2, y2), line_color, 1)
                    except ImportError:
                        # 简单的 Bresenham 画线
                        self._draw_line_numpy(img, x1, y1, x2, y2, line_color)

        return img

    @staticmethod
    def _draw_line_numpy(
        img: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple
    ):
        """使用 numpy 绘制简单直线。"""
        h, w = img.shape[:2]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steps = max(dx, dy)
        if steps == 0:
            return

        for t in range(steps + 1):
            x = int(x1 + (x2 - x1) * t / steps)
            y = int(y1 + (y2 - y1) * t / steps)
            if 0 <= x < w and 0 <= y < h:
                img[y, x] = color

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> dict:
        """
        获取单个样本。

        Returns:
            {
                "image": (3, H, W) float32 张量 [0, 1],
                "keypoints": (K, 2) float32 归一化坐标,
                "weights": (K,) float32 可见性,
                "heatmaps": (K, H', W') float32 热力图,
            }
        """
        sample = self.data[idx]
        keypoints = sample["keypoints"]
        weights = sample["weights"]

        # 生成图像
        img = self._draw_person(keypoints, weights)

        # 转换为张量并归一化
        img_tensor = torch.from_numpy(img).float().permute(2, 0, 1) / 255.0
        kp_tensor = torch.from_numpy(keypoints).float()
        weight_tensor = torch.from_numpy(weights).float()

        # 生成热力图
        from .heatmap import generate_heatmaps
        heatmaps = generate_heatmaps(
            kp_tensor.unsqueeze(0),
            weight_tensor.unsqueeze(0),
            self.heatmap_size,
            self.sigma,
        ).squeeze(0)

        result = {
            "image": img_tensor,
            "keypoints": kp_tensor,
            "weights": weight_tensor,
            "heatmaps": heatmaps,
        }

        if self.transform:
            result = self.transform(result)

        return result


def create_dataloader(
    dataset: Dataset,
    batch_size: int = 16,
    shuffle: bool = True,
    num_workers: int = 0,
) -> DataLoader:
    """
    创建数据加载器。

    Args:
        dataset: 数据集
        batch_size: 批大小
        shuffle: 是否打乱
        num_workers: 工作进程数

    Returns:
        DataLoader 实例
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
    )
