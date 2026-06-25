"""
文本分类示例
===========

使用 SVM 对文本进行情感分类 (正面/负面)。
本示例使用简化的 TF-IDF 特征提取方法。

本示例演示:
1. 文本数据的预处理和特征提取
2. TF-IDF 向量化 (从零实现)
3. SVM 文本分类
4. 模型评估
"""

import sys
import os
import re
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.svm import SVM
from src.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def preprocess_text(text):
    """
    文本预处理

    步骤:
    1. 转换为小写
    2. 移除标点符号
    3. 分词

    参数:
        text: 原始文本

    返回:
        预处理后的词语列表
    """
    text = text.lower()
    text = re.sub(r'[^a-z一-鿿\s]', '', text)
    tokens = text.split()
    return tokens


class TFIDFVectorizer:
    """
    TF-IDF 向量化器 (从零实现)

    TF (词频): 词在文档中出现的频率
    IDF (逆文档频率): log(总文档数 / 包含该词的文档数)
    TF-IDF = TF * IDF

    属性:
        vocabulary: 词汇表 (词 -> 索引)
        idf: IDF 值
    """

    def __init__(self, max_features=100):
        """
        初始化 TF-IDF 向量化器

        参数:
            max_features: 最大特征数 (选择 TF-IDF 值最高的词)
        """
        self.max_features = max_features
        self.vocabulary = {}
        self.idf = None

    def fit(self, documents):
        """
        学习词汇表和 IDF 值

        参数:
            documents: 文档列表，每个文档是词语列表

        返回:
            self
        """
        n_docs = len(documents)

        # 统计每个词在多少个文档中出现
        doc_freq = {}
        for doc in documents:
            unique_words = set(doc)
            for word in unique_words:
                doc_freq[word] = doc_freq.get(word, 0) + 1

        # 按文档频率排序，选择最常见的词
        sorted_words = sorted(doc_freq.items(), key=lambda x: -x[1])
        selected_words = sorted_words[:self.max_features]

        # 构建词汇表
        self.vocabulary = {word: idx for idx, (word, _) in enumerate(selected_words)}

        # 计算 IDF
        self.idf = np.zeros(len(self.vocabulary))
        for word, idx in self.vocabulary.items():
            df = doc_freq[word]
            self.idf[idx] = np.log(n_docs / (1 + df)) + 1  # 平滑

        return self

    def transform(self, documents):
        """
        将文档转换为 TF-IDF 向量

        参数:
            documents: 文档列表

        返回:
            X: TF-IDF 矩阵 (n_docs, n_features)
        """
        n_docs = len(documents)
        n_features = len(self.vocabulary)
        X = np.zeros((n_docs, n_features))

        for i, doc in enumerate(documents):
            # 计算词频
            word_count = {}
            for word in doc:
                if word in self.vocabulary:
                    word_count[word] = word_count.get(word, 0) + 1

            # 计算 TF-IDF
            total_words = len(doc) if len(doc) > 0 else 1
            for word, count in word_count.items():
                idx = self.vocabulary[word]
                tf = count / total_words
                X[i, idx] = tf * self.idf[idx]

            # L2 归一化
            norm = np.sqrt(np.sum(X[i] ** 2))
            if norm > 0:
                X[i] /= norm

        return X

    def fit_transform(self, documents):
        """学习并转换"""
        return self.fit(documents).transform(documents)


def load_sentiment_data():
    """
    加载情感分析数据集

    包含正面和负面的文本样本。
    """
    positive_texts = [
        "this movie is great and wonderful",
        "I really enjoyed this film it was amazing",
        "excellent performance and brilliant acting",
        "the story is beautiful and touching",
        "fantastic movie with great characters",
        "I love this movie it is my favorite",
        "wonderful experience highly recommended",
        "the plot is engaging and well written",
        "amhtaking visuals and stunning effects",
        "a masterpiece of modern cinema",
        "the actors delivered outstanding performances",
        "this is one of the best movies I have seen",
        "incredible storytelling and beautiful scenes",
        "I was deeply moved by this film",
        "perfect blend of drama and action",
        "the director did an amazing job",
        "this film exceeded all my expectations",
        "a truly remarkable and inspiring movie",
        "the music score was absolutely beautiful",
        "I would watch this movie again and again",
        "great movie with an excellent storyline",
        "the cinematography was breathtaking",
        "a heartwarming and delightful film",
        "the ending was perfect and satisfying",
        "I enjoyed every minute of this movie",
        "outstanding direction and superb acting",
        "this movie made me laugh and cry",
        "a wonderful journey from start to finish",
        "the dialogue was sharp and witty",
        "a feel good movie that lifts your spirits",
    ]

    negative_texts = [
        "this movie is terrible and boring",
        "I hated this film it was a waste of time",
        "awful acting and poor direction",
        "the story makes no sense at all",
        "worst movie I have ever watched",
        "I could not finish watching this disaster",
        "disappointing and poorly executed",
        "the plot is confusing and pointless",
        "bad special effects and cheap production",
        "a complete waste of money and time",
        "the characters were flat and uninteresting",
        "this is one of the worst movies ever made",
        "terrible script and bad dialogue",
        "I was extremely disappointed with this film",
        "boring and predictable from start to finish",
        "the director failed completely",
        "this film fell short of all expectations",
        "a truly awful and forgettable movie",
        "the soundtrack was annoying and loud",
        "I will never watch this movie again",
        "bad movie with a terrible storyline",
        "the editing was choppy and confusing",
        "a dull and lifeless film",
        "the ending was abrupt and unsatisfying",
        "I wasted two hours on this movie",
        "poor direction and wooden acting",
        "this movie put me to sleep",
        "a painful experience from start to finish",
        "the dialogue was cringe worthy",
        "a depressing and joyless movie",
    ]

    texts = positive_texts + negative_texts
    labels = np.array([1] * len(positive_texts) + [-1] * len(negative_texts))

    return texts, labels


