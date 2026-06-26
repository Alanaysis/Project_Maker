"""
曲线细分可视化
==============

展示贝塞尔曲线的递归细分过程，帮助理解 De Casteljau 算法。

使用方法:
    python -m examples.subdivision_viz
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from src.cubic_bezier import cubic_bezier_points
from src.subdivision import subdivide_bezier


def visualize_subdivision():
    """可视化贝塞尔曲线的细分过程"""

    # 定义三次贝塞尔曲线的控制点
    P0 = np.array([0.0, 0.0])
    P1 = np.array([1.0, 3.0])
    P2 = np.array([4.0, 3.0])
    P3 = np.array([5.0, 0.0])
    control_points = np.array([P0, P1, P2, P3])

    # 计算原始曲线
    original_curve = cubic_bezier_points(P0, P1, P2, P3, 500)

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('贝塞尔曲线递归细分可视化', fontsize=14)

    colors = ['blue', 'red', 'green', 'purple']
    line_objs = [[], []]  # 每层左右两段的曲线
    poly_objs = [[], []]  # 每层左右两段的多边形

    def init():
        """初始化"""
        for ax in axes.flat:
            ax.set_xlim(-1, 6)
            ax.set_ylim(-1, 4)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
        return []

    def get_curve_points(ctrl_pts, num=200):
        """根据控制点数量获取曲线点"""
        if len(ctrl_pts) == 2:
            return cubic_bezier_points(ctrl_pts[0], ctrl_pts[1], ctrl_pts[1], ctrl_pts[1], num)
        elif len(ctrl_pts) == 3:
            from src.quadratic_bezier import quadratic_bezier_points
            return quadratic_bezier_points(ctrl_pts[0], ctrl_pts[1], ctrl_pts[2], num)
        elif len(ctrl_pts) == 4:
            return cubic_bezier_points(ctrl_pts[0], ctrl_pts[1], ctrl_pts[2], ctrl_pts[3], num)
        return ctrl_pts

    def update(frame):
        """动画帧更新"""
        # 清空帧
        for ax in axes.flat:
            ax.clear()
            ax.set_xlim(-1, 6)
            ax.set_ylim(-1, 4)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)

        # 绘制原始曲线（灰色）
        axes[0, 0].plot(original_curve[:, 0], original_curve[:, 1], 'gray',
                        linewidth=1, alpha=0.3, label='原始曲线')

        if frame == 0:
            # 第0层：原始控制多边形
            axes[0, 0].plot(control_points[:, 0], control_points[:, 1], 'o-',
                            color='black', linewidth=2, markersize=10, label='控制多边形')
            axes[0, 0].set_title('第 0 层：原始曲线', fontsize=12)
            axes[0, 0].legend()
            return []

        # 递归细分
        segments = [(control_points, 0)]  # (控制点, 层级)
        current_level = 0
        queue = [(control_points, 0)]

        for _ in range(frame):
            next_queue = []
            for pts, lvl in queue:
                left, right = subdivide_bezier(pts, 0.5)
                next_queue.append((left, lvl + 1))
                next_queue.append((right, lvl + 1))
            queue = next_queue
            current_level = max(lvl for _, lvl in queue)

        # 按层级组织
        level_segments = {}
        for pts, lvl in queue:
            if lvl not in level_segments:
                level_segments[lvl] = []
            level_segments[lvl].append(pts)

        # 绘制各层
        for lvl in sorted(level_segments.keys()):
            segs = level_segments[lvl]
            color = colors[lvl % len(colors)]
            alpha = max(0.3, 1.0 - lvl * 0.15)

            for i, pts in enumerate(segs):
                curve_pts = get_curve_points(pts, 100)
                axes[0, 0].plot(curve_pts[:, 0], curve_pts[:, 1], color=color,
                               linewidth=1.5, alpha=alpha)
                axes[0, 0].plot(pts[:, 0], pts[:, 1], color=color,
                               linewidth=1, alpha=alpha * 0.7, linestyle='--')

        axes[0, 0].set_title(f'第 {current_level} 层：{len(queue)} 段', fontsize=12)
        axes[0, 0].legend()

        # 显示细分点
        if frame > 0:
            mid_pts = []
            for pts in level_segments.get(current_level, []):
                mid_pts.append(get_curve_points(pts, 50)[len(get_curve_points(pts, 50)) // 2])
            if mid_pts:
                mid_pts = np.array(mid_pts)
                axes[0, 0].scatter(mid_pts[:, 0], mid_pts[:, 1], c='yellow', s=50, zorder=5)

        # 细分过程可视化
        if frame <= 4:
            # 显示细分步骤
            left, right = subdivide_bezier(control_points, 0.5)

            ax1 = axes[0, 1]
            ax1.set_xlim(-1, 6)
            ax1.set_ylim(-1, 4)
            ax1.set_aspect('equal')
            ax1.grid(True, alpha=0.3)

            # 原始
            ax1.plot(original_curve[:, 0], original_curve[:, 1], 'gray',
                    linewidth=1, alpha=0.3)
            ax1.plot(control_points[:, 0], control_points[:, 1], 'k--', alpha=0.3)

            # 左段
            left_curve = get_curve_points(left, 200)
            ax1.plot(left_curve[:, 0], left_curve[:, 1], 'b-', linewidth=2, label='左段')
            ax1.plot(left[:, 0], left[:, 1], 'bo--', alpha=0.7, markersize=6)

            # 右段
            right_curve = get_curve_points(right, 200)
            ax1.plot(right_curve[:, 0], right_curve[:, 1], 'r-', linewidth=2, label='右段')
            ax1.plot(right[:, 0], right[:, 1], 'r--', alpha=0.7, markersize=6)

            ax1.set_title(f'第一次细分 (t=0.5)', fontsize=12)
            ax1.legend()

            # De Casteljau 中间步骤
            ax2 = axes[1, 0]
            ax2.set_xlim(-1, 6)
            ax2.set_ylim(-1, 4)
            ax2.set_aspect('equal')
            ax2.grid(True, alpha=0.3)

            # 显示 De Casteljau 的中间点
            n = len(control_points) - 1
            work = [control_points.copy()]
            for r in range(1, n + 1):
                prev = work[-1]
                current = np.zeros((len(prev) - 1, 2))
                for i in range(len(prev) - 1):
                    current[i] = 0.5 * prev[i] + 0.5 * prev[i + 1]
                work.append(current)

            # 绘制各层
            for r, pts in enumerate(work):
                ax2.plot(pts[:, 0], pts[:, 1], 'o-', color=colors[r % len(colors)],
                        linewidth=1.5, markersize=8, alpha=0.8,
                        label=f'第{r}层')

            ax2.set_title('De Casteljau 中间步骤', fontsize=12)
            ax2.legend(fontsize=8)

            # 细分点坐标
            ax3 = axes[1, 1]
            ax3.set_xlim(-1, 6)
            ax3.set_ylim(-1, 4)
            ax3.set_aspect('equal')
            ax3.grid(True, alpha=0.3)

            # 显示最终细分结果
            ax3.plot(left_curve[:, 0], left_curve[:, 1], 'b-', linewidth=2, label='左段曲线')
            ax3.plot(right_curve[:, 0], right_curve[:, 1], 'r-', linewidth=2, label='右段曲线')
            ax3.plot(control_points[:, 0], control_points[:, 1], 'k--', alpha=0.3, label='原始多边形')
            ax3.scatter([0.5], [0], c='yellow', s=100, zorder=5, label='分割点')

            ax3.set_title('细分结果对比', fontsize=12)
            ax3.legend(fontsize=8)

        return []

    # 创建动画
    num_frames = 8
    anim = FuncAnimation(fig, update, frames=num_frames, init_func=init,
                        interval=800, repeat=True)

    plt.tight_layout()
    plt.savefig('subdivision_viz.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("细分可视化图像已保存为 subdivision_viz.png")


if __name__ == '__main__':
    visualize_subdivision()
