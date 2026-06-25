"""
滤波器可视化工具
================

提供波特图、相频响应图、阶跃响应图等可视化功能。

功能:
- 波特图 (幅频 + 相频)
- 幅频响应图
- 相频响应图
- 阶跃响应图
- 冲激响应图
- 多滤波器对比图
- 极零点图
"""

import numpy as np
from typing import Optional, List, Tuple

try:
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _check_matplotlib():
    """检查 matplotlib 是否可用"""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib 未安装。请运行: pip install matplotlib"
        )


def plot_bode(filter_obj, f: np.ndarray,
              title: str = "波特图",
              save_path: Optional[str] = None,
              figsize: Tuple[float, float] = (10, 8)) -> None:
    """绘制波特图 (幅频响应 + 相频响应)

    Parameters
    ----------
    filter_obj
        滤波器对象，需要有 magnitude_db 和 phase 方法
    f : np.ndarray
        频率数组 (Hz)
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    mag_db = filter_obj.magnitude_db(f)
    phase_deg = filter_obj.phase(f)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    # 幅频响应
    ax1.semilogx(f, mag_db, 'b-', linewidth=1.5)
    ax1.set_ylabel('幅度 (dB)', fontsize=12)
    ax1.set_title(title, fontsize=14)
    ax1.grid(True, which='both', linestyle='--', alpha=0.7)
    ax1.axhline(y=-3, color='r', linestyle=':', alpha=0.5, label='-3 dB')
    ax1.legend()
    ax1.set_ylim([-60, 5])

    # 相频响应
    ax2.semilogx(f, phase_deg, 'g-', linewidth=1.5)
    ax2.set_xlabel('频率 (Hz)', fontsize=12)
    ax2.set_ylabel('相位 (度)', fontsize=12)
    ax2.grid(True, which='both', linestyle='--', alpha=0.7)
    ax2.set_yticks([-180, -135, -90, -45, 0, 45, 90])

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_magnitude(filter_obj, f: np.ndarray,
                   title: str = "幅频响应",
                   save_path: Optional[str] = None,
                   figsize: Tuple[float, float] = (10, 5)) -> None:
    """绘制幅频响应图

    Parameters
    ----------
    filter_obj
        滤波器对象
    f : np.ndarray
        频率数组 (Hz)
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    mag_db = filter_obj.magnitude_db(f)

    fig, ax = plt.subplots(figsize=figsize)
    ax.semilogx(f, mag_db, 'b-', linewidth=1.5)
    ax.set_xlabel('频率 (Hz)', fontsize=12)
    ax.set_ylabel('幅度 (dB)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.axhline(y=-3, color='r', linestyle=':', alpha=0.5, label='-3 dB')
    ax.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_phase(filter_obj, f: np.ndarray,
               title: str = "相频响应",
               save_path: Optional[str] = None,
               figsize: Tuple[float, float] = (10, 5)) -> None:
    """绘制相频响应图

    Parameters
    ----------
    filter_obj
        滤波器对象
    f : np.ndarray
        频率数组 (Hz)
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    phase_deg = filter_obj.phase(f)

    fig, ax = plt.subplots(figsize=figsize)
    ax.semilogx(f, phase_deg, 'g-', linewidth=1.5)
    ax.set_xlabel('频率 (Hz)', fontsize=12)
    ax.set_ylabel('相位 (度)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_step_response(filter_obj, t: np.ndarray,
                       title: str = "阶跃响应",
                       save_path: Optional[str] = None,
                       figsize: Tuple[float, float] = (10, 5)) -> None:
    """绘制阶跃响应图

    Parameters
    ----------
    filter_obj
        滤波器对象，需要有 step_response 方法
    t : np.ndarray
        时间数组 (秒)
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    step = filter_obj.step_response(t)

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(t * 1000, step, 'b-', linewidth=1.5, label='阶跃响应')
    ax.axhline(y=1.0, color='r', linestyle=':', alpha=0.5, label='终值')
    ax.axhline(y=0.632, color='g', linestyle=':', alpha=0.5, label='63.2% (1τ)')
    ax.set_xlabel('时间 (ms)', fontsize=12)
    ax.set_ylabel('幅度', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_impulse_response(filter_obj, t: np.ndarray,
                          title: str = "冲激响应",
                          save_path: Optional[str] = None,
                          figsize: Tuple[float, float] = (10, 5)) -> None:
    """绘制冲激响应图

    Parameters
    ----------
    filter_obj
        滤波器对象，需要有 impulse_response 方法
    t : np.ndarray
        时间数组 (秒)
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    impulse = filter_obj.impulse_response(t)

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(t * 1000, impulse, 'b-', linewidth=1.5)
    ax.set_xlabel('时间 (ms)', fontsize=12)
    ax.set_ylabel('幅度', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_comparison(filters: list, f: np.ndarray,
                    labels: Optional[List[str]] = None,
                    title: str = "滤波器对比",
                    save_path: Optional[str] = None,
                    figsize: Tuple[float, float] = (12, 6)) -> None:
    """对比多个滤波器的频率响应

    Parameters
    ----------
    filters : list
        滤波器对象列表
    f : np.ndarray
        频率数组 (Hz)
    labels : List[str], optional
        标签列表
    title : str
        图表标题
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    if labels is None:
        labels = [f"Filter {i+1}" for i in range(len(filters))]

    colors = ['b', 'r', 'g', 'm', 'c', 'y', 'k']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    for i, (filt, label) in enumerate(zip(filters, labels)):
        color = colors[i % len(colors)]
        mag_db = filt.magnitude_db(f)
        phase_deg = filt.phase(f)

        ax1.semilogx(f, mag_db, color=color, linewidth=1.5, label=label)
        ax2.semilogx(f, phase_deg, color=color, linewidth=1.5, label=label)

    ax1.set_ylabel('幅度 (dB)', fontsize=12)
    ax1.set_title(title, fontsize=14)
    ax1.grid(True, which='both', linestyle='--', alpha=0.7)
    ax1.legend()
    ax1.set_ylim([-60, 5])

    ax2.set_xlabel('频率 (Hz)', fontsize=12)
    ax2.set_ylabel('相位 (度)', fontsize=12)
    ax2.grid(True, which='both', linestyle='--', alpha=0.7)
    ax2.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_pole_zero(filter_obj, save_path: Optional[str] = None,
                   figsize: Tuple[float, float] = (6, 6)) -> None:
    """绘制极零点图

    Parameters
    ----------
    filter_obj
        滤波器对象，需要有 poles 和 zeros 属性
    save_path : str, optional
        保存路径
    figsize : Tuple[float, float]
        图表大小
    """
    _check_matplotlib()

    fig, ax = plt.subplots(figsize=figsize)

    # 绘制单位圆
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), 'k--', alpha=0.3)

    # 绘制极零点 (如果对象有这些属性)
    if hasattr(filter_obj, 'poles'):
        poles = filter_obj.poles
        ax.plot(np.real(poles), np.imag(poles), 'rx', markersize=10,
                markeredgewidth=2, label='极点')

    if hasattr(filter_obj, 'zeros'):
        zeros = filter_obj.zeros
        ax.plot(np.real(zeros), np.imag(zeros), 'bo', markersize=10,
                markerfacecolor='none', markeredgewidth=2, label='零点')

    ax.set_xlabel('实部 (σ)', fontsize=12)
    ax.set_ylabel('虚部 (jω)', fontsize=12)
    ax.set_title('极零点图', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    ax.set_aspect('equal')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
