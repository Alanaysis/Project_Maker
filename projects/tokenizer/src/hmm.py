"""
HMM 分词算法
Hidden Markov Model based Chinese Word Segmentation
"""

import json
import math
from collections import defaultdict


class HMM:
    """HMM 分词器"""

    # 状态定义
    STATES = {'B': 0, 'M': 1, 'E': 2, 'S': 3}
    STATE_LIST = ['B', 'M', 'E', 'S']

    def __init__(self):
        """初始化 HMM 模型"""
        self.start_prob = [0.0] * 4  # 初始概率
        self.trans_prob = [[0.0] * 4 for _ in range(4)]  # 转移概率
        self.emit_prob = [defaultdict(float) for _ in range(4)]  # 发射概率

    def train(self, corpus):
        """
        训练 HMM 模型

        Args:
            corpus: 标注语料列表，每行为 "字1/状态1 字2/状态2 ..."
                    例如: "我/S 爱/S 北京/B 天安门/E"

        Examples:
            >>> hmm = HMM()
            >>> corpus = ["我/S 爱/S 北京/B 天安门/E"]
            >>> hmm.train(corpus)
        """
        # 统计计数
        start_count = [0] * 4
        trans_count = [[0] * 4 for _ in range(4)]
        emit_count = [defaultdict(int) for _ in range(4)]
        state_count = [0] * 4

        for line in corpus:
            if not line.strip():
                continue

            # 解析标注
            words = line.strip().split()
            if not words:
                continue

            # 统计初始状态
            first_state = words[0].split('/')[-1]
            if first_state in self.STATES:
                start_count[self.STATES[first_state]] += 1

            # 统计转移和发射
            prev_state = None
            for word_state in words:
                parts = word_state.split('/')
                if len(parts) != 2:
                    continue

                char, state = parts
                if state not in self.STATES:
                    continue

                state_idx = self.STATES[state]

                # 发射计数
                emit_count[state_idx][char] += 1
                state_count[state_idx] += 1

                # 转移计数
                if prev_state is not None:
                    trans_count[prev_state][state_idx] += 1

                prev_state = state_idx

        # 计算概率（使用对数避免下溢）
        total_start = sum(start_count) or 1
        for i in range(4):
            self.start_prob[i] = math.log((start_count[i] + 1e-8) / (total_start + 4e-8))

        for i in range(4):
            total_trans = sum(trans_count[i]) or 1
            for j in range(4):
                self.trans_prob[i][j] = math.log((trans_count[i][j] + 1e-8) / (total_trans + 4e-8))

        for i in range(4):
            total_emit = state_count[i] or 1
            for char, count in emit_count[i].items():
                self.emit_prob[i][char] = math.log(count / total_emit)

    def viterbi(self, text):
        """
        维特比算法求最优状态序列

        Args:
            text: 输入文本

        Returns:
            list: 最优状态序列
        """
        if not text:
            return []

        T = len(text)
        N = 4  # 状态数

        # 初始化动态规划表
        dp = [[float('-inf')] * N for _ in range(T)]
        path = [[0] * N for _ in range(T)]

        # 初始状态
        for s in range(N):
            emit_prob = self.emit_prob[s].get(text[0], -100)
            dp[0][s] = self.start_prob[s] + emit_prob

        # 递推
        for t in range(1, T):
            for s in range(N):
                max_prob = float('-inf')
                max_state = 0
                for ps in range(N):
                    prob = dp[t - 1][ps] + self.trans_prob[ps][s]
                    if prob > max_prob:
                        max_prob = prob
                        max_state = ps
                emit_prob = self.emit_prob[s].get(text[t], -100)
                dp[t][s] = max_prob + emit_prob
                path[t][s] = max_state

        # 回溯找到最优路径
        states = [0] * T
        states[T - 1] = dp[T - 1].index(max(dp[T - 1]))
        for t in range(T - 2, -1, -1):
            states[t] = path[t + 1][states[t + 1]]

        return states

    def segment(self, text):
        """
        使用 HMM 进行分词

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Examples:
            >>> hmm = HMM()
            >>> hmm.load_model("data/hmm_model.json")
            >>> hmm.segment("我爱北京天安门")
            ['我', '爱', '北京', '天安门']
        """
        if not text:
            return []

        # 使用维特比算法得到状态序列
        states_idx = self.viterbi(text)

        # 将状态索引转换为状态字符
        states = [self.STATE_LIST[idx] for idx in states_idx]

        # 根据状态序列进行分词
        return self._states_to_words(text, states)

    def _states_to_words(self, text, states):
        """
        根据状态序列将文本切分为词语

        Args:
            text: 原始文本
            states: 状态序列

        Returns:
            list: 词语列表
        """
        words = []
        word = ""

        for char, state in zip(text, states):
            if state == 'B':
                word = char
            elif state == 'M':
                word += char
            elif state == 'E':
                word += char
                words.append(word)
                word = ""
            elif state == 'S':
                words.append(char)

        # 处理最后一个词
        if word:
            words.append(word)

        return words

    def save_model(self, filepath):
        """
        保存模型到文件

        Args:
            filepath: 保存路径
        """
        model = {
            'start_prob': self.start_prob,
            'trans_prob': self.trans_prob,
            'emit_prob': [dict(prob) for prob in self.emit_prob]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)

    def load_model(self, filepath):
        """
        从文件加载模型

        Args:
            filepath: 模型文件路径

        Raises:
            FileNotFoundError: 文件不存在
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                model = json.load(f)

            self.start_prob = model['start_prob']
            self.trans_prob = model['trans_prob']
            self.emit_prob = [defaultdict(float, prob) for prob in model['emit_prob']]
        except FileNotFoundError:
            raise FileNotFoundError(f"模型文件不存在: {filepath}")
