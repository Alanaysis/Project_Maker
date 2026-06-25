"""
特征选择示例

演示使用 PSO 进行特征选择。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src import FeatureSelector, FeatureSelectionConfig
from src.feature_selection import (
    simple_cross_validation_accuracy,
    create_sample_dataset,
)


def main():
    print("=" * 60)
    print("PSO 特征选择示例")
    print("=" * 60)

    # 示例 1: 简单数据集
    print("\n[示例 1] 简单数据集")
    print("-" * 40)

    X, y = create_sample_dataset(
        n_samples=100,
        n_features=10,
        n_informative=5,
    )
    print(f"数据集: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"有效特征: 前 5 个")

    config = FeatureSelectionConfig(
        n_features=10,
        n_particles=30,
        max_iterations=50,
        min_features=1,
        max_features=10,
        accuracy_weight=0.9,
        feature_weight=0.1,
        random_seed=42,
    )

    selector = FeatureSelector(config)
    result = selector.select(
        X, y,
        evaluator=simple_cross_validation_accuracy,
        verbose=True,
    )

    print(f"\n选择结果:")
    print(f"  最佳适应度: {result['best_fitness']:.6f}")
    print(f"  选择特征数: {result['n_selected_features']}")
    print(f"  选择特征索引: {result['selected_feature_indices']}")
    print(f"  最终准确率: {result['final_accuracy']:.2%}")

    # 示例 2: 高维数据集
    print("\n[示例 2] 高维数据集")
    print("-" * 40)

    X, y = create_sample_dataset(
        n_samples=200,
        n_features=50,
        n_informative=10,
    )
    print(f"数据集: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"有效特征: 前 10 个")

    config = FeatureSelectionConfig(
        n_features=50,
        n_particles=50,
        max_iterations=100,
        min_features=3,
        max_features=20,
        accuracy_weight=0.8,
        feature_weight=0.2,
        random_seed=42,
    )

    selector = FeatureSelector(config)
    result = selector.select(
        X, y,
        evaluator=simple_cross_validation_accuracy,
        verbose=True,
    )

    print(f"\n选择结果:")
    print(f"  最佳适应度: {result['best_fitness']:.6f}")
    print(f"  选择特征数: {result['n_selected_features']}")
    print(f"  选择特征索引: {result['selected_feature_indices']}")
    print(f"  最终准确率: {result['final_accuracy']:.2%}")

    # 分析选择的特征
    print(f"\n特征分析:")
    print(f"  总特征数: 50")
    print(f"  有效特征数: 10")
    print(f"  选择特征数: {result['n_selected_features']}")

    # 计算选择了多少有效特征
    selected_indices = set(result['selected_feature_indices'])
    informative_indices = set(range(10))
    selected_informative = selected_indices.intersection(informative_indices)
    print(f"  选择的有效特征数: {len(selected_informative)}")
    print(f"  有效特征召回率: {len(selected_informative) / 10:.2%}")

    # 示例 3: 不同权重对比
    print("\n[示例 3] 不同权重对比")
    print("-" * 40)

    X, y = create_sample_dataset(
        n_samples=100,
        n_features=20,
        n_informative=5,
    )

    weights = [
        (0.9, 0.1),  # 重视准确率
        (0.7, 0.3),  # 平衡
        (0.5, 0.5),  # 重视特征数量
    ]

    for acc_weight, feat_weight in weights:
        config = FeatureSelectionConfig(
            n_features=20,
            n_particles=30,
            max_iterations=50,
            accuracy_weight=acc_weight,
            feature_weight=feat_weight,
            random_seed=42,
        )

        selector = FeatureSelector(config)
        result = selector.select(
            X, y,
            evaluator=simple_cross_validation_accuracy,
            verbose=False,
        )

        print(
            f"  权重=({acc_weight}, {feat_weight}): "
            f"准确率={result['final_accuracy']:.2%}, "
            f"特征数={result['n_selected_features']}"
        )


if __name__ == "__main__":
    main()
