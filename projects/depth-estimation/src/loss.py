"""
深度估计损失函数

实现多种深度估计常用的损失函数:
- MSE Loss: 均方误差
- MAE Loss: 平均绝对误差
- SILog Loss: 尺度不变对数损失
- Gradient Loss: 梯度损失（边缘保持）
- Combined Loss: 组合损失
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional


class DepthMSELoss(nn.Module):
    """
    深度估计均方误差损失

    L = mean((pred - target)^2)

    Args:
        mask: 是否使用有效像素掩码
        normalize: 是否归一化深度值

    Example:
        >>> criterion = DepthMSELoss()
        >>> pred = torch.randn(2, 1, 64, 64)
        >>> target = torch.rand(2, 1, 64, 64)
        >>> loss = criterion(pred, target)
    """

    def __init__(self, mask: bool = False, normalize: bool = False):
        super().__init__()
        self.mask = mask
        self.normalize = normalize

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        计算 MSE 损失

        Args:
            pred: 预测深度图 (B, 1, H, W)
            target: 目标深度图 (B, 1, H, W)
            valid_mask: 有效像素掩码 (B, 1, H, W)，可选

        Returns:
            MSE 损失标量
        """
        if self.normalize:
            pred = self._normalize(pred)
            target = self._normalize(target)

        diff = (pred - target) ** 2

        if valid_mask is not None:
            diff = diff * valid_mask
            return diff.sum() / (valid_mask.sum() + 1e-8)

        return diff.mean()

    def _normalize(self, x: torch.Tensor) -> torch.Tensor:
        """归一化到 [0, 1]"""
        min_val = x.min()
        max_val = x.max()
        return (x - min_val) / (max_val - min_val + 1e-8)


class DepthMAELoss(nn.Module):
    """
    深度估计平均绝对误差损失

    L = mean(|pred - target|)

    Args:
        mask: 是否使用有效像素掩码

    Example:
        >>> criterion = DepthMAELoss()
        >>> pred = torch.randn(2, 1, 64, 64)
        >>> target = torch.rand(2, 1, 64, 64)
        >>> loss = criterion(pred, target)
    """

    def __init__(self):
        super().__init__()

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        计算 MAE 损失

        Args:
            pred: 预测深度图 (B, 1, H, W)
            target: 目标深度图 (B, 1, H, W)
            valid_mask: 有效像素掩码 (B, 1, H, W)，可选

        Returns:
            MAE 损失标量
        """
        diff = torch.abs(pred - target)

        if valid_mask is not None:
            diff = diff * valid_mask
            return diff.sum() / (valid_mask.sum() + 1e-8)

        return diff.mean()


class SILogLoss(nn.Module):
    """
    尺度不变对数损失 (Scale-Invariant Logarithmic Loss)

    L = (1/n) * sum(d_i^2) - (lambda/n^2) * (sum(d_i))^2

    其中 d_i = log(pred_i) - log(target_i)

    这是 Eigen et al. 提出的深度估计标准损失函数，
    对深度的绝对尺度不敏感。

    Args:
        lambda_weight: 正则化权重 (默认 0.5)
        min_depth: 最小深度值，防止 log(0)

    Reference:
        Eigen, D., Puhrsch, C., & Fergus, R. (2014).
        Depth Map Prediction from a Single Image using a Multi-Scale Deep Network.

    Example:
        >>> criterion = SILogLoss()
        >>> pred = torch.rand(2, 1, 64, 64) * 10 + 0.1
        >>> target = torch.rand(2, 1, 64, 64) * 10 + 0.1
        >>> loss = criterion(pred, target)
    """

    def __init__(self, lambda_weight: float = 0.5, min_depth: float = 1e-3):
        super().__init__()
        self.lambda_weight = lambda_weight
        self.min_depth = min_depth

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        计算 SILog 损失

        Args:
            pred: 预测深度图 (B, 1, H, W)
            target: 目标深度图 (B, 1, H, W)
            valid_mask: 有效像素掩码 (B, 1, H, W)，可选

        Returns:
            SILog 损失标量
        """
        # 确保深度值为正
        pred = torch.clamp(pred, min=self.min_depth)
        target = torch.clamp(target, min=self.min_depth)

        # 计算对数差
        log_diff = torch.log(pred) - torch.log(target)

        if valid_mask is not None:
            log_diff = log_diff * valid_mask
            n = valid_mask.sum() + 1e-8
        else:
            n = log_diff.numel()

        # SILog 损失
        first_term = (log_diff ** 2).sum() / n
        second_term = self.lambda_weight * (log_diff.sum() ** 2) / (n ** 2)

        return first_term - second_term


