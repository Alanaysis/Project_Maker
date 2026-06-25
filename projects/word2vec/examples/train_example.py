"""
Word2Vec 训练示例

展示如何使用 Word2Vec 进行词向量训练和查询
支持 Skip-gram、CBOW、负采样、层次 Softmax
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word2vec import Word2Vec


def simple_skipgram_example():
    """Skip-gram + 负采样示例"""
    print("=" * 60)
    print("Skip-gram + 负采样示例")
    print("=" * 60)

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

    # 创建模型（默认 Skip-gram + 负采样）
    model = Word2Vec(
        vector_size=50,
        window=3,
        min_count=1,
        negative=3,
        learning_rate=0.025,
        model_type='skipgram'
    )

    # 训练
    print("\n训练中...")
    losses = model.train(corpus * 20, epochs=50, verbose=True)

    # 查询相似词
    print("\n" + "=" * 60)
    print("相似词查询")
    print("=" * 60)

    for word in ["king", "queen", "prince"]:
        similar = model.most_similar(word, topn=3)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")

    # 计算词相似度
    print("\n" + "=" * 60)
    print("词相似度计算")
    print("=" * 60)

    pairs = [("king", "queen"), ("king", "man"), ("queen", "woman")]
    for w1, w2 in pairs:
        sim = model.similarity(w1, w2)
        print(f"{w1} - {w2}: {sim:.4f}")

    # 词类比
    print("\n" + "=" * 60)
    print("词类比")
    print("=" * 60)

    result = model.analogy("king", "man", topn=3)
    print("king - man + woman = ?")
    for w, sim in result:
        print(f"  {w}: {sim:.4f}")


def cbow_example():
    """CBOW 模型示例"""
    print("\n" + "=" * 60)
    print("CBOW 模型示例")
    print("=" * 60)

    corpus = [
        ["the", "king", "loves", "the", "queen"],
        ["the", "queen", "loves", "the", "king"],
        ["the", "prince", "is", "the", "son", "of", "the", "king"],
        ["the", "princess", "is", "the", "daughter", "of", "the", "queen"],
        ["a", "king", "is", "a", "man"],
        ["a", "queen", "is", "a", "woman"],
    ]

    model = Word2Vec(
        vector_size=50,
        window=3,
        min_count=1,
        negative=3,
        model_type='cbow'  # 切换到 CBOW
    )

    print("\n训练 CBOW 模型...")
    model.train(corpus * 20, epochs=50, verbose=True)

    print("\n相似词查询:")
    for word in ["king", "queen"]:
        similar = model.most_similar(word, topn=3)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")


def hierarchical_softmax_example():
    """层次 Softmax 示例"""
    print("\n" + "=" * 60)
    print("层次 Softmax 示例")
    print("=" * 60)

    corpus = [
        ["the", "king", "loves", "the", "queen"],
        ["the", "queen", "loves", "the", "king"],
        ["the", "prince", "is", "the", "son", "of", "the", "king"],
        ["the", "princess", "is", "the", "daughter", "of", "the", "queen"],
        ["a", "king", "is", "a", "man"],
        ["a", "queen", "is", "a", "woman"],
    ]

    model = Word2Vec(
        vector_size=50,
        window=3,
        min_count=1,
        use_hs=True  # 使用层次 Softmax
    )

    print("\n训练 Skip-gram + 层次 Softmax 模型...")
    model.train(corpus * 20, epochs=50, verbose=True)

    print("\n相似词查询:")
    for word in ["king", "queen"]:
        similar = model.most_similar(word, topn=3)
        print(f"\n{word} 的相似词:")
        for w, sim in similar:
            print(f"  {w}: {sim:.4f}")


def subsampling_example():
    """降采样示例"""
    print("\n" + "=" * 60)
    print("降采样示例")
    print("=" * 60)

    # 包含大量高频词的语料
    corpus = []
    for _ in range(50):
        corpus.append(["the", "king", "rules", "the", "kingdom"])
        corpus.append(["the", "queen", "is", "the", "king", "wife"])
        corpus.append(["a", "king", "is", "a", "man"])
        corpus.append(["a", "queen", "is", "a", "woman"])

    model = Word2Vec(
        vector_size=50,
        window=3,
        min_count=1,
        negative=3,
        subsample_threshold=1e-3  # 降采样阈值
    )

    print("\n训练带降采样的模型...")
    model.train(corpus, epochs=50, verbose=True)

    print("\n相似词查询:")
    similar = model.most_similar("king", topn=3)
    print("king 的相似词:")
    for w, sim in similar:
        print(f"  {w}: {sim:.4f}")


def save_load_example():
    """模型保存/加载示例"""
    print("\n" + "=" * 60)
    print("模型保存/加载示例")
    print("=" * 60)

    corpus = [
        ["the", "king", "loves", "the", "queen"],
        ["the", "queen", "loves", "the", "king"],
    ]

    # 训练模型
    model = Word2Vec(vector_size=50, min_count=1)
    model.train(corpus * 10, epochs=10, verbose=False)

    # 保存
    save_path = "/tmp/word2vec_model"
    model.save(save_path)
    print(f"模型已保存到 {save_path}")

    # 加载
    loaded = Word2Vec.load(save_path)
    print(f"模型已加载，词汇表大小: {loaded.vocab_size}")

    # 验证
    vec1 = model.get_vector("king")
    vec2 = loaded.get_vector("king")
    print(f"向量一致性: {all(abs(a - b) < 1e-10 for a, b in zip(vec1, vec2))}")

    # 清理
    import glob
    for f in glob.glob(save_path + "*"):
        os.remove(f)


if __name__ == "__main__":
    simple_skipgram_example()
    cbow_example()
    hierarchical_softmax_example()
    subsampling_example()
    save_load_example()
