"""
决策树可视化模块

提供以下可视化功能：
1. 树结构可视化
2. 决策边界可视化
3. 特征重要性可视化
"""

import numpy as np

# 尝试导入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import ListedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告: matplotlib 未安装，可视化功能将不可用。")
    print("请使用 'pip install matplotlib' 安装。")


def plot_tree(tree, feature_names=None, class_names=None, figsize=(12, 8),
              fontsize=10, filled=True, save_path=None):
    """
    绘制决策树结构

    参数:
    ----------
    tree : 决策树对象
        训练好的决策树
    feature_names : list, optional
        特征名称列表
    class_names : list, optional
        类别名称列表
    figsize : tuple (默认=(12, 8))
        图形大小
    fontsize : int (默认=10)
        字体大小
    filled : bool (默认=True)
        是否填充颜色
    save_path : str, optional
        保存路径

    返回:
    ----------
    fig : matplotlib.figure.Figure
        图形对象
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib 未安装，请使用 'pip install matplotlib' 安装")

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_axis_off()

    # 获取树的根节点
    root = tree.root
    if root is None:
        raise ValueError("决策树尚未训练")

    # 绘制树
    _draw_tree(ax, root, 0.5, 0.95, 0.5, 0.05, feature_names, class_names,
              fontsize, filled)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def _draw_tree(ax, node, x, y, width, height, feature_names, class_names,
              fontsize, filled, level=0):
    """
    递归绘制树节点

    参数:
    ----------
    ax : matplotlib.axes.Axes
        绘图区域
    node : 树节点
        当前节点
    x, y : float
        节点中心坐标
    width : float
        节点宽度
    height : float
        节点高度
    feature_names : list
        特征名称列表
    class_names : list
        类别名称列表
    fontsize : int
        字体大小
    filled : bool
        是否填充颜色
    level : int
        当前层级
    """
    if node.is_leaf():
        # 绘制叶节点
        if class_names and node.value < len(class_names):
            label = class_names[node.value]
        else:
            label = f"类 {node.value}"

        color = plt.cm.Set3(node.value / max(1, node.value + 1)) if filled else 'lightblue'

        bbox = dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor='black', linewidth=1)
        ax.text(x, y, label, ha='center', va='center', fontsize=fontsize,
               bbox=bbox, fontweight='bold')
    else:
        # 绘制内部节点
        if feature_names and node.feature_index < len(feature_names):
            feature_name = feature_names[node.feature_index]
        else:
            feature_name = f"特征 {node.feature_index}"

        if hasattr(node, 'threshold') and node.threshold is not None:
            label = f"{feature_name}\n<= {node.threshold:.2f}"
        else:
            label = feature_name

        color = plt.cm.Pastel1(0) if filled else 'lightyellow'

        bbox = dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor='black', linewidth=1)
        ax.text(x, y, label, ha='center', va='center', fontsize=fontsize,
               bbox=bbox)

        # 绘制子节点
        if hasattr(node, 'left') and node.left is not None:
            child_x = x - width / 2
            child_y = y - height
            ax.annotate('', xy=(child_x, child_y + 0.02), xytext=(x, y - 0.02),
                       arrowprops=dict(arrowstyle='->', color='green', lw=1.5))
            ax.text((x + child_x) / 2, (y + child_y) / 2, '是', fontsize=8,
                   color='green', ha='center')
            _draw_tree(ax, node.left, child_x, child_y, width / 2, height,
                      feature_names, class_names, fontsize, filled, level + 1)

        if hasattr(node, 'right') and node.right is not None:
            child_x = x + width / 2
            child_y = y - height
            ax.annotate('', xy=(child_x, child_y + 0.02), xytext=(x, y - 0.02),
                       arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
            ax.text((x + child_x) / 2, (y + child_y) / 2, '否', fontsize=8,
                   color='red', ha='center')
            _draw_tree(ax, node.right, child_x, child_y, width / 2, height,
                      feature_names, class_names, fontsize, filled, level + 1)

        # 处理多分支节点（ID3, C4.5）
        if hasattr(node, 'children') and node.children:
            n_children = len(node.children)
            for i, (value, child) in enumerate(node.children.items()):
                child_x = x - width / 2 + (i + 0.5) * width / n_children
                child_y = y - height
                ax.annotate('', xy=(child_x, child_y + 0.02), xytext=(x, y - 0.02),
                           arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
                ax.text((x + child_x) / 2, (y + child_y) / 2, f'={value}',
                       fontsize=8, color='blue', ha='center')
                _draw_tree(ax, child, child_x, child_y, width / n_children, height,
                          feature_names, class_names, fontsize, filled, level + 1)


def plot_decision_boundary(tree, X, y, feature_indices=None, feature_names=None,
                          class_names=None, figsize=(10, 8), h=0.02, save_path=None):
    """
    绘制决策边界

    参数:
    ----------
    tree : 决策树对象
        训练好的决策树
    X : numpy.ndarray
        特征矩阵
    y : numpy.ndarray
        标签向量
    feature_indices : list, optional
        要可视化的特征索引（默认使用前两个特征）
    feature_names : list, optional
        特征名称列表
    class_names : list, optional
        类别名称列表
    figsize : tuple (默认=(10, 8))
        图形大小
    h : float (默认=0.02)
        网格步长
    save_path : str, optional
        保存路径

    返回:
    ----------
    fig : matplotlib.figure.Figure
        图形对象
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib 未安装，请使用 'pip install matplotlib' 安装")

    if feature_indices is None:
        feature_indices = [0, 1]

    if len(feature_indices) != 2:
        raise ValueError("只能可视化两个特征")

    # 提取特征
    X_plot = X[:, feature_indices]

    # 创建网格
    x_min, x_max = X_plot[:, 0].min() - 1, X_plot[:, 0].max() + 1
    y_min, y_max = X_plot[:, 1].min() - 1, X_plot[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                         np.arange(y_min, y_max, h))

    # 预测网格点
    grid_points = np.c_[xx.ravel(), yy.ravel()]

    # 创建完整的特征矩阵
    if X.shape[1] > 2:
        # 如果有更多特征，用均值填充
        full_grid = np.zeros((grid_points.shape[0], X.shape[1]))
        full_grid[:, feature_indices] = grid_points
        for i in range(X.shape[1]):
            if i not in feature_indices:
                full_grid[:, i] = np.mean(X[:, i])
        Z = tree.predict(full_grid)
    else:
        Z = tree.predict(grid_points)

    Z = Z.reshape(xx.shape)

    # 绘制决策边界
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # 创建颜色映射
    n_classes = len(np.unique(y))
    cmap_light = ListedColormap(['#FFAAAA', '#AAFFAA', '#AAAAFF', '#FFFFAA', '#FFAAFF'])
    cmap_bold = ListedColormap(['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF'])

    # 绘制决策边界
    ax.contourf(xx, yy, Z, alpha=0.3, cmap=cmap_light)

    # 绘制数据点
    scatter = ax.scatter(X_plot[:, 0], X_plot[:, 1], c=y, cmap=cmap_bold,
                        edgecolors='black', linewidth=1, s=50)

    # 设置标签
    if feature_names and len(feature_names) > max(feature_indices):
        ax.set_xlabel(feature_names[feature_indices[0]], fontsize=12)
        ax.set_ylabel(feature_names[feature_indices[1]], fontsize=12)
    else:
        ax.set_xlabel(f"特征 {feature_indices[0]}", fontsize=12)
        ax.set_ylabel(f"特征 {feature_indices[1]}", fontsize=12)

    ax.set_title("决策树决策边界", fontsize=14, fontweight='bold')

    # 添加图例
    if class_names:
        handles = [mpatches.Patch(color=cmap_bold(i / max(1, n_classes - 1)),
                                  label=class_names[i])
                  for i in range(n_classes)]
        ax.legend(handles=handles, loc='best')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_feature_importance(tree, feature_names=None, figsize=(10, 6),
                           color='steelblue', save_path=None):
    """
    绘制特征重要性

    参数:
    ----------
    tree : 决策树对象
        训练好的决策树
    feature_names : list, optional
        特征名称列表
    figsize : tuple (默认=(10, 6))
        图形大小
    color : str (默认='steelblue')
        条形图颜色
    save_path : str, optional
        保存路径

    返回:
    ----------
    fig : matplotlib.figure.Figure
        图形对象
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib 未安装，请使用 'pip install matplotlib' 安装")

    if not hasattr(tree, 'feature_importances_') or tree.feature_importances_ is None:
        raise ValueError("决策树没有 feature_importances_ 属性")

    importances = tree.feature_importances_
    n_features = len(importances)

    # 创建特征名称
    if feature_names is None:
        feature_names = [f"特征 {i}" for i in range(n_features)]

    # 按重要性排序
    indices = np.argsort(importances)[::-1]

    # 绘制条形图
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    bars = ax.bar(range(n_features), importances[indices], color=color,
                  edgecolor='black', linewidth=0.5)

    # 设置标签
    ax.set_xticks(range(n_features))
    ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha='right')
    ax.set_ylabel("重要性", fontsize=12)
    ax.set_title("特征重要性", fontsize=14, fontweight='bold')

    # 添加数值标签
    for i, (idx, bar) in enumerate(zip(indices, bars)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
               f'{importances[idx]:.3f}', ha='center', va='bottom', fontsize=9)

    # 添加网格
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_learning_curve(tree_class, X, y, train_sizes=None, cv=5,
                       figsize=(10, 6), save_path=None, **tree_params):
    """
    绘制学习曲线

    参数:
    ----------
    tree_class : class
        决策树类
    X : numpy.ndarray
        特征矩阵
    y : numpy.ndarray
        标签向量
    train_sizes : list, optional
        训练集大小列表
    cv : int (默认=5)
        交叉验证折数
    figsize : tuple (默认=(10, 6))
        图形大小
    save_path : str, optional
        保存路径
    **tree_params : dict
        决策树参数

    返回:
    ----------
    fig : matplotlib.figure.Figure
        图形对象
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib 未安装，请使用 'pip install matplotlib' 安装")

    from .utils import train_test_split

    if train_sizes is None:
        train_sizes = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    train_scores = []
    val_scores = []

    for size in train_sizes:
        scores_train = []
        scores_val = []

        for i in range(cv):
            # 划分数据
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=1-size, random_state=i
            )

            # 训练模型
            tree = tree_class(**tree_params)
            tree.fit(X_train, y_train)

            # 评估
            scores_train.append(tree.score(X_train, y_train))
            scores_val.append(tree.score(X_val, y_val))

        train_scores.append(np.mean(scores_train))
        val_scores.append(np.mean(scores_val))

    # 绘制学习曲线
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    ax.plot(train_sizes, train_scores, 'o-', color='blue', label='训练集')
    ax.plot(train_sizes, val_scores, 'o-', color='red', label='验证集')

    ax.set_xlabel("训练集比例", fontsize=12)
    ax.set_ylabel("准确率", fontsize=12)
    ax.set_title("学习曲线", fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def plot_confusion_matrix(y_true, y_pred, class_names=None, figsize=(8, 6),
                         cmap='Blues', save_path=None):
    """
    绘制混淆矩阵

    参数:
    ----------
    y_true : numpy.ndarray
        真实标签
    y_pred : numpy.ndarray
        预测标签
    class_names : list, optional
        类别名称列表
    figsize : tuple (默认=(8, 6))
        图形大小
    cmap : str (默认='Blues')
        颜色映射
    save_path : str, optional
        保存路径

    返回:
    ----------
    fig : matplotlib.figure.Figure
        图形对象
    """
    if not HAS_MATPLOTLIB:
        raise ImportError("matplotlib 未安装，请使用 'pip install matplotlib' 安装")

    from .metrics import confusion_matrix

    cm = confusion_matrix(y_true, y_pred)
    n_classes = len(cm)

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # 绘制混淆矩阵
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)

    # 设置标签
    if class_names is None:
        class_names = [f"类 {i}" for i in range(n_classes)]

    ax.set(xticks=np.arange(n_classes),
           yticks=np.arange(n_classes),
           xticklabels=class_names,
           yticklabels=class_names,
           title="混淆矩阵",
           ylabel='真实标签',
           xlabel='预测标签')

    # 旋转标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # 添加数值
    for i in range(n_classes):
        for j in range(n_classes):
            ax.text(j, i, format(cm[i, j], 'd'),
                   ha="center", va="center",
                   color="white" if cm[i, j] > cm.max() / 2 else "black")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def print_tree_text(tree, feature_names=None, class_names=None):
    """
    以文本形式打印决策树

    参数:
    ----------
    tree : 决策树对象
        训练好的决策树
    feature_names : list, optional
        特征名称列表
    class_names : list, optional
        类别名称列表
    """
    root = tree.root
    if root is None:
        print("决策树尚未训练")
        return

    _print_node(root, "", feature_names, class_names)


