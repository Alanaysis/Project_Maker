"""
可视化模块 (Visualization Module)

提供FEM结果的可视化功能，包括网格、位移、应力云图等。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端 (non-interactive backend)
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.tri import Triangulation
from typing import Optional, List, Tuple


def plot_mesh(
    nodes: np.ndarray,
    elements: List[List[int]],
    title: str = "Finite Element Mesh",
    filename: str = "mesh.png",
    show_nodes: bool = True,
    show_elements: bool = True,
    aspect: str = 'equal',
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """
    绘制有限元网格 (Plot FEM mesh)

    参数:
        nodes: 节点坐标 (N, 2)
        elements: 单元连接表
        title: 标题
        filename: 输出文件名
        show_nodes: 是否显示节点
        show_elements: 是否显示单元
        aspect: 坐标轴比例
        figsize: 图形大小

    返回:
        fig: matplotlib Figure对象
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    if show_elements:
        # 绘制单元
        for elem in elements:
            # 获取单元节点坐标
            elem_nodes = nodes[elem]
            # 闭合多边形
            polygon = np.vstack([elem_nodes, elem_nodes[0]])
            ax.plot(polygon[:, 0], polygon[:, 1], 'k-', linewidth=0.5)

    if show_nodes:
        # 绘制节点
        ax.scatter(nodes[:, 0], nodes[:, 1], c='r', s=10, zorder=5)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect(aspect)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return fig


def plot_displacement(
    nodes: np.ndarray,
    elements: List[List[int]],
    displacement: np.ndarray,
    scale: float = 1.0,
    title: str = "Displacement Field",
    filename: str = "displacement.png",
    figsize: Tuple[int, int] = (12, 5)
) -> Tuple[plt.Figure, plt.Figure]:
    """
    绘制位移云图和变形形状 (Plot displacement contour and deformed shape)

    参数:
        nodes: 原始节点坐标
        elements: 单元连接表
        displacement: 节点位移向量
        scale: 变形缩放因子
        title: 标题
        filename: 输出文件名前缀
        figsize: 图形大小

    返回:
        figs: [位移云图, 变形图]
    """
    num_nodes = len(nodes)
    ux = displacement[0:num_nodes:2]
    uy = displacement[1:num_nodes:2]

    # 位移大小
    displacement_magnitude = np.sqrt(ux**2 + uy**2)

    # ---- 位移云图 ----
    fig1, ax1 = plt.subplots(1, 1, figsize=figsize)

    # 使用三角插值绘制云图
    for elem in elements:
        elem_nodes = nodes[elem]
        elem_disp = [displacement_magnitude[n] for n in elem]

        # 创建三角形
        tri = Triangulation(elem_nodes[:, 0], elem_nodes[:, 1])
        # 简化: 直接填充三角形
        polygon = np.vstack([elem_nodes, elem_nodes[0]])
        mean_disp = np.mean(elem_disp)
        cmap = cm.viridis
        norm = matplotlib.colors.Normalize(vmin=0, vmax=np.max(displacement_magnitude))
        color = cmap(norm(mean_disp))
        ax1.fill(polygon[:, 0], polygon[:, 1], color=color, alpha=0.8)

    # 绘制节点
    ax1.scatter(nodes[:, 0], nodes[:, 1], c=displacement_magnitude, cmap='viridis',
                s=20, edgecolors='black', linewidth=0.5, zorder=5)
    ax1.set_title(f'{title} (Max: {np.max(displacement_magnitude):.6f})', fontsize=12)
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3)
    plt.colorbar(cm.ScalarMappable(norm=norm, cmap='viridis'), ax=ax1, label='Displacement')

    plt.tight_layout()
    fig1.savefig(f'{filename}_displacement.png', dpi=150, bbox_inches='tight')
    plt.close(fig1)

    # ---- 变形形状 ----
    fig2, ax2 = plt.subplots(1, 1, figsize=figsize)

    # 原始网格
    for elem in elements:
        elem_nodes = nodes[elem]
        polygon = np.vstack([elem_nodes, elem_nodes[0]])
        ax2.plot(polygon[:, 0], polygon[:, 1], 'k-', linewidth=0.3, alpha=0.3)

    # 变形后网格
    deformed_nodes = nodes.copy()
    deformed_nodes[:, 0] += scale * ux
    deformed_nodes[:, 1] += scale * uy

    for elem in elements:
        elem_nodes = deformed_nodes[elem]
        polygon = np.vstack([elem_nodes, elem_nodes[0]])
        ax2.plot(polygon[:, 0], polygon[:, 1], 'r-', linewidth=0.5)

    ax2.scatter(nodes[:, 0], nodes[:, 1], c='b', s=10, zorder=5)
    ax2.scatter(deformed_nodes[:, 0], deformed_nodes[:, 1], c='r', s=10, zorder=5)
    ax2.set_title('Deformed Shape (scaled by {:.1f})'.format(scale), fontsize=12)
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.3)
    ax2.legend(['Original', 'Deformed'])

    plt.tight_layout()
    fig2.savefig(f'{filename}_deformed.png', dpi=150, bbox_inches='tight')
    plt.close(fig2)

    return fig1, fig2


