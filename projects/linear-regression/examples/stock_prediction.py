#!/usr/bin/env python3
"""股票价格预测示例

使用线性回归预测股票价格变化，演示：
1. 时间序列特征工程
2. 技术指标计算
3. 模型训练与评估
4. 特征重要性分析

注意：这是一个教学示例，实际股票预测远比这复杂。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from src.model import LinearRegression, RidgeRegression
from src.feature_engineering import StandardScaler, FeatureSelector
from src.evaluation import mean_squared_error, root_mean_squared_error
from src.evaluation import mean_absolute_error, r2_score
from src.utils import train_test_split, print_evaluation_report


def generate_stock_data(n_days: int = 500, random_state: int = 42) -> tuple:
    """生成模拟股票数据

    模拟股票价格的随机游走过程，并计算技术指标作为特征。

    特征：
    - return_1d: 前 1 天收益率
    - return_5d: 前 5 天收益率
    - ma_5: 5 日均线偏离度
    - ma_20: 20 日均线偏离度
    - volatility: 5 日波动率
    - volume_change: 成交量变化

    目标：当天收益率
    """
    np.random.seed(random_state)

    # 生成价格序列（随机游走）
    returns = np.random.randn(n_days) * 0.02  # 日收益率 ~2%
    prices = 100 * np.exp(np.cumsum(returns))  # 价格

    # 生成成交量
    volumes = np.random.lognormal(mean=10, sigma=0.5, size=n_days)

    # 计算技术指标作为特征
    features = []
    targets = []
    valid_start = 20  # 需要至少 20 天数据计算指标

    for i in range(valid_start, n_days - 1):
        # 特征
        return_1d = (prices[i] - prices[i - 1]) / prices[i - 1]
        return_5d = (prices[i] - prices[i - 5]) / prices[i - 5]
        ma_5 = np.mean(prices[i - 4 : i + 1])
        ma_20 = np.mean(prices[i - 19 : i + 1])
        ma_5_deviation = (prices[i] - ma_5) / ma_5
        ma_20_deviation = (prices[i] - ma_20) / ma_20
        volatility = np.std(returns[i - 4 : i + 1])
        volume_change = (volumes[i] - volumes[i - 1]) / volumes[i - 1]

        features.append(
            [return_1d, return_5d, ma_5_deviation, ma_20_deviation, volatility, volume_change]
        )

        # 目标：下一天收益率
        target = (prices[i + 1] - prices[i]) / prices[i]
        targets.append(target)

    X = np.array(features)
    y = np.array(targets)

    feature_names = [
        "return_1d",
        "return_5d",
        "ma_5_dev",
        "ma_20_dev",
        "volatility",
        "volume_chg",
    ]

    return X, y, feature_names, prices


def main():
    print("\n" + "#" * 60)
    print("#  Stock Price Prediction")
    print("#" * 60)

    # ========================================
    # Step 1: 数据生成与探索
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 1: Data Generation & Exploration")
    print("=" * 60)

    X, y, feature_names, prices = generate_stock_data(500)

    print(f"\n  Samples: {X.shape[0]} (trading days)")
    print(f"  Features: {feature_names}")
    print(f"  Target: Next day return")
    print(f"  Price range: {prices.min():.2f} - {prices.max():.2f}")
    print(f"  Daily return mean: {y.mean():.4f}")
    print(f"  Daily return std: {y.std():.4f}")

    # ========================================
    # Step 2: 特征工程
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 2: Feature Engineering")
    print("=" * 60)

    # 划分数据（时间序列不能随机打乱，这里简化处理）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"\n  Train: {len(X_train)} days, Test: {len(X_test)} days")

    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 特征选择（相关性）
    X_train_selected, selected_idx = FeatureSelector.correlation_selection(
        X_train_scaled, y_train, top_k=4
    )
    X_test_selected = X_test_scaled[:, selected_idx]

    print(f"  Selected features: {[feature_names[i] for i in selected_idx]}")

    # ========================================
    # Step 3: 模型训练
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 3: Model Training")
    print("=" * 60)

    # 普通线性回归
    model_lr = LinearRegression(learning_rate=0.001, n_iterations=2000)
    model_lr.fit(X_train_scaled, y_train)

    # 正规方程
    model_ne = LinearRegression(method="normal_equation")
    model_ne.fit(X_train_scaled, y_train)

    # Ridge 回归（防止过拟合）
    model_ridge = RidgeRegression(alpha=1.0, learning_rate=0.001, n_iterations=2000)
    model_ridge.fit(X_train_scaled, y_train)

    # 特征选择后的模型
    model_selected = LinearRegression(method="normal_equation")
    model_selected.fit(X_train_selected, y_train)

    # ========================================
    # Step 4: 模型评估
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 4: Model Evaluation")
    print("=" * 60)

    models = {
        "Linear Regression": (model_lr, X_test_scaled),
        "Normal Equation": (model_ne, X_test_scaled),
        "Ridge (alpha=1)": (model_ridge, X_test_scaled),
        "Feature Selected": (model_selected, X_test_selected),
    }

    print(f"\n  {'Model':<25} {'MSE':<12} {'MAE':<12} {'R2':<10}")
    print(f"  {'-'*59}")

    for name, (model, X_eval) in models.items():
        y_pred = model.predict(X_eval)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"  {name:<25} {mse:<12.6f} {mae:<12.6f} {r2:<10.4f}")

    # ========================================
    # Step 5: 特征重要性
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 5: Feature Importance")
    print("=" * 60)

    weights = model_ne.weights
    sorted_indices = np.argsort(np.abs(weights))[::-1]

    print(f"\n  {'Rank':<8} {'Feature':<15} {'Weight':<15}")
    print(f"  {'-'*38}")

    for rank, idx in enumerate(sorted_indices):
        print(f"  {rank+1:<8} {feature_names[idx]:<15} {weights[idx]:<15.6f}")

    # ========================================
    # Step 6: 模拟交易策略
    # ========================================
    print("\n" + "=" * 60)
    print("  Step 6: Simulated Trading Strategy")
    print("=" * 60)

    y_pred_all = model_ne.predict(X_test_scaled)

    # 简单策略：预测上涨则买入，预测下跌则卖出
    positions = np.sign(y_pred_all)  # 1=做多, -1=做空
    strategy_returns = positions * y_test
    buy_hold_returns = y_test

    cumulative_strategy = np.cumsum(strategy_returns)
    cumulative_buyhold = np.cumsum(buy_hold_returns)

    print(f"\n  Test period: {len(y_test)} days")
    print(f"  Strategy cumulative return: {cumulative_strategy[-1]:.4f}")
    print(f"  Buy & Hold cumulative return: {cumulative_buyhold[-1]:.4f}")
    print(f"  Strategy Sharpe (approx): {np.mean(strategy_returns)/np.std(strategy_returns)*np.sqrt(252):.2f}")

    print("\n  Note: This is a simplified educational example.")
    print("  Real stock prediction requires much more sophisticated models.")

    print("\n" + "#" * 60)
    print("#  Stock Prediction Completed!")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