class GradientLoss(nn.Module):
    """
    梯度损失 (边缘保持)

    计算预测深度图与目标深度图在 x 和 y 方向的梯度差异，
    鼓励预测深度图保持边缘锐利。

    L = mean(|grad_x(pred) - grad_x(target)| + |grad_y(pred) - grad_y(target)|)

    Args:
        weight_x: x 方向梯度权重
        weight_y: y 方向梯度权重

    Example:
        >>> criterion = GradientLoss()
        >>> pred = torch.randn(2, 1, 64, 64)
        >>> target = torch.rand(2, 1, 64, 64)
        >>> loss = criterion(pred, target)
    """

    def __init__(self, weight_x: float = 1.0, weight_y: float = 1.0):
        super().__init__()
        self.weight_x = weight_x
        self.weight_y = weight_y

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        计算梯度损失

        Args:
            pred: 预测深度图 (B, 1, H, W)
            target: 目标深度图 (B, 1, H, W)
            valid_mask: 有效像素掩码，可选

        Returns:
            梯度损失标量
        """
        # 计算 x 方向梯度 (水平)
        pred_dx = pred[:, :, :, 1:] - pred[:, :, :, :-1]
        target_dx = target[:, :, :, 1:] - target[:, :, :, :-1]

        # 计算 y 方向梯度 (垂直)
        pred_dy = pred[:, :, 1:, :] - pred[:, :, :-1, :]
        target_dy = target[:, :, 1:, :] - target[:, :, :-1, :]

        # 梯度差异
        loss_x = torch.abs(pred_dx - target_dx)
        loss_y = torch.abs(pred_dy - target_dy)

        if valid_mask is not None:
            mask_x = valid_mask[:, :, :, 1:] * valid_mask[:, :, :, :-1]
            mask_y = valid_mask[:, :, 1:, :] * valid_mask[:, :, :-1, :]

            loss_x = loss_x * mask_x
            loss_y = loss_y * mask_y

            loss = (
                self.weight_x * loss_x.sum() / (mask_x.sum() + 1e-8)
                + self.weight_y * loss_y.sum() / (mask_y.sum() + 1e-8)
            )
        else:
            loss = self.weight_x * loss_x.mean() + self.weight_y * loss_y.mean()

        return loss


class CombinedDepthLoss(nn.Module):
    """
    组合深度估计损失

    将多种损失函数加权组合:
    L = w1 * MSE + w2 * MAE + w3 * SILog + w4 * Gradient

    Args:
        mse_weight: MSE 损失权重
        mae_weight: MAE 损失权重
        silog_weight: SILog 损失权重
        gradient_weight: 梯度损失权重
        lambda_silog: SILog 正则化权重
        min_depth: 最小深度值

    Example:
        >>> criterion = CombinedDepthLoss()
        >>> pred = torch.rand(2, 1, 64, 64) * 10 + 0.1
        >>> target = torch.rand(2, 1, 64, 64) * 10 + 0.1
        >>> loss = criterion(pred, target)
    """

    def __init__(
        self,
        mse_weight: float = 1.0,
        mae_weight: float = 0.5,
        silog_weight: float = 1.0,
        gradient_weight: float = 0.5,
        lambda_silog: float = 0.5,
        min_depth: float = 1e-3,
    ):
        super().__init__()
        self.mse_weight = mse_weight
        self.mae_weight = mae_weight
        self.silog_weight = silog_weight
        self.gradient_weight = gradient_weight

        self.mse_loss = DepthMSELoss()
        self.mae_loss = DepthMAELoss()
        self.silog_loss = SILogLoss(lambda_weight=lambda_silog, min_depth=min_depth)
        self.gradient_loss = GradientLoss()

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        计算组合损失

        Args:
            pred: 预测深度图 (B, 1, H, W)
            target: 目标深度图 (B, 1, H, W)
            valid_mask: 有效像素掩码，可选

        Returns:
            包含各项损失和总损失的字典
        """
        loss_mse = self.mse_loss(pred, target, valid_mask)
        loss_mae = self.mae_loss(pred, target, valid_mask)
        loss_silog = self.silog_loss(pred, target, valid_mask)
        loss_gradient = self.gradient_loss(pred, target, valid_mask)

        total_loss = (
            self.mse_weight * loss_mse
            + self.mae_weight * loss_mae
            + self.silog_weight * loss_silog
            + self.gradient_weight * loss_gradient
        )

        return {
            "total": total_loss,
            "mse": loss_mse,
            "mae": loss_mae,
            "silog": loss_silog,
            "gradient": loss_gradient,
        }


class BerHuLoss(nn.Module):
    """
    BerHu 损失 (Reverse Huber Loss)

    当误差小于阈值 c 时使用 L1 损失，否则使用 L2 损失。
    阈值 c 由当前 batch 的误差分布自适应确定。

    L = |e|, if |e| <= c
    L = (e^2 + c^2) / (2*c), otherwise

    其中 c = max(|e|) / 5

    Args:
        threshold_ratio: 阈值比例 (默认 0.2)

    Reference:
        Laina, I., et al. (2016).
        Deeper Depth Prediction with Fully Convolutional Residual Networks.

    Example:
        >>> criterion = BerHuLoss()
        >>> pred = torch.randn(2, 1, 64, 64)
        >>> target = torch.rand(2, 1, 64, 64)
        >>> loss = criterion(pred, target)
    """

    def __init__(self, threshold_ratio: float = 0.2):
        super().__init__()
        self.threshold_ratio = threshold_ratio

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        计算 BerHu 损失

        Args:
            pred: 预测深度图
            target: 目标深度图
            valid_mask: 有效像素掩码，可选

        Returns:
            BerHu 损失标量
        """
        diff = torch.abs(pred - target)

        if valid_mask is not None:
            diff_masked = diff[valid_mask > 0]
        else:
            diff_masked = diff.reshape(-1)

        # 自适应阈值
        c = self.threshold_ratio * diff_masked.max()

        # BerHu 损失
        loss = torch.where(
            diff <= c,
            diff,
            (diff ** 2 + c ** 2) / (2 * c),
        )

        if valid_mask is not None:
            loss = loss * valid_mask
            return loss.sum() / (valid_mask.sum() + 1e-8)

        return loss.mean()
