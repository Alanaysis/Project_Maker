"""
词性标注器
支持 HMM 词性标注和简单规则标注
"""

import json
import math
from collections import defaultdict, Counter


class HMMPOSTagger:
    """基于 HMM 的词性标注器"""

    # 常用中文词性标签
    POS_TAGS = {
        'n': '名词', 'v': '动词', 'a': '形容词', 'd': '副词',
        'r': '代词', 'p': '介词', 'c': '连词', 'u': '助词',
        'm': '量词', 'q': '量词', 't': '时间词', 'f': '方位词',
        'x': '非语素字', 'w': '标点', 'eng': '英文',
    }

    def __init__(self):
        """初始化 HMM 词性标注器"""
        self.start_prob = {}    # 初始概率
        self.trans_prob = {}    # 转移概率
        self.emit_prob = {}     # 发射概率
        self.word_tag_freq = {} # 词-词性频率
        self.tag_freq = {}      # 词性频率

    def train(self, corpus):
        """
        训练 HMM 词性标注模型

        Args:
            corpus: 标注语料，格式为 [(word, tag), ...] 的列表
                    或 "word1/tag1 word2/tag2 ..." 格式的字符串列表

        Examples:
            >>> tagger = HMMPOSTagger()
            >>> corpus = [("我", "r"), ("爱", "v"), ("北京", "n")]
            >>> tagger.train([corpus])
        """
        # 统计计数
        start_count = Counter()
        trans_count = defaultdict(Counter)
        emit_count = defaultdict(Counter)
        tag_count = Counter()

        for sentence in corpus:
            if isinstance(sentence, str):
                # 解析字符串格式
                pairs = []
                for item in sentence.strip().split():
                    parts = item.rsplit('/', 1)
                    if len(parts) == 2:
                        pairs.append((parts[0], parts[1]))
                sentence = pairs

            if not sentence:
                continue

            # 统计初始状态
            start_count[sentence[0][1]] += 1

            # 统计转移和发射
            prev_tag = None
            for word, tag in sentence:
                emit_count[tag][word] += 1
                tag_count[tag] += 1

                if prev_tag is not None:
                    trans_count[prev_tag][tag] += 1

                prev_tag = tag

        # 计算概率
        total_start = sum(start_count.values()) or 1
        for tag, count in start_count.items():
            self.start_prob[tag] = math.log(count / total_start)

        for tag in tag_count:
            total_trans = sum(trans_count[tag].values()) or 1
            self.trans_prob[tag] = {}
            for next_tag in tag_count:
                count = trans_count[tag][next_tag]
                self.trans_prob[tag][next_tag] = math.log((count + 1e-8) / (total_trans + 1e-8 * len(tag_count)))

        for tag in tag_count:
            total_emit = tag_count[tag] or 1
            self.emit_prob[tag] = {}
            for word, count in emit_count[tag].items():
                self.emit_prob[tag][word] = math.log(count / total_emit)

        self.word_tag_freq = dict(emit_count)
        self.tag_freq = dict(tag_count)

    def tag(self, words):
        """
        对词语列表进行词性标注

        Args:
            words: 词语列表

        Returns:
            list: [(word, tag), ...] 标注结果

        Examples:
            >>> tagger = HMMPOSTagger()
            >>> tagger.train([...])
            >>> tagger.tag(["我", "爱", "北京"])
            [("我", "r"), ("爱", "v"), ("北京", "n")]
        """
        if not words:
            return []

        if not self.start_prob:
            # 未训练时使用简单规则
            return [(word, self._guess_tag(word)) for word in words]

        # 使用维特比算法
        tags = self._viterbi(words)
        return list(zip(words, tags))

    def _viterbi(self, words):
        """维特比算法求最优词性序列"""
        n = len(words)
        all_tags = list(self.tag_freq.keys())

        if not all_tags:
            return [self._guess_tag(word) for word in words]

        # 初始化
        dp = [{} for _ in range(n)]
        path = [{} for _ in range(n)]

        # 初始状态
        for tag in all_tags:
            start_p = self.start_prob.get(tag, -100)
            emit_p = self.emit_prob.get(tag, {}).get(words[0], -100)
            dp[0][tag] = start_p + emit_p
            path[0][tag] = None

        # 递推
        for t in range(1, n):
            for tag in all_tags:
                max_prob = float('-inf')
                max_prev = None

                for prev_tag in all_tags:
                    if prev_tag in dp[t - 1]:
                        trans_p = self.trans_prob.get(prev_tag, {}).get(tag, -100)
                        prob = dp[t - 1][prev_tag] + trans_p
                        if prob > max_prob:
                            max_prob = prob
                            max_prev = prev_tag

                emit_p = self.emit_prob.get(tag, {}).get(words[t], -100)
                dp[t][tag] = max_prob + emit_p if max_prev else -1000
                path[t][tag] = max_prev

        # 回溯
        tags = [None] * n
        # 找最后一个词的最佳标签
        best_tag = max(dp[n - 1], key=dp[n - 1].get) if dp[n - 1] else all_tags[0]
        tags[n - 1] = best_tag

        for t in range(n - 2, -1, -1):
            tags[t] = path[t + 1][tags[t + 1]]
            if tags[t] is None:
                tags[t] = self._guess_tag(words[t])

        return tags

    def _guess_tag(self, word):
        """简单猜测词性"""
        # 数字
        if word.isdigit():
            return 'm'
        # 标点
        if all(not c.isalnum() for c in word):
            return 'w'
        # 英文
        if word.isascii() and word.isalpha():
            return 'eng'
        # 默认名词
        return 'n'

    def save(self, filepath):
        """保存模型"""
        model = {
            'start_prob': self.start_prob,
            'trans_prob': self.trans_prob,
            'emit_prob': {tag: dict(prob) for tag, prob in self.emit_prob.items()},
            'tag_freq': self.tag_freq
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model, f, ensure_ascii=False, indent=2)

    def load(self, filepath):
        """加载模型"""
        with open(filepath, 'r', encoding='utf-8') as f:
            model = json.load(f)

        self.start_prob = model['start_prob']
        self.trans_prob = model['trans_prob']
        self.emit_prob = {tag: prob for tag, prob in model['emit_prob'].items()}
        self.tag_freq = model['tag_freq']


