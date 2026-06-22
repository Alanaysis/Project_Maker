"""
PCA 可视化模块

提供多种可视化工具，帮助理解 PCA 的降维效果：
1. 2D/3D 散点图：展示降维后的数据分布
2. 解释方差图：展示各主成分的贡献度
3. 双标图（Biplot）：同时展示样本和特征方向
"""

import numpy as np
from numpy.typing import NDArray

try:
    import matplotlib.pyplot as plt
    import matplotlib.figure

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _check_matplotlib() -> None:
    """检查 matplotlib 是否可用。"""
    if not HAS_MATPLOTLIB:
        raise ImportError("可视化功能需要 matplotlib，请安装: pip install matplotlib")


def plot_pca_2d(
    X_projected: NDArray[np.float64],
    labels: NDArray[np.int64] | None = None,
    title: str = "PCA 2D Projection",
    figsize: tuple[float, float] = (8, 6),
    save_path: str | None = None,
) -> "matplotlib.figure.Figure":
    """
    绘制 PCA 2D 投影散点图。

    Parameters
    ----------
    X_projected : np.ndarray of shape (n_samples, 2)
        PCA 降维后的 2D 数据。
    labels : np.ndarray of shape (n_samples,), optional
        样本标签（用于着色）。
    title : str
        图表标题。
    figsize : tuple
        图表大小。
    save_path : str, optional
        保存路径。如果不为 None，则保存图片。

    Returns
    -------
    fig : matplotlib.figure.Figure
        图表对象。
    """
    _check_matplotlib()

    fig, ax = plt.subplots(figsize=figsize)

    if labels is not None:
        unique_labels = np.unique(labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = labels == label
            ax.scatter(
                X_projected[mask, 0],
                X_projected[mask, 1],
                c=[color],
                label=f"Class {label}",
                alpha=0.7,
                edgecolors="w",
                linewidth=0.5,
            )
        ax.legend()
    else:
        ax.scatter(
            X_projected[:, 0],
            X_projected[:, 1],
            alpha=0.7,
            edgecolors="w",
            linewidth=0.5,
        )

    ax.set_xlabel("Principal Component 1")
    ax.set_ylabel("Principal Component 2")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_pca_3d(
    X_projected: NDArray[np.float64],
    labels: NDArray[np.int64] | None = None,
    title: str = "PCA 3D Projection",
    figsize: tuple[float, float] = (10, 8),
    save_path: str | None = None,
) -> "matplotlib.figure.Figure":
    """
    绘制 PCA 3D 投影散点图。

    Parameters
    ----------
    X_projected : np.ndarray of shape (n_samples, 3)
        PCA 降维后的 3D 数据。
    labels : np.ndarray of shape (n_samples,), optional
        样本标签（用于着色）。
    title : str
        图表标题。
    figsize : tuple
        图表大小。
    save_path : str, optional
        保存路径。

    Returns
    -------
    fig : matplotlib.figure.Figure
        图表对象。
    """
    _check_matplotlib()

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    if labels is not None:
        unique_labels = np.unique(labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = labels == label
            ax.scatter(
                X_projected[mask, 0],
                X_projected[mask, 1],
                X_projected[mask, 2],
                c=[color],
                label=f"Class {label}",
                alpha=0.7,
            )
        ax.legend()
    else:
        ax.scatter(
            X_projected[:, 0],
            X_projected[:, 1],
            X_projected[:, 2],
            alpha=0.7,
        )

    ax.set_xlabel("PC 1")
    ax.set_ylabel("PC 2")
    ax.set_zlabel("PC 3")
    ax.set_title(title)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_explained_variance(
    explained_variance_ratio: NDArray[np.float64],
    title: str = "Explained Variance Ratio",
    figsize: tuple[float, float] = (10, 5),
    save_path: str | None = None,
) -> "matplotlib.figure.Figure":
    """
    绘制解释方差比例图（柱状图 + 累积曲线）。

    Parameters
    ----------
    explained_variance_ratio : np.ndarray
        每个主成分的解释方差比例。
    title : str
        图表标题。
    figsize : tuple
        图表大小。
    save_path : str, optional
        保存路径。

    Returns
    -------
    fig : matplotlib.figure.Figure
        图表对象。
    """
    _check_matplotlib()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    n_components = len(explained_variance_ratio)
    x = np.arange(1, n_components + 1)

    # 左图：柱状图
    ax1.bar(x, explained_variance_ratio, alpha=0.7, color="steelblue")
    ax1.set_xlabel("Principal Component")
    ax1.set_ylabel("Explained Variance Ratio")
    ax1.set_title("Individual Variance")
    ax1.set_xticks(x)
    ax1.grid(True, alpha=0.3, axis="y")

    # 右图：累积曲线
    cumulative = np.cumsum(explained_variance_ratio)
    ax2.plot(x, cumulative, "o-", color="steelblue", linewidth=2)
    ax2.axhline(y=0.95, color="r", linestyle="--", alpha=0.5, label="95% threshold")
    ax2.set_xlabel("Number of Components")
    ax2.set_ylabel("Cumulative Explained Variance")
    ax2.set_title("Cumulative Variance")
    ax2.set_xticks(x)
    ax2.set_ylim(0, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def plot_biplot(
    X_projected: NDArray[np.float64],
    components: NDArray[np.float64],
    feature_names: list[str] | None = None,
    labels: NDArray[np.int64] | None = None,
    title: str = "PCA Biplot",
    figsize: tuple[float, float] = (10, 8),
    save_path: str | None = None,
) -> "matplotlib.figure.Figure":
    """
    绘制 PCA 双标图（Biplot）。

    双标图同时展示：
    - 样本点在主成分空间中的位置
    - 原始特征对主成分的贡献方向

    Parameters
    ----------
    X_projected : np.ndarray of shape (n_samples, 2)
        PCA 降维后的 2D 数据。
    components : np.ndarray of shape (n_components, n_features)
        主成分矩阵。
    feature_names : list of str, optional
        特征名称列表。
    labels : np.ndarray, optional
        样本标签。
    title : str
        图表标题。
    figsize : tuple
        图表大小。
    save_path : str, optional
        保存路径。

    Returns
    -------
    fig : matplotlib.figure.Figure
        图表对象。
    """
    _check_matplotlib()

    fig, ax = plt.subplots(figsize=figsize)

    # 绘制样本点
    if labels is not None:
        unique_labels = np.unique(labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for label, color in zip(unique_labels, colors):
            mask = labels == label
            ax.scatter(
                X_projected[mask, 0],
                X_projected[mask, 1],
                c=[color],
                label=f"Class {label}",
                alpha=0.5,
                s=30,
            )
        ax.legend()
    else:
        ax.scatter(X_projected[:, 0], X_projected[:, 1], alpha=0.5, s=30)

    # 绘制特征向量箭头
    n_features = components.shape[1]
    scale = np.max(np.abs(X_projected)) / np.max(np.abs(components)) * 0.8

    for i in range(n_features):
        ax.arrow(
            0, 0,
            components[0, i] * scale,
            components[1, i] * scale,
            head_width=0.05 * scale,
            head_length=0.03 * scale,
            fc="red",
            ec="red",
            alpha=0.8,
        )

        name = feature_names[i] if feature_names else f"Feature {i+1}"
        ax.annotate(
            name,
            xy=(components[0, i] * scale, components[1, i] * scale),
            fontsize=9,
            color="red",
            ha="center",
        )

    ax.set_xlabel("Principal Component 1")
    ax.set_ylabel("Principal Component 2")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color="k", linewidth=0.5)
    ax.axvline(x=0, color="k", linewidth=0.5)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig
