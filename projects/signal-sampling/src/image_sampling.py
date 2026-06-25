"""
图像采样实现
=============

实现图像的采样 (降采样) 和重建 (上采样)。

核心概念:
- 降采样: 减少像素数，需要抗混叠滤波
- 上采样: 增加像素数，需要插值
- 混叠: 不经滤波直接降采样会产生锯齿和摩尔纹

常用插值方法:
- 最近邻: 速度最快，质量最差
- 双线性: 速度较快，质量一般
- 双三次: 速度较慢，质量较好
"""

import numpy as np
from typing import Tuple, Optional


class ImageSampler:
    """图像采样器

    支持降采样和上采样操作。

    Parameters
    ----------
    image : np.ndarray
        输入图像 (2D 数组)
    """

    def __init__(self, image: np.ndarray):
        if image.ndim != 2:
            raise ValueError("输入必须是 2D 图像数组")
        self.image = image.astype(np.float64)

    def downsample(
        self,
        factor: int,
        method: str = 'average',
        anti_aliasing: bool = True,
    ) -> np.ndarray:
        """降采样

        Parameters
        ----------
        factor : int
            降采样因子
        method : str
            降采样方法: 'average', 'subsample'
        anti_aliasing : bool
            是否进行抗混叠滤波

        Returns
        -------
        np.ndarray
            降采样后的图像
        """
        if factor <= 0:
            raise ValueError("降采样因子必须为正整数")

        image = self.image.copy()

        # 抗混叠滤波
        if anti_aliasing:
            image = _box_blur(image, kernel_size=factor)

        h, w = image.shape
        new_h = h // factor
        new_w = w // factor

        if method == 'average':
            # 块平均
            result = np.zeros((new_h, new_w))
            for i in range(new_h):
                for j in range(new_w):
                    block = image[
                        i * factor : (i + 1) * factor,
                        j * factor : (j + 1) * factor,
                    ]
                    result[i, j] = np.mean(block)
            return result

        elif method == 'subsample':
            # 直接抽取
            return image[::factor, ::factor]

        else:
            raise ValueError(f"未知降采样方法: {method}")

    def upsample(
        self,
        factor: int,
        method: str = 'bilinear',
    ) -> np.ndarray:
        """上采样

        Parameters
        ----------
        factor : int
            上采样因子
        method : str
            插值方法: 'nearest', 'bilinear', 'bicubic'

        Returns
        -------
        np.ndarray
            上采样后的图像
        """
        if factor <= 0:
            raise ValueError("上采样因子必须为正整数")

        h, w = self.image.shape
        new_h = h * factor
        new_w = w * factor

        if method == 'nearest':
            return self._nearest_interpolation(new_h, new_w)
        elif method == 'bilinear':
            return self._bilinear_interpolation(new_h, new_w)
        elif method == 'bicubic':
            return self._bicubic_interpolation(new_h, new_w)
        else:
            raise ValueError(f"未知插值方法: {method}")

    def _nearest_interpolation(self, new_h: int, new_w: int) -> np.ndarray:
        """最近邻插值"""
        h, w = self.image.shape
        result = np.zeros((new_h, new_w))

        for i in range(new_h):
            for j in range(new_w):
                src_i = int(i * h / new_h)
                src_j = int(j * w / new_w)
                src_i = min(src_i, h - 1)
                src_j = min(src_j, w - 1)
                result[i, j] = self.image[src_i, src_j]

        return result

    def _bilinear_interpolation(self, new_h: int, new_w: int) -> np.ndarray:
        """双线性插值"""
        h, w = self.image.shape
        result = np.zeros((new_h, new_w))

        for i in range(new_h):
            for j in range(new_w):
                # 映射到原图坐标
                src_i = i * (h - 1) / (new_h - 1) if new_h > 1 else 0
                src_j = j * (w - 1) / (new_w - 1) if new_w > 1 else 0

                # 四个最近邻点
                i0 = int(np.floor(src_i))
                j0 = int(np.floor(src_j))
                i1 = min(i0 + 1, h - 1)
                j1 = min(j0 + 1, w - 1)

                # 插值权重
                di = src_i - i0
                dj = src_j - j0

                # 双线性插值
                result[i, j] = (
                    (1 - di) * (1 - dj) * self.image[i0, j0] +
                    (1 - di) * dj * self.image[i0, j1] +
                    di * (1 - dj) * self.image[i1, j0] +
                    di * dj * self.image[i1, j1]
                )

        return result

    def _bicubic_interpolation(self, new_h: int, new_w: int) -> np.ndarray:
        """双三次插值 (简化版)"""
        h, w = self.image.shape
        result = np.zeros((new_h, new_w))

        def cubic_kernel(x: float) -> float:
            """三次插值核"""
            x = abs(x)
            if x <= 1:
                return 1 - 2 * x * x + x * x * x
            elif x <= 2:
                return 4 - 8 * x + 5 * x * x - x * x * x
            else:
                return 0

        for i in range(new_h):
            for j in range(new_w):
                src_i = i * (h - 1) / (new_h - 1) if new_h > 1 else 0
                src_j = j * (w - 1) / (new_w - 1) if new_w > 1 else 0

                i_int = int(np.floor(src_i))
                j_int = int(np.floor(src_j))

                value = 0.0
                for di in range(-1, 3):
                    for dj in range(-1, 3):
                        ni = np.clip(i_int + di, 0, h - 1)
                        nj = np.clip(j_int + dj, 0, w - 1)

                        wi = cubic_kernel(src_i - (i_int + di))
                        wj = cubic_kernel(src_j - (j_int + dj))

                        value += self.image[ni, nj] * wi * wj

                result[i, j] = value

        return result


