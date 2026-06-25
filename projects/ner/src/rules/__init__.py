"""
基于规则的 NER 模块
===================

提供两种基于规则的命名实体识别方法:
- RegexNER: 基于正则表达式的实体识别
- DictNER: 基于词典的实体识别
"""

from .regex_ner import RegexNER
from .dict_ner import DictNER

__all__ = ["RegexNER", "DictNER"]
