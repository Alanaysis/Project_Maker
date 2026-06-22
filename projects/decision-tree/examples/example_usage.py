#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策树使用示例
"""

import numpy as np
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.decision_tree import DecisionTreeClassifier
from src.utils import train_test_split, accuracy_score
from src.metrics import confusion_matrix, precision_score, recall_score, f1_score

def create_sample_dataset():
    """
    创建示例数据集（鸢尾花数据集的简化版）

    返回:
    X: 特征矩阵
    y: 标签向量
    """
    np.random.seed(42)

    # 创建3类数据
    n_samples_per_class = 50
    n_features = 4

    # 类别0: 中心点 (0, 0, 0, 0)
    X0 = np.random.randn(n_samples_per_class, n_features) * 0.5 + np.array([0, 0, 0, 0])

    # 类别1: 中心点 (1, 1, 1, 1)
    X1 = np.random.randn(n_samples_per_class, n_features) * 0.5 + np.array([1, 1, 1, 1])

    # 类别2: 中心点 (2, 2, 2, 2)
    X2 = np.random.randn(n_samples_per_class, n_features) * 0.5 + np.array([2, 2, 2, 2])

    # 合并数据
    X = np.vstack([X0, X1, X2])
    y = np.array([0] * n_samples_per_class + [1] * n_samples_per_class + [2] * n_samples_per_class)

    return X, y

def main():
    """主函数"""
    print("=" * 60)
    print("决策树分类器示例")
    print("=" * 60)

    # 1. 创建数据集
    print("\n1. 创建示例数据集...")
    X, y = create_sample_dataset()
    print(f"   数据集大小: {X.shape[0]} 个样本, {X.shape[1]} 个特征")
    print(f"   类别数量: {len(np.unique(y))} 个")

    # 2. 划分数据集
    print("\n2. 划分数据集为训练集和测试集...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   训练集大小: {X_train.shape[0]} 个样本")
    print(f"   测试集大小: {X_test.shape[0]} 个样本")

    # 3. 创建并训练决策树
    print("\n3. 训练决策树分类器...")
    dt_classifier = DecisionTreeClassifier(max_depth=5, min_samples_split=5, min_samples_leaf=2)
    dt_classifier.fit(X_train, y_train)
    print("   训练完成!")

    # 4. 查看模型参数
    print("\n4. 模型参数:")
    params = dt_classifier.get_params()
    for key, value in params.items():
        print(f"   {key}: {value}")

    # 5. 打印决策树结构
    print("\n5. 决策树结构:")
    dt_classifier.print_tree()

    # 6. 预测
    print("\n6. 进行预测...")
    y_pred = dt_classifier.predict(X_test)
    print(f"   预测结果: {y_pred[:10]}...")

    # 7. 评估模型
    print("\n7. 模型评估:")
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   准确率: {accuracy:.4f}")

    # 计算其他指标
    precision = precision_score(y_test, y_pred, average='macro')
    recall = recall_score(y_test, y_pred, average='macro')
    f1 = f1_score(y_test, y_pred, average='macro')

    print(f"   精确率 (macro): {precision:.4f}")
    print(f"   召回率 (macro): {recall:.4f}")
    print(f"   F1分数 (macro): {f1:.4f}")

    # 8. 混淆矩阵
    print("\n8. 混淆矩阵:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # 9. 测试不同参数
    print("\n9. 测试不同参数的决策树...")
    max_depths = [2, 5, 10, None]
    for depth in max_depths:
        dt = DecisionTreeClassifier(max_depth=depth, min_samples_split=5, min_samples_leaf=2)
        dt.fit(X_train, y_train)
        accuracy = dt.score(X_test, y_test)
        print(f"   最大深度={depth}: 准确率={accuracy:.4f}")

    # 10. 测试不同分裂标准
    print("\n10. 测试不同分裂标准...")
    criteria = ['entropy', 'gini']
    for criterion in criteria:
        dt = DecisionTreeClassifier(max_depth=5, criterion=criterion)
        dt.fit(X_train, y_train)
        accuracy = dt.score(X_test, y_test)
        print(f"   标准={criterion}: 准确率={accuracy:.4f}")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()