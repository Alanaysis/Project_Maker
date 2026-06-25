"""
特征重要性分析示例

分析不同决策树算法的特征重要性，并进行可视化。
"""

import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.id3 import ID3DecisionTree
from src.c45 import C45DecisionTree
from src.cart_classifier import CARTClassifier
from src.cart_regressor import CARTRegressor
from src.utils import train_test_split


def generate_classification_data(n_samples=300):
    """
    生成分类数据集

    参数:
    ----------
    n_samples : int
        样本数量

    返回:
    ----------
    X : numpy.ndarray
        特征矩阵
    y : numpy.ndarray
        标签向量
    feature_names : list
        特征名称
    """
    np.random.seed(42)

    # 生成特征
    feature1 = np.random.randn(n_samples)  # 重要特征
    feature2 = np.random.randn(n_samples)  # 重要特征
    feature3 = np.random.randn(n_samples)  # 中等重要特征
    feature4 = np.random.randn(n_samples)  # 不重要特征
    feature5 = np.random.randn(n_samples)  # 不重要特征

    # 生成标签（基于前3个特征）
    y = (feature1 + 0.5 * feature2 + 0.3 * feature3 + np.random.randn(n_samples) * 0.5 > 0).astype(int)

    X = np.column_stack([feature1, feature2, feature3, feature4, feature5])
    feature_names = ['特征A', '特征B', '特征C', '特征D', '特征E']

    return X, y, feature_names


def generate_regression_data(n_samples=300):
    """
    生成回归数据集

    参数:
    ----------
    n_samples : int
        样本数量

    返回:
    ----------
    X : numpy.ndarray
        特征矩阵
    y : numpy.ndarray
        目标变量
    feature_names : list
        特征名称
    """
    np.random.seed(42)

    # 生成特征
    feature1 = np.random.randn(n_samples)  # 重要特征
    feature2 = np.random.randn(n_samples)  # 重要特征
    feature3 = np.random.randn(n_samples)  # 中等重要特征
    feature4 = np.random.randn(n_samples)  # 不重要特征
    feature5 = np.random.randn(n_samples)  # 不重要特征

    # 生成目标变量
    y = 3 * feature1 + 2 * feature2 + feature3 + np.random.randn(n_samples) * 0.5

    X = np.column_stack([feature1, feature2, feature3, feature4, feature5])
    feature_names = ['特征A', '特征B', '特征C', '特征D', '特征E']

    return X, y, feature_names


def analyze_feature_importance(model, feature_names, model_name):
    """
    分析特征重要性

    参数:
    ----------
    model : 决策树模型
        训练好的模型
    feature_names : list
        特征名称
    model_name : str
        模型名称
    """
    print(f"\n{model_name} 特征重要性:")
    print("-" * 40)

    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_

        # 按重要性排序
        indices = np.argsort(importances)[::-1]

        for i, idx in enumerate(indices):
            print(f"   {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")

        # 计算累积重要性
        cumulative = np.cumsum(importances[indices])
        print(f"\n   累积重要性 (前3个特征): {cumulative[2]:.4f}")
    else:
        print("   该模型没有 feature_importances_ 属性")


def compare_feature_importance(models, feature_names):
    """
    比较不同模型的特征重要性

    参数:
    ----------
    models : dict
        模型字典 {名称: 模型}
    feature_names : list
        特征名称
    """
    print("\n" + "=" * 60)
    print("特征重要性比较:")
    print("=" * 60)

    # 收集所有模型的特征重要性
    all_importances = {}
    for name, model in models.items():
        if hasattr(model, 'feature_importances_'):
            all_importances[name] = model.feature_importances_

    if not all_importances:
        print("没有可用的特征重要性数据")
        return

    # 打印表格
    print(f"\n{'特征':<10}", end="")
    for name in all_importances.keys():
        print(f"{name:<15}", end="")
    print()
    print("-" * (10 + 15 * len(all_importances)))

    for i, fname in enumerate(feature_names):
        print(f"{fname:<10}", end="")
        for name, importances in all_importances.items():
            print(f"{importances[i]:<15.4f}", end="")
        print()

    # 计算平均重要性
    print("-" * (10 + 15 * len(all_importances)))
    print(f"{'平均':<10}", end="")
    for name, importances in all_importances.items():
        print(f"{np.mean(importances):<15.4f}", end="")
    print()


