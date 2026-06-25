"""
点云可视化

使用 Open3D 和 matplotlib 进行 3D 点云可视化。
"""

import numpy as np

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class PointCloudVisualizer:
    """
    点云可视化工具

    支持基本的 3D 可视化、分类结果展示和分割结果可视化。
    """

    # 类别颜色映射
    CLASS_COLORS = plt.cm.tab10(np.linspace(0, 1, 10))

    # 部件颜色映射
    PART_COLORS = plt.cm.Set3(np.linspace(0, 1, 12))

    @staticmethod
    def visualize_pointcloud(points, title="Point Cloud", save_path=None):
        """
        可视化单个点云

        Args:
            points: (N, 3) 点云坐标
            title: 标题
            save_path: 保存路径
        """
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

        ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                   c='blue', s=1, alpha=0.6)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(title)

        # 设置相同的坐标轴范围
        max_range = np.max(np.abs(points))
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"可视化已保存到 {save_path}")
        else:
            plt.show()

        plt.close()

    @staticmethod
    def visualize_classification_result(points, true_label, pred_label,
                                         class_names=None, save_path=None):
        """
        可视化分类结果

        Args:
            points: (N, 3) 点云坐标
            true_label: 真实标签
            pred_label: 预测标签
            class_names: 类别名称列表
            save_path: 保存路径
        """
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # 根据预测结果选择颜色
        color = PointCloudVisualizer.CLASS_COLORS[pred_label % 10]
        ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                   c=[color], s=1, alpha=0.6)

        # 设置标题
        if class_names:
            true_name = class_names[true_label] if true_label < len(class_names) else str(true_label)
            pred_name = class_names[pred_label] if pred_label < len(class_names) else str(pred_label)
        else:
            true_name = str(true_label)
            pred_name = str(pred_label)

        correct = "✓" if true_label == pred_label else "✗"
        ax.set_title(f"True: {true_name} | Pred: {pred_name} {correct}")

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close()

    @staticmethod
    def visualize_segmentation_result(points, seg_labels, num_parts=None,
                                       save_path=None):
        """
        可视化分割结果

        Args:
            points: (N, 3) 点云坐标
            seg_labels: (N,) 逐点标签
            num_parts: 部件数
            save_path: 保存路径
        """
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        if num_parts is None:
            num_parts = len(np.unique(seg_labels))

        # 为每个部件分配颜色
        colors = PointCloudVisualizer.PART_COLORS[seg_labels % len(PointCloudVisualizer.PART_COLORS)]

        ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                   c=colors, s=1, alpha=0.6)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f"Segmentation Result ({num_parts} parts)")

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close()

    @staticmethod
    def visualize_multiple_views(points, title="Multiple Views", save_path=None):
        """
        多角度可视化点云

        Args:
            points: (N, 3) 点云坐标
            title: 标题
            save_path: 保存路径
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5),
                                  subplot_kw={'projection': '3d'})

        views = [
            ("Front View", 0, 0),
            ("Side View", 0, 90),
            ("Top View", 90, 0),
        ]

        for ax, (view_name, elev, azim) in zip(axes, views):
            ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                       c='blue', s=1, alpha=0.6)
            ax.view_init(elev=elev, azim=azim)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(view_name)

        fig.suptitle(title, fontsize=14)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close()

    @staticmethod
    def plot_training_history(history, save_path=None):
        """
        绘制训练历史

        Args:
            history: 训练历史字典
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        epochs = range(1, len(history["train_loss"]) + 1)

        # 损失曲线
        ax1.plot(epochs, history["train_loss"], 'b-', label='Train Loss')
        if history["val_loss"]:
            ax1.plot(epochs, history["val_loss"], 'r-', label='Val Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Training Loss')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 准确率曲线
        ax2.plot(epochs, history["train_acc"], 'b-', label='Train Acc')
        if history["val_acc"]:
            ax2.plot(epochs, history["val_acc"], 'r-', label='Val Acc')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.set_title('Training Accuracy')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        else:
            plt.show()

        plt.close()

    @staticmethod
    def visualize_with_open3d(points, colors=None):
        """
        使用 Open3D 可视化点云

        Args:
            points: (N, 3) 点云坐标
            colors: (N, 3) 颜色 (0-1)
        """
        if not HAS_OPEN3D:
            print("Open3D 未安装，使用 matplotlib 替代")
            PointCloudVisualizer.visualize_pointcloud(points)
            return

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        if colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(colors)

        o3d.visualization.draw_geometries([pcd],
                                           window_name="Point Cloud",
                                           width=800, height=600)

    @staticmethod
    def create_gif_rotation(points, output_path, num_frames=36):
        """
        创建点云旋转 GIF

        Args:
            points: (N, 3) 点云坐标
            output_path: GIF 保存路径
            num_frames: 帧数
        """
        from matplotlib.animation import FuncAnimation, PillowWriter

        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection='3d')

        max_range = np.max(np.abs(points))

        def update(frame):
            ax.clear()
            ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                       c='blue', s=1, alpha=0.6)
            ax.view_init(elev=20, azim=frame * 360 / num_frames)
            ax.set_xlim([-max_range, max_range])
            ax.set_ylim([-max_range, max_range])
            ax.set_zlim([-max_range, max_range])
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(f"Rotation: {frame * 360 / num_frames:.0f}°")

        anim = FuncAnimation(fig, update, frames=num_frames, interval=100)
        anim.save(output_path, writer=PillowWriter(fps=10))
        plt.close()
        print(f"GIF 已保存到 {output_path}")
