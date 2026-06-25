"""
文本情感分析示例

使用多项式朴素贝叶斯实现文本情感分析。
特征: 文本中词语的词频 (计数特征)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import MultinomialNaiveBayes
from src.evaluation import evaluate_model, print_confusion_matrix


def build_vocabulary() -> list[str]:
    """构建词汇表"""
    return [
        "good",       # 好
        "great",      # 很好
        "excellent",  # 优秀
        "amazing",    # 惊人
        "love",       # 爱
        "happy",      # 开心
        "bad",        # 坏
        "terrible",   # 糟糕
        "awful",      # 可怕
        "hate",       # 恨
        "sad",        # 伤心
        "angry",      # 生气
        "not",        # 不
        "very",       # 非常
    ]


def text_to_features(text: str, vocabulary: list[str]) -> list[int]:
    """
    将文本转换为词频特征向量

    Args:
        text: 文本内容
        vocabulary: 词汇表

    Returns:
        词频特征向量
    """
    text_lower = text.lower()
    words = text_lower.split()
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    return [word_counts.get(word, 0) for word in vocabulary]


def create_training_data() -> tuple[list[list[int]], list[int]]:
    """创建训练数据"""
    vocabulary = build_vocabulary()

    # 正面评论
    positive_reviews = [
        "good great excellent movie",
        "very good very amazing",
        "love this great good show",
        "excellent amazing very good",
        "great great love happy",
        "good excellent great very good",
        "amazing amazing love happy",
        "very good very great very excellent",
        "happy love good great amazing",
        "good good good great great",
        "excellent very good",
        "great amazing love happy good",
        "very amazing very great",
        "good happy love great",
        "excellent good amazing love",
    ]

    # 负面评论
    negative_reviews = [
        "bad terrible awful movie",
        "very bad very sad",
        "hate this bad terrible show",
        "terrible awful very bad",
        "bad bad hate angry",
        "bad terrible awful very bad",
        "awful angry hate sad",
        "very bad very terrible very awful",
        "sad hate bad terrible awful",
        "bad bad bad terrible terrible",
        "awful very bad",
        "terrible awful hate angry bad",
        "very awful very bad",
        "bad angry hate terrible",
        "awful bad terrible hate",
    ]

    X = []
    y = []

    for review in positive_reviews:
        X.append(text_to_features(review, vocabulary))
        y.append(0)  # 0: 正面

    for review in negative_reviews:
        X.append(text_to_features(review, vocabulary))
        y.append(1)  # 1: 负面

    return X, y


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("文本情感分析 - 多项式朴素贝叶斯")
    print("=" * 60)

    vocabulary = build_vocabulary()
    print(f"\n词汇表 ({len(vocabulary)} 个词):")
    print(", ".join(vocabulary))

    # 创建训练数据
    X_train, y_train = create_training_data()
    print(f"\n训练样本数: {len(X_train)}")
    print(f"  - 正面评论: {sum(1 for y in y_train if y == 0)}")
    print(f"  - 负面评论: {sum(1 for y in y_train if y == 1)}")

    # 训练模型
    clf = MultinomialNaiveBayes(alpha=1.0)
    clf.fit(X_train, y_train)
    print("\n模型训练完成!")

    # 测试评论
    test_reviews = [
        "good great amazing love",         # 正面
        "bad terrible hate angry",          # 负面
        "very good very great",             # 正面
        "awful sad bad terrible",           # 负面
        "excellent amazing happy love",     # 正面
        "not good very bad",                # 负面
        "great great great good",           # 正面
        "terrible awful hate sad angry",    # 负面
    ]

    print("\n" + "-" * 60)
    print("测试预测:")
    print("-" * 60)

    labels = {0: "正面", 1: "负面"}

    X_test = []
    y_test = []
    expected = [0, 1, 0, 1, 0, 1, 0, 1]

    for review in test_reviews:
        features = text_to_features(review, vocabulary)
        X_test.append(features)
        y_test.append(expected[test_reviews.index(review)])

    predictions = clf.predict(X_test)
    probabilities = clf.predict_proba(X_test)

    for review, pred, proba, exp in zip(
        test_reviews, predictions, probabilities, expected
    ):
        status = "正确" if pred == exp else "错误"
        print(f"\n评论: '{review}'")
        print(f"  预测: {labels[pred]} (实际: {labels[exp]}) [{status}]")
        print(f"  概率: 正面={proba[0]:.4f}, 负面={proba[1]:.4f}")

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
    print("\n各类别下特征的对数概率:")
    for cls in params["classes"]:
        label_name = labels[cls]
        print(f"\n{label_name}:")
        log_probs = params["feature_log_prob"][cls]
        for word, log_prob in zip(vocabulary, log_probs):
            print(f"  {word:>12}: {log_prob:.4f}")


if __name__ == "__main__":
    main()
