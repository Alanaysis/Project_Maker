"""
Sugeno 推理测试
"""

import pytest
import numpy as np
from src.fuzzy_set import FuzzySet, TriangularMF
from src.rule_engine import RuleEngine, FuzzyRule
from src.controller import FuzzyController


class TestSugenoInference:
    """Sugeno 推理测试"""

    def setup_method(self):
        """测试前准备"""
        self.engine = RuleEngine()

        # 添加简单规则
        self.engine.add_rule(FuzzyRule(
            antecedent=[('x', 'small', 'IS')],
            consequent=[('y', 'low')]
        ))
        self.engine.add_rule(FuzzyRule(
            antecedent=[('x', 'large', 'IS')],
            consequent=[('y', 'high')]
        ))

    def test_zero_order_sugeno(self):
        """测试零阶 Sugeno (结论为常数)"""
        fuzzy_inputs = {
            'x': {'small': 0.7, 'large': 0.3}
        }
        crisp_inputs = {'x': 5.0}

        # 零阶参数: 规则1输出=10, 规则2输出=50
        sugeno_params = {
            'y': [(10.0,), (50.0,)]
        }

        result, details = self.engine.infer_sugeno(fuzzy_inputs, crisp_inputs, sugeno_params)

        # 加权平均: (0.7*10 + 0.3*50) / (0.7+0.3) = (7+15)/1 = 22
        assert abs(result['y'] - 22.0) < 1e-10
        assert len(details) == 2

    def test_first_order_sugeno(self):
        """测试一阶 Sugeno (结论为线性函数)"""
        fuzzy_inputs = {
            'x': {'small': 0.6, 'large': 0.4}
        }
        crisp_inputs = {'x': 5.0}

        # 一阶参数: f = p0 + p1*x
        # 规则1: f = 2 + 0.5*5 = 4.5
        # 规则2: f = 1 + 1.0*5 = 6.0
        sugeno_params = {
            'y': [(2.0, 0.5), (1.0, 1.0)]
        }

        result, details = self.engine.infer_sugeno(fuzzy_inputs, crisp_inputs, sugeno_params)

        # 加权平均: (0.6*4.5 + 0.4*6.0) / (0.6+0.4) = (2.7+2.4)/1 = 5.1
        assert abs(result['y'] - 5.1) < 1e-10

    def test_sugeno_zero_activation(self):
        """测试零激活情况"""
        fuzzy_inputs = {
            'x': {'small': 0.0, 'large': 0.0}
        }
        crisp_inputs = {'x': 5.0}

        sugeno_params = {
            'y': [(10.0,), (50.0,)]
        }

        result, details = self.engine.infer_sugeno(fuzzy_inputs, crisp_inputs, sugeno_params)
        assert result['y'] == 0.0

    def test_sugeno_single_rule(self):
        """测试单条规则的 Sugeno 推理"""
        engine = RuleEngine()
        engine.add_rule(FuzzyRule(
            antecedent=[('temp', 'hot', 'IS')],
            consequent=[('output', 'high')]
        ))

        fuzzy_inputs = {'temp': {'hot': 0.8, 'cold': 0.2}}
        crisp_inputs = {'temp': 30.0}
        sugeno_params = {'output': [(5.0, 0.1)]}

        result, details = engine.infer_sugeno(fuzzy_inputs, crisp_inputs, sugeno_params)

        # f = 5.0 + 0.1*30 = 8.0, 权重=0.8, 结果=8.0
        assert abs(result['output'] - 8.0) < 1e-10


class TestControllerSugeno:
    """控制器 Sugeno 推理测试"""

    def test_control_sugeno(self):
        """测试控制器的 Sugeno 控制"""
        controller = FuzzyController()

        # 定义输入
        temp_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }
        controller.add_input_variable('temperature', temp_sets)

        # 添加规则
        controller.add_rule(FuzzyRule(
            antecedent=[('temperature', 'cold', 'IS')],
            consequent=[('power', 'low')]
        ))
        controller.add_rule(FuzzyRule(
            antecedent=[('temperature', 'warm', 'IS')],
            consequent=[('power', 'medium')]
        ))
        controller.add_rule(FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('power', 'high')]
        ))

        # 零阶 Sugeno 参数
        sugeno_params = {
            'power': [(20.0,), (50.0,), (90.0,)]
        }

        result, details = controller.control_sugeno(
            {'temperature': 25},
            sugeno_params
        )

        assert 'power' in result
        assert 0 <= result['power'] <= 100
        assert len(details) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
