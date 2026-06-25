"""词形还原模块 - Lemmatizer

提供词形还原功能，将词汇还原为词典形式。
使用规则和词典结合的方式实现。
"""

from typing import List, Dict


class Lemmatizer:
    """词形还原器

    基于规则和词典的词形还原实现。
    """

    # 常见不规则动词/名词映射
    IRREGULAR_FORMS: Dict[str, str] = {
        'am': 'be', 'is': 'be', 'are': 'be', 'was': 'be', 'were': 'be',
        'been': 'be', 'being': 'be',
        'has': 'have', 'had': 'have', 'having': 'have',
        'does': 'do', 'did': 'do', 'done': 'do', 'doing': 'do',
        'goes': 'go', 'went': 'go', 'gone': 'go', 'going': 'go',
        'takes': 'take', 'took': 'take', 'taken': 'take', 'taking': 'take',
        'comes': 'come', 'came': 'come', 'coming': 'come',
        'makes': 'make', 'made': 'make', 'making': 'make',
        'says': 'say', 'said': 'say', 'saying': 'say',
        'gets': 'get', 'got': 'get', 'gotten': 'get', 'getting': 'get',
        'knows': 'know', 'knew': 'know', 'known': 'know', 'knowing': 'know',
        'thinks': 'think', 'thought': 'think', 'thinking': 'think',
        'sees': 'see', 'saw': 'see', 'seen': 'see', 'seeing': 'see',
        'wants': 'want', 'wanted': 'want', 'wanting': 'want',
        'uses': 'use', 'used': 'use', 'using': 'use',
        'finds': 'find', 'found': 'find', 'finding': 'find',
        'gives': 'give', 'gave': 'give', 'given': 'give', 'giving': 'give',
        'tells': 'tell', 'told': 'tell', 'telling': 'tell',
        'works': 'work', 'worked': 'work', 'working': 'work',
        'calls': 'call', 'called': 'call', 'calling': 'call',
        'tries': 'try', 'tried': 'try', 'trying': 'try',
        'asks': 'ask', 'asked': 'ask', 'asking': 'ask',
        'needs': 'need', 'needed': 'need', 'needing': 'need',
        'feels': 'feel', 'felt': 'feel', 'feeling': 'feel',
        'becomes': 'become', 'became': 'become', 'becoming': 'become',
        'leaves': 'leave', 'left': 'leave', 'leaving': 'leave',
        'puts': 'put', 'putting': 'put',
        'means': 'mean', 'meant': 'mean', 'meaning': 'mean',
        'keeps': 'keep', 'kept': 'keep', 'keeping': 'keep',
        'lets': 'let', 'letting': 'let',
        'began': 'begin', 'begun': 'begin', 'beginning': 'begin',
        'seems': 'seem', 'seemed': 'seem', 'seeming': 'seem',
        'helps': 'help', 'helped': 'help', 'helping': 'help',
        'shows': 'show', 'showed': 'show', 'shown': 'show', 'showing': 'show',
        'hears': 'hear', 'heard': 'hear', 'hearing': 'hear',
        'runs': 'run', 'ran': 'run', 'running': 'run',
        'sits': 'sit', 'sat': 'sit', 'sitting': 'sit',
        'stands': 'stand', 'stood': 'stand', 'standing': 'stand',
        'loses': 'lose', 'lost': 'lose', 'losing': 'lose',
        'pays': 'pay', 'paid': 'pay', 'paying': 'pay',
        'meets': 'meet', 'met': 'meet', 'meeting': 'meet',
        'includes': 'include', 'included': 'include', 'including': 'include',
        'continues': 'continue', 'continued': 'continue', 'continuing': 'continue',
        'sets': 'set', 'setting': 'set',
        'learns': 'learn', 'learned': 'learn', 'learnt': 'learn', 'learning': 'learn',
        'changes': 'change', 'changed': 'change', 'changing': 'change',
        'leads': 'lead', 'led': 'lead', 'leading': 'lead',
        'understands': 'understand', 'understood': 'understand', 'understanding': 'understand',
        'watches': 'watch', 'watched': 'watch', 'watching': 'watch',
        'follows': 'follow', 'followed': 'follow', 'following': 'follow',
        'stops': 'stop', 'stopped': 'stop', 'stopping': 'stop',
        'speaks': 'speak', 'spoke': 'speak', 'spoken': 'speak', 'speaking': 'speak',
        'reads': 'read', 'reading': 'read',
        'spends': 'spend', 'spent': 'spend', 'spending': 'spend',
        'rises': 'rise', 'rose': 'rise', 'risen': 'rise', 'rising': 'rise',
        'requires': 'require', 'required': 'require', 'requiring': 'require',
        'suggests': 'suggest', 'suggested': 'suggest', 'suggesting': 'suggest',
        'reports': 'report', 'reported': 'report', 'reporting': 'report',
        'decides': 'decide', 'decided': 'decide', 'deciding': 'decide',
        'pulls': 'pull', 'pulled': 'pull', 'pulling': 'pull',
        'develops': 'develop', 'developed': 'develop', 'developing': 'develop',
        # 不规则名词复数
        'men': 'man', 'women': 'woman', 'children': 'child',
        'teeth': 'tooth', 'feet': 'foot', 'mice': 'mouse',
        'geese': 'goose', 'oxen': 'ox', 'sheep': 'sheep',
        'deer': 'deer', 'fish': 'fish', 'people': 'person',
        'data': 'datum', 'phenomena': 'phenomenon',
        'criteria': 'criterion', 'alumni': 'alumnus',
    }

    # 形容词比较级/最高级
    COMPARATIVE_FORMS: Dict[str, str] = {
        'better': 'good', 'best': 'good',
        'worse': 'bad', 'worst': 'bad',
        'more': 'much', 'most': 'much',
        'less': 'little', 'least': 'little',
        'further': 'far', 'furthest': 'far',
        'farther': 'far', 'farthest': 'far',
    }

    def __init__(self):
        self.irregular = self.IRREGULAR_FORMS.copy()
        self.irregular.update(self.COMPARATIVE_FORMS)

    def lemmatize(self, word: str, pos: str = 'n') -> str:
        """词形还原

        Args:
            word: 输入词汇
            pos: 词性 ('n'名词, 'v'动词, 'a'形容词, 'r'副词)

        Returns:
            词典形式
        """
        word_lower = word.lower()

        # 检查不规则形式
        if word_lower in self.irregular:
            return self.irregular[word_lower]

        # 根据词性应用规则
        if pos == 'v':
            return self._lemmatize_verb(word_lower)
        elif pos == 'n':
            return self._lemmatize_noun(word_lower)
        elif pos == 'a':
            return self._lemmatize_adjective(word_lower)

        return word_lower

    def _lemmatize_verb(self, word: str) -> str:
        """动词词形还原"""
        if word.endswith('ing'):
            base = word[:-3]
            if len(base) >= 2:
                # 检查双辅音（如 running -> runn -> run）
                if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in 'aeiou':
                    return base[:-1]
                if base.endswith('i'):  # lying -> lie
                    return base[:-1] + 'e'
                return base
        if word.endswith('ed'):
            base = word[:-2]
            if len(base) >= 2:
                # 检查双辅音（如 stopped -> stopp -> stop）
                if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in 'aeiou':
                    return base[:-1]
                if base.endswith('i'):  # tried -> try
                    return base[:-1] + 'e'
                return base
        if word.endswith('es'):
            return word[:-2] if len(word) > 3 else word[:-1]
        if word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        return word

    def _lemmatize_noun(self, word: str) -> str:
        """名词词形还原"""
        if word.endswith('ies') and len(word) > 4:
            return word[:-3] + 'y'
        if word.endswith('ves'):
            return word[:-3] + 'f'
        if word.endswith('ses') or word.endswith('xes') or word.endswith('zes'):
            return word[:-2]
        if word.endswith('s') and not word.endswith('ss') and not word.endswith('us'):
            return word[:-1]
        return word

    def _lemmatize_adjective(self, word: str) -> str:
        """形容词词形还原"""
        if word.endswith('er') and len(word) > 4:
            return word[:-2]
        if word.endswith('est') and len(word) > 4:
            return word[:-3]
        return word

    def lemmatize_tokens(self, tokens: List[str], pos: str = 'n') -> List[str]:
        """批量词形还原

        Args:
            tokens: token列表
            pos: 词性

        Returns:
            词形还原后的列表
        """
        return [self.lemmatize(token, pos) for token in tokens]
