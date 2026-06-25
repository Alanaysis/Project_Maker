"""词干提取模块 - Stemmer

提供英文词干提取功能，将词汇还原为词干形式。
使用 Porter Stemmer 算法实现。
"""

from typing import List


class PorterStemmer:
    """Porter 词干提取器

    简化版 Porter Stemmer 实现，处理常见英文词缀。
    """

    def stem(self, word: str) -> str:
        """提取词干

        Args:
            word: 输入词汇

        Returns:
            词干形式
        """
        if len(word) <= 2:
            return word

        word = word.lower()

        # Step 1: 处理复数和过去式
        word = self._step1(word)

        # Step 2: 处理 -tion, -ence 等
        word = self._step2(word)

        # Step 3: 处理 -ize, -ful 等
        word = self._step3(word)

        return word

    def _step1(self, word: str) -> str:
        """处理复数和过去式"""
        if word.endswith('sses'):
            return word[:-2]
        if word.endswith('ies'):
            return word[:-2]
        if word.endswith('ss'):
            return word
        if word.endswith('s'):
            return word[:-1]
        if word.endswith('eed'):
            return word[:-1]
        if word.endswith('ed') and self._contains_vowel(word[:-2]):
            stem = word[:-2]
            return self._remove_double_consonant(stem)
        if word.endswith('ing') and self._contains_vowel(word[:-3]):
            stem = word[:-3]
            return self._remove_double_consonant(stem)
        return word

    def _remove_double_consonant(self, word: str) -> str:
        """移除双辅音（如 runn -> run）"""
        if len(word) >= 2 and word[-1] == word[-2] and word[-1] not in 'aeiou':
            return word[:-1]
        return word

    def _step2(self, word: str) -> str:
        """处理 -tion, -ence 等后缀"""
        replacements = {
            'ational': 'ate',
            'tional': 'tion',
            'enci': 'ence',
            'anci': 'ance',
            'izer': 'ize',
            'alli': 'al',
            'entli': 'ent',
            'eli': 'e',
            'ousli': 'ous',
            'ization': 'ize',
            'ation': 'ate',
            'ator': 'ate',
            'alism': 'al',
            'iveness': 'ive',
            'fulness': 'ful',
            'ousness': 'ous',
            'aliti': 'al',
            'iviti': 'ive',
            'biliti': 'ble',
        }
        for suffix, replacement in replacements.items():
            if word.endswith(suffix) and self._contains_vowel(word[:-len(suffix)]):
                return word[:-len(suffix)] + replacement
        return word

    def _step3(self, word: str) -> str:
        """处理 -ize, -ful 等后缀"""
        replacements = {
            'icate': 'ic',
            'ative': '',
            'alize': 'al',
            'iciti': 'ic',
            'ical': 'ic',
            'ful': '',
            'ness': '',
        }
        for suffix, replacement in replacements.items():
            if word.endswith(suffix) and self._contains_vowel(word[:-len(suffix)]):
                return word[:-len(suffix)] + replacement
        return word

    def _contains_vowel(self, word: str) -> bool:
        """检查是否包含元音"""
        vowels = 'aeiou'
        return any(c in vowels for c in word)

    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """批量提取词干

        Args:
            tokens: token列表

        Returns:
            词干列表
        """
        return [self.stem(token) for token in tokens]
