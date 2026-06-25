"""
信用评分示例

使用逻辑回归实现信用评分模型。

场景描述：
- 输入：申请人的各项信息
- 输出：是否批准贷款（0: 拒绝, 1: 批准）

特征说明：
- income: 年收入（万元）
- debt_ratio: 负债收入比
- credit_history_length: 信用历史长度（年）
- num_credit_lines: 信用账户数量
- late_payments: 近期逾期次数
- employment_years: 工作年限
- home_ownership: 是否有房产 (0: 否, 1: 是)
"""

import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    LogisticRegression,
    LogisticRegressionL1,
    LogisticRegressionL2,
    ElasticNet,
    StandardScaler,
    train_test_split,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    roc_curve,
    auc_score,
    cross_validate
)


def generate_credit_data(n_samples: int = 1000, random_state: int = 42) -> tuple:
    """
    生成模拟信用数据

    Parameters
    ----------
    n_samples : int
        样本数量
    random_state : int
        随机种子

    Returns
    -------
    X : ndarray of shape (n_samples, 7)
        特征矩阵
    y : ndarray of shape (n_samples,)
        标签 (0: 拒绝, 1: 批准)
    """
    np.random.seed(random_state)

    # 生成批准贷款的申请人特征
    n_approved = n_samples // 2
    n_rejected = n_samples - n_approved

    # 批准的申请人
    approved_features = np.random.randn(n_approved, 7) * \
                        np.array([10, 0.1, 3, 2, 0.5, 3, 0.3]) + \
                        np.array([20, 0.3, 8, 5, 0.5, 5, 0.7])

    # 拒绝的申请人
    rejected_features = np.random.randn(n_rejected, 7) * \
                        np.array([5, 0.2, 2, 2, 1, 2, 0.3]) + \
                        np.array([8, 0.7, 3, 2, 2, 2, 0.3])

    # 合并数据
    X = np.vstack([approved_features, rejected_features])
    y = np.array([1] * n_approved + [0] * n_rejected)

    # 打乱数据
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y


def compare_regularization(X_train, X_test, y_train, y_test):
    """
    比较不同正则化方法的效果

    Parameters
    ----------
    X_train, X_test : ndarray
        训练集和测试集特征
    y_train, y_test : ndarray
        训练集和测试集标签
    """
    print("\n" + "=" * 60)
    print("正则化方法比较")
    print("=" * 60)

    # 无正则化
    model_lr = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    model_lr.fit(X_train, y_train)
    y_pred_lr = model_lr.predict(X_test)
    acc_lr = accuracy_score(y_test, y_pred_lr)
    f1_lr = f1_score(y_test, y_pred_lr)

    # L1正则化
    model_l1 = LogisticRegressionL1(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
    model_l1.fit(X_train, y_train)
    y_pred_l1 = model_l1.predict(X_test)
    acc_l1 = accuracy_score(y_test, y_pred_l1)
    f1_l1 = f1_score(y_test, y_pred_l1)

    # L2正则化
    model_l2 = LogisticRegressionL2(learning_rate=0.1, n_iterations=1000, lambda_param=0.1)
    model_l2.fit(X_train, y_train)
    y_pred_l2 = model_l2.predict(X_test)
    acc_l2 = accuracy_score(y_test, y_pred_l2)
    f1_l2 = f1_score(y_test, y_pred_l2)

    # Elastic Net
    model_en = ElasticNet(learning_rate=0.1, n_iterations=1000, l1_ratio=0.5, lambda_param=0.1)
    model_en.fit(X_train, y_train)
    y_pred_en = model_en.predict(X_test)
    acc_en = accuracy_score(y_test, y_pred_en)
    f1_en = f1_score(y_test, y_pred_en)

    print(f"\n{'方法':<20} {'准确率':<10} {'F1分数':<10}")
    print("-" * 40)
    print(f"{'无正则化':<20} {acc_lr:<10.4f} {f1_lr:<10.4f}")
    print(f"{'L1正则化':<20} {acc_l1:<10.4f} {f1_l1:<10.4f}")
    print(f"{'L2正则化':<20} {acc_l2:<10.4f} {f1_l2:<10.4f}")
    print(f"{'Elastic Net':<20} {acc_en:<10.4f} {f1_en:<10.4f}")

    # 显示L1正则化的稀疏性
    print(f"\nL1正则化后权重为0的特征数量: {np.sum(np.abs(model_l1.weights) < 1e-6)}")


def main():
    """主函数：运行信用评分示例"""
    print("=" * 60)
    print("信用评分示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n1. 生成模拟信用数据...")
    X, y = generate_credit_data(n_samples=1000)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   批准贷款: {np.sum(y == 1)} 人")
    print(f"   拒绝贷款: {np.sum(y == 0)} 人")

    # 2. 特征缩放
    print("\n2. 特征缩放...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("   已完成标准化")

    # 3. 交叉验证
    print("\n3. 交叉验证评估...")
    model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    cv_scores = cross_validate(model, X_scaled, y, cv=5, scoring='accuracy')
    print(f"   5折交叉验证分数: {cv_scores}")
    print(f"   平均准确率: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    # 4. 划分训练集和测试集
    print("\n4. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 5. 训练模型
    print("\n5. 训练逻辑回归模型...")
    model.fit(X_train, y_train)
    print("   训练完成")

    # 6. 预测
    print("\n6. 模型预测...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # 7. 评估
    print("\n7. 模型评估...")
    print(classification_report(y_test, y_pred))

    # 8. ROC曲线和AUC
    print("8. ROC曲线和AUC...")
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    auc = auc_score(fpr, tpr)
    print(f"   AUC: {auc:.4f}")

    # 9. 特征重要性
    print("\n9. 特征重要性...")
    feature_names = [
        "income",
        "debt_ratio",
        "credit_history_length",
        "num_credit_lines",
        "late_payments",
        "employment_years",
        "home_ownership"
    ]
    weights = model.weights
    for name, weight in sorted(zip(feature_names, weights), key=lambda x: abs(x[1]), reverse=True):
        print(f"   {name}: {weight:.4f}")

    # 10. 比较正则化方法
    compare_regularization(X_train, X_test, y_train, y_test)

    # 11. 评估新申请人
    print("\n" + "=" * 60)
    print("评估新申请人")
    print("=" * 60)
    new_applicants = np.array([
        [25, 0.2, 10, 6, 0, 8, 1],  # 优质申请人
        [10, 0.8, 2, 1, 3, 1, 0],   # 高风险申请人
    ])
    new_applicants_scaled = scaler.transform(new_applicants)
    predictions = model.predict(new_applicants_scaled)
    probabilities = model.predict_proba(new_applicants_scaled)

    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        decision = "批准" if pred == 1 else "拒绝"
        print(f"\n申请人 {i+1}:")
        print(f"   收入: {new_applicants[i, 0]}万元")
        print(f"   负债比: {new_applicants[i, 1]}")
        print(f"   信用历史: {new_applicants[i, 2]}年")
        print(f"   决策: {decision} (批准概率: {prob:.4f})")

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
