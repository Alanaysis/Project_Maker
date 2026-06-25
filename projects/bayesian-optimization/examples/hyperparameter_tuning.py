"""
超参数调优示例
==============

使用贝叶斯优化调优机器学习模型的超参数。
本示例使用 sklearn 的 SVM 分类器。
"""

import numpy as np
from sklearn.datasets import make_classification
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.optimizer import BayesianOptimizer
from src.acquisition import ExpectedImprovement


def svm_objective(params):
    """
    SVM 超参数优化目标函数

    参数：
        params: 超参数向量 [log_C, log_gamma]

    返回：
        交叉验证准确率
    """
    # 生成数据
    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=10,
                               n_informative=5, random_state=42)

    # 标准化
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # 解析超参数
    C = np.exp(params[0])  # C 在 [e^-3, e^3] 范围
    gamma = np.exp(params[1])  # gamma 在 [e^-5, e^1] 范围

    # 创建 SVM 模型
    svm = SVC(C=C, gamma=gamma, kernel='rbf', random_state=42)

    # 交叉验证
    scores = cross_val_score(svm, X, y, cv=5, scoring='accuracy')

    return scores.mean()


def main():
    """主函数"""
    print("=" * 60)
    print("贝叶斯优化 - SVM 超参数调优示例")
    print("=" * 60)

    # 搜索空间（对数尺度）
    bounds = [(-3, 3), (-5, 1)]  # [log_C, log_gamma]

    # 创建优化器
    optimizer = BayesianOptimizer(
        objective_function=svm_objective,
        bounds=bounds,
        acquisition=ExpectedImprovement(xi=0.01),
        kernel='matern',
        n_initial=5,
        maximize=True,
        random_state=42
    )

    # 运行优化
    print("\n开始超参数优化...")
    result = optimizer.optimize(n_iterations=15, verbose=True)

    # 打印结果
    print("\n" + "=" * 60)
    print("优化结果")
    print("=" * 60)

    best_C = np.exp(result['best_x'][0])
    best_gamma = np.exp(result['best_x'][1])

    print(f"最优超参数:")
    print(f"  C = {best_C:.4f}")
    print(f"  gamma = {best_gamma:.4f}")
    print(f"\n最优准确率: {result['best_y']:.4f}")
    print(f"评估次数: {result['n_evaluations']}")

    # 比较不同采集函数
    print("\n" + "=" * 60)
    print("不同采集函数比较")
    print("=" * 60)

    from src.acquisition import UpperConfidenceBound, ProbabilityOfImprovement

    acquisitions = {
        'EI': ExpectedImprovement(xi=0.01),
        'UCB': UpperConfidenceBound(kappa=2.0),
        'PI': ProbabilityOfImprovement(xi=0.01)
    }

    for name, acq in acquisitions.items():
        optimizer = BayesianOptimizer(
            objective_function=svm_objective,
            bounds=bounds,
            acquisition=acq,
            kernel='matern',
            n_initial=5,
            maximize=True,
            random_state=42
        )

        result = optimizer.optimize(n_iterations=10, verbose=False)
        print(f"{name}: 最优准确率 = {result['best_y']:.4f}")


if __name__ == '__main__':
    main()
