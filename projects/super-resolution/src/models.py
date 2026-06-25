"""
超分辨率模型实现

实现 SRCNN 和 ESPCN 两种经典超分辨率模型
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SRCNN(nn.Module):
    """
    SRCNN（超分辨率卷积神经网络）

    由 Dong 等人在 2014 年提出，是第一个使用深度学习进行超分辨率的方法。

    架构：
    1. 特征提取层：提取低分辨率图像的特征
    2. 非线性映射层：将特征映射到高分辨率空间
    3. 重建层：生成最终的高分辨率图像

    特点：
    - 先使用插值方法上采样，再使用CNN处理
    - 三层卷积网络
    - 简单但有效

    Args:
        num_channels (int): 输入图像通道数，默认 3（RGB）
        num_features (int): 特征提取层输出通道数，默认 64
        hidden_features (int): 隐藏层通道数，默认 32
    """

    def __init__(self, num_channels=3, num_features=64, hidden_features=32):
        super(SRCNN, self).__init__()

        # 特征提取层
        # 使用 9x9 卷积核提取局部特征
        self.feature_extraction = nn.Sequential(
            nn.Conv2d(num_channels, num_features, kernel_size=9, padding=4),
            nn.ReLU(inplace=True)
        )

        # 非线性映射层
        # 使用 1x1 卷积进行特征映射
        self.non_linear_mapping = nn.Sequential(
            nn.Conv2d(num_features, hidden_features, kernel_size=1),
            nn.ReLU(inplace=True)
        )

        # 重建层
        # 使用 5x5 卷积重建高分辨率图像
        self.reconstruction = nn.Conv2d(hidden_features, num_channels, kernel_size=5, padding=2)

    def forward(self, x):
        """
        前向传播

        Args:
            x (torch.Tensor): 低分辨率图像，形状 [B, C, H, W]

        Returns:
            torch.Tensor: 高分辨率图像，形状 [B, C, H, W]
        """
        # 特征提取
        features = self.feature_extraction(x)

        # 非线性映射
        mapped = self.non_linear_mapping(features)

        # 重建
        output = self.reconstruction(mapped)

        return output


class PixelShuffle(nn.Module):
    """
    像素重排（Pixel Shuffle）

    将特征图的通道维度重新排列到空间维度，实现上采样。

    例如：将 [B, C*r^2, H, W] 重排为 [B, C, H*r, W*r]

    这是 ESPCN 的核心组件，比传统的插值方法更高效。

    Args:
        scale_factor (int): 上采样因子
    """

    def __init__(self, scale_factor):
        super(PixelShuffle, self).__init__()
        self.scale_factor = scale_factor

    def forward(self, x):
        """
        前向传播

        Args:
            x (torch.Tensor): 输入特征图，形状 [B, C*r^2, H, W]

        Returns:
            torch.Tensor: 上采样后的特征图，形状 [B, C, H*r, W*r]
        """
        return F.pixel_shuffle(x, self.scale_factor)


class ESPCN(nn.Module):
    """
    ESPCN（高效亚像素卷积神经网络）

    由 Shi 等人在 2016 年提出，使用亚像素卷积实现高效上采样。

    架构：
    1. 特征提取层：在低分辨率空间提取特征
    2. 特征映射层：增加通道数以支持上采样
    3. 亚像素卷积层：使用 Pixel Shuffle 进行上采样

    特点：
    - 在低分辨率空间提取特征（计算效率高）
    - 使用亚像素卷积（Pixel Shuffle）
    - 实时处理能力
    - 参数量少

    Args:
        scale_factor (int): 上采样因子，默认 2
        num_channels (int): 输入图像通道数，默认 3（RGB）
        num_features (int): 特征通道数，默认 64
    """

    def __init__(self, scale_factor=2, num_channels=3, num_features=64):
        super(ESPCN, self).__init__()

        self.scale_factor = scale_factor

        # 特征提取层
        # 使用 5x5 卷积核提取特征
        self.feature_extraction = nn.Sequential(
            nn.Conv2d(num_channels, num_features, kernel_size=5, padding=2),
            nn.Tanh()
        )

        # 特征映射层
        # 增加通道数以支持上采样
        self.feature_mapping = nn.Sequential(
            nn.Conv2d(num_features, num_features, kernel_size=3, padding=1),
            nn.Tanh()
        )

        # 亚像素卷积层
        # 输出通道数 = num_channels * scale_factor^2
        self.sub_pixel = nn.Conv2d(
            num_features,
            num_channels * scale_factor * scale_factor,
            kernel_size=3,
            padding=1
        )

        # 像素重排
        self.pixel_shuffle = PixelShuffle(scale_factor)

    def forward(self, x):
        """
        前向传播

        Args:
            x (torch.Tensor): 低分辨率图像，形状 [B, C, H, W]

        Returns:
            torch.Tensor: 高分辨率图像，形状 [B, C, H*scale, W*scale]
        """
        # 特征提取
        features = self.feature_extraction(x)

        # 特征映射
        mapped = self.feature_mapping(features)

        # 亚像素卷积
        sub_pixel_features = self.sub_pixel(mapped)

        # 像素重排实现上采样
        output = self.pixel_shuffle(sub_pixel_features)

        return output


class ResidualBlock(nn.Module):
    """
    残差块

    用于构建更深的超分辨率网络（如 EDSR）。

    Args:
        num_features (int): 特征通道数
    """

    def __init__(self, num_features):
        super(ResidualBlock, self).__init__()

        self.conv1 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)

    def forward(self, x):
        """
        前向传播

        Args:
            x (torch.Tensor): 输入特征图

        Returns:
            torch.Tensor: 输出特征图（带残差连接）
        """
        residual = x
        out = self.relu(self.conv1(x))
        out = self.conv2(out)
        out = out + residual
        return out


class EDSR(nn.Module):
    """
    EDSR（增强深度超分辨率网络）

    由 Lim 等人在 2017 年提出，使用残差网络进行超分辨率。

    特点：
    - 使用残差块构建深层网络
    - 去除批归一化层
    - 使用残差缩放

    Args:
        scale_factor (int): 上采样因子，默认 2
        num_channels (int): 输入图像通道数，默认 3
        num_features (int): 特征通道数，默认 64
        num_blocks (int): 残差块数量，默认 16
    """

    def __init__(self, scale_factor=2, num_channels=3, num_features=64, num_blocks=16):
        super(EDSR, self).__init__()

        self.scale_factor = scale_factor

        # 浅层特征提取
        self.shallow_feature = nn.Conv2d(num_channels, num_features, kernel_size=3, padding=1)

        # 深层特征提取（残差块）
        self.deep_feature = nn.Sequential(
            *[ResidualBlock(num_features) for _ in range(num_blocks)]
        )

        # 上采样模块
        self.upsample = nn.Sequential(
            nn.Conv2d(num_features, num_features * scale_factor * scale_factor, kernel_size=3, padding=1),
            PixelShuffle(scale_factor)
        )

        # 重建层
        self.reconstruction = nn.Conv2d(num_features, num_channels, kernel_size=3, padding=1)

    def forward(self, x):
        """
        前向传播

        Args:
            x (torch.Tensor): 低分辨率图像

        Returns:
            torch.Tensor: 高分辨率图像
        """
        # 浅层特征提取
        shallow = self.shallow_feature(x)

        # 深层特征提取
        deep = self.deep_feature(shallow)

        # 上采样
        upsampled = self.upsample(deep + shallow)

        # 重建
        output = self.reconstruction(upsampled)

        return output


def get_model(model_name, **kwargs):
    """
    获取模型实例

    Args:
        model_name (str): 模型名称，可选 'srcnn', 'espcn', 'edsr'
        **kwargs: 模型参数

    Returns:
        nn.Module: 模型实例
    """
    models = {
        'srcnn': SRCNN,
        'espcn': ESPCN,
        'edsr': EDSR
    }

    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}. Choose from {list(models.keys())}")

    # 获取模型类的参数
    import inspect
    model_class = models[model_name]
    sig = inspect.signature(model_class.__init__)
    valid_params = set(sig.parameters.keys()) - {'self'}

    # 过滤无效参数
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

    return model_class(**filtered_kwargs)
