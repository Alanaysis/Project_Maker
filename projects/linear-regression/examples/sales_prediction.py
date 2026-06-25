#!/usr/bin/env python3
"""销量预测示例

使用线性回归预测产品销量，演示：
1. 多元特征处理
2. 正则化模型选择
3. 交叉验证调参
4. 完整的预测流水线
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression, RidgeRegression, ElasticNet
from src.feature_engineering import (
    StandardScaler,
    PolynomialFeatures,
    FeatureSelector,
    cross_validation,
)
from src.evaluation import mean_squared_error, root_mean_squared_error
from src.evaluation import mean_absolute_error, r2_score
from src.utils import train_test_split, print_evaluation_report


def generate_sales_data(n_samples: int = 300, random_state: int = 42) -> tuple:
    """生成模拟销量数据

    特征：
    - price: 价格（元）
    - advertising: 广告投入（万元）
    - competitor_price: 竞品价格（元）
    - season: 季节（1-4）
    - is_holiday: 是否节假日（0/1）
    - store_size: 门店面积（平方米）

    销量公式：
    sales = -10*price + 50*advertising + 8*competitor_price
          + 200*season + 500*is_holiday + 5*store_size + 1000 + noise
    """
    np.random.seed(random_state)

    price = np.random.uniform(10, 100, n_samples)
    advertising = np.random.uniform(0, 50, n_samples)
    competitor_price = np.random.uniform(10, 100, n_samples)
    season = np.random.randint(1, 5, n_samples).astype(float)
    is_holiday = np.random.binomial(1, 0.2, n_samples).astype(float)
    store_size = np.random.uniform(50, 500, n_samples)

    X = np.column_stack([price, advertising, competitor_price, season, is_holiday, store_size])

    true_weights = np.array([-10, 50, 8, 200, 500, 5])
    true_bias = 1000
    noise = np.random.randn(n_samples) * 100

    y = X @ true_weights + true_bias + noise

    feature_names = ["price", "advertising", "competitor_price", "season", "is_holiday", "store_size"]

    return X, y, feature_names, true_weights, true_bias


def main():
    print("\n" + "#" * 60)
    print("#  Sales Prediction")
    print("#" * 60)

    # ========================================
    # Step 1: 数据生成与探索
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 1: Data Generation & Exploration")
    print("=" * 60)

    X, y, feature_names, true_weights, true_bias = generate_sales_data(300)

    print(f"\n  Samples: {X.shape[0]}")
    print(f"  Features: {feature_names}")
    print(f"  Sales range: {y.min():.0f} - {y.max():.0f}")
    print(f"  Sales mean: {y.mean():.0f}")

    print(f"\n  True model:")
    print(f"    sales = {true_weights[0]}*price + {true_weights[1]}*advertising")
    print(f"          + {true_weights[2]}*competitor_price + {true_weights[3]}*season")
    print(f"          + {true_weights[4]}*is_holiday + {true_weights[5]}*store_size")
    print(f"          + {true_bias}")

    # ========================================
    # Step 2: 数据预处理
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 2: Data Preprocessing")
    print("=" * 60)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\n  Train: {len(X_train)}, Test: {len(X_test)}")

    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 多项式特征
    poly = PolynomialFeatures(degree=2)
    X_train_poly = poly.fit_transform(X_train_scaled)
    X_test_poly = poly.fit_transform(X_test_scaled)
    print(f"  Polynomial features (degree=2): {X_train_poly.shape[1]} features")

    # ========================================
    # Step 3: 模型训练与对比
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 3: Model Training & Comparison")
    print("=" * 60)

    results = {}

    # 普通线性回归
    lr = LinearRegression(learning_rate=0.001, n_iterations=2000)
    lr.fit(X_train_scaled, y_train)
    results["Linear Regression"] = (lr, X_test_scaled)

    # 正规方程
    ne = LinearRegression(method="normal_equation")
    ne.fit(X_train_scaled, y_train)
    results["Normal Equation"] = (ne, X_test_scaled)

    # Ridge
    ridge = RidgeRegression(alpha=10.0, learning_rate=0.001, n_iterations=2000)
    ridge.fit(X_train_scaled, y_train)
    results["Ridge (alpha=10)"] = (ridge, X_test_scaled)

    # Elastic Net
    enet = ElasticNet(alpha=1.0, l1_ratio=0.5, learning_rate=0.001, n_iterations=2000)
    enet.fit(X_train_scaled, y_train)
    results["Elastic Net"] = (enet, X_test_scaled)

    # 多项式特征 + Ridge
    ridge_poly = RidgeRegression(alpha=100.0, learning_rate=0.0001, n_iterations=5000)
    ridge_poly.fit(X_train_poly, y_train)
    results["Ridge + Poly(d=2)"] = (ridge_poly, X_test_poly)

    print(f"\n  {'Model':<25} {'Train R2':<12} {'Test R2':<12} {'Test RMSE':<15}")
    print(f"  {'-'*64}")

    for name, (model, X_eval) in results.items():
        y_train_pred = model.predict(X_eval if name == "Normal Equation" else
                                      X_train_scaled if "Poly" not in name else X_train_poly)
        # Recalculate properly
        y_test_pred = model.predict(X_eval)
        train_r2 = model.score(
            X_train_poly if "Poly" in name else X_train_scaled, y_train
        )
        test_r2 = r2_score(y_test, y_test_pred)
        test_rmse = root_mean_squared_error(y_test, y_test_pred)

        print(f"  {name:<25} {train_r2:<12.4f} {test_r2:<12.4f} {test_rmse:<15.2f}")

    # ========================================
    # Step 4: 交叉验证选择最佳模型
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 4: Cross Validation for Model Selection")
    print("=" * 60)

    print(f"\n  5-Fold CV Results (MSE):\n")

    cv_configs = [
        ("Linear Regression", LinearRegression, {"learning_rate": 0.001, "n_iterations": 1000}),
        ("Ridge (alpha=10)", RidgeRegression, {"alpha": 10.0, "learning_rate": 0.001, "n_iterations": 1000}),
        ("Elastic Net", ElasticNet, {"alpha": 1.0, "l1_ratio": 0.5, "learning_rate": 0.001, "n_iterations": 1000}),
    ]

    print(f"  {'Model':<25} {'CV Mean':<12} {'CV Std':<12}")
    print(f"  {'-'*49}")

    best_cv_score = float("inf")
    best_model_name = ""

    for name, model_class, params in cv_configs:
        np.random.seed(42)
        cv_result = cross_validation(
            X, y, model_class=model_class, model_params=params, n_folds=5, metric="mse"
        )
        print(f"  {name:<25} {cv_result['mean']:<12.2f} {cv_result['std']:<12.2f}")

        if cv_result["mean"] < best_cv_score:
            best_cv_score = cv_result["mean"]
            best_model_name = name

    print(f"\n  Best model by CV: {best_model_name}")

    # ========================================
    # Step 5: 最佳模型详细评估
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 5: Best Model Detailed Evaluation")
    print("=" * 60)

    best_model = results[best_model_name][0]
    best_X_test = results[best_model_name][1]

    y_train_pred = best_model.predict(X_train_scaled if "Poly" not in best_model_name else X_train_poly)
    y_test_pred = best_model.predict(best_X_test)

    print_evaluation_report(y_train, y_train_pred, "Train")
    print_evaluation_report(y_test, y_test_pred, "Test")

    # ========================================
    # Step 6: 特征重要性
    # ========================================
    print("=" * 60)
    print("  Step 6: Feature Importance")
    print("=" * 60)

    weights = ne.weights
    sorted_indices = np.argsort(np.abs(weights))[::-1]

    print(f"\n  {'Rank':<8} {'Feature':<20} {'Weight':<15} {'True Weight':<15}")
    print(f"  {'-'*58}")

    for rank, idx in enumerate(sorted_indices):
        print(
            f"  {rank+1:<8} {feature_names[idx]:<20} "
            f"{weights[idx]:<15.2f} {true_weights[idx]:<15.2f}"
        )

    # ========================================
    # Step 7: 预测新数据
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 7: Predict New Data")
    print("=" * 60)

    new_data = np.array([
        [50, 20, 60, 3, 0, 200],   # 中等价格, 中等广告, 竞品60, 秋季, 非假日, 中等店
        [30, 40, 80, 4, 1, 400],    # 低价, 高广告, 竞品80, 冬季, 假日, 大店
        [90, 5, 40, 1, 0, 80],      # 高价, 低广告, 竞品40, 春季, 非假日, 小店
    ])

    new_scaled = scaler.transform(new_data)
    predictions = ne.predict(new_scaled)
    true_values = new_data @ true_weights + true_bias

    print(f"\n  {'Price':<8} {'Advt':<8} {'CompP':<8} {'Season':<8} {'Holidy':<8} {'Size':<8} {'Predict':<12} {'True':<12}")
    print(f"  {'-'*72}")

    for i in range(len(new_data)):
        print(
            f"  {new_data[i][0]:<8.0f} {new_data[i][1]:<8.0f} "
            f"{new_data[i][2]:<8.0f} {new_data[i][3]:<8.0f} "
            f"{new_data[i][4]:<8.0f} {new_data[i][5]:<8.0f} "
            f"{predictions[i]:<12.0f} {true_values[i]:<12.0f}"
        )

    print("\n" + "#" * 60)
    print("#  Sales Prediction Completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
