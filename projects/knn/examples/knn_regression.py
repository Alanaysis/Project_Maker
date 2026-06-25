"""
KNN 回归示例

使用 KNN 回归器进行函数拟合和房价预测。
"""

import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import KNNRegressor, CrossValidator, train_test_split, mean_squared_error, r2_score


def generate_sine_data(n_samples=100, noise=0.1):
    """
    生成正弦函数数据

    Args:
        n_samples: 样本数量
        noise: 噪声水平

    Returns:
        X: 特征 (n_samples, 1)
        y: 目标值 (n_samples,)
    """
    np.random.seed(42)
    X = np.sort(np.random.uniform(0, 2 * np.pi, n_samples)).reshape(-1, 1)
    y = np.sin(X.ravel()) + np.random.randn(n_samples) * noise
    return X, y


def generate_house_data(n_samples=200):
    """
    生成模拟房价数据

    特征: 面积(平方米), 卧室数, 楼层, 房龄(年)
    目标: 价格(万元)

    Args:
        n_samples: 样本数量

    Returns:
        X: 特征矩阵 (n_samples, 4)
        y: 目标值 (n_samples,)
    """
    np.random.seed(42)

    # 生成特征
    area = np.random.uniform(50, 200, n_samples)  # 面积 50-200 平方米
    bedrooms = np.random.randint(1, 5, n_samples)  # 卧室 1-4
    floor = np.random.randint(1, 30, n_samples)  # 楼层 1-30
    age = np.random.uniform(0, 30, n_samples)  # 房龄 0-30 年

    X = np.column_stack([area, bedrooms, floor, age])

    # 生成房价（基于特征的线性组合 + 噪声）
    price = (area * 2.5 +
             bedrooms * 50 +
             floor * 3 -
             age * 5 +
             np.random.randn(n_samples) * 50)

    return X, price


def main():
    """运行回归示例"""
    print("=" * 60)
    print("KNN 回归示例")
    print("=" * 60)

    # ===== 示例 1: 正弦函数拟合 =====
    print("\n" + "=" * 60)
    print("示例 1: 正弦函数拟合")
    print("=" * 60)

    # 1. 加载数据
    print("\n1. 加载数据...")
    X, y = generate_sine_data(n_samples=100, noise=0.1)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")

    # 2. 划分数据集
    print("\n2. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 3. 测试不同 K 值
    print("\n3. 测试不同 K 值...")
    k_values = [1, 3, 5, 7, 11, 15]

    for k in k_values:
        reg = KNNRegressor(k=k, metric='euclidean', weights='uniform')
        reg.fit(X_train, y_train)
        y_pred = reg.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"   K={k:2d}: MSE = {mse:.4f}, R² = {r2:.4f}")

    # 4. 测试不同权重策略
    print("\n4. 测试不同权重策略...")
    for weights in ['uniform', 'distance']:
        reg = KNNRegressor(k=5, metric='euclidean', weights=weights)
        reg.fit(X_train, y_train)
        y_pred = reg.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print(f"   {weights:10s}: MSE = {mse:.4f}, R² = {r2:.4f}")

    # ===== 示例 2: 房价预测 =====
    print("\n" + "=" * 60)
    print("示例 2: 房价预测")
    print("=" * 60)

    # 1. 加载数据
    print("\n1. 加载数据...")
    X, y = generate_house_data(n_samples=200)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   特征: 面积(㎡), 卧室数, 楼层, 房龄(年)")

    # 2. 划分数据集
    print("\n2. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # 3. 训练模型
    print("\n3. 训练模型...")
    reg = KNNRegressor(k=5, metric='euclidean', weights='distance')
    reg.fit(X_train, y_train)

    # 4. 评估模型
    print("\n4. 模型评估...")
    y_pred = reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"   MSE: {mse:.4f}")
    print(f"   R²: {r2:.4f}")

    # 5. 预测示例
    print("\n5. 预测示例...")
    # 新房子: 120㎡, 3室, 15层, 5年房龄
    new_house = np.array([[120, 3, 15, 5]])
    predicted_price = reg.predict(new_house)
    print(f"   新房子: {new_house[0]}")
    print(f"   预测价格: {predicted_price[0]:.2f} 万元")

    # 6. 交叉验证
    print("\n6. 交叉验证选择最优 K...")
    cv = CrossValidator(n_folds=5, shuffle=True, random_state=42)
    cv_results = cv.select_k(
        X, y,
        k_range=[1, 3, 5, 7, 9, 11, 15],
        metric='euclidean',
        task='regression',
        weights='distance'
    )
    print(f"   最优 K: {cv_results['best_k']}")
    print(f"   最优 R²: {cv_results['best_score']:.4f}")

    # 7. 各 K 值的详细结果
    print("\n7. 各 K 值的交叉验证结果...")
    for k, score in sorted(cv_results['k_scores'].items()):
        std = cv_results['k_std'][k]
        print(f"   K={k:2d}: R² = {score:.4f} (±{std:.4f})")

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
