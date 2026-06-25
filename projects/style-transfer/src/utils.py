"""工具函数模块

提供图像加载、保存和预处理的实用函数。
"""

import torch
import numpy as np
from pathlib import Path
from typing import Union


def load_image(
    image_path: Union[str, Path],
    size: int = 512,
    device: str = "cpu",
) -> torch.Tensor:
    """加载并预处理图像

    Args:
        image_path: 图像文件路径
        size: 目标图像大小（最长边）
        device: 设备类型（cpu/cuda）

    Returns:
        预处理后的图像张量，shape 为 (1, 3, H, W)

    示例：
        >>> from src import load_image
        >>> image = load_image("path/to/image.jpg", size=512)
        >>> print(image.shape)
        torch.Size([1, 3, 512, 512])
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("请安装 Pillow: pip install Pillow")

    # 加载图像
    image = Image.open(image_path).convert("RGB")

    # 调整大小，保持宽高比
    width, height = image.size
    if width > height:
        new_width = size
        new_height = int(height * size / width)
    else:
        new_height = size
        new_width = int(width * size / height)

    image = image.resize((new_width, new_height), Image.LANCZOS)

    # 转换为张量
    image_array = np.array(image, dtype=np.float32) / 255.0

    # ImageNet 归一化
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image_array = (image_array - mean) / std

    # 转换为 PyTorch 张量：(H, W, C) -> (1, C, H, W)
    image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)

    return image_tensor.to(device)


def save_image(
    tensor: torch.Tensor,
    save_path: Union[str, Path],
    denormalize: bool = True,
) -> None:
    """保存图像张量为图像文件

    Args:
        tensor: 图像张量，shape 为 (1, 3, H, W) 或 (3, H, W)
        save_path: 保存路径
        denormalize: 是否进行反归一化

    示例：
        >>> from src import save_image
        >>> image = torch.randn(1, 3, 256, 256)
        >>> save_image(image, "output.jpg")
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("请安装 Pillow: pip install Pillow")

    # 确保 shape 为 (3, H, W)
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)

    # 移动到 CPU 并转换为 numpy
    image_array = tensor.cpu().detach().numpy()

    # 反归一化
    if denormalize:
        mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
        image_array = image_array * std + mean

    # 裁剪到 [0, 1] 范围
    image_array = np.clip(image_array, 0, 1)

    # 转换为 PIL Image：(C, H, W) -> (H, W, C)
    image_array = (image_array * 255).astype(np.uint8)
    image_array = image_array.transpose(1, 2, 0)

    image = Image.fromarray(image_array)

    # 确保目录存在
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存图像
    image.save(save_path)
    print(f"图像已保存到: {save_path}")


def show_image(tensor: torch.Tensor, title: str = "Image") -> None:
    """显示图像张量

    Args:
        tensor: 图像张量，shape 为 (1, 3, H, W) 或 (3, H, W)
        title: 图像标题
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("请安装 matplotlib: pip install matplotlib")

    # 确保 shape 为 (3, H, W)
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)

    # 反归一化
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    image = tensor.cpu() * std + mean

    # 裁剪到 [0, 1] 范围
    image = torch.clamp(image, 0, 1)

    # 转换为 numpy 并显示
    image = image.permute(1, 2, 0).numpy()

    plt.figure(figsize=(8, 8))
    plt.imshow(image)
    plt.title(title)
    plt.axis("off")
    plt.show()


def create_noise_image(
    content_image: torch.Tensor,
    noise_ratio: float = 0.6,
) -> torch.Tensor:
    """创建噪声图像（用于初始化）

    Args:
        content_image: 内容图像张量
        noise_ratio: 噪声比例（0-1），0 表示完全使用内容图像，1 表示完全随机噪声

    Returns:
        噪声图像张量
    """
    # 创建随机噪声
    noise = torch.randn_like(content_image)

    # 混合内容图像和噪声
    noise_image = content_image * (1 - noise_ratio) + noise * noise_ratio

    return noise_image


def get_device(device: str = "auto") -> torch.device:
    """获取计算设备

    Args:
        device: 设备类型（auto/cpu/cuda/mps）

    Returns:
        PyTorch 设备对象
    """
    if device == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    return torch.device(device)
