"""
动画曲线渲染
=============

使用 matplotlib 动画功能，动态展示贝塞尔曲线的绘制过程。

使用方法:
    python -m examples.animated_rendering
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from src.cubic_bezier import cubic_bezier_points
from src.quadratic_bezier import quadratic_bezier_points
from src.linear_bezier import linear_bezier_points
from src.tangent_normal import unit_tangent, unit_normal
from src.curve_length import curve_length_numerical


def animate_bezier_draw():
    """动画展示贝塞尔曲线的逐步绘制"""

    # 定义多条贝塞尔曲线
    curves = [
        {
            'name': '线性曲线',
            'type': 'linear',
            'control_points': [np.array([0, 0]), np.array([3, 3])],
            'color': 'blue'
        },
        {
            'name': '二次贝塞尔曲线',
            'type': 'quadratic',
            'control_points': [np.array([4, 0]), np.array([5.5, 3]), np.array([7, 0])],
            'color': 'red'
        },
        {
            'name': '三次贝塞尔曲线',
            'type': 'cubic',
            'control_points': [np.array([0.5, 4]), np.array([1.5, 6]),
                              np.array([4.5, 6]), np.array([5.5, 4])],
            'color': 'green'
        },
        {
            'name': 'S型曲线',
            'type': 'cubic',
            'control_points': [np.array([6, 4]), np.array([7, 6]),
                              np.array([9, 6]), np.array([10, 4])],
            'color': 'purple'
        },
    ]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 7)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('贝塞尔曲线动画渲染', fontsize=14)

    # 存储各条曲线的对象
    curve_lines = []
    ctrl_markers = []
    tangent_arrows = []
    normal_arrows = []
    length_text = []

    def init():
        for line in curve_lines:
            line.remove()
        for markers in ctrl_markers:
            for m in markers:
                m.remove()
        for arrows in tangent_arrows:
            for a in arrows:
                a.remove()
        for arrows in normal_arrows:
            for a in arrows:
                a.remove()
        for t in length_text:
            t.remove()
        curve_lines.clear()
        ctrl_markers.clear()
        tangent_arrows.clear()
        normal_arrows.clear()
        length_text.clear()
        return []

    def get_curve_pts(ctrl_pts, curve_type, num=100):
        """根据曲线类型获取采样点"""
        if curve_type == 'linear':
            return linear_bezier_points(ctrl_pts[0], ctrl_pts[1], num)
        elif curve_type == 'quadratic':
            return quadratic_bezier_points(ctrl_pts[0], ctrl_pts[1], ctrl_pts[2], num)
        elif curve_type == 'cubic':
            return cubic_bezier_points(ctrl_pts[0], ctrl_pts[1], ctrl_pts[2], ctrl_pts[3], num)
        return np.array(ctrl_pts)

    def update(frame):
        """动画帧更新"""
        curve_lines.clear()
        ctrl_markers.clear()
        tangent_arrows.clear()
        normal_arrows.clear()
        length_text.clear()

        for curve in curves:
            ctrl_pts = curve['control_points']
            color = curve['color']
            curve_type = curve['type']

            # 绘制控制多边形
            ctrl_array = np.array(ctrl_pts)
            ax.plot(ctrl_array[:, 0], ctrl_array[:, 1], '--', color=color,
                   alpha=0.4, linewidth=1)
            ax.scatter(ctrl_array[:, 0], ctrl_array[:, 1], c=color, s=60, zorder=5)

            # 逐步绘制曲线
            full_curve = get_curve_pts(ctrl_pts, curve_type, 500)
            progress = min(frame / 100.0, 1.0)
            num_pts = int(len(full_curve) * progress)

            if num_pts > 1:
                partial_curve = full_curve[:num_pts]
                line = ax.plot(partial_curve[:, 0], partial_curve[:, 1],
                             color=color, linewidth=3, zorder=3)[0]
                curve_lines.append(line)

                # 在曲线末端绘制切线和法线
                if num_pts > 10:
                    end_point = partial_curve[-1]
                    t_val = max(0.01, progress - 0.001)

                    # 计算当前曲线的切线
                    if curve_type == 'linear':
                        tangent = unit_tangent(np.array([ctrl_pts[0], ctrl_pts[1]]), t_val)
                    elif curve_type == 'quadratic':
                        tangent = unit_tangent(np.array(ctrl_pts), t_val)
                    elif curve_type == 'cubic':
                        tangent = unit_tangent(np.array(ctrl_pts), t_val)
                    else:
                        tangent = np.array([1, 0])

                    normal = unit_normal(np.array(ctrl_pts), t_val)

                    arrow_scale = 0.5
                    # 切线箭头
                    t_arrow = ax.arrow(end_point[0], end_point[1],
                                     tangent[0] * arrow_scale, tangent[1] * arrow_scale,
                                     head_width=0.1, head_length=0.05,
                                     fc='yellow', ec='yellow', alpha=0.8)
                    tangent_arrows.append(t_arrow)

                    # 法线箭头
                    n_arrow = ax.arrow(end_point[0], end_point[1],
                                     normal[0] * arrow_scale, normal[1] * arrow_scale,
                                     head_width=0.1, head_length=0.05,
                                     fc='cyan', ec='cyan', alpha=0.8)
                    normal_arrows.append(n_arrow)

                    # 标注长度
                    length = curve_length_numerical(np.array(ctrl_pts), 500)
                    mid_idx = num_pts // 2
                    text = ax.text(partial_curve[mid_idx][0], partial_curve[mid_idx][1] + 0.3,
                                 f'{curve["name"]}: L={length:.2f}',
                                 fontsize=9, color=color)
                    length_text.append(text)

        return []

    # 创建动画
    anim = FuncAnimation(fig, update, frames=101, init_func=init,
                        interval=50, repeat=True, repeat_delay=1000)

    plt.tight_layout()
    plt.savefig('animated_rendering.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("动画渲染结果已保存为 animated_rendering.png")


def animate_de_casteljau():
    """动画展示 De Casteljau 算法的递归过程"""

    # 三次贝塞尔曲线的控制点
    P0 = np.array([1.0, 1.0])
    P1 = np.array([3.0, 5.0])
    P2 = np.array([7.0, 5.0])
    P3 = np.array([9.0, 1.0])
    control_points = np.array([P0, P1, P2, P3])

    # 计算完整曲线
    full_curve = cubic_bezier_points(P0, P1, P2, P3, 500)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title("De Casteljau 算法动画", fontsize=14)

    t_value = 0.4  # 细分参数

    def init():
        ax.clear()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        return []

    def update(frame):
        ax.clear()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        # 计算 De Casteljau 的各层点
        n = len(control_points) - 1
        work = [control_points.copy()]

        for r in range(1, n + 1):
            prev = work[-1]
            current = np.zeros((len(prev) - 1, 2))
            for i in range(len(prev) - 1):
                current[i] = (1 - t_value) * prev[i] + t_value * prev[i + 1]
            work.append(current)

        # 显示动画进度
        current_layer = min(frame // 10, n)

        colors = ['blue', 'red', 'green', 'purple', 'orange']
        for r in range(current_layer + 1):
            pts = work[r]
            alpha = max(0.3, 1.0 - r * 0.2)
            ax.plot(pts[:, 0], pts[:, 1], 'o-', color=colors[r % len(colors)],
                   linewidth=2, markersize=8, alpha=alpha,
                   label=f'第{r}层')

        # 显示最终结果
        if current_layer >= n:
            result_point = work[n][0]
            ax.scatter(result_point[0], result_point[1], c='yellow', s=200,
                      zorder=5, marker='*', label='B(t)')

            # 显示曲线
            ax.plot(full_curve[:, 0], full_curve[:, 1], 'k-', alpha=0.3,
                   linewidth=1, label='完整曲线')

        ax.set_title(f"De Casteljau 算法 (t={t_value})\n当前层: {current_layer}/{n}",
                    fontsize=12)
        ax.legend(fontsize=9)

        return []

    anim = FuncAnimation(fig, update, frames=60, init_func=init,
                        interval=100, repeat=True)

    plt.tight_layout()
    plt.savefig('de_casteljau_anim.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("De Casteljau 动画已保存为 de_casteljau_anim.png")


if __name__ == '__main__':
    print("选择要运行的动画:")
    print("  1. 贝塞尔曲线逐步绘制")
    print("  2. De Casteljau 算法动画")
    print()

    choice = input("请输入选项 (1/2): ").strip()

    if choice == '1':
        animate_bezier_draw()
    elif choice == '2':
        animate_de_casteljau()
    else:
        print("无效选项，运行曲线绘制动画")
        animate_bezier_draw()