def analyze_feature_correlation(X, feature_names):
    """
    分析特征之间的相关性

    参数:
    ----------
    X : numpy.ndarray
        特征矩阵
    feature_names : list
        特征名称
    """
    print("\n特征相关性分析:")
    print("-" * 40)

    # 计算相关系数矩阵
    corr_matrix = np.corrcoef(X.T)

    # 打印相关系数矩阵
    print(f"\n{'':10}", end="")
    for name in feature_names:
        print(f"{name:<10}", end="")
    print()

    for i, name in enumerate(feature_names):
        print(f"{name:<10}", end="")
        for j in range(len(feature_names)):
            print(f"{corr_matrix[i, j]:<10.3f}", end="")
        print()

    # 找出高度相关的特征对
    print("\n高度相关的特征对 (|r| > 0.5):")
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            if abs(corr_matrix[i, j]) > 0.5:
                print(f"   {feature_names[i]} - {feature_names[j]}: {corr_matrix[i, j]:.3f}")


def main():
    """主函数"""
    print("=" * 60)
    print("特征重要性分析示例")
    print("=" * 60)

    # 1. 分类问题
    print("\n" + "=" * 60)
    print("1. 分类问题特征重要性分析")
    print("=" * 60)

    X_cls, y_cls, feature_names_cls = generate_classification_data(n_samples=300)
    print(f"\n数据集: {X_cls.shape[0]} 个样本, {X_cls.shape[1]} 个特征")
    print(f"特征: {feature_names_cls}")

    # 划分数据集
    X_train_cls, X_test_cls, y_train_cls, y_test_cls = train_test_split(
        X_cls, y_cls, test_size=0.2, random_state=42
    )

    # 训练不同模型
    print("\n训练分类模型...")

    id3_tree = ID3DecisionTree(max_depth=5)
    id3_tree.fit(X_train_cls, y_train_cls)

    c45_tree = C45DecisionTree(max_depth=5)
    c45_tree.fit(X_train_cls, y_train_cls)

    cart_tree = CARTClassifier(max_depth=5)
    cart_tree.fit(X_train_cls, y_train_cls)

    # 分析特征重要性
    analyze_feature_importance(id3_tree, feature_names_cls, "ID3 决策树")
    analyze_feature_importance(c45_tree, feature_names_cls, "C4.5 决策树")
    analyze_feature_importance(cart_tree, feature_names_cls, "CART 分类树")

    # 比较特征重要性
    cls_models = {
        'ID3': id3_tree,
        'C4.5': c45_tree,
        'CART': cart_tree
    }
    compare_feature_importance(cls_models, feature_names_cls)

    # 分析特征相关性
    analyze_feature_correlation(X_cls, feature_names_cls)

    # 2. 回归问题
    print("\n" + "=" * 60)
    print("2. 回归问题特征重要性分析")
    print("=" * 60)

    X_reg, y_reg, feature_names_reg = generate_regression_data(n_samples=300)
    print(f"\n数据集: {X_reg.shape[0]} 个样本, {X_reg.shape[1]} 个特征")
    print(f"特征: {feature_names_reg}")

    # 划分数据集
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X_reg, y_reg, test_size=0.2, random_state=42
    )

    # 训练回归模型
    print("\n训练回归模型...")

    reg_tree = CARTRegressor(max_depth=5)
    reg_tree.fit(X_train_reg, y_train_reg)

    # 分析特征重要性
    analyze_feature_importance(reg_tree, feature_names_reg, "CART 回归树")

    # 3. 特征选择示例
    print("\n" + "=" * 60)
    print("3. 基于特征重要性的特征选择")
    print("=" * 60)

    if hasattr(cart_tree, 'feature_importances_'):
        importances = cart_tree.feature_importances_
        threshold = 0.1  # 重要性阈值

        print(f"\n重要性阈值: {threshold}")
        print("\n选择的特征:")
        selected_features = []
        for i, (fname, importance) in enumerate(zip(feature_names_cls, importances)):
            if importance >= threshold:
                selected_features.append(i)
                print(f"   {fname}: {importance:.4f} (已选择)")
            else:
                print(f"   {fname}: {importance:.4f} (未选择)")

        print(f"\n共选择 {len(selected_features)} 个特征")

        # 使用选择的特征重新训练
        X_train_selected = X_train_cls[:, selected_features]
        X_test_selected = X_test_cls[:, selected_features]

        selected_tree = CARTClassifier(max_depth=5)
        selected_tree.fit(X_train_selected, y_train_cls)

        accuracy_full = cart_tree.score(X_test_cls, y_test_cls)
        accuracy_selected = selected_tree.score(X_test_selected, y_test_cls)

        print(f"\n使用全部特征准确率: {accuracy_full:.4f}")
        print(f"使用选择特征准确率: {accuracy_selected:.4f}")
        print(f"特征数量减少: {X_cls.shape[1]} -> {len(selected_features)}")

    return cls_models


if __name__ == "__main__":
    main()
