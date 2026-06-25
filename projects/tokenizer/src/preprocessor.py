"""
文本预处理模块
提供文本预处理、搜索引擎分词、机器翻译分词等实际应用
"""

import re
from collections import Counter


class TextPreprocessor:
    """文本预处理器"""

    def __init__(self, tokenizer=None, pos_tagger=None):
        """
        初始化文本预处理器

        Args:
            tokenizer: 分词器对象
            pos_tagger: 词性标注器对象
        """
        self.tokenizer = tokenizer
        self.pos_tagger = pos_tagger

    def preprocess(self, text, options=None):
        """
        文本预处理

        Args:
            text: 输入文本
            options: 预处理选项字典
                - lowercase: 转小写（英文）
                - remove_punctuation: 移除标点
                - remove_numbers: 移除数字
                - remove_stopwords: 移除停用词
                - remove_spaces: 移除多余空格
                - normalize_unicode: Unicode 标准化

        Returns:
            str: 预处理后的文本
        """
        if options is None:
            options = {
                'lowercase': False,
                'remove_punctuation': False,
                'remove_numbers': False,
                'remove_stopwords': False,
                'remove_spaces': True,
                'normalize_unicode': True,
            }

        result = text

        # Unicode 标准化
        if options.get('normalize_unicode', False):
            result = self._normalize_unicode(result)

        # 转小写
        if options.get('lowercase', False):
            result = result.lower()

        # 移除标点
        if options.get('remove_punctuation', False):
            result = self._remove_punctuation(result)

        # 移除数字
        if options.get('remove_numbers', False):
            result = self._remove_numbers(result)

        # 移除多余空格
        if options.get('remove_spaces', True):
            result = self._normalize_spaces(result)

        return result

    def _normalize_unicode(self, text):
        """Unicode 标准化"""
        import unicodedata
        return unicodedata.normalize('NFKC', text)

    def _remove_punctuation(self, text):
        """移除标点"""
        # 中文标点
        cn_punct = '，。！？、；：""''（）【】《》——…'
        # 英文标点
        en_punct = r'[.,!?;:\"\'\(\)\[\]\{\}<>\-_]'
        # 合并
        pattern = f'[{re.escape(cn_punct)}]|{en_punct}'
        return re.sub(pattern, '', text)

    def _remove_numbers(self, text):
        """移除数字"""
        return re.sub(r'\d+', '', text)

    def _normalize_spaces(self, text):
        """标准化空格"""
        # 合并多个空格为一个
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def tokenize_and_clean(self, text):
        """
        分词并清洗

        Args:
            text: 输入文本

        Returns:
            list: 清洗后的词语列表
        """
        if self.tokenizer is None:
            raise RuntimeError("请先设置分词器")

        # 分词
        tokens = self.tokenizer.segment(text)

        # 清洗
        cleaned = []
        for token in tokens:
            # 去除空白
            token = token.strip()
            if not token:
                continue
            # 去除标点
            if all(not c.isalnum() for c in token):
                continue
            cleaned.append(token)

        return cleaned

    def extract_keywords(self, text, top_k=10):
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前 k 个关键词

        Returns:
            list: [(word, freq), ...] 关键词列表
        """
        # 分词
        tokens = self.tokenize_and_clean(text)

        # 统计词频
        word_freq = Counter(tokens)

        # 返回高频词
        return word_freq.most_common(top_k)


class SearchTokenizer:
    """搜索引擎分词器"""

    # 搜索停用词
    STOPWORDS = {
        '的', '了', '在', '是', '我', '有', '和', '就',
        '不', '人', '都', '一', '一个', '上', '也', '很',
        '到', '说', '要', '去', '你', '会', '着', '没有',
        '看', '好', '自己', '这', '他', '她', '它',
        'the', 'a', 'an', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall',
        'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'this', 'that', 'these', 'those', 'my', 'your',
        'his', 'her', 'its', 'our', 'their',
        'and', 'or', 'but', 'if', 'then', 'else',
        'for', 'of', 'to', 'in', 'on', 'at', 'by', 'with',
    }

    def __init__(self, tokenizer, remove_stopwords=True):
        """
        初始化搜索引擎分词器

        Args:
            tokenizer: 分词器对象
            remove_stopwords: 是否移除停用词
        """
        self.tokenizer = tokenizer
        self.remove_stopwords = remove_stopwords

    def tokenize(self, text):
        """
        搜索分词

        Args:
            text: 搜索文本

        Returns:
            list: 分词结果
        """
        if not text:
            return []

        # 分词
        tokens = self.tokenizer.segment(text)

        # 清洗
        result = []
        for token in tokens:
            token = token.strip().lower()
            if not token:
                continue
            # 跳过纯标点
            if all(not c.isalnum() for c in token):
                continue
            # 跳过停用词
            if self.remove_stopwords and token in self.STOPWORDS:
                continue
            result.append(token)

        return result

    def build_index(self, documents):
        """
        构建倒排索引

        Args:
            documents: 文档列表，每项为 (doc_id, text)

        Returns:
            dict: 倒排索引 {word: [(doc_id, positions), ...]}
        """
        index = {}

        for doc_id, text in documents:
            tokens = self.tokenize(text)

            for pos, token in enumerate(tokens):
                if token not in index:
                    index[token] = []
                index[token].append((doc_id, pos))

        return index

    def search(self, query, index, top_k=10):
        """
        搜索

        Args:
            query: 查询文本
            index: 倒排索引
            top_k: 返回前 k 个结果

        Returns:
            list: [(doc_id, score), ...] 搜索结果
        """
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        # 计算文档得分
        doc_scores = Counter()

        for token in query_tokens:
            if token in index:
                for doc_id, pos in index[token]:
                    doc_scores[doc_id] += 1

        # 返回得分最高的文档
        return doc_scores.most_common(top_k)


class MachineTranslationTokenizer:
    """机器翻译分词器"""

    def __init__(self, tokenizer, pos_tagger=None):
        """
        初始化机器翻译分词器

        Args:
            tokenizer: 分词器对象
            pos_tagger: 词性标注器对象
        """
        self.tokenizer = tokenizer
        self.pos_tagger = pos_tagger

    def tokenize_for_translation(self, text):
        """
        为机器翻译进行分词

        Args:
            text: 输入文本

        Returns:
            dict: 包含分词结果和额外信息
        """
        # 分词
        tokens = self.tokenizer.segment(text)

        # 词性标注
        pos_tags = []
        if self.pos_tagger:
            pos_tags = self.pos_tagger.tag(tokens)

        # 提取特征
        features = {
            'tokens': tokens,
            'pos_tags': pos_tags,
            'length': len(tokens),
            'has_numbers': any(t.isdigit() for t in tokens),
            'has_english': any(t.isascii() and t.isalpha() for t in tokens),
        }

        return features

    def prepare_parallel_corpus(self, source_texts, target_texts):
        """
        准备平行语料

        Args:
            source_texts: 源语言文本列表
            target_texts: 目标语言文本列表

        Returns:
            list: [(src_tokens, tgt_tokens), ...] 平行语料对
        """
        parallel = []

        for src, tgt in zip(source_texts, target_texts):
            src_tokens = self.tokenizer.segment(src)
            tgt_tokens = tgt.strip().split()
            parallel.append((src_tokens, tgt_tokens))

        return parallel

    def align_tokens(self, source_tokens, target_tokens):
        """
        简单的词对齐

        Args:
            source_tokens: 源语言词语列表
            target_tokens: 目标语言词语列表

        Returns:
            list: [(src_idx, tgt_idx), ...] 对齐结果
        """
        alignments = []

        # 简单的一对一对齐
        for i in range(min(len(source_tokens), len(target_tokens))):
            alignments.append((i, i))

        return alignments
