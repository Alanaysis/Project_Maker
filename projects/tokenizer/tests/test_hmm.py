"""
HMM 分词测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hmm import HMM


class TestHMM:
    """HMM 测试类"""

    def test_init(self):
        """测试初始化"""
        hmm = HMM()
        assert len(hmm.start_prob) == 4
        assert len(hmm.trans_prob) == 4
        assert len(hmm.emit_prob) == 4

    def test_train(self):
        """测试训练"""
        hmm = HMM()
        corpus = [
            "我/S 爱/S 北京/B 天安门/E",
            "你/S 好/S"
        ]
        hmm.train(corpus)

        # 检查概率是否已更新
        assert any(p != 0.0 for p in hmm.start_prob)
        assert any(any(p != 0.0 for p in row) for row in hmm.trans_prob)

    def test_segment_empty(self):
        """测试空文本分词"""
        hmm = HMM()
        result = hmm.segment("")
        assert result == []

    def test_states_to_words(self):
        """测试状态转词语"""
        hmm = HMM()
        text = "我爱北京"
        states = ['S', 'S', 'B', 'E']
        result = hmm._states_to_words(text, states)
        assert result == ["我", "爱", "北京"]

    def test_states_to_words_single(self):
        """测试单字词状态转词语"""
        hmm = HMM()
        text = "我"
        states = ['S']
        result = hmm._states_to_words(text, states)
        assert result == ["我"]

    def test_states_to_words_multi_char(self):
        """测试多字词状态转词语"""
        hmm = HMM()
        text = "天安门"
        states = ['B', 'M', 'E']
        result = hmm._states_to_words(text, states)
        assert result == ["天安门"]

    def test_save_load_model(self, tmp_path):
        """测试保存和加载模型"""
        hmm = HMM()
        corpus = [
            "我/S 爱/S 北京/B 天安门/E",
            "你/S 好/S"
        ]
        hmm.train(corpus)

        # 保存模型
        model_path = str(tmp_path / "test_model.json")
        hmm.save_model(model_path)

        # 加载模型
        hmm2 = HMM()
        hmm2.load_model(model_path)

        # 验证模型参数一致
        assert hmm.start_prob == hmm2.start_prob
        assert hmm.trans_prob == hmm2.trans_prob

    def test_load_nonexistent_model(self):
        """测试加载不存在的模型"""
        hmm = HMM()
        with pytest.raises(FileNotFoundError):
            hmm.load_model("nonexistent.json")

    def test_viterbi(self):
        """测试维特比算法"""
        hmm = HMM()
        corpus = [
            "我/S 爱/S 北京/B 天安门/E"
        ]
        hmm.train(corpus)

        states = hmm.viterbi("我爱北京天安门")
        assert len(states) == 7  # "我爱北京天安门" 有 7 个字符
        assert all(s in range(4) for s in states)
