"""
文本分类示例

使用 Word2Vec 词向量进行文本分类任务
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec
from src.applications import TextClassifier


def main():
    print("=" * 60)
    print("文本分类示例")
    print("=" * 60)

    # 1. 准备训练语料（包含多个主题）
    corpus = []

    # 体育类
    sports_sentences = [
        ["the", "player", "scored", "a", "goal", "in", "the", "match"],
        ["the", "team", "won", "the", "championship", "this", "year"],
        ["the", "football", "game", "was", "exciting", "and", "intense"],
        ["the", "basketball", "player", "dunked", "the", "ball"],
        ["the", "coach", "trained", "the", "team", "for", "the", "season"],
        ["the", "athlete", "broke", "the", "world", "record"],
        ["the", "soccer", "match", "ended", "in", "a", "draw"],
        ["the", "tennis", "player", "won", "the", "tournament"],
    ] * 20

    # 科技类
    tech_sentences = [
        ["the", "computer", "processor", "is", "very", "fast"],
        ["the", "software", "developer", "wrote", "the", "code"],
        ["the", "algorithm", "solves", "the", "problem", "efficiently"],
        ["the", "data", "is", "stored", "in", "the", "database"],
        ["the", "network", "connection", "is", "stable", "and", "fast"],
        ["the", "machine", "learning", "model", "achieved", "high", "accuracy"],
        ["the", "server", "handles", "millions", "of", "requests"],
        ["the", "program", "runs", "on", "the", "operating", "system"],
    ] * 20

    # 美食类
    food_sentences = [
        ["the", "chef", "cooked", "a", "delicious", "meal"],
        ["the", "recipe", "requires", "fresh", "ingredients"],
        ["the", "restaurant", "serves", "excellent", "food"],
        ["the", "cake", "was", "sweet", "and", "moist"],
        ["the", "pizza", "has", "cheese", "and", "tomato", "topping"],
        ["the", "soup", "is", "hot", "and", "flavorful"],
        ["the", "bread", "is", "fresh", "from", "the", "oven"],
        ["the", "salad", "is", "healthy", "and", "nutritious"],
    ] * 20

    corpus = sports_sentences + tech_sentences + food_sentences

    # 2. 训练 Word2Vec 模型
    print("\n训练 Word2Vec 模型...")
    w2v = Word2Vec(vector_size=50, window=5, min_count=1, negative=5)
    w2v.train(corpus, epochs=50, verbose=False)
    print(f"词汇表大小: {w2v.vocab_size}")

    # 3. 训练分类器
    print("\n训练文本分类器...")

    # 准备训练数据
    train_sentences = []
    train_labels = []

    for sent in sports_sentences[:15]:
        train_sentences.append(sent)
        train_labels.append(0)  # 体育

    for sent in tech_sentences[:15]:
        train_sentences.append(sent)
        train_labels.append(1)  # 科技

    for sent in food_sentences[:15]:
        train_sentences.append(sent)
        train_labels.append(2)  # 美食

    classifier = TextClassifier(w2v.model.W_in, w2v.vocab.word2idx)
    classifier.train(train_sentences, train_labels)

    # 4. 测试分类器
    print("\n测试分类器...")

    test_cases = [
        (["the", "player", "scored", "a", "goal"], "体育"),
        (["the", "computer", "is", "very", "fast"], "科技"),
        (["the", "food", "is", "delicious"], "美食"),
        (["the", "team", "won", "the", "game"], "体育"),
        (["the", "software", "is", "efficient"], "科技"),
        (["the", "recipe", "is", "simple"], "美食"),
    ]

    label_names = {0: "体育", 1: "科技", 2: "美食"}

    for words, expected in test_cases:
        pred = classifier.predict(words)
        pred_name = label_names.get(pred, "未知")
        status = "v" if pred_name == expected else "x"
        print(f"  [{status}] {' '.join(words)} -> {pred_name} (期望: {expected})")

    # 5. 评估
    print("\n评估分类器...")
    test_sentences = []
    test_labels = []

    for sent in sports_sentences[15:]:
        test_sentences.append(sent)
        test_labels.append(0)

    for sent in tech_sentences[15:]:
        test_sentences.append(sent)
        test_labels.append(1)

    for sent in food_sentences[15:]:
        test_sentences.append(sent)
        test_labels.append(2)

    metrics = classifier.evaluate(test_sentences, test_labels)
    print(f"  准确率: {metrics['accuracy']:.2%}")
    print(f"  正确数: {metrics['correct']}/{metrics['total']}")

    for label, acc in metrics['class_accuracy'].items():
        print(f"  类别 {label_names.get(label, label)} 准确率: {acc:.2%}")


if __name__ == "__main__":
    main()