class RuleBasedPOSTagger:
    """基于规则的词性标注器"""

    # 常见词缀规则
    SUFFIX_RULES = {
        '的': 'u',
        '地': 'u',
        '得': 'u',
        '了': 'u',
        '着': 'u',
        '过': 'u',
        '吗': 'u',
        '呢': 'u',
        '吧': 'u',
        '啊': 'u',
        '呀': 'u',
        '哦': 'u',
    }

    # 常见词性规则
    WORD_RULES = {
        # 代词
        '我': 'r', '你': 'r', '他': 'r', '她': 'r', '它': 'r',
        '我们': 'r', '你们': 'r', '他们': 'r', '她们': 'r', '它们': 'r',
        '这': 'r', '那': 'r', '这里': 'r', '那里': 'r',
        '什么': 'r', '谁': 'r', '哪': 'r', '哪里': 'r',

        # 介词
        '在': 'p', '从': 'p', '到': 'p', '向': 'p', '往': 'p',
        '把': 'p', '被': 'p', '给': 'p', '对': 'p', '和': 'p',
        '跟': 'p', '比': 'p', '为了': 'p', '因为': 'p',

        # 连词
        '和': 'c', '与': 'c', '或': 'c', '或者': 'c',
        '但是': 'c', '但': 'c', '然而': 'c', '不过': 'c',
        '因为': 'c', '所以': 'c', '如果': 'c', '虽然': 'c',

        # 副词
        '不': 'd', '没': 'd', '没有': 'd', '很': 'd', '非常': 'd',
        '太': 'd', '更': 'd', '最': 'd', '都': 'd', '也': 'd',
        '就': 'd', '才': 'd', '只': 'd', '仅': 'd',
        '已经': 'd', '正在': 'd', '将': 'd', '会': 'd',

        # 量词
        '个': 'q', '只': 'q', '条': 'q', '张': 'q', '本': 'q',
        '把': 'q', '件': 'q', '块': 'q', '元': 'q',
        '些': 'q', '点': 'q',

        # 时间词
        '今天': 't', '明天': 't', '昨天': 't',
        '现在': 't', '以前': 't', '以后': 't',
        '上午': 't', '下午': 't', '晚上': 't',
    }

    # 动词后缀
    VERB_SUFFIXES = ['化', '于', '以', '使', '让', '令']

    # 形容词后缀
    ADJ_SUFFIXES = ['性', '型', '式', '般', '样']

    def __init__(self):
        """初始化规则词性标注器"""
        pass

    def tag(self, words):
        """
        对词语列表进行词性标注

        Args:
            words: 词语列表

        Returns:
            list: [(word, tag), ...] 标注结果

        Examples:
            >>> tagger = RuleBasedPOSTagger()
            >>> tagger.tag(["我", "爱", "北京"])
            [("我", "r"), ("爱", "v"), ("北京", "n")]
        """
        return [(word, self._get_tag(word)) for word in words]

    def _get_tag(self, word):
        """获取单个词的词性"""
        # 1. 查找精确匹配
        if word in self.WORD_RULES:
            return self.WORD_RULES[word]

        # 2. 查找后缀匹配
        if word in self.SUFFIX_RULES:
            return self.SUFFIX_RULES[word]

        # 3. 数字
        if word.isdigit() or self._is_number(word):
            return 'm'

        # 4. 标点
        if all(not c.isalnum() for c in word):
            return 'w'

        # 5. 英文
        if word.isascii():
            if word.isalpha():
                return 'eng'
            return 'x'

        # 6. 词缀规则
        if word.endswith(tuple(self.VERB_SUFFIXES)):
            return 'v'

        if word.endswith(tuple(self.ADJ_SUFFIXES)):
            return 'a'

        # 7. 默认名词
        return 'n'

    def _is_number(self, word):
        """判断是否为数字"""
        try:
            float(word)
            return True
        except ValueError:
            return False


