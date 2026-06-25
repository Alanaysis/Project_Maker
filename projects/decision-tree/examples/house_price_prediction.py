"""
房价预测示例

使用 CART 回归决策树预测房价。

特征包括：
- 面积 (平方米)
- 卧室数量
- 卫生间数量
- 楼层
- 建筑年份
- 距离地铁距离 (公里)
"""

import numpy as np
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cart_regressor import CARTRegressor
from src.utils import train_test_split
from src.evaluation import mean_squared_error, r2_score, mean_absolute_error


def generate_house_data(n_samples=500):
    """
    生成房价数据集

    参数:
    ----------
    n_samples : int
        样本数量

    返回:
    ----------
    X : numpy.ndarray
        特征矩阵
    y : numpy.ndarray
        目标变量（房价，单位：万元）
    feature_names : list
        特征名称
    """
    np.random.seed(42)

    # 生成特征
    area = np.random.uniform(50, 200, n_samples)  # 面积 50-200 平方米
    bedrooms = np.random.randint(1, 5, n_samples)  # 卧室 1-4
    bathrooms = np.random.randint(1, 3, n_samples)  # 卫生间 1-2
    floor = np.random.randint(1, 30, n_samples)  # 楼层 1-29
    year_built = np.random.randint(1990, 2024, n_samples)  # 建筑年份 1990-2023
    distance_to_subway = np.random.uniform(0.1, 5, n_samples)  # 距地铁距离 0.1-5 公里

    # 生成房价（基于特征的线性组合 + 噪声）
    price = (
        3 * area +  # 面积每增加1平方米，价格增加3万
        20 * bedrooms +  # 每个卧室增加20万
        30 * bathrooms +  # 每个卫生间增加30万
        0.5 * floor +  # 每层增加0.5万
        0.5 * (year_built - 1990) +  # 每年增加0.5万
        -15 * distance_to_subway +  # 距地铁每远1公里，减少15万
        50 +  # 基础价格50万
        np.random.normal(0, 30, n_samples)  # 噪声
    )

    # 确保价格为正
    price = np.maximum(price, 100)

    # 组合特征
    X = np.column_stack([area, bedrooms, bathrooms, floor, year_built, distance_to_subway])

    feature_names = ['面积', '卧室数量', '卫生间数量', '楼层', '建筑年份', '距地铁距离']

    return X, price, feature_names


def evaluate_regression(model, X_test, y_test, model_name):
    """
    评估回归模型性能

    参数:
    ----------
    model : CARTRegressor
        训练好的模型
    X_test : numpy.ndarray
        测试特征
    y_test : numpy.ndarray
        测试标签
    model_name : str
        模型名称
    """
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n{model_name} 评估结果:")
    print(f"  均方误差 (MSE):     {mse:.2f}")
    print(f"  均方根误差 (RMSE):  {rmse:.2f}")
    print(f"  平均绝对误差 (MAE): {mae:.2f}")
    print(f"  R² 分数:            {r2:.4f}")

    return {'mse': mse, 'rmse': rmse, 'mae': mae, 'r2': r2}


def main():
    """主函数"""
    print("=" * 60)
    print("房价预测示例 - CART 回归决策树")
    print("=" * 60)

    # 1. 生成数据
    print("\n1. 生成房价数据集...")
    X, y, feature_names = generate_house_data(n_samples=500)
    print(f"   数据集大小: {X.shape[0]} 个样本, {X.shape[1]} 个特征")
    print(f"   特征: {feature_names}")
    print(f"   房价范围: {y.min():.2f} - {y.max():.2f} 万元")

    # 2. 划分数据集
    print("\n2. 划分数据集 (80% 训练, 20% 测试)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   训练集大小: {X_train.shape[0]}")
    print(f"   测试集大小: {X_test.shape[0]}")

    # 3. 训练不同深度的回归树
    print("\n3. 训练不同深度的回归树...")

    results = {}
    depths = [3, 5, 10, None]

    for depth in depths:
        depth_name = str(depth) if depth else "不限制"
        print(f"\n   训练深度为 {depth_name} 的回归树...")

        tree = CARTRegressor(max_depth=depth, min_samples_split=5, min_samples_leaf=2)
        tree.fit(X_train, y_train)

        results[f"深度={depth_name}"] = evaluate_regression(
            tree, X_test, y_test, f"回归树 (深度={depth_name})"
        )

    # 4. 比较结果
    print("\n" + "=" * 60)
    print("不同深度回归树比较:")
    print("=" * 60)
    print(f"{'深度':<12} {'MSE':<12} {'RMSE':<12} {'MAE':<12} {'R²':<10}")
    print("-" * 60)
    for name, metrics in results.items():
        print(f"{name:<12} {metrics['mse']:<12.2f} {metrics['rmse']:<12.2f} "
              f"{metrics['mae']:<12.2f} {metrics['r2']:<10.4f}")

    # 5. 使用最优深度的模型进行预测
    print("\n5. 使用最优模型进行预测...")
    best_depth = min(results.items(), key=lambda x: x[1]['mse'])[0]
    print(f"   最优模型: {best_depth}")

    # 重新训练最优模型
    best_tree = CARTRegressor(max_depth=5, min_samples_split=5, min_samples_leaf=2)
    best_tree.fit(X_train, y_train)

    # 预测示例
    print("\n6. 预测示例:")
    print("-" * 40)

    # 创建一些测试样本
    test_samples = np.array([
        [100, 2, 1, 10, 2010, 1.0],  # 100平，2室1卫，10层，2010年建，距地铁1公里
        [150, 3, 2, 15, 2015, 0.5],  # 150平，3室2卫，15层，2015年建，距地铁0.5公里
        [80, 1, 1, 5, 2000, 3.0],    # 80平，1室1卫，5层，2000年建，距地铁3公里
        [200, 4, 2, 25, 2020, 0.2],  # 200平，4室2卫，25层，2020年建，距地铁0.2公里
    ])

    predictions = best_tree.predict(test_samples)

    for i, (sample, pred) in enumerate(zip(test_samples, predictions)):
        print(f"\n   样本 {i+1}:")
        print(f"     面积: {sample[0]:.0f} 平方米")
        print(f"     卧室: {sample[1]:.0f} 个")
        print(f"     卫生间: {sample[2]:.0f} 个")
        print(f"     楼层: {sample[3]:.0f} 层")
        print(f"     建筑年份: {sample[4]:.0f}")
        print(f"     距地铁: {sample[5]:.1f} 公里")
        print(f"     预测房价: {pred:.2f} 万元")

    # 6. 特征重要性分析
    print("\n7. 特征重要性分析:")
    print("-" * 40)
    if hasattr(best_tree, 'feature_importances_'):
        for fname, importance in zip(feature_names, best_tree.feature_importances_):
            print(f"   {fname}: {importance:.4f}")

    # 7. 打印决策树结构
    print("\n8. 回归树结构 (深度限制为3):")
    print("-" * 40)
    simple_tree = CARTRegressor(max_depth=3, min_samples_split=10)
    simple_tree.fit(X_train, y_train)
    simple_tree.print_tree(feature_names=feature_names)

    return results


if __name__ == "__main__":
    main()
