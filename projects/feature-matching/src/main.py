"""
特征匹配主程序

提供命令行接口进行特征点检测和匹配。
"""

import cv2
import numpy as np
import argparse
import os
import sys
import logging
from typing import List, Tuple, Optional

from .detector import FeatureDetector
from .descriptor import DescriptorExtractor
from .matcher import FeatureMatcher
from .visualizer import Visualizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_image(path: str, grayscale: bool = True) -> np.ndarray:
    """
    加载图像

    Args:
        path: 图像路径
        grayscale: 是否加载为灰度图

    Returns:
        图像数组

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 图像加载失败
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")

    if grayscale:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        img = cv2.imread(path, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError(f"Failed to load image: {path}")

    logger.info(f"加载图像: {path}, 尺寸: {img.shape}")
    return img


def process_single_image(image_path: str,
                         method: str = 'sift',
                         output_dir: str = 'output'):
    """
    处理单张图像

    Args:
        image_path: 图像路径
        method: 检测方法
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载图像
    image = load_image(image_path)

    # 初始化检测器
    detector = FeatureDetector(method=method)

    # 检测特征点
    keypoints, descriptors = detector.detect_and_compute(image)

    # 绘制特征点
    vis = Visualizer()
    img_kp = vis.draw_keypoints(image, keypoints)

    # 保存结果
    output_path = os.path.join(output_dir, f'{method}_keypoints.jpg')
    cv2.imwrite(output_path, img_kp)

    # 绘制统计图
    if descriptors is not None:
        # 计算描述子统计
        stats = {
            'num_keypoints': len(keypoints),
            'descriptor_shape': descriptors.shape
        }
        logger.info(f"特征点统计: {stats}")

    logger.info(f"处理完成，结果保存到: {output_dir}")
    return keypoints, descriptors


def match_images(image1_path: str,
                 image2_path: str,
                 method: str = 'sift',
                 matcher_type: str = 'bf',
                 output_dir: str = 'output'):
    """
    匹配两张图像

    Args:
        image1_path: 第一张图像路径
        image2_path: 第二张图像路径
        method: 检测方法
        matcher_type: 匹配器类型
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载图像
    img1 = load_image(image1_path)
    img2 = load_image(image2_path)

    # 初始化组件
    detector = FeatureDetector(method=method)
    matcher = FeatureMatcher(method=matcher_type, cross_check=True)

    # 检测特征点
    kp1, des1 = detector.detect_and_compute(img1)
    kp2, des2 = detector.detect_and_compute(img2)

    # 特征匹配
    matches = matcher.match(des1, des2)

    # 按距离排序
    matches = sorted(matches, key=lambda x: x.distance)

    # 可视化
    vis = Visualizer()

    # 绘制匹配结果
    img_matches = vis.draw_matches(img1, kp1, img2, kp2, matches)
    match_path = os.path.join(output_dir, f'{method}_matches.jpg')
    cv2.imwrite(match_path, img_matches)

    # 绘制统计图
    stats_path = os.path.join(output_dir, f'{method}_statistics.png')
    vis.plot_match_statistics(matches, output_path=stats_path)

    # 打印统计信息
    distances = [m.distance for m in matches]
    logger.info(f"匹配统计:")
    logger.info(f"  特征点数: 图像1={len(kp1)}, 图像2={len(kp2)}")
    logger.info(f"  匹配数量: {len(matches)}")
    logger.info(f"  平均距离: {np.mean(distances):.2f}")
    logger.info(f"  最小距离: {np.min(distances):.2f}")
    logger.info(f"  最大距离: {np.max(distances):.2f}")

    return matches


def compare_methods(image1_path: str,
                    image2_path: str,
                    output_dir: str = 'output'):
    """
    对比不同检测方法

    Args:
        image1_path: 第一张图像路径
        image2_path: 第二张图像路径
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载图像
    img1 = load_image(image1_path)
    img2 = load_image(image2_path)

    results = {}

    for method in ['sift', 'orb']:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试 {method.upper()} 方法")
        logger.info(f"{'='*50}")

        # 初始化
        detector = FeatureDetector(method=method)
        matcher = FeatureMatcher(method='bf', cross_check=True)

        # 检测
        kp1, des1 = detector.detect_and_compute(img1)
        kp2, des2 = detector.detect_and_compute(img2)

        # 匹配
        matches = matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        # 记录结果
        results[method] = {
            'keypoints1': len(kp1),
            'keypoints2': len(kp2),
            'matches': len(matches),
            'avg_distance': np.mean([m.distance for m in matches]) if matches else 0
        }

        # 可视化
        vis = Visualizer()
        img_matches = vis.draw_matches(img1, kp1, img2, kp2, matches)
        match_path = os.path.join(output_dir, f'{method}_matches.jpg')
        cv2.imwrite(match_path, img_matches)

    # 打印对比结果
    logger.info(f"\n{'='*50}")
    logger.info("方法对比结果:")
    logger.info(f"{'='*50}")
    for method, stats in results.items():
        logger.info(f"{method.upper():>10}: 特征点={stats['keypoints1']}/{stats['keypoints2']}, "
                    f"匹配={stats['matches']}, 平均距离={stats['avg_distance']:.2f}")

    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='特征匹配工具 - SIFT/ORB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图像特征检测
  python -m src.main detect --input image.jpg --method sift

  # 两张图像匹配
  python -m src.main match --input1 img1.jpg --input2 img2.jpg --method sift

  # 对比不同方法
  python -m src.main compare --input1 img1.jpg --input2 img2.jpg
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # detect命令
    detect_parser = subparsers.add_parser('detect', help='检测图像特征点')
    detect_parser.add_argument('--input', required=True, help='输入图像路径')
    detect_parser.add_argument('--method', default='sift', choices=['sift', 'orb'],
                               help='检测方法 (default: sift)')
    detect_parser.add_argument('--output', default='output', help='输出目录')

    # match命令
    match_parser = subparsers.add_parser('match', help='匹配两张图像')
    match_parser.add_argument('--input1', required=True, help='第一张图像路径')
    match_parser.add_argument('--input2', required=True, help='第二张图像路径')
    match_parser.add_argument('--method', default='sift', choices=['sift', 'orb'],
                              help='检测方法 (default: sift)')
    match_parser.add_argument('--matcher', default='bf', choices=['bf', 'flann'],
                              help='匹配器类型 (default: bf)')
    match_parser.add_argument('--output', default='output', help='输出目录')

    # compare命令
    compare_parser = subparsers.add_parser('compare', help='对比不同方法')
    compare_parser.add_argument('--input1', required=True, help='第一张图像路径')
    compare_parser.add_argument('--input2', required=True, help='第二张图像路径')
    compare_parser.add_argument('--output', default='output', help='输出目录')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    try:
        if args.command == 'detect':
            process_single_image(args.input, args.method, args.output)
        elif args.command == 'match':
            match_images(args.input1, args.input2, args.method, args.matcher, args.output)
        elif args.command == 'compare':
            compare_methods(args.input1, args.input2, args.output)
    except Exception as e:
        logger.error(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
