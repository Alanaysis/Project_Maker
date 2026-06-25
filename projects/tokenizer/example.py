#!/usr/bin/env python3
"""
分词器使用示例
展示中文分词、英文分词、子词分词、词性标注等功能
"""

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from src.tokenizer import Tokenizer
from src.english import EnglishTokenizer
from src.subword import BPETokenizer, WordPieceTokenizer, UnigramTokenizer
from src.pos_tagger import POSTagger
from src.preprocessor import TextPreprocessor, SearchTokenizer


def demo_chinese_tokenizer():
    """演示中文分词"""
    print("=" * 60)
    print("中文分词演示")
    print("=" * 60)

    # 创建分词器
    tokenizer = Tokenizer()

    # 加载词典
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dict.txt")
    if os.path.exists(dict_path):
        tokenizer.load_dictionary(dict_path)
    else:
        # 手动添加词典
        tokenizer.dictionary.add("我", 200)
        tokenizer.dictionary.add("爱", 150)
        tokenizer.dictionary.add("北京", 100)
        tokenizer.dictionary.add("天安门", 50)
        tokenizer.dictionary.add("中华人民共和国", 80)
        tokenizer.dictionary.add("研究", 70)
        tokenizer.dictionary.add("研究生", 40)
        tokenizer.dictionary.add("生命", 65)
        tokenizer.dictionary.add("的", 300)
        tokenizer.dictionary.add("起源", 45)

    # 测试文本
    text = "我爱北京天安门"
    print(f"\n原文: {text}")

    # 正向最大匹配
    fmm_result = tokenizer.fmm(text)
    print(f"FMM:  {fmm_result}")

    # 逆向最大匹配
    bmm_result = tokenizer.bmm(text)
    print(f"BMM:  {bmm_result}")

    # 双向最大匹配
    bimm_result = tokenizer.bimm(text)
    print(f"BiMM: {bimm_result}")

    # 歧义文本
    text2 = "研究生命的起源"
    print(f"\n原文: {text2}")
    print(f"FMM:  {tokenizer.fmm(text2)}")
    print(f"BMM:  {tokenizer.bmm(text2)}")
    print(f"BiMM: {tokenizer.bimm(text2)}")

    # HMM 分词
    print("\nHMM 分词:")
    corpus = [
        "我/S 爱/S 北京/B 天安门/E",
        "中华人民共和国/B 天安门/E"
    ]
    tokenizer.train_hmm(corpus)
    print(f"我爱北京天安门: {tokenizer.hmm('我爱北京天安门')}")


def demo_english_tokenizer():
    """演示英文分词"""
    print("\n" + "=" * 60)
    print("英文分词演示")
    print("=" * 60)

    # 创建英文分词器
    tokenizer = EnglishTokenizer(expand_contractions=True)

    # 基本分词
    text = "Hello, world! How are you?"
    print(f"\n原文: {text}")
    print(f"分词: {tokenizer.tokenize(text)}")

    # 缩写处理
    text2 = "I can't believe it's raining today."
    print(f"\n原文: {text2}")
    print(f"分词: {tokenizer.tokenize(text2)}")

    # 数字处理
    text3 = "The price is $3.14 and the discount is 15%"
    print(f"\n原文: {text3}")
    print(f"分词: {tokenizer.tokenize(text3)}")

    # 缩略词
    text4 = "Mr. Smith went to Washington D.C."
    print(f"\n原文: {text4}")
    print(f"分词: {tokenizer.tokenize(text4)}")

    # 只返回单词
    text5 = "Hello, world! 123"
    print(f"\n原文: {text5}")
    print(f"单词: {tokenizer.tokenize_words_only(text5)}")

    # 分句
    text6 = "Hello world. How are you? I am fine!"
    print(f"\n原文: {text6}")
    print(f"分句: {tokenizer.sentence_split(text6)}")


def demo_subword_tokenizer():
    """演示子词分词"""
    print("\n" + "=" * 60)
    print("子词分词演示")
    print("=" * 60)

    # 训练语料
    corpus = [
        "low lower newest wide",
        "low low low",
        "newer wider lower"
    ]

    # BPE 分词
    print("\nBPE 分词:")
    bpe = BPETokenizer(vocab_size=50)
    bpe.train(corpus)
    text = "lower newest"
    print(f"原文: {text}")
    print(f"分词: {bpe.tokenize(text)}")

    # WordPiece 分词
    print("\nWordPiece 分词:")
    wp = WordPieceTokenizer(vocab_size=100)
    wp.train(["unaffable", "unlikely", "unhappy", "understand"])
    text = "unaffable unlikely"
    print(f"原文: {text}")
    print(f"分词: {wp.tokenize(text)}")

    # Unigram 分词
    print("\nUnigram 分词:")
    uni = UnigramTokenizer(vocab_size=50)
    uni.train(corpus)
    text = "lower newest"
    print(f"原文: {text}")
    print(f"分词: {uni.tokenize(text)}")


def demo_pos_tagging():
    """演示词性标注"""
    print("\n" + "=" * 60)
    print("词性标注演示")
    print("=" * 60)

    # 规则标注
    print("\n规则标注:")
    tagger = POSTagger(method='rule')
    words = ["我", "爱", "北京", "天安门"]
    print(f"词语: {words}")
    print(f"标注: {tagger.tag(words)}")

    # HMM 标注
    print("\nHMM 标注:")
    tagger_hmm = POSTagger(method='hmm')
    corpus = [
        [("我", "r"), ("爱", "v"), ("北京", "n")],
        [("你", "r"), ("好", "a")]
    ]
    tagger_hmm.train(corpus)
    print(f"词语: {words}")
    print(f"标注: {tagger_hmm.tag(words)}")

    # 复杂句子
    words2 = ["今天", "天气", "真", "好"]
    print(f"\n词语: {words2}")
    print(f"标注: {tagger.tag(words2)}")


def demo_applications():
    """演示实际应用"""
    print("\n" + "=" * 60)
    print("实际应用演示")
    print("=" * 60)

    # 文本预处理
    print("\n文本预处理:")
    preprocessor = TextPreprocessor()
    text = "  Hello,   World!  123  "
    print(f"原文: '{text}'")
    print(f"预处理: '{preprocessor.preprocess(text)}'")

    # 搜索引擎分词
    print("\n搜索引擎分词:")
    # 创建简单词典
    tokenizer = Tokenizer()
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dict.txt")
    if os.path.exists(dict_path):
        tokenizer.load_dictionary(dict_path)
    tokenizer.dictionary.add("北京", 100)
    tokenizer.dictionary.add("天安门", 50)
    tokenizer.dictionary.add("上海", 80)
    tokenizer.dictionary.add("外滩", 40)

    search_tokenizer = SearchTokenizer(tokenizer, remove_stopwords=True)

    # 构建索引
    documents = [
        (1, "北京天安门"),
        (2, "上海外滩"),
        (3, "北京故宫")
    ]
    index = search_tokenizer.build_index(documents)
    print(f"索引: {index}")

    # 搜索
    results = search_tokenizer.search("北京", index)
    print(f"搜索 '北京': {results}")


def main():
    """主函数"""
    print("分词器功能演示")
    print("=" * 60)

    # 中文分词
    demo_chinese_tokenizer()

    # 英文分词
    demo_english_tokenizer()

    # 子词分词
    demo_subword_tokenizer()

    # 词性标注
    demo_pos_tagging()

    # 实际应用
    demo_applications()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
