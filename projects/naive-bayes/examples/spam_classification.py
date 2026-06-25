"""
垃圾邮件分类示例

使用伯努利朴素贝叶斯实现垃圾邮件检测。
特征: 邮件中是否包含特定关键词 (二值特征)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import BernoulliNaiveBayes
from src.evaluation import evaluate_model, print_confusion_matrix


def build_vocabulary() -> list[str]:
    """构建词汇表"""
    return [
        "free",       # 免费
        "win",        # 赢取
        "winner",     # 获奖者
        "click",      # 点击
        "subscribe",  # 订阅
        "offer",      # 优惠
        "discount",   # 折扣
        "urgent",     # 紧急
        "meeting",    # 会议
        "report",     # 报告
        "project",    # 项目
        "schedule",   # 日程
        "team",       # 团队
        "deadline",   # 截止日期
    ]


def text_to_features(text: str, vocabulary: list[str]) -> list[int]:
    """
    将文本转换为二值特征向量

    Args:
        text: 邮件文本
        vocabulary: 词汇表

    Returns:
        二值特征向量，1表示词汇表中的词出现，0表示未出现
    """
    text_lower = text.lower()
    words = set(text_lower.split())
    return [1 if word in words else 0 for word in vocabulary]


def create_training_data() -> tuple[list[list[int]], list[int]]:
    """创建训练数据"""
    vocabulary = build_vocabulary()

    # 垃圾邮件样本
    spam_emails = [
        "free win winner click here now",
        "you are a winner click subscribe",
        "free offer discount click now",
        "win free discount offer urgent",
        "click here for free win",
        "urgent winner free offer",
        "free discount subscribe click",
        "winner winner free offer click",
        "click now free win offer",
        "urgent free discount winner",
    ]

    # 正常邮件样本
    ham_emails = [
        "meeting schedule project report",
        "team meeting tomorrow schedule",
        "project deadline report team",
        "schedule meeting team project",
        "report project deadline meeting",
        "team project schedule deadline",
        "meeting report project team",
        "deadline schedule team meeting",
        "project team meeting schedule",
        "report deadline project team",
    ]

    X = []
    y = []

    for email in spam_emails:
        X.append(text_to_features(email, vocabulary))
        y.append(1)  # 1: 垃圾邮件

    for email in ham_emails:
        X.append(text_to_features(email, vocabulary))
        y.append(0)  # 0: 正常邮件

    return X, y


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("垃圾邮件分类 - 伯努利朴素贝叶斯")
    print("=" * 60)

    vocabulary = build_vocabulary()
    print(f"\n词汇表 ({len(vocabulary)} 个词):")
    print(", ".join(vocabulary))

    # 创建训练数据
    X_train, y_train = create_training_data()
    print(f"\n训练样本数: {len(X_train)}")
    print(f"  - 垃圾邮件: {sum(1 for y in y_train if y == 1)}")
    print(f"  - 正常邮件: {sum(1 for y in y_train if y == 0)}")

    # 训练模型
    clf = BernoulliNaiveBayes(alpha=1.0)
    clf.fit(X_train, y_train)
    print("\n模型训练完成!")

    # 测试邮件
    test_emails = [
        "free win click here now",           # 垃圾邮件
        "meeting schedule project team",      # 正常邮件
        "urgent free discount offer",         # 垃圾邮件
        "report deadline project schedule",   # 正常邮件
        "winner free click subscribe",        # 垃圾邮件
    ]

    print("\n" + "-" * 60)
    print("测试预测:")
    print("-" * 60)

    labels = {0: "正常邮件", 1: "垃圾邮件"}

    X_test = []
    y_test = []
    expected = [1, 0, 1, 0, 1]

    for email, exp in zip(test_emails, expected):
        features = text_to_features(email, vocabulary)
        X_test.append(features)
        y_test.append(exp)

    predictions = clf.predict(X_test)
    probabilities = clf.predict_proba(X_test)

    for email, pred, proba, exp in zip(
        test_emails, predictions, probabilities, expected
    ):
        status = "正确" if pred == exp else "错误"
        print(f"\n邮件: '{email}'")
        print(f"  预测: {labels[pred]} (实际: {labels[exp]}) [{status}]")
        print(f"  概率: 正常={proba[0]:.4f}, 垃圾={proba[1]:.4f}")

    # 评估
    print("\n" + "=" * 60)
    print("模型评估")
    print("=" * 60)

    results = evaluate_model(y_test, predictions, labels=[0, 1])

    print(f"\n准确率: {results['accuracy']:.4f}")
    print(f"精确率 (宏平均): {results['precision_macro']:.4f}")
    print(f"召回率 (宏平均): {results['recall_macro']:.4f}")
    print(f"F1分数 (宏平均): {results['f1_macro']:.4f}")

    print("\n混淆矩阵:")
    print(print_confusion_matrix(y_test, predictions, labels=[0, 1]))

    print("\n分类报告:")
    print(results["report"])

    # 展示模型学到的特征重要性
    print("\n" + "=" * 60)
    print("特征分析")
    print("=" * 60)

    params = clf.get_params()
    print("\n各类别下特征为1的对数概率:")
    for cls in params["classes"]:
        label_name = labels[cls]
        print(f"\n{label_name}:")
        log_probs = params["feature_log_prob"][cls]
        for word, (log_p0, log_p1) in zip(vocabulary, log_probs):
            print(f"  {word:>12}: P(出现)={log_p1:.4f}")


if __name__ == "__main__":
    main()
