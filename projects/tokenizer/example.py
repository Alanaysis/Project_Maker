#!/usr/bin/env python3
"""
中文分词器使用示例
"""

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from src.tokenizer import Tokenizer


def main():
    """主函数"""
    # 创建分词器
    tokenizer = Tokenizer()

    # 加载词典
    dict_path = os.path.join(os.path.dirname(__file__), "data", "dict.txt")
    tokenizer.load_dictionary(dict_path)
    print(f"词典加载完成，共 {tokenizer.dictionary.size()} 个词条")

    # 测试文本
    test_texts = [
        "我爱北京天安门",
        "中华人民共和国",
        "研究生命的起源",
        "今天天气真好",
        "机器学习是人工智能的重要分支",
    ]

    # 使用不同算法分词
    for text in test_texts:
        print(f"\n原文: {text}")
        print("-" * 40)

        # 正向最大匹配
        fmm_result = tokenizer.fmm(text)
        print(f"FMM: {'/'.join(fmm_result)}")

        # 逆向最大匹配
        bmm_result = tokenizer.bmm(text)
        print(f"BMM: {'/'.join(bmm_result)}")

    # 训练 HMM 模型
    print("\n" + "=" * 40)
    print("训练 HMM 模型...")
    corpus = [
        "我/S 爱/S 北京/B 天安门/E",
        "中华/B 人民/M 共和国/E",
        "研究/S 生命/S 的/S 起源/S",
        "今天/S 天气/S 真/S 好/S",
        "机器/B 学习/E 是/S 人工/B 智能/E 的/S 重要/S 分支/S",
    ]
    tokenizer.train_hmm(corpus)

    # 使用 HMM 分词
    print("\nHMM 分词结果:")
    for text in test_texts:
        hmm_result = tokenizer.hmm(text)
        print(f"{text}: {'/'.join(hmm_result)}")


if __name__ == "__main__":
    main()
