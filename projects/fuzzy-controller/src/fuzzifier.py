"""
模糊化模块

将精确输入值转换为模糊值（隶属度）

模糊化过程：
1. 接收精确输入值
2. 使用隶属函数计算每个模糊集合的隶属度
3. 返回模糊化的结果
"""

import numpy as np
from typing import Dict, List, Tuple, Union
from .fuzzy_set import FuzzySet


class Fuzzifier:
    """
    模糊化器

    将精确输入值转换为模糊隶属度

    使用方法:
        # 定义输入变量的模糊集合
        temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }

        # 创建模糊化器
        fuzzifier = Fuzzifier({'temperature': temperature_sets})

        # 模糊化输入值
        fuzzy_values = fuzzifier.fuzzify({'temperature': 25})
    """

    def __init__(self, input_variables: Dict[str, Dict[str, FuzzySet]] = None):
        """
        初始化模糊化器

        参数:
            input_variables: 输入变量的模糊集合定义
                格式: {变量名: {模糊集合名: FuzzySet}}
        """
        self.input_variables = input_variables or {}

    def add_variable(self, variable_name: str, fuzzy_sets: Dict[str, FuzzySet]):
        """
        添加输入变量及其模糊集合

        参数:
            variable_name: 变量名
            fuzzy_sets: 模糊集合字典
        """
        self.input_variables[variable_name] = fuzzy_sets

    def fuzzify(self, crisp_inputs: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        模糊化精确输入

        参数:
            crisp_inputs: 精确输入值
                格式: {变量名: 精确值}

        返回:
            模糊化结果
                格式: {变量名: {模糊集合名: 隶属度}}
        """
        fuzzy_outputs = {}

        for var_name, crisp_value in crisp_inputs.items():
            if var_name not in self.input_variables:
                raise ValueError(f"未定义的输入变量: {var_name}")

            fuzzy_outputs[var_name] = {}
            fuzzy_sets = self.input_variables[var_name]

            for set_name, fuzzy_set in fuzzy_sets.items():
                membership_value = fuzzy_set.membership(crisp_value)
                fuzzy_outputs[var_name][set_name] = membership_value

        return fuzzy_outputs

    def fuzzify_single(self, variable_name: str, crisp_value: float) -> Dict[str, float]:
        """
        模糊化单个变量

        参数:
            variable_name: 变量名
            crisp_value: 精确值

        返回:
            {模糊集合名: 隶属度}
        """
        if variable_name not in self.input_variables:
            raise ValueError(f"未定义的输入变量: {variable_name}")

        fuzzy_sets = self.input_variables[variable_name]
        result = {}

        for set_name, fuzzy_set in fuzzy_sets.items():
            result[set_name] = fuzzy_set.membership(crisp_value)

        return result

    def get_variable_names(self) -> List[str]:
        """
        获取所有输入变量名

        返回:
            变量名列表
        """
        return list(self.input_variables.keys())

    def get_set_names(self, variable_name: str) -> List[str]:
        """
        获取指定变量的模糊集合名

        参数:
            variable_name: 变量名

        返回:
            模糊集合名列表
        """
        if variable_name not in self.input_variables:
            raise ValueError(f"未定义的输入变量: {variable_name}")

        return list(self.input_variables[variable_name].keys())

    def __repr__(self):
        var_names = list(self.input_variables.keys())
        return f"Fuzzifier(variables={var_names})"
