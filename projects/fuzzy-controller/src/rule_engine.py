"""
模糊规则引擎模块

实现模糊规则的定义、存储和推理

模糊规则格式:
    IF <前提> THEN <结论>

前提可以包含:
    - IS 操作: x IS A
    - AND 操作: x IS A AND y IS B
    - OR 操作: x IS A OR y IS B
    - NOT 操作: x IS NOT A

推理方法:
    - Mamdani 推理
    - Sugeno 推理
"""

import numpy as np
from typing import Dict, List, Tuple, Union, Callable
from .fuzzy_set import FuzzySet


class FuzzyRule:
    """
    模糊规则类

    表示一条模糊规则: IF antecedent THEN consequent

    示例:
        rule = FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')],
            operator='AND'
        )
    """

    def __init__(self, antecedent: List[Tuple[str, str, str]],
                 consequent: List[Tuple[str, str]],
                 operator: str = 'AND',
                 weight: float = 1.0):
        """
        初始化模糊规则

        参数:
            antecedent: 前提条件列表
                每个元素: (变量名, 模糊集合名, 操作符)
                操作符: 'IS', 'IS_NOT'
            consequent: 结论列表
                每个元素: (变量名, 模糊集合名)
            operator: 条件之间的连接符 ('AND', 'OR')
            weight: 规则权重 (0-1)
        """
        self.antecedent = antecedent
        self.consequent = consequent
        self.operator = operator.upper()
        self.weight = weight

    def evaluate(self, fuzzy_inputs: Dict[str, Dict[str, float]]) -> float:
        """
        评估规则的前提条件

        参数:
            fuzzy_inputs: 模糊输入
                格式: {变量名: {模糊集合名: 隶属度}}

        返回:
            规则激活强度 (0-1)
        """
        if not self.antecedent:
            return 1.0

        activation_levels = []

        for var_name, set_name, operator in self.antecedent:
            if var_name not in fuzzy_inputs:
                raise ValueError(f"未找到输入变量: {var_name}")

            if set_name not in fuzzy_inputs[var_name]:
                raise ValueError(f"未找到模糊集合: {set_name}")

            membership = fuzzy_inputs[var_name][set_name]

            if operator.upper() == 'IS_NOT':
                membership = 1.0 - membership

            activation_levels.append(membership)

        # 使用连接符计算激活强度
        if self.operator == 'AND':
            activation = min(activation_levels)
        elif self.operator == 'OR':
            activation = max(activation_levels)
        else:
            raise ValueError(f"不支持的操作符: {self.operator}")

        # 应用权重
        activation *= self.weight

        return activation

    def __repr__(self):
        antecedent_str = f" {self.operator} ".join(
            [f"{var} {op} {set_name}" for var, set_name, op in self.antecedent]
        )
        consequent_str = ", ".join(
            [f"{var} IS {set_name}" for var, set_name in self.consequent]
        )
        return f"IF {antecedent_str} THEN {consequent_str}"


