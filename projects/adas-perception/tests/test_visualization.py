"""
可视化模块测试
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.visualization import Visualizer


class TestVisualizer:
    """可视化工具测试"""

    def setup_method(self):
        """测试前准备"""
        self.visualizer = Visualizer()

    def test_init(self):
        """测试初始化"""
        assert self.visualizer is not None
        assert hasattr(self.visualizer, 'class_colors')

    def test_visualize_boxes3d(self):
        """测试 3D 边界框可视化"""
        # 创建模拟边界框
        boxes = np.array([
            [0, 0, 0, 2, 4, 1.5, 0],      # 一个汽车
            [5, 5, 0, 0.6, 0.8, 1.7, 0.5], # 一个行人
            [-3, -3, 0, 0.6, 1.8, 1.7, 1.0] # 一个骑车人
        ])

        # 测试可视化函数是否能正常调用
        try:
            line_sets = self.visualizer.visualize_boxes3d(boxes)
            assert len(line_sets) == 3
        except Exception as e:
            pytest.fail(f"可视化 3D 边界框失败: {e}")

    def test_visualize_boxes3d_with_labels(self):
        """测试带标签的 3D 边界框可视化"""
        # 创建模拟边界框
        boxes = np.array([
            [0, 0, 0, 2, 4, 1.5, 0],
            [5, 5, 0, 0.6, 0.8, 1.7, 0.5],
        ])

        # 创建模拟标签
        labels = np.array([0, 1])  # Car, Pedestrian

        try:
            line_sets = self.visualizer.visualize_boxes3d(boxes, labels=labels)
            assert len(line_sets) == 2
        except Exception as e:
            pytest.fail(f"可视化带标签的 3D 边界框失败: {e}")

    def test_visualize_boxes3d_with_scores(self):
        """测试带分数的 3D 边界框可视化"""
        # 创建模拟边界框
        boxes = np.array([
            [0, 0, 0, 2, 4, 1.5, 0],
            [5, 5, 0, 0.6, 0.8, 1.7, 0.5],
        ])

        # 创建模拟分数
        scores = np.array([0.95, 0.85])

        try:
            line_sets = self.visualizer.visualize_boxes3d(boxes, scores=scores)
            assert len(line_sets) == 2
        except Exception as e:
            pytest.fail(f"可视化带分数的 3D 边界框失败: {e}")

    def test_create_box3d_line_set(self):
        """测试创建单个 3D 边界框线集"""
        # 创建模拟边界框
        box = np.array([0, 0, 0, 2, 4, 1.5, 0])

        try:
            line_set = self.visualizer._create_box3d_line_set(box, color=(0, 1, 0))
            assert line_set is not None
        except Exception as e:
            pytest.fail(f"创建 3D 边界框线集失败: {e}")

    def test_draw_line(self):
        """测试绘制直线"""
        # 创建模拟图像
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        try:
            self.visualizer._draw_line(image, 10, 10, 90, 90, color=[255, 255, 255])
            # 验证直线被绘制
            assert image[10, 10].tolist() == [255, 255, 255]
        except Exception as e:
            pytest.fail(f"绘制直线失败: {e}")


class TestVisualizerIntegration:
    """可视化工具集成测试"""

    def setup_method(self):
        """测试前准备"""
        self.visualizer = Visualizer()

    def test_plot_training_curves(self):
        """测试绘制训练曲线"""
        # 创建模拟数据
        train_losses = [0.5, 0.4, 0.3, 0.25, 0.2]
        val_losses = [0.6, 0.5, 0.4, 0.35, 0.3]
        val_metrics = [0.6, 0.65, 0.7, 0.72, 0.75]

        try:
            # 测试函数是否能正常调用
            # 注意：这里不测试实际显示，只测试函数是否能正常运行
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            self.visualizer.plot_training_curves(
                train_losses, val_losses, val_metrics, 'mAP'
            )
        except Exception as e:
            pytest.fail(f"绘制训练曲线失败: {e}")

    def test_plot_confusion_matrix(self):
        """测试绘制混淆矩阵"""
        # 创建模拟混淆矩阵
        confusion_matrix = np.array([
            [50, 5, 2],
            [3, 45, 4],
            [1, 2, 48]
        ])
        class_names = ['Car', 'Pedestrian', 'Cyclist']

        try:
            # 测试函数是否能正常调用
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            self.visualizer.plot_confusion_matrix(confusion_matrix, class_names)
        except Exception as e:
            pytest.fail(f"绘制混淆矩阵失败: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
