"""
交互式贝塞尔曲线绘制
====================

使用 matplotlib 的交互功能，让用户点击鼠标来添加控制点，
实时显示贝塞尔曲线。

使用方法:
    python -m examples.interactive_bezier

操作:
    - 左键点击: 添加控制点
    - 右键点击: 完成当前曲线
    - ESC: 退出
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from src.cubic_bezier import cubic_bezier_points
from src.quadratic_bezier import quadratic_bezier_points


class InteractiveBezier:
    """交互式贝塞尔曲线绘制器"""

    def __init__(self, curve_degree=3):
        self.curve_degree = curve_degree
        self.control_points = []
        self.completed_curves = []
        self.fig = None
        self.ax = None
        self.curve_line = None
        self.cp_scatter = None
        self.poly_lines = []

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_xlim(-2, 12)
        self.ax.set_ylim(-2, 10)
        self.ax.set_aspect('equal')
        self.ax.set_title('交互式贝塞尔曲线绘制\n左键点击添加控制点 | 右键完成 | ESC退出', fontsize=12)
        self.ax.grid(True, alpha=0.3)

        # 连接事件
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        # 绘制网格背景
        self.ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.2)
        self.ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.2)

        plt.show()

    def on_click(self, event):
        """处理鼠标点击事件"""
        if event.xdata is None or event.ydata is None:
            return

        if event.button == 1:  # 左键：添加控制点
            self.control_points.append([event.xdata, event.ydata])
            self.update_display()

            # 如果控制点数量达到要求，自动完成曲线
            if len(self.control_points) == self.curve_degree + 1:
                self.finish_curve()

        elif event.button == 3:  # 右键：完成当前曲线
            if len(self.control_points) >= 2:
                self.finish_curve()

    def on_key(self, event):
        """处理键盘事件"""
        if event.key == 'escape':
            plt.close()
        elif event.key == 'backspace':
            # 删除最后一个控制点
            if self.control_points:
                self.control_points.pop()
                self.update_display()
        elif event.key == 'r':
            # 重置
            self.control_points = []
            self.completed_curves = []
            self.clear_display()

    def finish_curve(self):
        """完成当前曲线并绘制"""
        if len(self.control_points) < 2:
            return

        pts = np.array(self.control_points)
        self.completed_curves.append(pts.copy())

        # 绘制曲线
        if len(pts) == 2:
            curve_pts = cubic_bezier_points(pts[0], pts[1], pts[1], pts[1], 200)
        elif len(pts) == 3:
            curve_pts = quadratic_bezier_points(pts[0], pts[1], pts[2], 200)
        elif len(pts) == 4:
            curve_pts = cubic_bezier_points(pts[0], pts[1], pts[2], pts[3], 200)
        else:
            curve_pts = pts

        self.ax.plot(curve_pts[:, 0], curve_pts[:, 1], 'b-', linewidth=2, label='曲线')

        # 清空当前控制点
        self.control_points = []
        self.update_display()

    def update_display(self):
        """更新显示"""
        self.clear_display()

        # 绘制已完成的曲线
        colors = ['b', 'r', 'g', 'm', 'c', 'y', 'k']
        for i, pts in enumerate(self.completed_curves):
            color = colors[i % len(colors)]
            if len(pts) == 2:
                curve_pts = cubic_bezier_points(pts[0], pts[1], pts[1], pts[1], 200)
            elif len(pts) == 3:
                curve_pts = quadratic_bezier_points(pts[0], pts[1], pts[2], 200)
            elif len(pts) == 4:
                curve_pts = cubic_bezier_points(pts[0], pts[1], pts[2], pts[3], 200)
            else:
                curve_pts = pts
            self.ax.plot(curve_pts[:, 0], curve_pts[:, 1], color=color, linewidth=2)
            # 绘制控制多边形
            self.ax.plot(pts[:, 0], pts[:, 1], '--', color=color, alpha=0.5)

        # 绘制当前控制点
        if self.control_points:
            pts = np.array(self.control_points)
            self.cp_scatter = self.ax.scatter(pts[:, 0], pts[:, 1], c='red', s=100, zorder=5)
            self.ax.plot(pts[:, 0], pts[:, 1], 'ro-', linewidth=2, markersize=8)
            # 绘制控制多边形
            self.ax.plot(pts[:, 0], pts[:, 1], 'r--', alpha=0.5)
            # 标注控制点
            for i, (x, y) in enumerate(pts):
                self.ax.text(x, y + 0.2, f'P{i}', ha='center', fontsize=10)

    def clear_display(self):
        """清除当前绘制"""
        if self.curve_line:
            self.curve_line.remove()
        if self.cp_scatter:
            self.cp_scatter.remove()
        for line in self.poly_lines:
            line.remove()
        self.poly_lines = []


def main():
    """主函数"""
    print("交互式贝塞尔曲线绘制")
    print("=" * 40)
    print("操作说明:")
    print("  - 左键点击: 添加控制点")
    print("  - 右键点击: 完成当前曲线")
    print("  - Backspace: 删除最后一个控制点")
    print("  - R: 重置画布")
    print("  - ESC: 退出")
    print()
    InteractiveBezier(curve_degree=3)


if __name__ == '__main__':
    main()
