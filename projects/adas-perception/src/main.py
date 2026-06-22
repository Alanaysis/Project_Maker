"""
自动驾驶感知系统主模块

提供系统的主要功能入口。
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional

import torch
import numpy as np

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data.point_cloud import PointCloud
from src.data.kitti_loader import KITTILoader
from src.models.pointpillars import PointPillars, build_pointpillars
from src.utils.visualization import Visualizer


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ADASPerception:
    """
    自动驾驶感知系统类。
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = 'cuda',
        config: Optional[Dict] = None
    ):
        """
        初始化感知系统。

        Args:
            model_path: 模型权重路径
            device: 设备 ('cuda' 或 'cpu')
            config: 配置字典
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.config = config or {}

        # 初始化模型
        self.model = self._load_model(model_path)

        # 初始化可视化工具
        self.visualizer = Visualizer()

        logger.info(f"感知系统初始化完成，使用设备: {self.device}")

    def _load_model(self, model_path: Optional[str]) -> PointPillars:
        """
        加载模型。

        Args:
            model_path: 模型权重路径

        Returns:
            模型
        """
        # 构建模型
        model = build_pointpillars(self.config)

        # 加载权重
        if model_path and os.path.exists(model_path):
            logger.info(f"加载模型权重: {model_path}")
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            logger.warning("未找到模型权重，使用随机初始化")

        model = model.to(self.device)
        model.eval()

        return model

    def detect(
        self,
        points: np.ndarray,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.5
    ) -> Dict:
        """
        执行 3D 目标检测。

        Args:
            points: (N, 4) 点云数据 [x, y, z, intensity]
            confidence_threshold: 置信度阈值
            nms_threshold: NMS 阈值

        Returns:
            检测结果字典
        """
        # 预处理
        points = self._preprocess(points)

        # 转换为 tensor
        points_tensor = torch.from_numpy(points).float().to(self.device)
        points_tensor = points_tensor.unsqueeze(0)  # 添加 batch 维度

        # 推理
        with torch.no_grad():
            predictions = self.model(points_tensor)

        # 后处理
        boxes, scores, labels = self._post_process(
            predictions, confidence_threshold, nms_threshold
        )

        return {
            'boxes': boxes,
            'scores': scores,
            'labels': labels
        }

    def _preprocess(self, points: np.ndarray) -> np.ndarray:
        """
        预处理点云。

        Args:
            points: (N, 4) 点云数据

        Returns:
            预处理后的点云
        """
        # 范围过滤
        x_range = self.config.get('x_range', (-40, 40))
        y_range = self.config.get('y_range', (-40, 40))
        z_range = self.config.get('z_range', (-3, 1))

        mask = (
            (points[:, 0] >= x_range[0]) &
            (points[:, 0] <= x_range[1]) &
            (points[:, 1] >= y_range[0]) &
            (points[:, 1] <= y_range[1]) &
            (points[:, 2] >= z_range[0]) &
            (points[:, 2] <= z_range[1])
        )

        return points[mask]

    def _post_process(
        self,
        predictions: Dict,
        confidence_threshold: float,
        nms_threshold: float
    ) -> tuple:
        """
        后处理预测结果。

        Args:
            predictions: 模型预测结果
            confidence_threshold: 置信度阈值
            nms_threshold: NMS 阈值

        Returns:
            (boxes, scores, labels)
        """
        cls_score = predictions['cls_score']
        bbox_pred = predictions['bbox_pred']
        dir_pred = predictions['dir_pred']

        # 这里简化处理，实际应用中需要实现完整的后处理逻辑
        # 包括：边界框解码、NMS、置信度过滤等

        # 模拟输出
        boxes = np.zeros((0, 7))
        scores = np.zeros(0)
        labels = np.zeros(0, dtype=int)

        return boxes, scores, labels

    def visualize(
        self,
        points: np.ndarray,
        boxes: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None,
        scores: Optional[np.ndarray] = None
    ) -> None:
        """
        可视化结果。

        Args:
            points: (N, 4) 点云数据
            boxes: (M, 7) 3D 边界框
            labels: (M,) 类别标签
            scores: (M,) 置信度分数
        """
        if boxes is not None and len(boxes) > 0:
            self.visualizer.visualize_detection_result(
                points, boxes, labels, scores,
                point_size=2.0,
                background_color=[0.1, 0.1, 0.1]
            )
        else:
            self.visualizer.visualize_point_cloud(
                points,
                point_size=2.0,
                background_color=[0.1, 0.1, 0.1]
            )

    def evaluate(
        self,
        data_loader: KITTILoader,
        num_samples: Optional[int] = None
    ) -> Dict:
        """
        评估模型性能。

        Args:
            data_loader: 数据加载器
            num_samples: 评估样本数量

        Returns:
            评估结果字典
        """
        logger.info("开始评估...")

        results = []
        num_samples = num_samples or len(data_loader)

        for i in range(min(num_samples, len(data_loader))):
            # 获取数据
            sample = data_loader[i]
            points = sample['points']

            # 执行检测
            detection_result = self.detect(points)
            results.append(detection_result)

            if (i + 1) % 100 == 0:
                logger.info(f"已处理 {i + 1}/{num_samples} 个样本")

        # 计算评估指标
        metrics = self._compute_metrics(results, data_loader)

        logger.info(f"评估完成: {metrics}")

        return metrics

    def _compute_metrics(
        self,
        results: list,
        data_loader: KITTILoader
    ) -> Dict:
        """
        计算评估指标。

        Args:
            results: 检测结果列表
            data_loader: 数据加载器

        Returns:
            评估指标字典
        """
        # 这里简化处理，实际应用中需要实现完整的评估逻辑
        # 包括：AP 计算、mAP 计算等

        metrics = {
            'mAP': 0.0,
            'AP_Car': 0.0,
            'AP_Pedestrian': 0.0,
            'AP_Cyclist': 0.0
        }

        return metrics


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='自动驾驶感知系统')

    parser.add_argument(
        '--mode',
        type=str,
        default='demo',
        choices=['demo', 'evaluate', 'visualize'],
        help='运行模式'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='模型权重路径'
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        default=None,
        help='数据集目录'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='cuda',
        choices=['cuda', 'cpu'],
        help='设备'
    )

    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.5,
        help='置信度阈值'
    )

    parser.add_argument(
        '--nms-threshold',
        type=float,
        default=0.5,
        help='NMS 阈值'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 配置
    config = {
        'voxel_size': [0.16, 0.16, 4],
        'point_cloud_range': [-40, -40, -3, 40, 40, 1],
        'num_classes': 3,
        'x_range': (-40, 40),
        'y_range': (-40, 40),
        'z_range': (-3, 1)
    }

    # 初始化感知系统
    perception = ADASPerception(
        model_path=args.model_path,
        device=args.device,
        config=config
    )

    if args.mode == 'demo':
        # 演示模式
        logger.info("运行演示模式...")

        # 创建模拟点云
        points = np.random.rand(10000, 4).astype(np.float32)
        points[:, :3] = points[:, :3] * 80 - 40  # 范围 [-40, 40]
        points[:, 3] = points[:, 3] * 255  # 强度 [0, 255]

        # 执行检测
        result = perception.detect(
            points,
            confidence_threshold=args.confidence_threshold,
            nms_threshold=args.nms_threshold
        )

        # 可视化
        perception.visualize(
            points,
            result['boxes'],
            result['labels'],
            result['scores']
        )

    elif args.mode == 'evaluate':
        # 评估模式
        if args.data_dir is None:
            logger.error("评估模式需要指定数据集目录")
            return

        logger.info(f"评估数据集: {args.data_dir}")

        # 加载数据集
        data_loader = KITTILoader(args.data_dir, split='training')

        # 执行评估
        metrics = perception.evaluate(data_loader, num_samples=100)

        # 打印结果
        logger.info("评估结果:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")

    elif args.mode == 'visualize':
        # 可视化模式
        if args.data_dir is None:
            logger.error("可视化模式需要指定数据集目录")
            return

        logger.info(f"可视化数据集: {args.data_dir}")

        # 加载数据集
        data_loader = KITTILoader(args.data_dir, split='training')

        # 可视化第一个样本
        sample = data_loader[0]
        perception.visualize(sample['points'])

    logger.info("程序运行完成")


if __name__ == '__main__':
    main()