def plot_stress(
    nodes: np.ndarray,
    elements: List[List[int]],
    element_stresses: List[np.ndarray],
    stress_type: str = "von_mises",
    title: str = "Stress Distribution",
    filename: str = "stress.png",
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    绘制应力云图 (Plot stress contour)

    参数:
        nodes: 节点坐标
        elements: 单元连接表
        element_stresses: 每个单元的应力值或应力向量
        stress_type: 'von_mises' 或 'sigma_x' 等
        title: 标题
        filename: 输出文件名
        figsize: 图形大小

    返回:
        fig: matplotlib Figure对象
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # 提取应力值
    if stress_type == "von_mises":
        stress_values = [
            np.sqrt(s[0]**2 - s[0]*s[1] + s[1]**2 + 3*s[2]**2)
            if isinstance(s, np.ndarray) and len(s) >= 3 else s
            for s in element_stresses
        ]
    elif isinstance(element_stresses[0], np.ndarray):
        stress_values = [s[0] if len(s) > 0 else 0 for s in element_stresses]
    else:
        stress_values = element_stresses

    max_stress = max(stress_values) if stress_values else 1.0
    min_stress = min(stress_values) if stress_values else 0.0

    # 绘制应力云图
    for elem, stress_val in zip(elements, stress_values):
        elem_nodes = nodes[elem]
        polygon = np.vstack([elem_nodes, elem_nodes[0]])

        cmap = cm.viridis if stress_type == "von_mises" else cm.plasma
        norm = matplotlib.colors.Normalize(vmin=min_stress, vmax=max_stress)
        color = cmap(norm(stress_val))
        ax.fill(polygon[:, 0], polygon[:, 1], color=color, alpha=0.8, edgecolor='k', linewidth=0.3)

    ax.set_title(f'{title} (Min: {min_stress:.4f}, Max: {max_stress:.4f})', fontsize=12)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    plt.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label=stress_type)

    plt.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return fig


