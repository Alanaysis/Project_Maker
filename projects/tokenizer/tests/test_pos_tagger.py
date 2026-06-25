"""
词性标注器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pos_tagger import HMMPOSTagger, RuleBasedPOSTagger, POSTagger


class TestHMMPOSTagger:
    """HMM 词性标注器测试类"""

    def test_init(self):
        """测试初始化"""
        tagger = HMMPOSTagger()
        assert len(tagger.start_prob) == 0
        assert len(tagger.trans_prob) == 0

    def test_train_with_tuples(self):
        """测试使用元组训练"""
        tagger = HMMPOSTagger()
        corpus = [
            [("我", "r"), ("爱", "v"), ("北京", "n")],
            [("你", "r"), ("好", "a")]
        ]
        tagger.train(corpus)
        assert len(tagger.start_prob) > 0
        assert len(tagger.trans_prob) > 0

    def test_train_with_strings(self):
        """测试使用字符串训练"""
        tagger = HMMPOSTagger()
        corpus = [
            "我/r 爱/v 北京/n",
            "你/r 好/a"
        ]
        tagger.train(corpus)
        assert len(tagger.start_prob) > 0

    def test_tag(self):
        """测试标注"""
        tagger = HMMPOSTagger()
        corpus = [
            [("我", "r"), ("爱", "v"), ("北京", "n")],
            [("你", "r"), ("好", "a")]
        ]
        tagger.train(corpus)
        result = tagger.tag(["我", "爱", "北京"])
        assert len(result) == 3
        assert all(isinstance(pair, tuple) for pair in result)

    def test_tag_empty(self):
        """测试空输入"""
        tagger = HMMPOSTagger()
        result = tagger.tag([])
        assert result == []

    def test_tag_without_training(self):
        """测试未训练时标注"""
        tagger = HMMPOSTagger()
        result = tagger.tag(["我", "爱", "北京"])
        assert len(result) == 3

    def test_save_load(self, tmp_path):
        """测试保存和加载"""
        tagger = HMMPOSTagger()
        corpus = [
            [("我", "r"), ("爱", "v"), ("北京", "n")],
            [("你", "r"), ("好", "a")]
        ]
        tagger.train(corpus)

        # 保存
        model_path = str(tmp_path / "pos_model.json")
        tagger.save(model_path)

        # 加载
        tagger2 = HMMPOSTagger()
        tagger2.load(model_path)

        # 验证
        assert tagger.start_prob == tagger2.start_prob
        assert tagger.tag_freq == tagger2.tag_freq


class TestRuleBasedPOSTagger:
    """规则词性标注器测试类"""

    def test_init(self):
        """测试初始化"""
        tagger = RuleBasedPOSTagger()
        assert tagger is not None

    def test_tag_pronoun(self):
        """测试代词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["我", "你", "他"])
        assert result[0][1] == 'r'
        assert result[1][1] == 'r'
        assert result[2][1] == 'r'

    def test_tag_preposition(self):
        """测试介词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["在", "从", "到"])
        assert result[0][1] == 'p'
        assert result[1][1] == 'p'
        assert result[2][1] == 'p'

    def test_tag_conjunction(self):
        """测试连词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["和", "但是", "因为"])
        assert result[0][1] == 'c'
        assert result[1][1] == 'c'
        assert result[2][1] == 'c'

    def test_tag_adverb(self):
        """测试副词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["不", "很", "非常"])
        assert result[0][1] == 'd'
        assert result[1][1] == 'd'
        assert result[2][1] == 'd'

    def test_tag_measure_word(self):
        """测试量词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["个", "只", "条"])
        assert result[0][1] == 'q'
        assert result[1][1] == 'q'
        assert result[2][1] == 'q'

    def test_tag_time(self):
        """测试时间词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["今天", "明天", "昨天"])
        assert result[0][1] == 't'
        assert result[1][1] == 't'
        assert result[2][1] == 't'

    def test_tag_number(self):
        """测试数字标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["123", "456"])
        assert result[0][1] == 'm'
        assert result[1][1] == 'm'

    def test_tag_english(self):
        """测试英文标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["hello", "world"])
        assert result[0][1] == 'eng'
        assert result[1][1] == 'eng'

    def test_tag_punctuation(self):
        """测试标点标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag([",", "!", "?"])
        assert result[0][1] == 'w'
        assert result[1][1] == 'w'
        assert result[2][1] == 'w'

    def test_tag_empty(self):
        """测试空输入"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag([])
        assert result == []

    def test_tag_auxiliary(self):
        """测试助词标注"""
        tagger = RuleBasedPOSTagger()
        result = tagger.tag(["的", "了", "着"])
        assert result[0][1] == 'u'
        assert result[1][1] == 'u'
        assert result[2][1] == 'u'


class TestPOSTagger:
    """统一词性标注器测试类"""

    def test_init(self):
        """测试初始化"""
        tagger = POSTagger(method='rule')
        assert tagger.method == 'rule'

    def test_tag_rule(self):
        """测试规则标注"""
        tagger = POSTagger(method='rule')
        result = tagger.tag(["我", "爱", "北京"])
        assert len(result) == 3

    def test_tag_hmm(self):
        """测试 HMM 标注"""
        tagger = POSTagger(method='hmm')
        corpus = [
            [("我", "r"), ("爱", "v"), ("北京", "n")]
        ]
        tagger.train(corpus)
        result = tagger.tag(["我", "爱", "北京"])
        assert len(result) == 3

    def test_tag_invalid_method(self):
        """测试无效方法"""
        tagger = POSTagger()
        with pytest.raises(ValueError):
            tagger.tag(["我"], method='invalid')

    def test_tag_text(self):
        """测试文本标注"""
        tagger = POSTagger(method='rule')
        result = tagger.tag_text("我爱北京")
        assert len(result) > 0

    def test_save_load_hmm(self, tmp_path):
        """测试保存和加载 HMM 模型"""
        tagger = POSTagger(method='hmm')
        corpus = [
            [("我", "r"), ("爱", "v"), ("北京", "n")]
        ]
        tagger.train(corpus)

        # 保存
        model_path = str(tmp_path / "hmm_pos.json")
        tagger.save_hmm_model(model_path)

        # 加载
        tagger2 = POSTagger(method='hmm')
        tagger2.load_hmm_model(model_path)

        # 验证
        assert tagger.hmm_tagger.tag_freq == tagger2.hmm_tagger.tag_freq
