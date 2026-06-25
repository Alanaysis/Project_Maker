"""
疾病诊断示例

使用逻辑回归实现疾病诊断分类器。

场景描述：
- 输入：患者的各项检查指标
- 输出：是否患病（0: 健康, 1: 患病）

特征说明：
- age: 年龄
- blood_pressure: 血压
- cholesterol: 胆固醇
- blood_sugar: 血糖
- heart_rate: 心率
- bmi: 体重指数
- smoking: 吸烟史 (0: 否, 1: 是)
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
    auc_score,
    cross_validate
)


def generate_medical_data(n_samples: int = 800, random_state: int = 42) -> tuple:
    """
    生成模拟医疗数据

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
        标签 (0: 健康, 1: 患病)
    """
    np.random.seed(random_state)

    # 生成健康人群特征
    n_healthy = n_samples // 2
    n_diseased = n_samples - n_healthy

    # 健康人群
    healthy_features = np.random.randn(n_healthy, 7) * np.array([10, 10, 20, 10, 10, 3, 0.3]) + \
                       np.array([40, 120, 180, 90, 70, 22, 0.2])

    # 患病人群
    diseased_features = np.random.randn(n_diseased, 7) * np.array([10, 15, 25, 15, 12, 4, 0.3]) + \
                        np.array([55, 150, 240, 130, 85, 28, 0.6])

    # 合并数据
    X = np.vstack([healthy_features, diseased_features])
    y = np.array([0] * n_healthy + [1] * n_diseased)

    # 打乱数据
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y


def main():
    """主函数：运行疾病诊断示例"""
    print("=" * 60)
    print("疾病诊断示例")
    print("=" * 60)

    # 1. 生成数据
    print("\n1. 生成模拟医疗数据...")
    X, y = generate_medical_data(n_samples=800)
    print(f"   数据集大小: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"   健康人群: {np.sum(y == 0)} 人")
    print(f"   患病人群: {np.sum(y == 1)} 人")

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
        "age",
        "blood_pressure",
        "cholesterol",
        "blood_sugar",
        "heart_rate",
        "bmi",
        "smoking"
    ]
    weights = model.weights
    for name, weight in sorted(zip(feature_names, weights), key=lambda x: abs(x[1]), reverse=True):
        print(f"   {name}: {weight:.4f}")

    # 10. 诊断新患者
    print("\n10. 诊断新患者...")
    new_patients = np.array([
        [35, 115, 170, 85, 65, 21, 0],  # 年轻健康患者
        [60, 160, 250, 140, 90, 30, 1],  # 老年高危患者
    ])
    new_patients_scaled = scaler.transform(new_patients)
    predictions = model.predict(new_patients_scaled)
    probabilities = model.predict_proba(new_patients_scaled)

    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        diagnosis = "健康" if pred == 0 else "患病"
        print(f"   患者 {i+1}: {diagnosis} (患病概率: {prob:.4f})")

    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
