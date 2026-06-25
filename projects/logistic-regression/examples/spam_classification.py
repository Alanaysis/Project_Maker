"""
垃圾邮件分类示例

使用逻辑回归实现垃圾邮件分类器。

场景描述：
- 输入：邮件的特征（如关键词频率、邮件长度等）
- 输出：是否为垃圾邮件（0: 正常邮件, 1: 垃圾邮件）

特征说明：
- word_freq_free: "free"出现的频率
- word_freq_money: "money"出现的频率
- word_freq_win: "win"出现的频率
- word_freq_click: "click"出现的频率
- word_freq_offer: "offer"出现的频率
- capital_run_length_avg: 连续大写字母的平均长度
- capital_run_length_max: 连续大写字母的最大长度
"""

import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    LogisticRegression,
    StandardScaler,
    train_test_split,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    roc_curve,
    auc_score
)


def generate_spam_data(n_samples: int = 1000, random_state: int = 42) -> tuple:
    """
    生成模拟垃圾邮件数据

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
        标签 (0: 正常邮件, 1: 垃圾邮件)
    """
    np.random.seed(random_state)

    # 生成正常邮件特征
    n_normal = n_samples // 2
    n_spam = n_samples - n_normal

    # 正常邮件：关键词频率较低
    normal_features = np.random.randn(n_normal, 7) * 0.5 + np.array([0.1, 0.05, 0.02, 0.03, 0.02, 1.5, 5])

    # 垃圾邮件：关键词频率较高
    spam_features = np.random.randn(n_spam, 7) * 0.5 + np.array([0.8, 0.6, 0.5, 0.7, 0.6, 4.0, 15])

    # 合并数据
    X = np.vstack([normal_features, spam_features])
    y = np.array([0] * n_normal + [1] * n_spam)

    # 打乱数据
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y


def main():
    """主函数：运行垃圾邮件分类示例"""
    print("=" * 60)
    print("垃圾邮件分类示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n1. 生成模拟数据...")
    X, y = generate_spam_data(n_samples=1000)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   正常邮件: {np.sum(y == 0)} 封")
    print(f"   垃圾邮件: {np.sum(y == 1)} 封")

    # 2. 特征缩放
    print("\n2. 特征缩放...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("   已完成标准化")

    # 3. 划分训练集和测试集
    print("\n3. 划分数据集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 4. 训练模型
    print("\n4. 训练逻辑回归模型...")
    model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    model.fit(X_train, y_train)
    print("   训练完成")

    # 5. 预测
    print("\n5. 模型预测...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # 6. 评估
    print("\n6. 模型评估...")
    print(classification_report(y_test, y_pred))

    # 7. ROC曲线和AUC
    print("7. ROC曲线和AUC...")
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    auc = auc_score(fpr, tpr)
    print(f"   AUC: {auc:.4f}")

    # 8. 特征重要性
    print("\n8. 特征重要性...")
    feature_names = [
        "word_freq_free",
        "word_freq_money",
        "word_freq_win",
        "word_freq_click",
        "word_freq_offer",
        "capital_run_length_avg",
        "capital_run_length_max"
    ]
    weights = model.weights
    for name, weight in sorted(zip(feature_names, weights), key=lambda x: abs(x[1]), reverse=True):
        print(f"   {name}: {weight:.4f}")

    # 9. 预测新邮件
    print("\n9. 预测新邮件...")
    new_emails = np.array([
        [0.1, 0.05, 0.02, 0.03, 0.02, 1.5, 5],  # 正常邮件特征
        [0.9, 0.7, 0.6, 0.8, 0.7, 5.0, 20],      # 垃圾邮件特征
    ])
    new_emails_scaled = scaler.transform(new_emails)
    predictions = model.predict(new_emails_scaled)
    probabilities = model.predict_proba(new_emails_scaled)

    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        email_type = "正常邮件" if pred == 0 else "垃圾邮件"
        print(f"   邮件 {i+1}: {email_type} (概率: {prob:.4f})")

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
