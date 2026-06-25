"""
热力图回归损失函数 (Heatmap Regression Loss Functions).

姿态估计常用的损失函数:
1. MSE Loss: 均方误差，最基础的热力图回归损失
2. OKHMLoss: Online Hard Keypoint Mining，在线困难关键点挖掘
3. Bone Length Loss: 骨骼长度约束（可选）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional


class KeypointMSELoss(nn.Module):
    """
    关键点热力图均方误差损失。

    L = (1/K) * sum_k ||H_k - H_k^gt||^2

    其中:
    - H_k: 预测的第 k 个关键点热力图
    - H_k^gt: Ground Truth 热力图
    - K: 关键点数量

    Args:
        use_target_weight: 是否使用目标权重
        loss_weight: 损失权重系数
    """

    def __init__(self, use_target_weight: bool = True, loss_weight: float = 1.0):
        super().__init__()
        self.use_target_weight = use_target_weight
        self.loss_weight = loss_weight
        self.criterion = nn.MSELoss(reduction="mean")

    def forward(
        self,
        pred_heatmaps: torch.Tensor,
        target_heatmaps: torch.Tensor,
        target_weights: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        计算 MSE 损失。

        Args:
            pred_heatmaps: 预测热力图 (batch, K, H, W)
            target_heatmaps: 目标热力图 (batch, K, H, W)
            target_weights: 关键点权重 (batch, K)，1 表示可见，0 表示不可见

        Returns:
            包含 'loss' 和各分项损失的字典
        """
        batch_size, num_keypoints, h, w = pred_heatmaps.shape

        if self.use_target_weight and target_weights is not None:
            # 按关键点计算损失，应用权重
            # 展平空间维度
            pred_flat = pred_heatmaps.view(batch_size, num_keypoints, -1)
            target_flat = target_heatmaps.view(batch_size, num_keypoints, -1)

            # 计算每个关键点的 MSE
            mse_per_keypoint = ((pred_flat - target_flat) ** 2).mean(dim=2)  # (B, K)

            # 应用权重
            weighted_mse = mse_per_keypoint * target_weights  # (B, K)

            # 平均
            num_visible = target_weights.sum().clamp(min=1.0)
            loss = weighted_mse.sum() / num_visible
        else:
            loss = self.criterion(pred_heatmaps, target_heatmaps)

        return {
            "loss": loss * self.loss_weight,
            "mse_loss": loss.detach(),
        }


class KeypointOHKMLoss(nn.Module):
    """
    Online Hard Keypoint Mining (OHKM) 损失。

    只对损失最大的 Top-K 个关键点计算损失，
    忽略容易预测的关键点，专注于困难样本。

    Args:
        topk: 选择损失最大的 Top-K 个关键点
        use_target_weight: 是否使用目标权重
        loss_weight: 损失权重系数
    """

    def __init__(
        self,
        topk: int = 8,
        use_target_weight: bool = True,
        loss_weight: float = 1.0,
    ):
        super().__init__()
        self.topk = topk
        self.use_target_weight = use_target_weight
        self.loss_weight = loss_weight

    def forward(
        self,
        pred_heatmaps: torch.Tensor,
        target_heatmaps: torch.Tensor,
        target_weights: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        计算 OHKM 损失。

        Args:
            pred_heatmaps: 预测热力图 (batch, K, H, W)
            target_heatmaps: 目标热力图 (batch, K, H, W)
            target_weights: 关键点权重 (batch, K)

        Returns:
            包含损失的字典
        """
        batch_size, num_keypoints, h, w = pred_heatmaps.shape

        # 计算每个关键点的损失
        pred_flat = pred_heatmaps.view(batch_size, num_keypoints, -1)
        target_flat = target_heatmaps.view(batch_size, num_keypoints, -1)

        mse_per_keypoint = ((pred_flat - target_flat) ** 2).mean(dim=2)  # (B, K)

        # 应用目标权重
        if self.use_target_weight and target_weights is not None:
            mse_per_keypoint = mse_per_keypoint * target_weights

        # 选择 Top-K 困难关键点
        topk = min(self.topk, num_keypoints)
        topk_loss, _ = torch.topk(mse_per_keypoint, topk, dim=1)  # (B, topk)

        loss = topk_loss.mean()

        return {
            "loss": loss * self.loss_weight,
            "ohkm_loss": loss.detach(),
        }


class CombinedPoseLoss(nn.Module):
    """
    组合姿态估计损失。

    结合 MSE 损失和 OHKM 损失。

    Args:
        mse_weight: MSE 损失权重
        ohkm_weight: OHKM 损失权重
        ohkm_topk: OHKM 的 Top-K
        use_target_weight: 是否使用目标权重
    """

    def __init__(
        self,
        mse_weight: float = 1.0,
        ohkm_weight: float = 0.5,
        ohkm_topk: int = 8,
        use_target_weight: bool = True,
    ):
        super().__init__()
        self.mse_loss = KeypointMSELoss(use_target_weight, mse_weight)
        self.ohkm_loss = KeypointOHKMLoss(ohkm_topk, use_target_weight, ohkm_weight)

    def forward(
        self,
        pred_heatmaps: torch.Tensor,
        target_heatmaps: torch.Tensor,
        target_weights: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        计算组合损失。

        Args:
            pred_heatmaps: 预测热力图 (batch, K, H, W)
            target_heatmaps: 目标热力图 (batch, K, H, W)
            target_weights: 关键点权重 (batch, K)

        Returns:
            包含总损失和各分项损失的字典
        """
        mse_dict = self.mse_loss(pred_heatmaps, target_heatmaps, target_weights)
        ohkm_dict = self.ohkm_loss(pred_heatmaps, target_heatmaps, target_weights)

        total_loss = mse_dict["loss"] + ohkm_dict["loss"]

        return {
            "loss": total_loss,
            "mse_loss": mse_dict["mse_loss"],
            "ohkm_loss": ohkm_dict["ohkm_loss"],
        }