def train_test_split(X, y, test_ratio=0.3, seed=42):
    """划分训练集和测试集"""
    np.random.seed(seed)
    n = len(y)
    indices = np.random.permutation(n)
    test_size = int(n * test_ratio)

    test_idx = indices[:test_size]
    train_idx = indices[test_size:]

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def main():
    print("=" * 60)
    print("文本分类示例 - SVM 情感分析")
    print("=" * 60)

    # 1. 加载数据
    texts, labels = load_sentiment_data()
    print(f"\n数据集大小: {len(texts)} 文本")
    print(f"  正面: {np.sum(labels == 1)}")
    print(f"  负面: {np.sum(labels == -1)}")

    # 2. 文本预处理
    print("\n文本预处理...")
    processed_texts = [preprocess_text(text) for text in texts]

    # 3. TF-IDF 特征提取
    print("TF-IDF 特征提取...")
    vectorizer = TFIDFVectorizer(max_features=50)
    X = vectorizer.fit_transform(processed_texts)
    print(f"特征维度: {X.shape[1]}")

    # 显示最重要的特征词
    print(f"\nTop 10 特征词:")
    sorted_vocab = sorted(
        vectorizer.vocabulary.items(),
        key=lambda x: vectorizer.idf[x[1]]
    )
    for word, idx in sorted_vocab[:10]:
        print(f"  {word}: IDF={vectorizer.idf[idx]:.4f}")

    # 4. 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X, labels, test_ratio=0.3)
    print(f"\n训练集: {X_train.shape[0]} 样本")
    print(f"测试集: {X_test.shape[0]} 样本")

    # 5. 训练 SVM
    print("\n" + "-" * 60)
    print("训练 SVM 分类器")
    print("-" * 60)

    svm = SVM(kernel="linear", C=1.0, max_passes=100)
    svm.fit(X_train, y_train)
    print(f"支持向量数量: {svm.get_n_support_vectors()}")

    # 6. 评估
    y_pred = svm.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print(f"\n评估结果:")
    print(f"  准确率:   {acc:.4f}")
    print(f"  精确率:   {prec:.4f}")
    print(f"  召回率:   {rec:.4f}")
    print(f"  F1 分数:  {f1:.4f}")

    # 7. 混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    classes = np.unique(np.concatenate([y_test, y_pred]))
    class_names = {1: "正面", -1: "负面"}
    print(f"\n混淆矩阵:")
    print(f"{'':>10}", end="")
    for c in classes:
        print(f"{'预测' + class_names[c]:>10}", end="")
    print()
    for i, c_true in enumerate(classes):
        print(f"{'真实' + class_names[c_true]:>10}", end="")
        for j, c_pred in enumerate(classes):
            print(f"{cm[i, j]:>10d}", end="")
        print()

    # 8. 预测新文本
    print("\n" + "-" * 60)
    print("预测新文本")
    print("-" * 60)

    new_texts = [
        "this is an amazing and wonderful movie",
        "I hated this terrible film",
        "the acting was great and the story was beautiful",
        "worst movie ever complete waste of time",
        "I enjoyed this film it was quite good",
    ]

    new_processed = [preprocess_text(text) for text in new_texts]
    new_X = vectorizer.transform(new_processed)
    new_pred = svm.predict(new_X)

    for text, pred in zip(new_texts, new_pred):
        sentiment = "正面" if pred == 1 else "负面"
        print(f"  [{sentiment}] {text}")

    # 9. 不同核函数对比
    print("\n" + "-" * 60)
    print("不同核函数对比")
    print("-" * 60)

    for kernel in ["linear", "rbf", "polynomial"]:
        svm_k = SVM(kernel=kernel, C=1.0, gamma=1.0, max_passes=100)
        svm_k.fit(X_train, y_train)
        y_pred_k = svm_k.predict(X_test)
        acc_k = accuracy_score(y_test, y_pred_k)
        print(f"  {kernel:<15} 准确率: {acc_k:.4f}")


if __name__ == "__main__":
    main()
