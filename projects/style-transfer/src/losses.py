"""损失函数模块

风格迁移的核心是定义合适的损失函数：
1. 内容损失（Content Loss）：保持内容图像的语义信息
2. 风格损失（Style Loss）：提取并迁移风格图像的纹理特征
3. 全变分损失（Total Variation Loss）：使生成图像更平滑

总损失函数：
    L_total = α * L_content + β * L_style + γ * L_tv

其中 α, β, γ 是权重系数，控制各项的重要程度。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .gram_matrix import gram_matrix


class ContentLoss(nn.Module):
    """内容损失

    内容损失衡量生成图像与内容图像在高层特征上的差异。
    通常使用预训练 CNN 的高层特征（如 VGG 的 conv4_2）来提取内容信息。

    数学定义：
        L_content = 1/2 * Σ (F_content - F_generated)^2

    其中 F_content 和 F_generated 分别是内容图像和生成图像的特征图。

    直觉理解：
        - 高层特征包含图像的语义信息（如物体形状、布局）
        - 最小化内容损失意味着保留内容图像的"含义"
        - 不同层的特征捕捉不同级别的信息
    """

    def __init__(self, weight: float = 1.0):
        """初始化内容损失

        Args:
            weight: 损失权重
        """
        super().__init__()
        self.weight = weight
        self.target = None
        self.loss = 0.0

    def set_target(self, target: torch.Tensor) -> None:
        """设置目标特征（内容图像的特征）

        Args:
            target: 内容图像的特征图
        """
        self.target = target.detach()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """计算内容损失

        Args:
            input: 生成图像的特征图

        Returns:
            内容损失值
        """
        if self.target is None:
            raise ValueError("请先调用 set_target() 设置目标特征")

        self.loss = F.mse_loss(input, self.target) * self.weight
        return input

    def get_loss(self) -> torch.Tensor:
        """获取当前损失值"""
        return self.loss


class StyleLoss(nn.Module):
    """风格损失

    风格损失衡量生成图像与风格图像在纹理特征上的差异。
    通过比较 Gram 矩阵来捕捉风格信息。

    数学定义：
        L_style = 1/(4*N^2*M^2) * Σ (Gram(F_style) - Gram(F_generated))^2

    其中：
        - N 是通道数
        - M 是特征图的空间尺寸（H*W）
        - Gram(F) 是特征图 F 的 Gram 矩阵

    直觉理解：
        - Gram 矩阵编码了特征通道之间的相关性
        - 这些相关性对应于图像的纹理和风格
        - 不同层的 Gram 矩阵捕捉不同尺度的纹理
        - 最小化风格损失意味着匹配风格图像的"感觉"
    """

    def __init__(self, weight: float = 1.0):
        """初始化风格损失

        Args:
            weight: 损失权重
        """
        super().__init__()
        self.weight = weight
        self.target_gram = None
        self.loss = 0.0

    def set_target(self, target: torch.Tensor) -> None:
        """设置目标特征（风格图像的特征）

        Args:
            target: 风格图像的特征图
        """
        self.target_gram = gram_matrix(target, normalize=True).detach()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """计算风格损失

        Args:
            input: 生成图像的特征图

        Returns:
            风格损失值
        """
        if self.target_gram is None:
            raise ValueError("请先调用 set_target() 设置目标特征")

        input_gram = gram_matrix(input, normalize=True)
        self.loss = F.mse_loss(input_gram, self.target_gram) * self.weight
        return input

    def get_loss(self) -> torch.Tensor:
        """获取当前损失值"""
        return self.loss


class TotalVariationLoss(nn.Module):
    """全变分损失（Total Variation Loss）

    全变分损失用于平滑生成图像，减少噪声和伪影。
    它通过惩罚相邻像素之间的差异来实现。

    数学定义：
        L_tv = Σ |I(i,j) - I(i+1,j)| + |I(i,j) - I(i,j+1)|

    直觉理解：
        - 自然图像通常是平滑的，相邻像素值变化不大
        - 风格迁移可能产生噪声或伪影
        - 全变分损失鼓励图像的局部平滑性
        - 有助于生成更自然、更美观的结果
    """

    def __init__(self, weight: float = 1e-5):
        """初始化全变分损失

        Args:
            weight: 损失权重（通常很小）
        """
        super().__init__()
        self.weight = weight
        self.loss = 0.0

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        """计算全变分损失

        Args:
            input: 生成图像，shape 为 (batch_size, channels, height, width)

        Returns:
            全变分损失值
        """
        # 水平方向的差异
        horizontal_diff = torch.abs(input[:, :, :, :-1] - input[:, :, :, 1:])
        # 垂直方向的差异
        vertical_diff = torch.abs(input[:, :, :-1, :] - input[:, :, 1:, :])

        self.loss = (torch.mean(horizontal_diff) + torch.mean(vertical_diff)) * self.weight
        return input

    def get_loss(self) -> torch.Tensor:
        """获取当前损失值"""
        return self.loss


class StyleTransferLoss(nn.Module):
    """风格迁移总损失

    组合内容损失、风格损失和全变分损失的总损失函数。
    """

    def __init__(
        self,
        content_weight: float = 1.0,
        style_weight: float = 1e6,
        tv_weight: float = 1e-5,
    ):
        """初始化总损失

        Args:
            content_weight: 内容损失权重
            style_weight: 风格损失权重（通常较大）
            tv_weight: 全变分损失权重（通常很小）
        """
        super().__init__()
        self.content_weight = content_weight
        self.style_weight = style_weight
        self.tv_weight = tv_weight

        self.content_losses: list[ContentLoss] = []
        self.style_losses: list[StyleLoss] = []
        self.tv_loss = TotalVariationLoss(tv_weight)

    def add_content_loss(self, weight: float = 1.0) -> ContentLoss:
        """添加内容损失层"""
        loss = ContentLoss(weight)
        self.content_losses.append(loss)
        return loss

    def add_style_loss(self, weight: float = 1.0) -> StyleLoss:
        """添加风格损失层"""
        loss = StyleLoss(weight)
        self.style_losses.append(loss)
        return loss

    def get_total_loss(self) -> torch.Tensor:
        """计算总损失

        Returns:
            总损失值
        """
        total = torch.tensor(0.0)

        # 内容损失
        for loss in self.content_losses:
            total = total + loss.get_loss() * self.content_weight

        # 风格损失
        for loss in self.style_losses:
            total = total + loss.get_loss() * self.style_weight

        # 全变分损失
        total = total + self.tv_loss.get_loss()

        return total

    def get_loss_dict(self) -> dict[str, float]:
        """获取各项损失的字典

        Returns:
            包含各项损失值的字典
        """
        loss_dict = {
            "content_loss": sum(l.get_loss().item() for l in self.content_losses) * self.content_weight,
            "style_loss": sum(l.get_loss().item() for l in self.style_losses) * self.style_weight,
            "tv_loss": self.tv_loss.get_loss().item(),
        }
        loss_dict["total_loss"] = sum(loss_dict.values())
        return loss_dict
