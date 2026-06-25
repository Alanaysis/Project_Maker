#!/usr/bin/env python3
"""特征工程示例

演示特征工程的核心技术：
- 特征缩放（标准化、归一化）
- 多项式特征
- 特征选择
- 交叉验证
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression, RidgeRegression
from src.feature_engineering import (
    StandardScaler,
    MinMaxScaler,
    PolynomialFeatures,
    FeatureSelector,
    cross_validation,
)
from src.evaluation import mean_squared_error, r2_score
from src.utils import generate_linear_data, generate_nonlinear_data, train_test_split


def demo_feature_scaling():
    """演示特征缩放的重要性"""
    print("=" * 60)
    print("  Demo 1: Feature Scaling")
    print("=" * 60)

    np.random.seed(42)

    # 生成特征量纲差异很大的数据
    n_samples = 200
    X = np.zeros((n_samples, 3))
    X[:, 0] = np.random.randn(n_samples) * 0.01  # 很小的范围
    X[:, 1] = np.random.randn(n_samples) * 1000  # 很大的范围
    X[:, 2] = np.random.randn(n_samples) * 1     # 中等范围

    true_weights = np.array([100.0, 0.001, 10.0])
    y = X @ true_weights + 0.1 * np.random.randn(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\n  Feature scales: x1 ~ 0.01, x2 ~ 1000, x3 ~ 1")
    print(f"  True weights: [100.0, 0.001, 10.0]")

    # 不缩放
    model_no_scale = LinearRegression(learning_rate=1e-8, n_iterations=1000)
    model_no_scale.fit(X_train, y_train)
    r2_no_scale = r2_score(y_test, model_no_scale.predict(X_test))

    # 标准化缩放
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model_scaled = LinearRegression(learning_rate=0.01, n_iterations=500)
    model_scaled.fit(X_train_scaled, y_train)
    r2_scaled = r2_score(y_test, model_scaled.predict(X_test_scaled))

    # 归一化缩放
    scaler_mm = MinMaxScaler()
    X_train_mm = scaler_mm.fit_transform(X_train)
    X_test_mm = scaler_mm.transform(X_test)

    model_mm = LinearRegression(learning_rate=0.1, n_iterations=500)
    model_mm.fit(X_train_mm, y_train)
    r2_mm = r2_score(y_test, model_mm.predict(X_test_mm))

    print(f"\n  {'Method':<20} {'Learning Rate':<15} {'Test R2':<10}")
    print(f"  {'-'*45}")
    print(f"  {'No Scaling':<20} {'1e-8':<15} {r2_no_scale:<10.4f}")
    print(f"  {'StandardScaler':<20} {'0.01':<15} {r2_scaled:<10.4f}")
    print(f"  {'MinMaxScaler':<20} {'0.1':<15} {r2_mm:<10.4f}")

    print(f"\n  Observation: Feature scaling allows using larger learning rates")
    print(f"  and helps gradient descent converge faster and more reliably")


def demo_polynomial_features():
    """演示多项式特征处理非线性关系"""
    print("\n" + "=" * 60)
    print("  Demo 2: Polynomial Features")
    print("=" * 60)

    # 生成非线性数据: y = 0.5*x^2 + x + 2
    np.random.seed(42)
    X, y = generate_nonlinear_data(n_samples=100, noise=0.5, random_state=42)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\n  Data: y = 0.5*x^2 + x + 2 + noise")
    print(f"  Non-linear relationship!")

    # 线性模型（不使用多项式特征）
    model_linear = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model_linear.fit(X_train, y_train)
    r2_linear = r2_score(y_test, model_linear.predict(X_test))

    # 多项式特征 (degree=2)
    poly = PolynomialFeatures(degree=2)
    X_train_poly = poly.fit_transform(X_train)
    X_test_poly = poly.fit_transform(X_test)

    model_poly = LinearRegression(learning_rate=0.001, n_iterations=2000)
    model_poly.fit(X_train_poly, y_train)
    r2_poly = r2_score(y_test, model_poly.predict(X_test_poly))

    # 多项式特征 (degree=3)
    poly3 = PolynomialFeatures(degree=3)
    X_train_poly3 = poly3.fit_transform(X_train)
    X_test_poly3 = poly3.fit_transform(X_test)

    model_poly3 = LinearRegression(learning_rate=0.0001, n_iterations=5000)
    model_poly3.fit(X_train_poly3, y_train)
    r2_poly3 = r2_score(y_test, model_poly3.predict(X_test_poly3))

    print(f"\n  {'Model':<25} {'Test R2':<10}")
    print(f"  {'-'*35}")
    print(f"  {'Linear (degree=1)':<25} {r2_linear:<10.4f}")
    print(f"  {'Polynomial (degree=2)':<25} {r2_poly:<10.4f}")
    print(f"  {'Polynomial (degree=3)':<25} {r2_poly3:<10.4f}")

    print(f"\n  Original features: {X_train.shape[1]}")
    print(f"  Polynomial (d=2) features: {X_train_poly.shape[1]}")
    print(f"  Polynomial (d=3) features: {X_train_poly3.shape[1]}")

    print(f"\n  Observation: Polynomial features allow linear models to fit")
    print(f"  non-linear data. Degree=2 captures the quadratic relationship.")


def demo_feature_selection():
    """演示特征选择"""
    print("\n" + "=" * 60)
    print("  Demo 3: Feature Selection")
    print("=" * 60)

    np.random.seed(42)
    n_samples = 200
    n_features = 20

    # 只有前 5 个特征有用
    true_weights = np.zeros(n_features)
    true_weights[:5] = np.array([3.0, -2.0, 1.5, 0.5, -1.0])

    X, y = generate_linear_data(
        n_samples=n_samples,
        n_features=n_features,
        noise=0.5,
        true_weights=true_weights,
        true_bias=2.0,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\n  Data: {n_samples} samples, {n_features} features")
    print(f"  Only first 5 features are relevant")

    # 方差阈值选择
    X_train_var, var_indices = FeatureSelector.variance_threshold(X_train, threshold=0.5)
    X_test_var = X_test[:, var_indices]

    model_var = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model_var.fit(X_train_var, y_train)
    r2_var = r2_score(y_test, model_var.predict(X_test_var))

    # 相关性选择
    X_train_corr, corr_indices = FeatureSelector.correlation_selection(
        X_train, y_train, top_k=5
    )
    X_test_corr = X_test[:, corr_indices]

    model_corr = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model_corr.fit(X_train_corr, y_train)
    r2_corr = r2_score(y_test, model_corr.predict(X_test_corr))

    # RFE 选择
    ranking, rfe_indices = FeatureSelector.rfe_ranking(X_train, y_train, n_features_to_select=5)
    X_train_rfe = X_train[:, rfe_indices]
    X_test_rfe = X_test[:, rfe_indices]

    model_rfe = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model_rfe.fit(X_train_rfe, y_train)
    r2_rfe = r2_score(y_test, model_rfe.predict(X_test_rfe))

    # 全部特征
    model_all = LinearRegression(learning_rate=0.01, n_iterations=1000)
    model_all.fit(X_train, y_train)
    r2_all = r2_score(y_test, model_all.predict(X_test))

    print(f"\n  {'Method':<25} {'Features Used':<15} {'Test R2':<10}")
    print(f"  {'-'*50}")
    print(f"  {'All Features':<25} {n_features:<15} {r2_all:<10.4f}")
    print(f"  {'Variance Threshold':<25} {len(var_indices):<15} {r2_var:<10.4f}")
    print(f"  {'Correlation (top 5)':<25} {len(corr_indices):<15} {r2_corr:<10.4f}")
    print(f"  {'RFE (top 5)':<25} {len(rfe_indices):<15} {r2_rfe:<10.4f}")

    print(f"\n  Selected feature indices (Correlation): {corr_indices}")
    print(f"  True relevant features: [0, 1, 2, 3, 4]")


def demo_cross_validation():
    """演示交叉验证"""
    print("\n" + "=" * 60)
    print("  Demo 4: Cross Validation")
    print("=" * 60)

    np.random.seed(42)
    X, y = generate_linear_data(
        n_samples=100,
        n_features=3,
        noise=1.0,
        true_weights=np.array([2.0, -1.0, 3.0]),
        true_bias=1.0,
        random_state=42,
    )

    print(f"\n  Data: 100 samples, 3 features")
    print(f"  5-Fold Cross Validation\n")

    # 测试不同学习率
    learning_rates = [0.001, 0.01, 0.1]

    print(f"  {'Learning Rate':<15} {'CV MSE (mean)':<15} {'CV MSE (std)':<15}")
    print(f"  {'-'*45}")

    for lr in learning_rates:
        np.random.seed(42)
        result = cross_validation(
            X, y,
            model_class=LinearRegression,
            model_params={"learning_rate": lr, "n_iterations": 500},
            n_folds=5,
            metric="mse",
        )
        print(f"  {lr:<15.3f} {result['mean']:<15.4f} {result['std']:<15.4f}")

    print(f"\n  Cross validation helps select hyperparameters reliably")
    print(f"  Lower mean MSE with reasonable std indicates a good choice")


def main():
    print("\n" + "#" * 60)
    print("#  Feature Engineering Examples")
    print("#" * 60)

    demo_feature_scaling()
    demo_polynomial_features()
    demo_feature_selection()
    demo_cross_validation()

    print("\n" + "#" * 60)
    print("#  All feature engineering examples completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
