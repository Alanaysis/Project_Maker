"""风格迁移核心实现

本模块实现了基于 VGG 网络的神经风格迁移算法。

算法流程：
1. 使用预训练 VGG 网络作为特征提取器
2. 从内容图像提取内容特征（高层特征）
3. 从风格图像提取风格特征（多层 Gram 矩阵）
4. 初始化生成图像（通常使用内容图像 + 噪声）
5. 通过优化生成图像来最小化总损失

核心思想：
    内容特征在 CNN 的高层（如 conv4_2）中编码语义信息
    风格特征通过各层的 Gram 矩阵编码纹理信息
    通过优化生成图像，使其同时匹配内容和风格
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from typing import Optional, Callable

from .losses import ContentLoss, StyleLoss, TotalVariationLoss
from .gram_matrix import gram_matrix


# VGG19 的层名称映射
VGG_LAYERS = {
    "conv1_1": 0, "relu1_1": 1, "conv1_2": 2, "relu1_2": 3,
    "pool1": 4,
    "conv2_1": 5, "relu2_1": 6, "conv2_2": 7, "relu2_2": 8,
    "pool2": 9,
    "conv3_1": 10, "relu3_1": 11, "conv3_2": 12, "relu3_2": 13,
    "conv3_3": 14, "relu3_3": 15, "conv3_4": 16, "relu3_4": 17,
    "pool3": 18,
    "conv4_1": 19, "relu4_1": 20, "conv4_2": 21, "relu4_2": 22,
    "conv4_3": 23, "relu4_3": 24, "conv4_4": 25, "relu4_4": 26,
    "pool4": 27,
    "conv5_1": 28, "relu5_1": 29, "conv5_2": 30, "relu5_2": 31,
    "conv5_3": 32, "relu5_3": 33, "conv5_4": 34, "relu5_4": 35,
    "pool5": 36,
}


class StyleTransfer:
    """神经风格迁移

    实现基于 VGG19 的 Gatys 风格迁移算法。

    示例：
        >>> from src import StyleTransfer, load_image, save_image
        >>>
        >>> # 加载图像
        >>> content = load_image("content.jpg", size=512)
        >>> style = load_image("style.jpg", size=512)
        >>>
        >>> # 创建风格迁移器
        >>> transfer = StyleTransfer(
        ...     content_layers=["conv4_2"],
        ...     style_layers=["conv1_1", "conv2_1", "conv3_1", "conv4_1", "conv5_1"],
        ...     content_weight=1.0,
        ...     style_weight=1e6,
        ... )
        >>>
        >>> # 执行风格迁移
        >>> output = transfer.transfer(
        ...     content_image=content,
        ...     style_image=style,
        ...     num_steps=300,
        ... )
        >>>
        >>> # 保存结果
        >>> save_image(output, "output.jpg")
    """

    def __init__(
        self,
        content_layers: Optional[list[str]] = None,
        style_layers: Optional[list[str]] = None,
        content_weight: float = 1.0,
        style_weight: float = 1e6,
        tv_weight: float = 1e-5,
        device: str = "auto",
    ):
        """初始化风格迁移器

        Args:
            content_layers: 用于内容提取的层名称列表
            style_layers: 用于风格提取的层名称列表
            content_weight: 内容损失权重
            style_weight: 风格损失权重
            tv_weight: 全变分损失权重
            device: 计算设备
        """
        # 默认层设置
        if content_layers is None:
            content_layers = ["conv4_2"]
        if style_layers is None:
            style_layers = ["conv1_1", "conv2_1", "conv3_1", "conv4_1", "conv5_1"]

        self.content_layers = content_layers
        self.style_layers = style_layers
        self.content_weight = content_weight
        self.style_weight = style_weight
        self.tv_weight = tv_weight

        # 设备设置
        if device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        # 加载 VGG19 模型
        self.vgg = self._load_vgg()

        # 损失函数
        self.content_losses: list[ContentLoss] = []
        self.style_losses: list[StyleLoss] = []
        self.tv_loss = TotalVariationLoss(tv_weight)

        # 构建模型
        self.model = self._build_model()

    def _load_vgg(self) -> nn.Module:
        """加载预训练 VGG19 模型

        Returns:
            VGG19 模型（只保留特征提取部分）
        """
        vgg = models.vgg19(pretrained=True).features

        # 冻结所有参数
        for param in vgg.parameters():
            param.requires_grad_(False)

        return vgg.to(self.device).eval()

    def _build_model(self) -> nn.Sequential:
        """构建风格迁移模型

        在 VGG19 的适当位置插入内容损失和风格损失层。

        Returns:
            包含损失层的模型
        """
        model = nn.Sequential()

        content_layer_indices = [VGG_LAYERS[name] for name in self.content_layers]
        style_layer_indices = [VGG_LAYERS[name] for name in self.style_layers]

        # 添加损失层
        content_loss_idx = 0
        style_loss_idx = 0

        for i, layer in enumerate(self.vgg.children()):
            model.add_module(str(i), layer)

            # 在指定层后插入内容损失
            if i in content_layer_indices:
                content_loss = ContentLoss(weight=self.content_weight)
                model.add_module(f"content_loss_{content_loss_idx}", content_loss)
                self.content_losses.append(content_loss)
                content_loss_idx += 1

            # 在指定层后插入风格损失
            if i in style_layer_indices:
                style_loss = StyleLoss(weight=self.style_weight)
                model.add_module(f"style_loss_{style_loss_idx}", style_loss)
                self.style_losses.append(style_loss)
                style_loss_idx += 1

        # 截断模型：只保留到最后一个损失层
        last_loss_idx = 0
        for i, (name, _) in enumerate(model.named_children()):
            if "content_loss" in name or "style_loss" in name:
                last_loss_idx = i

        # 创建截断后的模型
        truncated_model = nn.Sequential()
        for i, (name, layer) in enumerate(model.named_children()):
            truncated_model.add_module(name, layer)
            if i == last_loss_idx:
                break

        return truncated_model

    def _set_targets(self, content_image: torch.Tensor, style_image: torch.Tensor) -> None:
        """设置内容和风格目标

        Args:
            content_image: 内容图像
            style_image: 风格图像
        """
        # 设置内容目标
        content_idx = 0
        x = content_image
        for layer in self.model.children():
            x = layer(x)
            if isinstance(layer, ContentLoss):
                self.content_losses[content_idx].set_target(x)
                content_idx += 1

        # 设置风格目标
        style_idx = 0
        x = style_image
        for layer in self.model.children():
            x = layer(x)
            if isinstance(layer, StyleLoss):
                self.style_losses[style_idx].set_target(x)
                style_idx += 1

    def transfer(
        self,
        content_image: torch.Tensor,
        style_image: torch.Tensor,
        num_steps: int = 300,
        optimizer_type: str = "lbfgs",
        learning_rate: float = 1.0,
        init_method: str = "content",
        noise_ratio: float = 0.6,
        callback: Optional[Callable[[int, dict[str, float]], None]] = None,
    ) -> torch.Tensor:
        """执行风格迁移

        Args:
            content_image: 内容图像张量
            style_image: 风格图像张量
            num_steps: 优化迭代次数
            optimizer_type: 优化器类型（lbfgs/adam）
            learning_rate: 学习率
            init_method: 初始化方法（content/noise/random）
            noise_ratio: 噪声比例（当 init_method="noise" 时使用）
            callback: 回调函数，每步调用，参数为 (step, loss_dict)

        Returns:
            生成的图像张量
        """
        # 确保图像在正确设备上
        content_image = content_image.to(self.device)
        style_image = style_image.to(self.device)

        # 设置目标特征
        self._set_targets(content_image, style_image)

        # 初始化生成图像
        if init_method == "content":
            generated = content_image.clone().requires_grad_(True)
        elif init_method == "noise":
            generated = (content_image * (1 - noise_ratio) +
                        torch.randn_like(content_image) * noise_ratio)
            generated = generated.requires_grad_(True)
        elif init_method == "random":
            generated = torch.randn_like(content_image).requires_grad_(True)
        else:
            raise ValueError(f"未知的初始化方法: {init_method}")

        # 设置优化器
        if optimizer_type == "lbfgs":
            optimizer = optim.LBFGS([generated], lr=learning_rate)
        elif optimizer_type == "adam":
            optimizer = optim.Adam([generated], lr=learning_rate)
        else:
            raise ValueError(f"未知的优化器类型: {optimizer_type}")

        # 优化循环
        step = [0]  # 使用列表以便在闭包中修改

        def closure():
            """优化器的闭包函数"""
            # 清零梯度
            optimizer.zero_grad()

            # 前向传播（触发损失计算）
            self.model(generated)

            # 计算全变分损失
            self.tv_loss(generated)

            # 计算总损失
            total_loss = torch.tensor(0.0, device=self.device)
            for loss in self.content_losses:
                total_loss = total_loss + loss.get_loss()
            for loss in self.style_losses:
                total_loss = total_loss + loss.get_loss()
            total_loss = total_loss + self.tv_loss.get_loss()

            # 反向传播
            total_loss.backward()

            # 回调函数
            step[0] += 1
            if callback and step[0] % 10 == 0:
                loss_dict = {
                    "step": step[0],
                    "total_loss": total_loss.item(),
                    "content_loss": sum(l.get_loss().item() for l in self.content_losses),
                    "style_loss": sum(l.get_loss().item() for l in self.style_losses),
                    "tv_loss": self.tv_loss.get_loss().item(),
                }
                callback(step[0], loss_dict)

            return total_loss

        # 执行优化
        for i in range(num_steps):
            if optimizer_type == "lbfgs":
                optimizer.step(closure)
            else:
                closure()
                optimizer.step()

            # 限制图像值范围
            with torch.no_grad():
                generated.clamp_(-2.5, 2.5)

        return generated.detach()

    def get_loss_summary(self) -> dict[str, float]:
        """获取损失摘要

        Returns:
            包含各项损失值的字典
        """
        return {
            "content_loss": sum(l.get_loss().item() for l in self.content_losses),
            "style_loss": sum(l.get_loss().item() for l in self.style_losses),
            "tv_loss": self.tv_loss.get_loss().item(),
        }
