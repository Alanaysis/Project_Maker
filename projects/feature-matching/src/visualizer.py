"""
可视化工具模块

提供特征点绘制、匹配结果展示、统计图表等功能。
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class Visualizer:
    """
    可视化工具

    提供特征点绘制、匹配结果展示、统计图表等功能。

    Example:
        >>> vis = Visualizer()
        >>> vis.draw_keypoints(image, keypoints, 'output.jpg')
        >>> vis.draw_matches(img1, kp1, img2, kp2, matches, 'matches.jpg')
    """

    @staticmethod
    def draw_keypoints(image: np.ndarray,
                       keypoints: List[cv2.KeyPoint],
                       output_path: Optional[str] = None,
                       rich: bool = True) -> np.ndarray:
        """
        绘制特征点

        Args:
            image: 原始图像
            keypoints: 关键点列表
            output_path: 输出路径，如果为None则不保存
            rich: 是否绘制丰富的关键点信息（尺度、方向）

        Returns:
            绘制了关键点的图像
        """
        if rich:
            flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
        else:
            flags = cv2.DRAW_MATCHES_FLAGS_DEFAULT

        img_kp = cv2.drawKeypoints(
            image, keypoints, None,
            flags=flags,
            color=(0, 255, 0)
        )

        if output_path:
            cv2.imwrite(output_path, img_kp)
            logger.info(f"关键点图像已保存到: {output_path}")

        return img_kp

    @staticmethod
    def draw_matches(img1: np.ndarray,
                     kp1: List[cv2.KeyPoint],
                     img2: np.ndarray,
                     kp2: List[cv2.KeyPoint],
                     matches: List[cv2.DMatch],
                     output_path: Optional[str] = None,
                     max_matches: int = 100) -> np.ndarray:
        """
        绘制匹配结果

        Args:
            img1: 第一张图像
            kp1: 第一张图像的关键点
            img2: 第二张图像
            kp2: 第二张图像的关键点
            matches: 匹配结果
            output_path: 输出路径
            max_matches: 最大绘制匹配数

        Returns:
            绘制了匹配结果的图像
        """
        # 限制绘制的匹配数量
        if len(matches) > max_matches:
            matches = sorted(matches, key=lambda x: x.distance)[:max_matches]
            logger.info(f"限制绘制 {max_matches} 个最佳匹配")

        img_matches = cv2.drawMatches(
            img1, kp1, img2, kp2, matches, None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
            matchColor=(0, 255, 0),
            singlePointColor=(255, 0, 0)
        )

        if output_path:
            cv2.imwrite(output_path, img_matches)
            logger.info(f"匹配图像已保存到: {output_path}")

        return img_matches

    @staticmethod
    def plot_match_statistics(matches: List[cv2.DMatch],
                              output_path: Optional[str] = None,
                              show: bool = False):
        """
        绘制匹配统计图表

        Args:
            matches: 匹配结果列表
            output_path: 输出路径
            show: 是否显示图表
        """
        if not matches:
            logger.warning("匹配列表为空，无法绘制统计图")
            return

        distances = [m.distance for m in matches]

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # 1. 距离分布直方图
        axes[0].hist(distances, bins=50, edgecolor='black', alpha=0.7)
        axes[0].set_xlabel('Distance')
        axes[0].set_ylabel('Count')
        axes[0].set_title('Match Distance Distribution')
        axes[0].axvline(np.mean(distances), color='r', linestyle='--',
                        label=f'Mean: {np.mean(distances):.2f}')
        axes[0].legend()

        # 2. 距离累积分布
        sorted_distances = np.sort(distances)
        cumulative = np.arange(1, len(sorted_distances) + 1) / len(sorted_distances)
        axes[1].plot(sorted_distances, cumulative, 'b-')
        axes[1].set_xlabel('Distance')
        axes[1].set_ylabel('Cumulative Probability')
        axes[1].set_title('Cumulative Distance Distribution')
        axes[1].grid(True, alpha=0.3)

        # 3. 匹配质量饼图
        mean_dist = np.mean(distances)
        good = sum(1 for d in distances if d < mean_dist)
        poor = len(distances) - good
        axes[2].pie([good, poor],
                    labels=[f'Good (<{mean_dist:.1f})', f'Poor (>={mean_dist:.1f})'],
                    autopct='%1.1f%%',
                    colors=['#4CAF50', '#FF5722'])
        axes[2].set_title('Match Quality')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"统计图已保存到: {output_path}")

        if show:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def create_comparison_grid(images: List[np.ndarray],
                               titles: List[str],
                               output_path: Optional[str] = None,
                               figsize: tuple = None):
        """
        创建图像对比网格

        Args:
            images: 图像列表
            titles: 标题列表
            output_path: 输出路径
            figsize: 图像大小
        """
        n = len(images)
        cols = min(3, n)
        rows = (n + cols - 1) // cols

        if figsize is None:
            figsize = (5 * cols, 4 * rows)

        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        for i, (img, title) in enumerate(zip(images, titles)):
            if len(img.shape) == 2:
                axes[i].imshow(img, cmap='gray')
            else:
                axes[i].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            axes[i].set_title(title)
            axes[i].axis('off')

        # 隐藏多余的子图
        for i in range(n, rows * cols):
            axes[i].axis('off')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info(f"对比图已保存到: {output_path}")

        plt.close()
