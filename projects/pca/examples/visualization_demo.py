#!/usr/bin/env python3
"""
PCA 可视化示例

演示如何使用可视化工具展示 PCA 结果：
1. 2D 散点图
2. 解释方差图
3. 双标图（Biplot）

注意：此示例需要 matplotlib 库。
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pca import PCA
from src.visualization import plot_pca_2d, plot_explained_variance, plot_biplot

try:
    import matplotlib
    matplotlib.use("Agg")  # 非交互式后端
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：未安装 matplotlib，将跳过可视化部分。")
    print("安装命令：pip install matplotlib")


def create_cluster_data():
    """创建带有聚类结构的数据。"""
    np.random.seed(42)

    # 三个聚类
    cluster1 = np.random.randn(50, 5) + np.array([5, 5, 0, 0, 0])
    cluster2 = np.random.randn(50, 5) + np.array([-5, -5, 0, 0, 0])
    cluster3 = np.random.randn(50, 5) + np.array([0, 0, 5, 0, 0])

    X = np.vstack([cluster1, cluster2, cluster3])
    labels = np.array([0]*50 + [1]*50 + [2]*50)

    return X, labels


def main():
    print("=" * 60)
    print("PCA 可视化示例")
    print("=" * 60)

    # 创建数据
    print("\n[1] 创建带聚类结构的数据...")
    X, labels = create_cluster_data()
    print(f"   数据形状: {X.shape}")
    print(f"   聚类数量: {len(np.unique(labels))}")

    # PCA 降维
    print("\n[2] PCA 降维...")
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)
    print(f"   降维后形状: {X_2d.shape}")
    print(f"   解释方差比例: {pca.explained_variance_ratio_}")

    if not HAS_MATPLOTLIB:
        print("\n跳过可视化（未安装 matplotlib）")
        return

    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # 3. 2D 散点图
    print("\n[3] 绘制 2D 散点图...")
    fig1 = plot_pca_2d(
        X_2d,
        labels=labels,
        title="PCA 2D Projection - Cluster Data",
        save_path=os.path.join(output_dir, "pca_2d_scatter.png"),
    )
    print(f"   保存至: {output_dir}/pca_2d_scatter.png")
    plt.close(fig1)

    # 4. 解释方差图
    print("\n[4] 绘制解释方差图...")
    # 先用全部成分拟合
    pca_full = PCA(n_components=5)
    pca_full.fit(X)

    fig2 = plot_explained_variance(
        pca_full.explained_variance_ratio_,
        title="PCA - Explained Variance Analysis",
        save_path=os.path.join(output_dir, "pca_variance.png"),
    )
    print(f"   保存至: {output_dir}/pca_variance.png")
    plt.close(fig2)

    # 5. 双标图
    print("\n[5] 绘制双标图...")
    feature_names = ["Feature A", "Feature B", "Feature C", "Feature D", "Feature E"]
    fig3 = plot_biplot(
        X_2d,
        components=pca.components_,
        feature_names=feature_names,
        labels=labels,
        title="PCA Biplot - Feature Contributions",
        save_path=os.path.join(output_dir, "pca_biplot.png"),
    )
    print(f"   保存至: {output_dir}/pca_biplot.png")
    plt.close(fig3)

    # 6. 分析主成分贡献
    print("\n[6] 各特征对主成分的贡献:")
    for i in range(2):
        print(f"\n   PC{i+1} (解释方差: {pca.explained_variance_ratio_[i]:.2%}):")
        for j, name in enumerate(feature_names):
            contribution = pca.components_[i, j]
            bar = "+" * int(abs(contribution) * 20) if contribution >= 0 else "-" * int(abs(contribution) * 20)
            print(f"     {name:<12} {contribution:>+.4f}  {bar}")

    print("\n" + "=" * 60)
    print("可视化示例完成！")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
