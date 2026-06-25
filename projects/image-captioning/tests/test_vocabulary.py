"""
测试词汇表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vocabulary import Vocabulary


class TestVocabulary:
    """词汇表测试套件。"""

    def test_initial_special_tokens(self):
        """测试特殊标记初始化。"""
        vocab = Vocabulary()
        assert len(vocab) == 4
        assert vocab.pad_idx == 0
        assert vocab.start_idx == 1
        assert vocab.end_idx == 2
        assert vocab.unk_idx == 3

    def test_build_from_captions(self):
        """测试从描述构建词汇表。"""
        captions = [
            "a dog is running",
            "a cat is sleeping",
            "the dog is happy",
        ]
        vocab = Vocabulary.from_captions(captions, min_freq=1)
        assert len(vocab) > 4  # 4 个特殊标记 + 普通词
        assert "dog" in vocab.word2idx
        assert "cat" in vocab.word2idx

    def test_encode_decode(self):
        """测试编码和解码。"""
        captions = ["a dog is running", "a cat is sleeping"]
        vocab = Vocabulary.from_captions(captions)

        # 编码
        indices = vocab.encode("a dog is running")
        assert indices[0] == vocab.start_idx
        assert indices[-1] == vocab.end_idx

        # 解码
        decoded = vocab.decode(indices, skip_special=True)
        assert decoded == "a dog is running"

    def test_encode_with_max_length(self):
        """测试带最大长度的编码。"""
        captions = ["a dog is running in the park"]
        vocab = Vocabulary.from_captions(captions)

        indices = vocab.encode("a dog is running in the park", max_length=4)
        assert len(indices) == 4

    def test_unknown_word(self):
        """测试未知词处理。"""
        captions = ["a dog"]
        vocab = Vocabulary.from_captions(captions)

        indices = vocab.encode("a unknown_word")
        assert vocab.unk_idx in indices

    def test_min_freq(self):
        """测试最小词频过滤。"""
        captions = ["a a a b c"]
        vocab = Vocabulary.from_captions(captions, min_freq=2)
        # "a" 出现3次，应该在词汇表中
        assert "a" in vocab.word2idx
        # "b" 和 "c" 只出现1次，不应在词汇表中
        assert "b" not in vocab.word2idx
        assert "c" not in vocab.word2idx

    def test_decode_skip_special(self):
        """测试解码时跳过特殊标记。"""
        vocab = Vocabulary.from_captions(["hello world"])
        indices = [vocab.start_idx, vocab.word2idx.get("hello", vocab.unk_idx), vocab.end_idx]
        decoded = vocab.decode(indices, skip_special=True)
        assert "<start>" not in decoded
        assert "<end>" not in decoded

    def test_encode_decode_roundtrip(self):
        """测试编码-解码往返一致性。"""
        captions = ["a dog is running", "the cat sleeps"]
        vocab = Vocabulary.from_captions(captions)

        original = "a dog is running"
        encoded = vocab.encode(original)
        decoded = vocab.decode(encoded, skip_special=True)
        assert decoded == original


def run_tests():
    """运行所有测试。"""
    test = TestVocabulary()
    tests = [getattr(test, name) for name in dir(test) if name.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__} - {e}")
            failed += 1
    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("词汇表测试")
    print("-" * 40)
    success = run_tests()
    sys.exit(0 if success else 1)
