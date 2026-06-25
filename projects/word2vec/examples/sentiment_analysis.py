"""
情感分析示例

使用 Word2Vec 词向量进行情感分析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec
from src.applications import SentimentAnalyzer


def main():
    print("=" * 60)
    print("情感分析示例")
    print("=" * 60)

    # 1. 准备语料
    corpus = []

    # 正面语料
    positive_sentences = [
        ["this", "movie", "is", "excellent", "and", "wonderful"],
        ["the", "food", "was", "delicious", "and", "amazing"],
        ["i", "love", "this", "beautiful", "sunny", "day"],
        ["the", "performance", "was", "outstanding", "and", "brilliant"],
        ["this", "book", "is", "fantastic", "and", "inspiring"],
        ["the", "service", "was", "excellent", "and", "friendly"],
        ["i", "enjoy", "this", "great", "wonderful", "experience"],
        ["the", "team", "did", "an", "amazing", "job"],
    ] * 30

    # 负面语料
    negative_sentences = [
        ["this", "movie", "is", "terrible", "and", "boring"],
        ["the", "food", "was", "awful", "and", "disgusting"],
        ["i", "hate", "this", "horrible", "rainy", "day"],
        ["the", "performance", "was", "poor", "and", "disappointing"],
        ["this", "book", "is", "bad", "and", "uninteresting"],
        ["the", "service", "was", "terrible", "and", "rude"],
        ["i", "dislike", "this", "awful", "painful", "experience"],
        ["the", "team", "did", "a", "horrible", "job"],
    ] * 30

    corpus = positive_sentences + negative_sentences

    # 2. 训练 Word2Vec 模型
    print("\n训练 Word2Vec 模型...")
    w2v = Word2Vec(vector_size=50, window=5, min_count=1, negative=5)
    w2v.train(corpus, epochs=50, verbose=False)
    print(f"词汇表大小: {w2v.vocab_size}")

    # 3. 构建情感分析器
    print("\n构建情感分析器...")
    analyzer = SentimentAnalyzer(w2v.model.W_in, w2v.vocab.word2idx)

    # 情感词典
    positive_words = [
        "excellent", "wonderful", "amazing", "great", "fantastic",
        "outstanding", "brilliant", "love", "enjoy", "beautiful",
        "delicious", "inspiring", "friendly", "good", "nice"
    ]

    negative_words = [
        "terrible", "awful", "horrible", "bad", "disgusting",
        "boring", "poor", "disappointing", "hate", "dislike",
        "rude", "uninteresting", "painful", "ugly", "worst"
    ]

    analyzer.build_sentiment_lexicon(positive_words, negative_words)

    # 4. 测试情感分析
    print("\n测试情感分析...")

    test_cases = [
        (["this", "movie", "is", "excellent"], "正面"),
        (["this", "movie", "is", "terrible"], "负面"),
        (["the", "food", "was", "delicious"], "正面"),
        (["the", "food", "was", "awful"], "负面"),
        (["i", "love", "this", "beautiful", "day"], "正面"),
        (["i", "hate", "this", "horrible", "day"], "负面"),
        (["the", "service", "was", "excellent"], "正面"),
        (["the", "service", "was", "terrible"], "负面"),
    ]

    for words, expected in test_cases:
        result = analyzer.analyze(words)
        sentiment = "正面" if result['sentiment'] > 0.05 else (
            "负面" if result['sentiment'] < -0.05 else "中性"
        )
        status = "v" if sentiment == expected else "x"
        print(f"  [{status}] {' '.join(words)}")
        print(f"       情感得分: {result['sentiment']:.4f} -> {sentiment}")

    # 5. 评估
    print("\n评估情感分析器...")
    test_sentences = []
    test_labels = []

    for sent in positive_sentences[20:]:
        test_sentences.append(sent)
        test_labels.append(1)

    for sent in negative_sentences[20:]:
        test_sentences.append(sent)
        test_labels.append(-1)

    metrics = analyzer.evaluate(test_sentences, test_labels)
    print(f"  准确率: {metrics['accuracy']:.2%}")
    print(f"  正确数: {metrics['correct']}/{metrics['total']}")


if __name__ == "__main__":
    main()