def plot_convergence(
    mesh_sizes: List[float],
    values: List[float],
    analytical: Optional[float] = None,
    title: str = "Mesh Convergence Study",
    filename: str = "convergence.png"
) -> plt.Figure:
    """
    绘制网格收敛性分析图 (Plot mesh convergence study)

    参数:
        mesh_sizes: 网格尺寸列表 (越小越密)
        values: 对应的计算值
        analytical: 解析解 (可选)
        title: 标题
        filename: 输出文件名

    返回:
        fig: matplotlib Figure对象
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    ax.plot(mesh_sizes, values, 'bo-', linewidth=2, markersize=8, label='FEM Result')

    if analytical is not None:
        ax.axhline(y=analytical, color='r', linestyle='--', linewidth=2, label='Analytical Solution')
        ax.axhspan(analytical * 0.95, analytical * 1.05, alpha=0.1, color='r',
                   label='±5% tolerance')

    ax.set_xlabel('Element Size', fontsize=12)
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

    plt.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return fig


def create_visualization_dashboard(
    nodes: np.ndarray,
    elements: List[List[int]],
    displacement: np.ndarray,
    element_stresses: List[np.ndarray],
    output_prefix: str = "fem_results"
) -> None:
    """
    创建完整的FEM结果仪表盘 (Create complete FEM results dashboard)

    生成所有可视化图表:
    1. 原始网格
    2. 位移云图
    3. 变形形状
    4. Von Mises应力云图

    参数:
        nodes: 节点坐标
        elements: 单元连接表
        displacement: 节点位移向量
        element_stresses: 每个单元的应力
        output_prefix: 输出文件前缀
    """
    # 1. 网格
    plot_mesh(nodes, elements, title="Finite Element Mesh",
              filename=f"{output_prefix}_mesh.png")

    # 2. 位移
    ux = displacement[0:len(nodes):2]
    uy = displacement[1:len(nodes):2]
    max_disp = np.sqrt(np.max(ux**2) + np.max(uy**2))
    scale = max(1.0, 100.0 / max(max_disp, 1e-10))

    plot_displacement(nodes, elements, displacement, scale=scale,
                      title="Displacement Field",
                      filename=f"{output_prefix}_disp")

    # 3. 应力
    plot_stress(nodes, elements, element_stresses, stress_type="von_mises",
                title="Von Mises Stress Distribution",
                filename=f"{output_prefix}_stress.png")

    print(f"Visualizations saved with prefix: {output_prefix}")


def plot_beam_deformation(
    nodes: np.ndarray,
    elements: List[List[int]],
    displacement: np.ndarray,
    title: str = "Beam Deformation",
    filename: str = "beam_deformation.png",
    scale: float = 10.0
) -> plt.Figure:
    """
    专门用于梁弯曲变形的可视化 (Specialized visualization for beam bending)

    参数:
        nodes: 节点坐标
        elements: 单元连接表
        displacement: 节点位移向量
        title: 标题
        filename: 输出文件名
        scale: 变形缩放因子

    返回:
        fig: matplotlib Figure对象
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 原始形状
    ax0 = axes[0]
    # 提取中心线节点 (y = height/2)
    center_mask = np.abs(nodes[:, 1] - nodes.shape[0] * 0.0) < 0.01  # 简化
    if not np.any(center_mask):
        center_mask = nodes[:, 1] >= np.max(nodes[:, 1]) * 0.99
    center_nodes = nodes[center_mask]
    if len(center_nodes) > 1:
        sorted_idx = np.argsort(center_nodes[:, 0])
        ax0.plot(center_nodes[sorted_idx, 0], center_nodes[sorted_idx, 1], 'k-', linewidth=2)
    ax0.set_title('Original Shape')
    ax0.set_xlabel('X')
    ax0.set_ylabel('Y')
    ax0.set_aspect('equal')
    ax0.grid(True)

    # 变形形状
    ax1 = axes[1]
    deformed = nodes.copy()
    ux = displacement[0:len(nodes):2]
    uy = displacement[1:len(nodes):2]
    deformed[:, 0] += scale * ux
    deformed[:, 1] += scale * uy

    if len(center_nodes) > 1:
        deformed_center = deformed[center_mask]
        sorted_idx = np.argsort(deformed_center[:, 0])
        ax1.plot(deformed_center[sorted_idx, 0], deformed_center[sorted_idx, 1], 'r-', linewidth=2)
    ax1.set_title(f'Deformed Shape (x{scale})')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_aspect('equal')
    ax1.grid(True)

    # 挠度曲线
    ax2 = axes[2]
    if len(center_nodes) > 1:
        sorted_idx = np.argsort(center_nodes[:, 0])
        deflection = uy[center_mask][sorted_idx]
        ax2.plot(center_nodes[sorted_idx, 0], deflection, 'b-', linewidth=2)
    ax2.set_title('Deflection Curve (uy)')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Deflection uy')
    ax2.grid(True)

    plt.suptitle(title, fontsize=14)
    plt.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return fig
