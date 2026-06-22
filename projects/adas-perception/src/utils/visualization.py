"""
可视化工具模块

提供点云和检测结果的可视化功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict

# 可选导入 open3d
try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    print("警告: open3d 未安装，部分可视化功能将不可用")


class Visualizer:
    """
    可视化工具类。
    """

    def __init__(self):
        """初始化可视化工具"""
        # 类别颜色映射
        self.class_colors = {
            'Car': (0, 1, 0),        # 绿色
            'Pedestrian': (1, 0, 0), # 红色
            'Cyclist': (0, 0, 1),    # 蓝色
            'Van': (1, 1, 0),        # 黄色
            'Truck': (1, 0, 1),      # 紫色
            'Tram': (0, 1, 1),       # 青色
            'Misc': (0.5, 0.5, 0.5), # 灰色
        }

    def visualize_point_cloud(
        self,
        points: np.ndarray,
        point_size: float = 2.0,
        background_color: List[float] = [0, 0, 0],
        window_name: str = "点云可视化"
    ) -> None:
        """
        可视化点云。

        Args:
            points: (N, 3) 或 (N, 4) 点云数据
            point_size: 点大小
            background_color: 背景颜色
            window_name: 窗口名称
        """
        # 创建 Open3D 点云
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points[:, :3])

        # 如果有颜色信息
        if points.shape[1] >= 6:
            pcd.colors = o3d.utility.Vector3dVector(points[:, 3:6])

        # 设置可视化选项
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name=window_name)

        # 添加点云
        vis.add_geometry(pcd)

        # 设置渲染选项
        render_option = vis.get_render_option()
        render_option.point_size = point_size
        render_option.background_color = np.array(background_color)

        # 运行可视化
        vis.run()
        vis.destroy_window()

    def visualize_boxes3d(
        self,
        boxes: np.ndarray,
        labels: Optional[np.ndarray] = None,
        scores: Optional[np.ndarray] = None,
        color: Tuple[float, float, float] = (0, 1, 0),
        line_width: float = 2.0
    ) -> o3d.geometry.LineSet:
        """
        创建 3D 边界框可视化。

        Args:
            boxes: (M, 7) 3D 边界框 [x, y, z, w, l, h, θ]
            labels: (M,) 类别标签
            scores: (M,) 置信度分数
            color: 默认颜色
            line_width: 线宽

        Returns:
            Open3D 线集对象
        """
        line_sets = []

        for i in range(len(boxes)):
            box = boxes[i]

            # 获取类别颜色
            if labels is not None:
                label = labels[i]
                if isinstance(label, int):
                    # 使用类别索引
                    color = list(self.class_colors.values())[label % len(self.class_colors)]
                elif isinstance(label, str):
                    color = self.class_colors.get(label, color)

            # 创建 3D 边界框
            line_set = self._create_box3d_line_set(box, color)
            line_sets.append(line_set)

        return line_sets

    def _create_box3d_line_set(
        self,
        box: np.ndarray,
        color: Tuple[float, float, float]
    ) -> o3d.geometry.LineSet:
        """
        创建单个 3D 边界框的线集。

        Args:
            box: (7,) 3D 边界框 [x, y, z, w, l, h, θ]
            color: 颜色

        Returns:
            Open3D 线集对象
        """
        x, y, z, w, l, h, theta = box

        # 计算 8 个顶点
        # 底面 4 个点
        # 左下角
        x0 = x - w / 2 * np.cos(theta) + l / 2 * np.sin(theta)
        y0 = y - w / 2 * np.sin(theta) - l / 2 * np.cos(theta)
        z0 = z - h / 2

        # 右下角
        x1 = x + w / 2 * np.cos(theta) + l / 2 * np.sin(theta)
        y1 = y + w / 2 * np.sin(theta) - l / 2 * np.cos(theta)
        z1 = z - h / 2

        # 右上角
        x2 = x + w / 2 * np.cos(theta) - l / 2 * np.sin(theta)
        y2 = y + w / 2 * np.sin(theta) + l / 2 * np.cos(theta)
        z2 = z - h / 2

        # 左上角
        x3 = x - w / 2 * np.cos(theta) - l / 2 * np.sin(theta)
        y3 = y - w / 2 * np.sin(theta) + l / 2 * np.cos(theta)
        z3 = z - h / 2

        # 顶面 4 个点
        x4 = x0
        y4 = y0
        z4 = z + h / 2

        x5 = x1
        y5 = y1
        z5 = z + h / 2

        x6 = x2
        y6 = y2
        z6 = z + h / 2

        x7 = x3
        y7 = y3
        z7 = z + h / 2

        # 创建顶点数组
        vertices = np.array([
            [x0, y0, z0],
            [x1, y1, z1],
            [x2, y2, z2],
            [x3, y3, z3],
            [x4, y4, z4],
            [x5, y5, z5],
            [x6, y6, z6],
            [x7, y7, z7]
        ])

        # 创建边数组
        lines = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
            [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
            [0, 4], [1, 5], [2, 6], [3, 7]   # 侧面
        ]

        # 创建线集
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(vertices)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector([color] * len(lines))

        return line_set

    def visualize_detection_result(
        self,
        points: np.ndarray,
        boxes: np.ndarray,
        labels: Optional[np.ndarray] = None,
        scores: Optional[np.ndarray] = None,
        point_size: float = 2.0,
        background_color: List[float] = [0, 0, 0]
    ) -> None:
        """
        可视化检测结果。

        Args:
            points: (N, 3) 或 (N, 4) 点云数据
            boxes: (M, 7) 3D 边界框
            labels: (M,) 类别标签
            scores: (M,) 置信度分数
            point_size: 点大小
            background_color: 背景颜色
        """
        # 创建 Open3D 点云
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points[:, :3])

        # 创建 3D 边界框
        line_sets = self.visualize_boxes3d(boxes, labels, scores)

        # 可视化
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name="检测结果可视化")

        # 添加点云
        vis.add_geometry(pcd)

        # 添加 3D 边界框
        for line_set in line_sets:
            vis.add_geometry(line_set)

        # 设置渲染选项
        render_option = vis.get_render_option()
        render_option.point_size = point_size
        render_option.background_color = np.array(background_color)

        # 运行可视化
        vis.run()
        vis.destroy_window()

    def visualize_bev(
        self,
        points: np.ndarray,
        boxes: Optional[np.ndarray] = None,
        bev_range: Tuple[float, float, float, float] = (-50, 50, -50, 50),
        resolution: float = 0.1,
        point_size: float = 1.0
    ) -> None:
        """
        可视化鸟瞰图。

        Args:
            points: (N, 3) 或 (N, 4) 点云数据
            boxes: (M, 7) 3D 边界框
            bev_range: (x_min, x_max, y_min, y_max) BEV 范围
            resolution: 分辨率
            point_size: 点大小
        """
        x_min, x_max, y_min, y_max = bev_range

        # 计算图像尺寸
        width = int((x_max - x_min) / resolution)
        height = int((y_max - y_min) / resolution)

        # 创建 BEV 图像
        bev_image = np.zeros((height, width, 3), dtype=np.uint8)

        # 将点云映射到 BEV
        mask = (
            (points[:, 0] >= x_min) & (points[:, 0] <= x_max) &
            (points[:, 1] >= y_min) & (points[:, 1] <= y_max)
        )
        filtered_points = points[mask]

        # 计算像素坐标
        x_coords = ((filtered_points[:, 0] - x_min) / resolution).astype(int)
        y_coords = ((filtered_points[:, 1] - y_min) / resolution).astype(int)

        # 限制坐标范围
        x_coords = np.clip(x_coords, 0, width - 1)
        y_coords = np.clip(y_coords, 0, height - 1)

        # 绘制点云
        for i in range(len(filtered_points)):
            x, y = x_coords[i], y_coords[i]
            bev_image[y, x] = [255, 255, 255]  # 白色

        # 绘制 3D 边界框
        if boxes is not None:
            for box in boxes:
                self._draw_box_on_bev(bev_image, box, bev_range, resolution)

        # 显示 BEV 图像
        plt.figure(figsize=(10, 10))
        plt.imshow(bev_image, origin='lower')
        plt.title('鸟瞰图 (BEV)')
        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')

        # 设置刻度
        x_ticks = np.linspace(0, width, 11)
        y_ticks = np.linspace(0, height, 11)
        x_labels = np.linspace(x_min, x_max, 11)
        y_labels = np.linspace(y_min, y_max, 11)

        plt.xticks(x_ticks, [f'{x:.0f}' for x in x_labels])
        plt.yticks(y_ticks, [f'{y:.0f}' for y in y_labels])

        plt.show()

    def _draw_box_on_bev(
        self,
        image: np.ndarray,
        box: np.ndarray,
        bev_range: Tuple[float, float, float, float],
        resolution: float
    ) -> None:
        """
        在 BEV 图像上绘制边界框。

        Args:
            image: BEV 图像
            box: (7,) 3D 边界框 [x, y, z, w, l, h, θ]
            bev_range: (x_min, x_max, y_min, y_max) BEV 范围
            resolution: 分辨率
        """
        x_min, x_max, y_min, y_max = bev_range
        x, y, z, w, l, h, theta = box

        # 计算 4 个顶点 (BEV 视图)
        corners = np.array([
            [-w/2, -l/2],
            [w/2, -l/2],
            [w/2, l/2],
            [-w/2, l/2]
        ])

        # 旋转
        cos_val = np.cos(theta)
        sin_val = np.sin(theta)
        rotation_matrix = np.array([
            [cos_val, -sin_val],
            [sin_val, cos_val]
        ])
        corners = corners @ rotation_matrix.T

        # 平移
        corners[:, 0] += x
        corners[:, 1] += y

        # 转换为像素坐标
        corners[:, 0] = ((corners[:, 0] - x_min) / resolution).astype(int)
        corners[:, 1] = ((corners[:, 1] - y_min) / resolution).astype(int)

        # 限制坐标范围
        corners[:, 0] = np.clip(corners[:, 0], 0, image.shape[1] - 1)
        corners[:, 1] = np.clip(corners[:, 1], 0, image.shape[0] - 1)

        # 绘制边界框
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]

            # 使用 Bresenham 算法绘制直线
            self._draw_line(image, x1, y1, x2, y2, color=[0, 255, 0])

    def _draw_line(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: List[int]
    ) -> None:
        """
        使用 Bresenham 算法绘制直线。

        Args:
            image: 图像
            x1, y1: 起点坐标
            x2, y2: 终点坐标
            color: 颜色
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            # 绘制像素
            if 0 <= x1 < image.shape[1] and 0 <= y1 < image.shape[0]:
                image[y1, x1] = color

            # 检查是否到达终点
            if x1 == x2 and y1 == y2:
                break

            # 更新坐标
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def plot_training_curves(
        self,
        train_losses: List[float],
        val_losses: List[float],
        val_metrics: List[float],
        metric_name: str = 'mAP'
    ) -> None:
        """
        绘制训练曲线。

        Args:
            train_losses: 训练损失列表
            val_losses: 验证损失列表
            val_metrics: 验证指标列表
            metric_name: 指标名称
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 绘制损失曲线
        epochs = range(1, len(train_losses) + 1)
        ax1.plot(epochs, train_losses, 'b-', label='训练损失')
        ax1.plot(epochs, val_losses, 'r-', label='验证损失')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('损失')
        ax1.set_title('训练和验证损失')
        ax1.legend()
        ax1.grid(True)

        # 绘制指标曲线
        ax2.plot(epochs, val_metrics, 'g-', label=metric_name)
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel(metric_name)
        ax2.set_title(f'验证 {metric_name}')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.show()

    def plot_confusion_matrix(
        self,
        confusion_matrix: np.ndarray,
        class_names: List[str]
    ) -> None:
        """
        绘制混淆矩阵。

        Args:
            confusion_matrix: 混淆矩阵
            class_names: 类别名称列表
        """
        fig, ax = plt.subplots(figsize=(8, 8))

        # 绘制混淆矩阵
        im = ax.imshow(confusion_matrix, interpolation='nearest', cmap=plt.cm.Blues)
        ax.set_title('混淆矩阵')
        plt.colorbar(im, ax=ax)

        # 设置刻度
        tick_marks = np.arange(len(class_names))
        ax.set_xticks(tick_marks)
        ax.set_xticklabels(class_names, rotation=45)
        ax.set_yticks(tick_marks)
        ax.set_yticklabels(class_names)

        # 添加数值
        thresh = confusion_matrix.max() / 2.
        for i in range(confusion_matrix.shape[0]):
            for j in range(confusion_matrix.shape[1]):
                ax.text(j, i, format(confusion_matrix[i, j], 'd'),
                        ha="center", va="center",
                        color="white" if confusion_matrix[i, j] > thresh else "black")

        ax.set_ylabel('真实标签')
        ax.set_xlabel('预测标签')
        plt.tight_layout()
        plt.show()


def create_demo_visualization():
    """创建演示可视化"""
    # 创建模拟点云
    points = np.random.rand(1000, 3).astype(np.float32) * 10 - 5

    # 创建模拟边界框
    boxes = np.array([
        [0, 0, 0, 2, 4, 1.5, 0],      # 一个汽车
        [5, 5, 0, 0.6, 0.8, 1.7, 0.5], # 一个行人
        [-3, -3, 0, 0.6, 1.8, 1.7, 1.0] # 一个骑车人
    ])

    labels = np.array([0, 1, 2])  # Car, Pedestrian, Cyclist
    scores = np.array([0.95, 0.85, 0.90])

    # 创建可视化工具
    visualizer = Visualizer()

    # 可视化检测结果
    visualizer.visualize_detection_result(
        points, boxes, labels, scores,
        point_size=3.0,
        background_color=[0.1, 0.1, 0.1]
    )