def downsample_image(
    image: np.ndarray,
    factor: int,
    anti_aliasing: bool = True,
) -> np.ndarray:
    """降采样图像 (便捷函数)

    Parameters
    ----------
    image : np.ndarray
        输入图像
    factor : int
        降采样因子
    anti_aliasing : bool
        是否抗混叠

    Returns
    -------
    np.ndarray
        降采样后的图像
    """
    sampler = ImageSampler(image)
    return sampler.downsample(factor, anti_aliasing=anti_aliasing)


def upsample_image(
    image: np.ndarray,
    factor: int,
    method: str = 'bilinear',
) -> np.ndarray:
    """上采样图像 (便捷函数)

    Parameters
    ----------
    image : np.ndarray
        输入图像
    factor : int
        上采样因子
    method : str
        插值方法

    Returns
    -------
    np.ndarray
        上采样后的图像
    """
    sampler = ImageSampler(image)
    return sampler.upsample(factor, method=method)


def demonstrate_image_aliasing(
    size: int = 256,
    downsample_factor: int = 4,
) -> dict:
    """演示图像混叠

    Parameters
    ----------
    size : int
        图像大小
    downsample_factor : int
        降采样因子

    Returns
    -------
    dict
        演示结果
    """
    # 生成测试图像 (棋盘格 + 高频纹理)
    image = _generate_test_image(size)

    sampler = ImageSampler(image)

    # 带抗混叠的降采样
    downsampled_aa = sampler.downsample(downsample_factor, anti_aliasing=True)

    # 不带抗混叠的降采样
    downsampled_no_aa = sampler.downsample(downsample_factor, anti_aliasing=False)

    # 上采样
    upsampled_nearest = ImageSampler(downsampled_aa).upsample(
        downsample_factor, method='nearest'
    )
    upsampled_bilinear = ImageSampler(downsampled_aa).upsample(
        downsample_factor, method='bilinear'
    )

    return {
        "original": image,
        "downsampled_with_aa": downsampled_aa,
        "downsampled_without_aa": downsampled_no_aa,
        "upsampled_nearest": upsampled_nearest,
        "upsampled_bilinear": upsampled_bilinear,
    }


def _box_blur(image: np.ndarray, kernel_size: int) -> np.ndarray:
    """盒式模糊 (抗混叠滤波)

    Parameters
    ----------
    image : np.ndarray
        输入图像
    kernel_size : int
        核大小

    Returns
    -------
    np.ndarray
        模糊后的图像
    """
    h, w = image.shape
    result = np.zeros_like(image)
    half = kernel_size // 2

    for i in range(h):
        for j in range(w):
            # 计算局部平均
            i_start = max(0, i - half)
            i_end = min(h, i + half + 1)
            j_start = max(0, j - half)
            j_end = min(w, j + half + 1)

            result[i, j] = np.mean(image[i_start:i_end, j_start:j_end])

    return result


def _generate_test_image(size: int) -> np.ndarray:
    """生成测试图像

    Parameters
    ----------
    size : int
        图像大小

    Returns
    -------
    np.ndarray
        测试图像
    """
    image = np.zeros((size, size))

    # 棋盘格
    block_size = size // 8
    for i in range(size):
        for j in range(size):
            if (i // block_size + j // block_size) % 2 == 0:
                image[i, j] = 1.0

    # 添加高频纹理
    x = np.linspace(0, 4 * np.pi, size)
    y = np.linspace(0, 4 * np.pi, size)
    X, Y = np.meshgrid(x, y)
    texture = 0.3 * np.sin(X * 4) * np.sin(Y * 4)

    image = image + texture
    image = np.clip(image, 0, 1)

    return image
