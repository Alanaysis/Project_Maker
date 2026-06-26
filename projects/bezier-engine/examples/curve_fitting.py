"""
曲线拟合（从点集生成贝塞尔曲线）
================================

使用最小二乘法拟合贝塞尔曲线到给定的数据点集。

数学基础:
    给定数据点 {q₀, q₁, ..., qₘ} 和曲线次数 n，
    寻找控制点 P₀, P₁, ..., Pₙ 使得:
        min Σ ||B(tᵢ) - qᵢ||²

    这转化为线性方程组求解问题。

使用方法:
    python -m examples.curve_fitting
"""

import numpy as np
import matplotlib.pyplot as plt
from src.cubic_bezier import cubic_bezier_points


def chord_length_parameterization(points: np.ndarray) -> np.ndarray:
    """
    弦长参数化。

    为每个数据点分配参数 t，使用相邻点之间的欧几里得距离的累积和。

    参数:
        points: 数据点数组，形状为 (m, 2)

    返回:
        参数值数组，形状为 (m,)
    """
    if len(points) < 2:
        return np.linspace(0, 1, len(points))

    # 计算相邻点之间的距离
    diffs = np.diff(points, axis=0)
    distances = np.linalg.norm(diffs, axis=1)

    # 累积距离
    cumulative = np.zeros(len(points))
    cumulative[1:] = np.cumsum(distances)

    # 归一化到 [0, 1]
    if cumulative[-1] > 0:
        cumulative /= cumulative[-1]

    return cumulative


def fit_cubic_bezier(points: np.ndarray, num_iterations: int = 5) -> np.ndarray:
    """
    使用迭代最小二乘法拟合三次贝塞尔曲线到数据点。

    参数:
        points: 数据点数组，形状为 (m, 2)
        num_iterations: 迭代次数

    返回:
        拟合的控制点数组，形状为 (4, 2)
    """
    if len(points) < 2:
        raise ValueError("至少需要2个数据点")

    # 初始参数化
    t = chord_length_parameterization(points)

    # 初始控制点：P0 = 第一个点, P3 = 最后一个点
    P0 = points[0]
    P3 = points[-1]

    for iteration in range(num_iterations):
        # 构建矩阵方程 A * [P1, P2]^T = b
        # 对于每个数据点 qᵢ，有:
        #   B(tᵢ) = (1-tᵢ)³·P0 + 3(1-tᵢ)²tᵢ·P1 + 3(1-tᵢ)tᵢ²·P2 + tᵢ³·P3
        # 移项:
        #   3(1-tᵢ)²tᵢ·P1 + 3(1-tᵢ)tᵢ²·P2 = qᵢ - (1-tᵢ)³·P0 - tᵢ³·P3

        A = []
        b = []

        for i, (ti, qi) in enumerate(zip(t, points)):
            u = 1.0 - ti
            # 系数矩阵
            a11 = 3.0 * u * u * ti   # P1 的系数
            a12 = 3.0 * u * ti * ti  # P2 的系数
            A.append([a11, a12])

            # 右侧向量
            bi = qi - u * u * u * P0 - ti * ti * ti * P3
            b.append(bi)

        A = np.array(A)
        b = np.array(b)

        # 求解最小二乘: [P1, P2] = (A^T A)^{-1} A^T b
        # 分别求解 x 和 y 分量
        AtA = A.T @ A
        Atb_x = A.T @ b[:, 0]
        Atb_y = A.T @ b[:, 1]

        P1_x, P2_x = np.linalg.solve(AtA, Atb_x)
        P1_y, P2_y = np.linalg.solve(AtA, Atb_y)

        P1 = np.array([P1_x, P1_y])
        P2 = np.array([P2_x, P2_y])

        # 重新参数化（使用拟合曲线的弦长）
        curve_pts = cubic_bezier_points(P0, P1, P2, P3, len(points))
        t = chord_length_parameterization(curve_pts)

    return np.array([P0, P1, P2, P3])


def fit_multiple_cubic_beziers(points: np.ndarray, segments: int = 3) -> list:
    """
    将数据点分割为多段，每段拟合一条三次贝塞尔曲线。

    参数:
        points: 数据点数组
        segments: 分段数量

    返回:
        控制点列表
    """
    n = len(points)
    segment_size = n // segments
    control_points_list = []

    for i in range(segments):
        start = i * segment_size
        end = start + segment_size + 1 if i < segments - 1 else n

        # 取该段的子集
        segment_points = points[start:end]

        if len(segment_points) >= 2:
            ctrl = fit_cubic_bezier(segment_points)
            control_points_list.append(ctrl)

    return control_points_list


def main():
    """主函数：演示曲线拟合"""

    # 生成测试数据
    np.random.seed(42)

    # 定义原始控制点
    true_P0 = np.array([0.0, 0.0])
    true_P1 = np.array([1.0, 3.0])
    true_P2 = np.array([4.0, 3.0])
    true_P3 = np.array([5.0, 0.0])

    # 生成曲线上的点并添加噪声
    t_true = np.linspace(0, 1, 50)
    true_curve = np.array([
        (1 - t)**3 * true_P0 + 3*(1-t)**2*t * true_P1 +
        3*(1-t)*t**2 * true_P2 + t**3 * true_P3
        for t in t_true
    ])

    # 添加噪声
    noise = np.random.randn(50, 2) * 0.1
    noisy_points = true_curve + noise

    # 拟合曲线
    fitted_ctrl = fit_cubic_bezier(noisy_points)

    # 绘制结果
    fig, ax = plt.subplots(figsize=(10, 8))

    # 原始曲线
    true_curve_pts = cubic_bezier_points(true_P0, true_P1, true_P2, true_P3, 200)
    ax.plot(true_curve_pts[:, 0], true_curve_pts[:, 1], 'g-', linewidth=2,
           label='原始曲线', alpha=0.7)

    # 原始控制多边形
    ax.plot([true_P0[0], true_P1[0], true_P2[0], true_P3[0]],
           [true_P0[1], true_P1[1], true_P2[1], true_P3[1]],
           'g--', alpha=0.5, label='原始控制多边形')

    # 噪声数据点
    ax.scatter(noisy_points[:, 0], noisy_points[:, 1], c='red', s=20,
              alpha=0.6, label='噪声数据点')

    # 拟合曲线
    fitted_curve = cubic_bezier_points(fitted_ctrl[0], fitted_ctrl[1],
                                        fitted_ctrl[2], fitted_ctrl[3], 200)
    ax.plot(fitted_curve[:, 0], fitted_curve[:, 1], 'b-', linewidth=2,
           label='拟合曲线')

    # 拟合控制多边形
    ax.plot([fitted_ctrl[0][0], fitted_ctrl[1][0], fitted_ctrl[2][0], fitted_ctrl[3][0]],
           [fitted_ctrl[0][1], fitted_ctrl[1][1], fitted_ctrl[2][1], fitted_ctrl[3][1]],
           'b--', alpha=0.5, label='拟合控制多边形')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('贝塞尔曲线拟合（从噪声数据点）')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig('curve_fitting.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("曲线拟合结果已保存为 curve_fitting.png")

    # 打印控制点
    print("\n原始控制点:")
    print(f"  P0 = {true_P0}")
    print(f"  P1 = {true_P1}")
    print(f"  P2 = {true_P2}")
    print(f"  P3 = {true_P3}")
    print("\n拟合控制点:")
    for i, p in enumerate(fitted_ctrl):
        print(f"  P{i} = {p}")


if __name__ == '__main__':
    main()
