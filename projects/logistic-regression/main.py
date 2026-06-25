#!/usr/bin/env python3
"""
逻辑回归项目主入口

运行方式: python main.py
"""

import sys
import os
import numpy as np

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import (
    LogisticRegression,
    OneVsRestClassifier,
    SoftmaxRegression,
    LogisticRegressionL1,
    LogisticRegressionL2,
    ElasticNet,
    StandardScaler,
    MinMaxScaler,
    train_test_split,
    cross_validate,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    roc_curve,
    auc_score,
    BatchGradientDescent,
    StochasticGradientDescent,
    MiniBatchGradientDescent,
    AdamOptimizer
)


def demo_basic_logistic_regression():
    """演示基础逻辑回归"""
    print("=" * 60)
    print("1. 基础逻辑回归演示")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 训练模型
    model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    model.fit(X_train, y_train)

    # 预测
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # 评估
    print(f"\n准确率: {accuracy_score(y_test, y_pred):.4f}")
    print(f"精确率: {precision_score(y_test, y_pred):.4f}")
    print(f"召回率: {recall_score(y_test, y_pred):.4f}")
    print(f"F1分数: {f1_score(y_test, y_pred):.4f}")

    # ROC曲线和AUC
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    auc = auc_score(fpr, tpr)
    print(f"AUC: {auc:.4f}")


def demo_multiclass():
    """演示多分类"""
    print("\n" + "=" * 60)
    print("2. 多分类演示")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X = np.random.randn(150, 2)
    y = np.zeros(150, dtype=int)
    y[X[:, 0] + X[:, 1] > 1] = 1
    y[X[:, 0] + X[:, 1] > 2] = 2

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # One-vs-Rest
    print("\nOne-vs-Rest:")
    ovr = OneVsRestClassifier(learning_rate=0.1, n_iterations=1000)
    ovr.fit(X_train, y_train)
    y_pred_ovr = ovr.predict(X_test)
    print(f"准确率: {accuracy_score(y_test, y_pred_ovr):.4f}")

    # Softmax回归
    print("\nSoftmax回归:")
    softmax = SoftmaxRegression(learning_rate=0.1, n_iterations=1000)
    softmax.fit(X_train, y_train)
    y_pred_softmax = softmax.predict(X_test)
    print(f"准确率: {accuracy_score(y_test, y_pred_softmax):.4f}")


def demo_regularization():
    """演示正则化"""
    print("\n" + "=" * 60)
    print("3. 正则化演示")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X = np.random.randn(100, 5)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 无正则化
    model_lr = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    model_lr.fit(X_train, y_train)
    acc_lr = model_lr.score(X_test, y_test)

    # L1正则化
    model_l1 = LogisticRegressionL1(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
    model_l1.fit(X_train, y_train)
    acc_l1 = model_l1.score(X_test, y_test)

    # L2正则化
    model_l2 = LogisticRegressionL2(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
    model_l2.fit(X_train, y_train)
    acc_l2 = model_l2.score(X_test, y_test)

    # Elastic Net
    model_en = ElasticNet(learning_rate=0.1, n_iterations=1000, l1_ratio=0.5, lambda_param=0.1)
    model_en.fit(X_train, y_train)
    acc_en = model_en.score(X_test, y_test)

    print(f"\n{'方法':<20} {'准确率':<10}")
    print("-" * 30)
    print(f"{'无正则化':<20} {acc_lr:<10.4f}")
    print(f"{'L1正则化':<20} {acc_l1:<10.4f}")
    print(f"{'L2正则化':<20} {acc_l2:<10.4f}")
    print(f"{'Elastic Net':<20} {acc_en:<10.4f}")

    print(f"\nL1正则化后权重为0的特征数量: {np.sum(np.abs(model_l1.weights) < 1e-6)}")


def demo_feature_engineering():
    """演示特征工程"""
    print("\n" + "=" * 60)
    print("4. 特征工程演示")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X = np.random.randn(100, 3) * np.array([100, 10, 1])  # 不同尺度
    y = (X[:, 0] + X[:, 1] + X[:, 2] > 0).astype(int)

    print("\n原始数据统计:")
    print(f"特征1 - 均值: {X[:, 0].mean():.2f}, 标准差: {X[:, 0].std():.2f}")
    print(f"特征2 - 均值: {X[:, 1].mean():.2f}, 标准差: {X[:, 1].std():.2f}")
    print(f"特征3 - 均值: {X[:, 2].mean():.2f}, 标准差: {X[:, 2].std():.2f}")

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\n标准化后数据统计:")
    print(f"特征1 - 均值: {X_scaled[:, 0].mean():.2f}, 标准差: {X_scaled[:, 0].std():.2f}")
    print(f"特征2 - 均值: {X_scaled[:, 1].mean():.2f}, 标准差: {X_scaled[:, 1].std():.2f}")
    print(f"特征3 - 均值: {X_scaled[:, 2].mean():.2f}, 标准差: {X_scaled[:, 2].std():.2f}")

    # 交叉验证
    model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    cv_scores = cross_validate(model, X_scaled, y, cv=5, scoring='accuracy')
    print(f"\n5折交叉验证分数: {cv_scores}")
    print(f"平均准确率: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")


def demo_optimizers():
    """演示优化算法"""
    print("\n" + "=" * 60)
    print("5. 优化算法演示")
    print("=" * 60)

    # 生成数据
    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 批量梯度下降
    model_bgd = BatchGradientDescent(learning_rate=0.1, n_iterations=1000)
    model_bgd.fit(X_train, y_train)
    acc_bgd = model_bgd.score(X_test, y_test)

    # 随机梯度下降
    model_sgd = StochasticGradientDescent(learning_rate=0.01, n_iterations=100)
    model_sgd.fit(X_train, y_train)
    acc_sgd = model_sgd.score(X_test, y_test)

    # 小批量梯度下降
    model_mbgd = MiniBatchGradientDescent(learning_rate=0.1, n_iterations=1000, batch_size=32)
    model_mbgd.fit(X_train, y_train)
    acc_mbgd = model_mbgd.score(X_test, y_test)

    # Adam优化器
    model_adam = AdamOptimizer(learning_rate=0.001, n_iterations=1000)
    model_adam.fit(X_train, y_train)
    acc_adam = model_adam.score(X_test, y_test)

    print(f"\n{'优化器':<20} {'准确率':<10}")
    print("-" * 30)
    print(f"{'批量梯度下降':<20} {acc_bgd:<10.4f}")
    print(f"{'随机梯度下降':<20} {acc_sgd:<10.4f}")
    print(f"{'小批量梯度下降':<20} {acc_mbgd:<10.4f}")
    print(f"{'Adam优化器':<20} {acc_adam:<10.4f}")


def main():
    """主函数"""
    print("=" * 60)
    print("逻辑回归项目演示")
    print("=" * 60)

    # 1. 基础逻辑回归
    demo_basic_logistic_regression()

    # 2. 多分类
    demo_multiclass()

    # 3. 正则化
    demo_regularization()

    # 4. 特征工程
    demo_feature_engineering()

    # 5. 优化算法
    demo_optimizers()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n更多示例请运行:")
    print("  python examples/spam_classification.py")
    print("  python examples/disease_diagnosis.py")
    print("  python examples/credit_scoring.py")


if __name__ == '__main__':
    main()
