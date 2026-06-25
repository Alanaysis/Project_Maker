"""应用模块测试"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications import TextGenerator, SpellingCorrector, InputMethod
from src.language_model import LanguageModel


@pytest.fixture
def trained_lm():
    """已训练的语言模型"""
    corpus = [
        "the cat sat on the mat",
        "the dog sat on the rug",
        "the cat ate the fish",
        "the dog chased the cat",
        "a cat and a dog played together",
        "the fish swam in the pond",
        "the mat was on the floor",
        "the rug was soft and warm",
    ]
    lm = LanguageModel(n=2, smoothing="add_k", k=1.0)
    lm.train(corpus)
    return lm


class TestTextGenerator:
    """文本生成器测试"""

    def test_init(self, trained_lm):
        """测试初始化"""
        gen = TextGenerator(trained_lm)
        assert gen.lm is trained_lm

    def test_generate(self, trained_lm):
        """测试生成文本"""
        gen = TextGenerator(trained_lm)
        text = gen.generate(seed="the", max_length=5)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_generate_diverse(self, trained_lm):
        """测试多样生成"""
        gen = TextGenerator(trained_lm)
        samples = gen.generate_diverse(seed="the", num_samples=3, max_length=5)
        assert len(samples) == 3
        for s in samples:
            assert isinstance(s, str)

    def test_generate_with_prefix(self, trained_lm):
        """测试前缀续写"""
        gen = TextGenerator(trained_lm)
        text = gen.generate_with_prefix("the cat", max_length=5)
        assert isinstance(text, str)
        assert "the" in text


class TestSpellingCorrector:
    """拼写纠错器测试"""

    def test_init(self, trained_lm):
        """测试初始化"""
        corrector = SpellingCorrector(trained_lm)
        assert corrector.lm is trained_lm

    def test_edits1(self):
        """测试编辑距离 1"""
        edits = SpellingCorrector._edits1("the")
        assert isinstance(edits, set)
        assert len(edits) > 0
        # 删除操作
        assert "he" in edits or "te" in edits or "th" in edits

    def test_edits2(self):
        """测试编辑距离 2"""
        edits = SpellingCorrector._edits2("ab")
        assert isinstance(edits, set)
        assert len(edits) > 0

    def test_correct_word(self, trained_lm):
        """测试词纠正"""
        corrector = SpellingCorrector(trained_lm)

        # 已知词应该保持不变
        result = corrector.correct_word("the")
        assert result == "the"

        # cat 应该保持不变
        result = corrector.correct_word("cat")
        assert result == "cat"

    def test_correct_word_with_context(self, trained_lm):
        """测试带上下文的词纠正"""
        corrector = SpellingCorrector(trained_lm)

        result = corrector.correct_word("cat", context="the")
        assert isinstance(result, str)

    def test_correct_text(self, trained_lm):
        """测试文本纠正"""
        corrector = SpellingCorrector(trained_lm)

        result = corrector.correct_text("the cat sat")
        assert isinstance(result, str)
        assert "the" in result
        assert "cat" in result

    def test_suggest(self, trained_lm):
        """测试拼写建议"""
        corrector = SpellingCorrector(trained_lm)

        suggestions = corrector.suggest("cat", n=3)
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3

    def test_suggest_unknown_word(self, trained_lm):
        """测试未知词的建议"""
        corrector = SpellingCorrector(trained_lm)

        suggestions = corrector.suggest("xyzabc", n=5)
        assert isinstance(suggestions, list)


class TestInputMethod:
    """输入法测试"""

    def test_init(self, trained_lm):
        """测试初始化"""
        im = InputMethod(trained_lm)
        assert im.lm is trained_lm

    def test_complete_prefix(self, trained_lm):
        """测试前缀补全"""
        im = InputMethod(trained_lm)

        # "c" 应该能匹配 "cat"
        candidates = im.complete_prefix("c", n=5)
        assert isinstance(candidates, list)

        # 检查候选词格式
        for word, score in candidates:
            assert isinstance(word, str)
            assert word.startswith("c")

    def test_complete_prefix_with_context(self, trained_lm):
        """测试带上下文的前缀补全"""
        im = InputMethod(trained_lm)

        candidates = im.complete_prefix("c", context="the", n=5)
        assert isinstance(candidates, list)

    def test_predict_next_words(self, trained_lm):
        """测试预测下一个词"""
        im = InputMethod(trained_lm)

        predictions = im.predict_next_words("the", n=5)
        assert isinstance(predictions, list)
        assert len(predictions) <= 5

        for word, score in predictions:
            assert isinstance(word, str)
            assert isinstance(score, float)

    def test_get_candidates(self, trained_lm):
        """测试获取候选词"""
        im = InputMethod(trained_lm)

        candidates = im.get_candidates("c", n=5)
        assert isinstance(candidates, list)

    def test_get_candidates_with_context(self, trained_lm):
        """测试带上下文的候选词"""
        im = InputMethod(trained_lm)

        candidates = im.get_candidates("c", context="the", n=5)
        assert isinstance(candidates, list)
