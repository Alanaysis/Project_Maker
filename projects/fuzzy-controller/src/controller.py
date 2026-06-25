"""
模糊控制器模块

将所有组件组合成完整的模糊控制系统

核心循环:
输入 → 模糊化 → 规则推理 → 去模糊化 → 输出

支持两种推理方法:
- Mamdani 推理: 结论部分使用模糊集合
- Sugeno (TSK) 推理: 结论部分使用线性函数
"""

import numpy as np
from typing import Dict, List, Tuple, Union
from .fuzzy_set import FuzzySet
from .fuzzifier import Fuzzifier
from .rule_engine import RuleEngine, FuzzyRule
from .defuzzifier import Defuzzifier


class FuzzyController:
    """
    模糊控制器

    实现完整的模糊逻辑控制系统

    使用方法:
        # 1. 定义输入变量的模糊集合
        temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }

        # 2. 定义输出变量的模糊集合
        fan_speed_sets = {
            'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
            'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
            'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
        }

        # 3. 创建控制器
        controller = FuzzyController()

        # 4. 添加输入变量
        controller.add_input_variable('temperature', temperature_sets)

        # 5. 添加输出变量
        controller.add_output_variable('fan_speed', fan_speed_sets)

        # 6. 添加规则
        controller.add_rule(FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')]
        ))

        # 7. 控制
        output = controller.control({'temperature': 25})
        print(output)  # {'fan_speed': 精确值}
    """

    def __init__(self, defuzzify_method: str = 'cog'):
        """
        初始化模糊控制器

        参数:
            defuzzify_method: 去模糊化方法 ('cog', 'mom', 'cos', 'wa')
        """
        self.fuzzifier = Fuzzifier()
        self.rule_engine = RuleEngine()
        self.defuzzifier = Defuzzifier(defuzzify_method)

        # 存储输入和输出变量的模糊集合
        self.input_variables = {}
        self.output_variables = {}

        # 存储输出变量的论域范围
        self.output_universes = {}

    def add_input_variable(self, variable_name: str, fuzzy_sets: Dict[str, FuzzySet]):
        """
        添加输入变量及其模糊集合

        参数:
            variable_name: 变量名
            fuzzy_sets: 模糊集合字典
        """
        self.input_variables[variable_name] = fuzzy_sets
        self.fuzzifier.add_variable(variable_name, fuzzy_sets)

    def add_output_variable(self, variable_name: str, fuzzy_sets: Dict[str, FuzzySet],
                            universe: Tuple[float, float] = None):
        """
        添加输出变量及其模糊集合

        参数:
            variable_name: 变量名
            fuzzy_sets: 模糊集合字典
            universe: 论域范围 (min, max)
        """
        self.output_variables[variable_name] = fuzzy_sets

        if universe is not None:
            self.output_universes[variable_name] = universe

    def add_rule(self, rule: FuzzyRule):
        """
        添加模糊规则

        参数:
            rule: 模糊规则
        """
        self.rule_engine.add_rule(rule)

    def add_rules(self, rules: List[FuzzyRule]):
        """
        批量添加模糊规则

        参数:
            rules: 规则列表
        """
        for rule in rules:
            self.rule_engine.add_rule(rule)

    def set_defuzzify_method(self, method: str):
        """
        设置去模糊化方法

        参数:
            method: 方法名称
        """
        self.defuzzifier.set_method(method)

    def control(self, crisp_inputs: Dict[str, float],
                output_x_ranges: Dict[str, Tuple[float, float]] = None,
                num_points: int = 100) -> Dict[str, float]:
        """
        执行模糊控制

        参数:
            crisp_inputs: 精确输入值
                格式: {变量名: 精确值}
            output_x_ranges: 输出变量的论域范围
                格式: {变量名: (min, max)}
            num_points: 采样点数

        返回:
            精确输出值
                格式: {变量名: 精确值}
        """
        # 使用预定义的论域范围（如果未指定）
        if output_x_ranges is None:
            output_x_ranges = self.output_universes

        if not output_x_ranges:
            raise ValueError("必须指定输出变量的论域范围")

        # 步骤1: 模糊化
        fuzzy_inputs = self.fuzzifier.fuzzify(crisp_inputs)

        # 步骤2: 规则推理
        # 使用Mamdani推理获取模糊输出
        fuzzy_outputs, x_arrays = self.rule_engine.infer_mamdani(
            fuzzy_inputs,
            self.output_variables,
            output_x_ranges,
            num_points
        )

        # 步骤3: 去模糊化
        crisp_outputs = {}
        for var_name, mf_values in fuzzy_outputs.items():
            if isinstance(x_arrays, dict):
                x = x_arrays[var_name]
            else:
                x = x_arrays
            crisp_outputs[var_name] = self.defuzzifier.defuzzify(x, mf_values)

        return crisp_outputs

    def control_sugeno(self, crisp_inputs: Dict[str, float],
                       sugeno_params: Dict[str, List[Tuple[float, ...]]] = None,
                       ) -> Tuple[Dict[str, float], List]:
        """
        使用 Sugeno (TSK) 推理方法执行模糊控制

        Sugeno 模型的结论部分是输入变量的线性函数:
        - 零阶: f = p0
        - 一阶: f = p0 + p1*x1 + p2*x2 + ...

        参数:
            crisp_inputs: 精确输入值
                格式: {变量名: 精确值}
            sugeno_params: 每条规则的 Sugeno 参数
                格式: {输出变量名: [(p0, p1, ...), ...]}

        返回:
            (精确输出值, 规则详情)
        """
        # 模糊化
        fuzzy_inputs = self.fuzzifier.fuzzify(crisp_inputs)

        # Sugeno 推理
        result, rule_details = self.rule_engine.infer_sugeno(
            fuzzy_inputs, crisp_inputs, sugeno_params
        )

        return result, rule_details

    def control_step_by_step(self, crisp_inputs: Dict[str, float],
                             output_x_ranges: Dict[str, Tuple[float, float]] = None,
                             num_points: int = 100) -> Dict:
        """
        逐步执行模糊控制 (用于调试)

        参数:
            crisp_inputs: 精确输入值
            output_x_ranges: 输出变量的论域范围
            num_points: 采样点数

        返回:
            每一步的结果
        """
        if output_x_ranges is None:
            output_x_ranges = self.output_universes

        results = {}

        # 步骤1: 模糊化
        fuzzy_inputs = self.fuzzifier.fuzzify(crisp_inputs)
        results['fuzzy_inputs'] = fuzzy_inputs

        # 步骤2: 规则激活
        rule_activations = []
        for rule in self.rule_engine.get_rules():
            activation = rule.evaluate(fuzzy_inputs)
            rule_activations.append({
                'rule': str(rule),
                'activation': activation
            })
        results['rule_activations'] = rule_activations

        # 步骤3: 推理
        fuzzy_outputs, x_arrays = self.rule_engine.infer_mamdani(
            fuzzy_inputs,
            self.output_variables,
            output_x_ranges,
            num_points
        )
        results['fuzzy_outputs'] = fuzzy_outputs

        # 步骤4: 去模糊化
        crisp_outputs = {}
        for var_name, mf_values in fuzzy_outputs.items():
            if isinstance(x_arrays, dict):
                x = x_arrays[var_name]
            else:
                x = x_arrays
            crisp_outputs[var_name] = self.defuzzifier.defuzzify(x, mf_values)
        results['crisp_outputs'] = crisp_outputs

        return results

    def get_input_variables(self) -> Dict[str, Dict[str, FuzzySet]]:
        """
        获取所有输入变量

        返回:
            输入变量字典
        """
        return self.input_variables.copy()

    def get_output_variables(self) -> Dict[str, Dict[str, FuzzySet]]:
        """
        获取所有输出变量

        返回:
            输出变量字典
        """
        return self.output_variables.copy()

    def get_rules(self) -> List[FuzzyRule]:
        """
        获取所有规则

        返回:
            规则列表
        """
        return self.rule_engine.get_rules()

    def __repr__(self):
        input_vars = list(self.input_variables.keys())
        output_vars = list(self.output_variables.keys())
        n_rules = len(self.rule_engine)
        return f"FuzzyController(inputs={input_vars}, outputs={output_vars}, rules={n_rules})"