def _print_node(node, indent, feature_names, class_names):
    """递归打印节点"""
    if node.is_leaf():
        if class_names and node.value < len(class_names):
            label = class_names[node.value]
        else:
            label = f"类 {node.value}"
        print(f"{indent}预测: {label}")
        return

    if feature_names and node.feature_index < len(feature_names):
        feature_name = feature_names[node.feature_index]
    else:
        feature_name = f"特征 {node.feature_index}"

    if hasattr(node, 'threshold') and node.threshold is not None:
        print(f"{indent}[{feature_name} <= {node.threshold:.4f}]")
    else:
        print(f"{indent}[{feature_name}]")

    # 处理二叉树节点
    if hasattr(node, 'left') and node.left is not None:
        print(f"{indent}├── 是:")
        _print_node(node.left, indent + "│   ", feature_names, class_names)

    if hasattr(node, 'right') and node.right is not None:
        print(f"{indent}└── 否:")
        _print_node(node.right, indent + "    ", feature_names, class_names)

    # 处理多分支节点
    if hasattr(node, 'children') and node.children:
        for i, (value, child) in enumerate(node.children.items()):
            is_last = i == len(node.children) - 1
            prefix = "└──" if is_last else "├──"
            print(f"{indent}{prefix} 值 = {value}:")
            _print_node(child, indent + ("    " if is_last else "│   "),
                       feature_names, class_names)
