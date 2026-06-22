"""
Word2Vec 训练示例

展示如何使用 Word2Vec 进行词向量训练和查询
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec


def simple_example():
    """简单示例"""
    print("=" * 50)
    print("简单示例：训练小语料")
    print("=" * 50)

    # 准备语料
    corpus = [
        ["the", "king", "loves", "the", "queen"],
        ["the", "queen", "loves", "the", "king"],
        ["the", "prince", "is", "the", "son", "of", "the", "king"],
        ["the", "princess", "is", "the", "daughter", "of", "the", "queen"],
        ["a", "king", "is", "a", "man"],
        ["a", "queen", "is", "a", "woman"],
        ["a", "prince", "is", "a", "boy"],
        ["a", "princess", "is", "a", "girl"]
    ]

    # 创建模型
    model = Word2Vec(
        vector_size=50,    # 向量维度
        window=3,          # 上下文窗口
        min_count=1,       # 最小词频
        negative=3,        # 负样本数量
        learning_rate=0.025 # 学习率
    )

    # 训练（重复语料以增加训练量）
    print("\n训练中...")
    losses = model.train(corpus * 20, epochs=50, verbose=True)

    # 查询相似词
    print("\n" + "=" * 50)
    print("相似词查询")
    print("=" * 50)

    for word in ["king", "queen", "prince"]:
        similar = model.most_similar(word, topn=3)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")

    # 计算词相似度
    print("\n" + "=" * 50)
    print("词相似度计算")
    print("=" * 50)

    pairs = [("king", "queen"), ("king", "man"), ("queen", "woman")]
    for w1, w2 in pairs:
        sim = model.similarity(w1, w2)
        print(f"{w1} - {w2}: {sim:.4f}")


def larger_example():
    """更大语料示例"""
    print("\n" + "=" * 50)
    print("更大语料示例")
    print("=" * 50)

    # 生成更多样化的语料
    corpus = []

    # 皇室相关
    royal_sentences = [
        ["the", "king", "rules", "the", "kingdom"],
        ["the", "queen", "is", "the", "king", "wife"],
        ["the", "prince", "will", "be", "the", "next", "king"],
        ["the", "princess", "is", "the", "queen", "daughter"],
        ["the", "royal", "family", "lives", "in", "the", "castle"],
        ["the", "king", "and", "queen", "are", "rulers"],
        ["the", "prince", "and", "princess", "are", "royal"],
    ] * 30

    # 家庭相关
    family_sentences = [
        ["the", "man", "is", "a", "father"],
        ["the", "woman", "is", "a", "mother"],
        ["the", "boy", "is", "a", "son"],
        ["the", "girl", "is", "a", "daughter"],
        ["the", "father", "and", "mother", "are", "parents"],
        ["the", "son", "and", "daughter", "are", "children"],
        ["the", "man", "and", "woman", "are", "people"],
    ] * 30

    corpus = royal_sentences + family_sentences

    # 创建模型
    model = Word2Vec(
        vector_size=100,
        window=5,
        min_count=2,
        negative=5,
        learning_rate=0.025
    )

    # 训练
    print("\n训练中...")
    losses = model.train(corpus, epochs=100, verbose=True)

    # 查询
    print("\n" + "=" * 50)
    print("相似词查询")
    print("=" * 50)

    for word in ["king", "queen", "man", "woman"]:
        similar = model.most_similar(word, topn=3)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")

    # 词类比
    print("\n" + "=" * 50)
    print("词类比")
    print("=" * 50)

    analogies = [
        ("king", "man", "woman"),    # king - man + woman = ?
        ("queen", "woman", "man"),   # queen - woman + man = ?
    ]

    for pos, neg, neg2 in analogies:
        result = model.analogy(pos, neg, topn=3)
        print(f"\n{pos} - {neg} + {neg2} = ?")
        for w, sim in result[:3]:
            print(f"  {w}: {sim:.4f}")


if __name__ == "__main__":
    simple_example()
    larger_example()
