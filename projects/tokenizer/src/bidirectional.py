"""
双向最大匹配分词算法
Bidirectional Maximum Matching (BiMM)
结合正向和逆向最大匹配，选择更优结果
"""


class BiMM:
    """双向最大匹配分词器"""

    def __init__(self, dictionary):
        """
        初始化双向最大匹配分词器

        Args:
            dictionary: Dictionary 词典对象
        """
        from .fmm import FMM
        from .bmm import BMM

        self.dictionary = dictionary
        self.fmm = FMM(dictionary)
        self.bmm = BMM(dictionary)

    def segment(self, text):
        """
        双向最大匹配分词

        策略：
        1. 如果 FMM 和 BMM 结果相同，返回该结果
        2. 如果词数不同，选择词数较少的
        3. 如果词数相同，选择单字较少的
        4. 如果单字数也相同，选择 BMM 结果

        Args:
            text: 待分词的文本

        Returns:
            list: 分词结果列表

        Examples:
            >>> from .dictionary import Dictionary
            >>> dict = Dictionary()
            >>> dict.add("研究", 100)
            >>> dict.add("研究生", 100)
            >>> dict.add("生命", 100)
            >>> dict.add("的", 100)
            >>> dict.add("起源", 100)
            >>> bimm = BiMM(dict)
            >>> bimm.segment("研究生命的起源")
            ['研究', '生命', '的', '起源']
        """
        if not text:
            return []

        fmm_result = self.fmm.segment(text)
        bmm_result = self.bmm.segment(text)

        # 规则 1: 结果相同则返回
        if fmm_result == bmm_result:
            return fmm_result

        # 规则 2: 词数不同选词数少的
        if len(fmm_result) != len(bmm_result):
            return fmm_result if len(fmm_result) < len(bmm_result) else bmm_result

        # 规则 3: 词数相同选单字少的
        fmm_single = sum(1 for w in fmm_result if len(w) == 1)
        bmm_single = sum(1 for w in bmm_result if len(w) == 1)

        if fmm_single != bmm_single:
            return fmm_result if fmm_single < bmm_single else bmm_result

        # 规则 4: 都相同则选择 BMM（逆向通常更准确）
        return bmm_result

    def segment_with_info(self, text):
        """
        双向最大匹配分词（带详细信息）

        Args:
            text: 待分词的文本

        Returns:
            dict: 包含分词结果和详细信息
        """
        if not text:
            return {'result': [], 'fmm': [], 'bmm': [], 'method': 'empty'}

        fmm_result = self.fmm.segment(text)
        bmm_result = self.bmm.segment(text)

        if fmm_result == bmm_result:
            method = 'consensus'
            result = fmm_result
        elif len(fmm_result) != len(bmm_result):
            method = 'fmm_fewer_words' if len(fmm_result) < len(bmm_result) else 'bmm_fewer_words'
            result = fmm_result if len(fmm_result) < len(bmm_result) else bmm_result
        else:
            fmm_single = sum(1 for w in fmm_result if len(w) == 1)
            bmm_single = sum(1 for w in bmm_result if len(w) == 1)
            if fmm_single < bmm_single:
                method = 'fmm_fewer_singles'
                result = fmm_result
            elif bmm_single < fmm_single:
                method = 'bmm_fewer_singles'
                result = bmm_result
            else:
                method = 'bmm_default'
                result = bmm_result

        return {
            'result': result,
            'fmm': fmm_result,
            'bmm': bmm_result,
            'method': method
        }