class POSTagger:
    """统一词性标注接口"""

    def __init__(self, method='rule'):
        """
        初始化词性标注器

        Args:
            method: 标注方法，'hmm' 或 'rule'
        """
        self.method = method
        self.hmm_tagger = HMMPOSTagger()
        self.rule_tagger = RuleBasedPOSTagger()

    def train(self, corpus):
        """
        训练词性标注模型（仅 HMM 方法需要）

        Args:
            corpus: 标注语料
        """
        self.hmm_tagger.train(corpus)

    def tag(self, words, method=None):
        """
        进行词性标注

        Args:
            words: 词语列表
            method: 标注方法，None 使用默认方法

        Returns:
            list: [(word, tag), ...] 标注结果
        """
        method = method or self.method

        if method == 'hmm':
            return self.hmm_tagger.tag(words)
        elif method == 'rule':
            return self.rule_tagger.tag(words)
        else:
            raise ValueError(f"不支持的标注方法: {method}")

    def tag_text(self, text, tokenizer=None):
        """
        对文本进行分词和词性标注

        Args:
            text: 输入文本
            tokenizer: 分词器对象

        Returns:
            list: [(word, tag), ...] 标注结果
        """
        if tokenizer is None:
            # 简单按字符分词
            words = list(text)
        else:
            words = tokenizer.segment(text)

        return self.tag(words)

    def save_hmm_model(self, filepath):
        """保存 HMM 模型"""
        self.hmm_tagger.save(filepath)

    def load_hmm_model(self, filepath):
        """加载 HMM 模型"""
        self.hmm_tagger.load(filepath)
