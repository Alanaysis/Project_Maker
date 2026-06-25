"""
新闻分类示例

使用多项式朴素贝叶斯实现新闻文章分类。
特征: 文章中词语的词频 (计数特征)
类别: 科技、体育、财经
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import MultinomialNaiveBayes
from src.evaluation import evaluate_model, print_confusion_matrix


def build_vocabulary() -> list[str]:
    """构建词汇表"""
    return [
        # 科技相关
        "technology", "software", "computer", "internet", "digital",
        "app", "data", "online", "system", "program",
        # 体育相关
        "game", "team", "player", "score", "match",
        "champion", "goal", "season", "coach", "league",
        # 财经相关
        "market", "stock", "company", "profit", "invest",
        "trade", "economy", "bank", "fund", "growth",
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

    # 科技类新闻
    tech_news = [
        "technology software computer internet digital",
        "new app data online system program",
        "computer technology digital internet software",
        "data system program online technology",
        "digital internet computer software app",
        "technology system program data online",
        "software computer internet digital technology",
        "app online data system program technology",
        "internet digital computer software technology",
        "program data system online app technology",
        "digital technology software computer internet",
        "online data system program app technology",
    ]

    # 体育类新闻
    sports_news = [
        "game team player score match",
        "champion goal season coach league",
        "team player game match score",
        "score match game team player",
        "champion league season goal coach",
        "player team game score match",
        "match score game team player",
        "coach season champion league goal",
        "team game player match score",
        "league champion goal season coach",
        "game score team player match",
        "season goal champion league coach",
    ]

    # 财经类新闻
    finance_news = [
        "market stock company profit invest",
        "trade economy bank fund growth",
        "stock market company invest profit",
        "profit invest market stock company",
        "economy bank fund growth trade",
        "company market stock profit invest",
        "invest profit company market stock",
        "bank economy trade fund growth",
        "market stock company profit invest",
        "fund growth trade economy bank",
        "stock market invest company profit",
        "trade growth economy bank fund",
    ]

    X = []
    y = []

    for news in tech_news:
        X.append(text_to_features(news, vocabulary))
        y.append(0)  # 0: 科技

    for news in sports_news:
        X.append(text_to_features(news, vocabulary))
        y.append(1)  # 1: 体育

    for news in finance_news:
        X.append(text_to_features(news, vocabulary))
        y.append(2)  # 2: 财经

    return X, y


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("新闻分类 - 多项式朴素贝叶斯")
    print("=" * 60)

    vocabulary = build_vocabulary()
    print(f"\n词汇表 ({len(vocabulary)} 个词):")
    print("  科技:", ", ".join(vocabulary[0:10]))
    print("  体育:", ", ".join(vocabulary[10:20]))
    print("  财经:", ", ".join(vocabulary[20:30]))

    # 创建训练数据
    X_train, y_train = create_training_data()
    print(f"\n训练样本数: {len(X_train)}")
    print(f"  - 科技类: {sum(1 for y in y_train if y == 0)}")
    print(f"  - 体育类: {sum(1 for y in y_train if y == 1)}")
    print(f"  - 财经类: {sum(1 for y in y_train if y == 2)}")

    # 训练模型
    clf = MultinomialNaiveBayes(alpha=1.0)
    clf.fit(X_train, y_train)
    print("\n模型训练完成!")

    # 测试新闻
    test_news = [
        "new technology software app digital computer",     # 科技
        "team player game score match champion",            # 体育
        "market stock company profit invest growth",        # 财经
        "computer internet technology system data",         # 科技
        "goal season league coach player team",             # 体育
        "economy bank trade fund stock market",             # 财经
        "digital online app program system technology",     # 科技
        "match score game team player goal",                # 体育
        "invest profit company growth economy bank",        # 财经
    ]

    print("\n" + "-" * 60)
    print("测试预测:")
    print("-" * 60)

    labels = {0: "科技", 1: "体育", 2: "财经"}

    X_test = []
    y_test = []
    expected = [0, 1, 2, 0, 1, 2, 0, 1, 2]

    for news in test_news:
        features = text_to_features(news, vocabulary)
        X_test.append(features)
        y_test.append(expected[test_news.index(news)])

    predictions = clf.predict(X_test)
    probabilities = clf.predict_proba(X_test)

    for news, pred, proba, exp in zip(
        test_news, predictions, probabilities, expected
    ):
        status = "正确" if pred == exp else "错误"
        print(f"\n新闻: '{news}'")
        print(f"  预测: {labels[pred]} (实际: {labels[exp]}) [{status}]")
        print(
            f"  概率: 科技={proba[0]:.4f}, 体育={proba[1]:.4f}, 财经={proba[2]:.4f}"
        )

    # 评估
    print("\n" + "=" * 60)
    print("模型评估")
    print("=" * 60)

    results = evaluate_model(y_test, predictions, labels=[0, 1, 2])

    print(f"\n准确率: {results['accuracy']:.4f}")
    print(f"精确率 (宏平均): {results['precision_macro']:.4f}")
    print(f"召回率 (宏平均): {results['recall_macro']:.4f}")
    print(f"F1分数 (宏平均): {results['f1_macro']:.4f}")

    print("\n混淆矩阵:")
    print(print_confusion_matrix(y_test, predictions, labels=[0, 1, 2]))

    print("\n分类报告:")
    print(results["report"])

    # 展示模型学到的特征重要性
    print("\n" + "=" * 60)
    print("特征分析 - 各类别最重要的5个特征")
    print("=" * 60)

    params = clf.get_params()
    for cls in params["classes"]:
        label_name = labels[cls]
        log_probs = params["feature_log_prob"][cls]

        # 按对数概率排序
        word_probs = list(zip(vocabulary, log_probs))
        word_probs.sort(key=lambda x: x[1], reverse=True)

        print(f"\n{label_name}类:")
        for word, log_prob in word_probs[:5]:
            print(f"  {word:>15}: {log_prob:.4f}")


if __name__ == "__main__":
    main()