class RuleEngine:
    """
    模糊规则引擎

    管理和执行模糊规则集合

    使用方法:
        engine = RuleEngine()

        # 添加规则
        engine.add_rule(FuzzyRule(...))

        # 执行推理
        results = engine.infer(fuzzy_inputs, output_sets)
    """

    def __init__(self, rules: List[FuzzyRule] = None):
        """
        初始化规则引擎

        参数:
            rules: 初始规则列表
        """
        self.rules = rules or []

    def add_rule(self, rule: FuzzyRule):
        """
        添加规则

        参数:
            rule: 模糊规则
        """
        self.rules.append(rule)

    def remove_rule(self, index: int):
        """
        移除规则

        参数:
            index: 规则索引
        """
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
        else:
            raise IndexError(f"规则索引超出范围: {index}")

    def clear_rules(self):
        """清空所有规则"""
        self.rules.clear()

    def infer(self, fuzzy_inputs: Dict[str, Dict[str, float]],
              output_variables: Dict[str, Dict[str, FuzzySet]]) -> Dict[str, Dict[str, float]]:
        """
        执行模糊推理

        参数:
            fuzzy_inputs: 模糊输入
                格式: {变量名: {模糊集合名: 隶属度}}
            output_variables: 输出变量的模糊集合定义
                格式: {变量名: {模糊集合名: FuzzySet}}

        返回:
            推理结果
                格式: {变量名: {模糊集合名: 裁剪后的隶属度}}
        """
        # 初始化输出结果
        results = {}
        for var_name, fuzzy_sets in output_variables.items():
            results[var_name] = {}
            for set_name in fuzzy_sets:
                results[var_name][set_name] = 0.0

        # 评估每条规则
        for rule in self.rules:
            # 计算规则激活强度
            activation = rule.evaluate(fuzzy_inputs)

            # 应用激活强度到结论
            for var_name, set_name in rule.consequent:
                if var_name in results and set_name in results[var_name]:
                    # 取最大值 (模糊 OR)
                    results[var_name][set_name] = max(
                        results[var_name][set_name],
                        activation
                    )

        return results

    def infer_mamdani(self, fuzzy_inputs: Dict[str, Dict[str, float]],
                      output_variables: Dict[str, Dict[str, FuzzySet]],
                      x_range: Dict[str, Tuple[float, float]] = None,
                      num_points: int = 100) -> Dict[str, np.ndarray]:
        """
        Mamdani 推理方法

        参数:
            fuzzy_inputs: 模糊输入
            output_variables: 输出变量的模糊集合
            x_range: 输出变量的论域范围
            num_points: 采样点数

        返回:
            模糊输出
                格式: {变量名: 裁剪后的隶属函数值数组}
        """
        if x_range is None:
            raise ValueError("Mamdani推理需要指定 x_range")

        # 计算每条规则的激活强度
        rule_activations = []
        for rule in self.rules:
            activation = rule.evaluate(fuzzy_inputs)
            rule_activations.append((rule, activation))

        # 对每个输出变量进行推理
        outputs = {}
        for var_name, fuzzy_sets in output_variables.items():
            if var_name not in x_range:
                raise ValueError(f"未指定变量 {var_name} 的论域范围")

            x_min, x_max = x_range[var_name]
            x = np.linspace(x_min, x_max, num_points)

            # 初始化输出隶属函数
            output_mf = np.zeros(num_points)

            # 应用每条规则的裁剪
            for rule, activation in rule_activations:
                for rule_var, set_name in rule.consequent:
                    if rule_var == var_name and set_name in fuzzy_sets:
                        # 获取模糊集合的隶属函数值
                        fuzzy_set = fuzzy_sets[set_name]
                        mf_values = fuzzy_set.membership(x)

                        # 裁剪 (取最小值)
                        clipped = np.minimum(mf_values, activation)

                        # 聚合 (取最大值)
                        output_mf = np.maximum(output_mf, clipped)

            outputs[var_name] = output_mf

        return outputs, x

    def infer_sugeno(self, fuzzy_inputs: Dict[str, Dict[str, float]],
                     crisp_inputs: Dict[str, float],
                     sugeno_params: Dict[str, List[Tuple[float, ...]]],
                     ) -> Tuple[float, Dict[str, float]]:
        """
        Sugeno (TSK) 推理方法

        Sugeno 模型的结论部分是输入变量的线性函数，而非模糊集合。
        对于零阶 Sugeno，结论为常数；对于一阶 Sugeno，结论为线性函数。

        参数:
            fuzzy_inputs: 模糊输入
                格式: {变量名: {模糊集合名: 隶属度}}
            crisp_inputs: 精确输入值 (用于计算 Sugeno 结论函数)
                格式: {变量名: 精确值}
            sugeno_params: 每条规则的 Sugeno 参数
                格式: {输出变量名: [(p0, p1, ...), ...]}
                每个元组 (p0, p1, ..., pn) 对应一条规则：
                f = p0 + p1*x1 + p2*x2 + ...
                其中 xi 是精确输入值

        返回:
            (加权平均输出, 每条规则的详情)
        """
        weighted_sum = 0.0
        weight_total = 0.0
        rule_details = []

        for i, rule in enumerate(self.rules):
            # 计算规则激活强度
            activation = rule.evaluate(fuzzy_inputs)

            # 计算每条规则的 Sugeno 输出
            rule_outputs = {}
            for var_name, params_list in sugeno_params.items():
                if i < len(params_list):
                    params = params_list[i]
                    # 零阶: f = p0
                    # 一阶: f = p0 + p1*x1 + p2*x2 + ...
                    output_value = params[0]
                    input_values = list(crisp_inputs.values())
                    for j in range(1, len(params)):
                        if j - 1 < len(input_values):
                            output_value += params[j] * input_values[j - 1]
                    rule_outputs[var_name] = output_value

            rule_details.append({
                'rule': str(rule),
                'activation': activation,
                'outputs': rule_outputs
            })

            weighted_sum += activation
            weight_total += activation

        # 加权平均去模糊化
        if weight_total == 0:
            result = {}
            for var_name in sugeno_params:
                result[var_name] = 0.0
            return result, rule_details

        # 计算加权平均
        result = {}
        for var_name in sugeno_params:
            numerator = 0.0
            for i, detail in enumerate(rule_details):
                if var_name in detail['outputs']:
                    numerator += detail['activation'] * detail['outputs'][var_name]
            result[var_name] = numerator / weight_total

        return result, rule_details

    def get_rules(self) -> List[FuzzyRule]:
        """
        获取所有规则

        返回:
            规则列表
        """
        return self.rules.copy()

    def __len__(self):
        return len(self.rules)

    def __repr__(self):
        return f"RuleEngine(rules={len(self.rules)})"
