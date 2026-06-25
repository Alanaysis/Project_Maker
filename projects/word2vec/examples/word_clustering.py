"""
词聚类示例

使用 Word2Vec 词向量进行语义聚类
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec
from src.applications import WordClusterer


def main():
    print("=" * 60)
    print("词聚类示例")
    print("=" * 60)

    # 1. 准备语料（包含多个语义类别）
    corpus = []

    # 动物类
    animal_sentences = [
        ["the", "cat", "is", "a", "small", "animal"],
        ["the", "dog", "is", "a", "loyal", "pet"],
        ["the", "bird", "can", "fly", "in", "the", "sky"],
        ["the", "fish", "swims", "in", "the", "water"],
        ["the", "horse", "runs", "very", "fast"],
        ["the", "elephant", "is", "a", "large", "animal"],
        ["the", "cat", "and", "dog", "are", "pets"],
        ["the", "bird", "sings", "beautifully"],
    ] * 30

    # 颜色类
    color_sentences = [
        ["the", "sky", "is", "blue", "and", "beautiful"],
        ["the", "grass", "is", "green", "and", "fresh"],
        ["the", "sun", "is", "yellow", "and", "bright"],
        ["the", "blood", "is", "red", "and", "vital"],
        ["the", "snow", "is", "white", "and", "pure"],
        ["the", "night", "is", "black", "and", "dark"],
        ["the", "orange", "is", "orange", "and", "sweet"],
        ["the", "purple", "flower", "blooms", "in", "spring"],
    ] * 30

    # 水果类
    fruit_sentences = [
        ["the", "apple", "is", "red", "and", "sweet"],
        ["the", "banana", "is", "yellow", "and", "long"],
        ["the", "orange", "is", "juicy", "and", "refreshing"],
        ["the", "grape", "is", "small", "and", "purple"],
        ["the", "strawberry", "is", "red", "and", "delicious"],
        ["the", "watermelon", "is", "large", "and", "green"],
        ["the", "apple", "and", "banana", "are", "fruits"],
        ["the", "mango", "is", "sweet", "and", "tropical"],
    ] * 30

    # 国家类
    country_sentences = [
        ["china", "is", "a", "large", "country"],
        ["japan", "is", "an", "island", "nation"],
        ["korea", "is", "in", "east", "asia"],
        ["india", "is", "a", "populous", "country"],
        ["thailand", "is", "a", "tropical", "nation"],
        ["vietnam", "is", "in", "southeast", "asia"],
        ["china", "and", "japan", "are", "neighbors"],
        ["korea", "and", "india", "are", "asian", "countries"],
    ] * 30

    corpus = animal_sentences + color_sentences + fruit_sentences + country_sentences

    # 2. 训练 Word2Vec 模型
    print("\n训练 Word2Vec 模型...")
    w2v = Word2Vec(vector_size=50, window=5, min_count=1, negative=5)
    w2v.train(corpus, epochs=50, verbose=False)
    print(f"词汇表大小: {w2v.vocab_size}")

    # 3. 词聚类
    print("\n词聚类...")

    # 要聚类的词
    words = [
        "cat", "dog", "bird", "fish", "horse", "elephant",
        "blue", "green", "yellow", "red", "white", "black",
        "apple", "banana", "orange", "grape", "strawberry", "watermelon",
        "china", "japan", "korea", "india", "thailand", "vietnam"
    ]

    clusterer = WordClusterer(w2v.model.W_in, w2v.vocab.word2idx, w2v.vocab.idx2word)

    # 聚类为 4 类
    clusters = clusterer.cluster(words, k=4)

    print("\n聚类结果 (k=4):")
    print("-" * 40)
    print(clusterer.get_cluster_summary(clusters))

    # 4. 查看每个词的最近邻
    print("\n词相似度查询:")
    print("-" * 40)

    query_words = ["cat", "blue", "apple", "china"]
    for word in query_words:
        similar = w2v.most_similar(word, topn=5)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")


if __name__ == "__main__":
    main()
