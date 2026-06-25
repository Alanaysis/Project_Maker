#!/usr/bin/env python3
"""房价预测示例

使用线性回归预测房价，演示完整的机器学习工作流程：
1. 数据生成与探索
2. 特征工程
3. 模型训练（多种方法对比）
4. 模型评估
5. 结果分析
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression, RidgeRegression, LassoRegression
from src.feature_engineering import StandardScaler, PolynomialFeatures, cross_validation
from src.evaluation import mean_squared_error, root_mean_squared_error
from src.evaluation import mean_absolute_error, r2_score
from src.utils import train_test_split, print_evaluation_report


def generate_house_data(n_samples: int = 500, random_state: int = 42) -> tuple:
    """生成模拟房价数据

    特征说明：
    - area: 面积（平方米）
    - bedrooms: 卧室数量
    - age: 房龄（年）
    - distance: 距市中心距离（公里）
    - floor: 楼层

    房价公式：
    price = 5000*area + 50000*bedrooms - 2000*age
          - 10000*distance + 5000*floor + 100000 + noise
    """
    np.random.seed(random_state)

    area = np.random.uniform(50, 200, n_samples)           # 50-200 平方米
    bedrooms = np.random.randint(1, 5, n_samples).astype(float)  # 1-4 间
    age = np.random.uniform(0, 30, n_samples)               # 0-30 年
    distance = np.random.uniform(1, 20, n_samples)          # 1-20 公里
    floor = np.random.randint(1, 30, n_samples).astype(float)  # 1-30 层

    X = np.column_stack([area, bedrooms, age, distance, floor])

    # 房价公式
    true_weights = np.array([5000, 50000, -2000, -10000, 5000])
    true_bias = 100000
    noise = np.random.randn(n_samples) * 20000

    y = X @ true_weights + true_bias + noise

    feature_names = ["area", "bedrooms", "age", "distance", "floor"]

    return X, y, feature_names, true_weights, true_bias


def main():
    print("\n" + "#" * 60)
    print("#  House Price Prediction")
    print("#" * 60)

    # ========================================
    # Step 1: 数据生成与探索
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 1: Data Generation & Exploration")
    print("=" * 60)

    X, y, feature_names, true_weights, true_bias = generate_house_data(500)

    print(f"\n  Samples: {X.shape[0]}")
    print(f"  Features: {feature_names}")
    print(f"  Price range: {y.min():.0f} - {y.max():.0f}")
    print(f"  Price mean: {y.mean():.0f}")

    print(f"\n  True model:")
    print(f"    price = {true_weights[0]}*area + {true_weights[1]}*bedrooms")
    print(f"          + {true_weights[2]}*age + {true_weights[3]}*distance")
    print(f"          + {true_weights[4]}*floor + {true_bias}")

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

    print(f"  StandardScaler applied")

    # ========================================
    # Step 3: 模型训练与对比
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 3: Model Training & Comparison")
    print("=" * 60)

    models = {}

    # 普通线性回归
    lr = LinearRegression(learning_rate=0.01, n_iterations=2000)
    lr.fit(X_train_scaled, y_train)
    models["Linear Regression"] = lr

    # 正规方程
    lr_ne = LinearRegression(method="normal_equation")
    lr_ne.fit(X_train_scaled, y_train)
    models["Normal Equation"] = lr_ne

    # Ridge 回归
    ridge = RidgeRegression(alpha=1.0, learning_rate=0.01, n_iterations=2000)
    ridge.fit(X_train_scaled, y_train)
    models["Ridge (alpha=1.0)"] = ridge

    # Lasso 回归
    lasso = LassoRegression(alpha=100.0, learning_rate=0.01, n_iterations=2000)
    lasso.fit(X_train_scaled, y_train)
    models["Lasso (alpha=100)"] = lasso

    print(f"\n  {'Model':<25} {'Train R2':<12} {'Test R2':<12} {'Test RMSE':<15}")
    print(f"  {'-'*64}")

    for name, model in models.items():
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)

        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        test_rmse = root_mean_squared_error(y_test, y_test_pred)

        print(f"  {name:<25} {train_r2:<12.4f} {test_r2:<12.4f} {test_rmse:<15.0f}")

    # ========================================
    # Step 4: 详细评估最佳模型
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 4: Detailed Evaluation (Best Model)")
    print("=" * 60)

    best_model = models["Normal Equation"]
    y_train_pred = best_model.predict(X_train_scaled)
    y_test_pred = best_model.predict(X_test_scaled)

    print_evaluation_report(y_train, y_train_pred, "Train")
    print_evaluation_report(y_test, y_test_pred, "Test")

    # ========================================
    # Step 5: 特征重要性分析
    # ========================================
    print("=" * 60)
    print("  Step 5: Feature Importance Analysis")
    print("=" * 60)

    # 标准化后的权重反映特征重要性
    weights = best_model.weights
    sorted_indices = np.argsort(np.abs(weights))[::-1]

    print(f"\n  {'Rank':<8} {'Feature':<15} {'Weight':<15} {'Importance':<15}")
    print(f"  {'-'*53}")

    for rank, idx in enumerate(sorted_indices):
        importance = abs(weights[idx]) / np.sum(np.abs(weights)) * 100
        print(f"  {rank+1:<8} {feature_names[idx]:<15} {weights[idx]:<15.2f} {importance:<15.1f}%")

    print(f"\n  True weights: {dict(zip(feature_names, true_weights))}")

    # ========================================
    # Step 6: 交叉验证
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 6: Cross Validation")
    print("=" * 60)

    # 用标准化前的数据做交叉验证（CV 内部会训练新模型）
    np.random.seed(42)
    cv_result = cross_validation(
        X, y,
        model_class=LinearRegression,
        model_params={"learning_rate": 0.01, "n_iterations": 1000},
        n_folds=5,
        metric="r2",
    )

    print(f"\n  5-Fold Cross Validation (R2):")
    print(f"    Scores: {cv_result['scores']}")
    print(f"    Mean:   {cv_result['mean']:.4f}")
    print(f"    Std:    {cv_result['std']:.4f}")

    # ========================================
    # Step 7: 预测示例
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 7: Prediction Examples")
    print("=" * 60)

    new_houses = np.array([
        [100, 3, 5, 5, 10],    # 100平, 3室, 5年, 5公里, 10层
        [150, 4, 10, 10, 20],   # 150平, 4室, 10年, 10公里, 20层
        [60, 1, 20, 15, 3],     # 60平, 1室, 20年, 15公里, 3层
    ])

    new_houses_scaled = scaler.transform(new_houses)
    predictions = best_model.predict(new_houses_scaled)

    # 计算真实价格
    true_prices = new_houses @ true_weights + true_bias

    print(f"\n  {'Area':<8} {'Beds':<6} {'Age':<6} {'Dist':<6} {'Floor':<6} {'Predicted':<15} {'True':<15}")
    print(f"  {'-'*62}")

    for i in range(len(new_houses)):
        print(
            f"  {new_houses[i][0]:<8.0f} {new_houses[i][1]:<6.0f} "
            f"{new_houses[i][2]:<6.0f} {new_houses[i][3]:<6.0f} "
            f"{new_houses[i][4]:<6.0f} {predictions[i]:<15.0f} {true_prices[i]:<15.0f}"
        )

    print("\n" + "#" * 60)
    print("#  House Price Prediction Completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
