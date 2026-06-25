"""
规则引擎测试
"""

import pytest
import numpy as np
from src.fuzzy_set import FuzzySet, TriangularMF, TrapezoidalMF
from src.rule_engine import RuleEngine, FuzzyRule


class TestFuzzyRule:
    """模糊规则测试"""

    def test_simple_rule(self):
        """测试简单规则"""
        rule = FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')]
        )

        fuzzy_inputs = {
            'temperature': {
                'cold': 0.0,
                'warm': 0.5,
                'hot': 0.8
            }
        }

        activation = rule.evaluate(fuzzy_inputs)
        assert activation == 0.8

    def test_and_rule(self):
        """测试AND规则"""
        rule = FuzzyRule(
            antecedent=[
                ('temperature', 'hot', 'IS'),
                ('humidity', 'humid', 'IS')
            ],
            consequent=[('fan_speed', 'fast')],
            operator='AND'
        )

        fuzzy_inputs = {
            'temperature': {
                'hot': 0.8
            },
            'humidity': {
                'humid': 0.6
            }
        }

        activation = rule.evaluate(fuzzy_inputs)
        assert activation == 0.6  # min(0.8, 0.6)

    def test_or_rule(self):
        """测试OR规则"""
        rule = FuzzyRule(
            antecedent=[
                ('temperature', 'hot', 'IS'),
                ('humidity', 'humid', 'IS')
            ],
            consequent=[('fan_speed', 'fast')],
            operator='OR'
        )

        fuzzy_inputs = {
            'temperature': {
                'hot': 0.8
            },
            'humidity': {
                'humid': 0.6
            }
        }

        activation = rule.evaluate(fuzzy_inputs)
        assert activation == 0.8  # max(0.8, 0.6)

    def test_not_rule(self):
        """测试NOT规则"""
        rule = FuzzyRule(
            antecedent=[('temperature', 'cold', 'IS_NOT')],
            consequent=[('fan_speed', 'slow')]
        )

        fuzzy_inputs = {
            'temperature': {
                'cold': 0.3
            }
        }

        activation = rule.evaluate(fuzzy_inputs)
        assert activation == 0.7  # 1 - 0.3

    def test_weighted_rule(self):
        """测试带权重的规则"""
        rule = FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[('fan_speed', 'fast')],
            weight=0.5
        )

        fuzzy_inputs = {
            'temperature': {
                'hot': 0.8
            }
        }

        activation = rule.evaluate(fuzzy_inputs)
        assert activation == 0.4  # 0.8 * 0.5

    def test_missing_variable(self):
        """测试缺少变量"""
        rule = FuzzyRule(
            antecedent=[('pressure', 'high', 'IS')],
            consequent=[('fan_speed', 'fast')]
        )

        fuzzy_inputs = {
            'temperature': {
                'hot': 0.8
            }
        }

        with pytest.raises(ValueError, match="未找到输入变量"):
            rule.evaluate(fuzzy_inputs)

    def test_missing_set(self):
        """测试缺少模糊集合"""
        rule = FuzzyRule(
            antecedent=[('temperature', 'medium', 'IS')],
            consequent=[('fan_speed', 'fast')]
        )

        fuzzy_inputs = {
            'temperature': {
                'cold': 0.0,
                'warm': 0.5,
                'hot': 0.8
            }
        }

        with pytest.raises(ValueError, match="未找到模糊集合"):
            rule.evaluate(fuzzy_inputs)


class TestRuleEngine:
    """规则引擎测试"""

    def setup_method(self):
        """测试前准备"""
        # 创建模糊集合
        self.temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }

        self.fan_speed_sets = {
            'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
            'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
            'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
        }

        # 创建规则
        self.rules = [
            FuzzyRule(
                antecedent=[('temperature', 'cold', 'IS')],
                consequent=[('fan_speed', 'slow')]
            ),
            FuzzyRule(
                antecedent=[('temperature', 'warm', 'IS')],
                consequent=[('fan_speed', 'medium')]
            ),
            FuzzyRule(
                antecedent=[('temperature', 'hot', 'IS')],
                consequent=[('fan_speed', 'fast')]
            )
        ]

        # 创建规则引擎
        self.engine = RuleEngine(self.rules)

    def test_add_rule(self):
        """测试添加规则"""
        engine = RuleEngine()
        assert len(engine) == 0

        engine.add_rule(self.rules[0])
        assert len(engine) == 1

    def test_remove_rule(self):
        """测试移除规则"""
        engine = RuleEngine(self.rules)
        assert len(engine) == 3

        engine.remove_rule(1)
        assert len(engine) == 2

    def test_remove_rule_invalid_index(self):
        """测试移除无效索引的规则"""
        with pytest.raises(IndexError):
            self.engine.remove_rule(10)

    def test_clear_rules(self):
        """测试清空规则"""
        self.engine.clear_rules()
        assert len(self.engine) == 0

    def test_infer(self):
        """测试推理"""
        fuzzy_inputs = {
            'temperature': {
                'cold': 0.0,
                'warm': 0.5,
                'hot': 0.5
            }
        }

        output_variables = {
            'fan_speed': self.fan_speed_sets
        }

        results = self.engine.infer(fuzzy_inputs, output_variables)

        assert 'fan_speed' in results
        assert 'slow' in results['fan_speed']
        assert 'medium' in results['fan_speed']
        assert 'fast' in results['fan_speed']

        # warm=0.5 激活 medium 规则
        assert results['fan_speed']['medium'] == 0.5
        # hot=0.5 激活 fast 规则
        assert results['fan_speed']['fast'] == 0.5

    def test_infer_mamdani(self):
        """测试Mamdani推理"""
        fuzzy_inputs = {
            'temperature': {
                'cold': 0.0,
                'warm': 0.5,
                'hot': 0.5
            }
        }

        output_variables = {
            'fan_speed': self.fan_speed_sets
        }

        x_range = {'fan_speed': (0, 100)}
        fuzzy_outputs, x = self.engine.infer_mamdani(
            fuzzy_inputs, output_variables, x_range, num_points=100
        )

        assert 'fan_speed' in fuzzy_outputs
        assert len(fuzzy_outputs['fan_speed']) == 100
        assert len(x) == 100

    def test_get_rules(self):
        """测试获取规则"""
        rules = self.engine.get_rules()

        assert len(rules) == 3
        assert rules is not self.rules  # 返回副本

    def test_multiple_consequents(self):
        """测试多结论规则"""
        rule = FuzzyRule(
            antecedent=[('temperature', 'hot', 'IS')],
            consequent=[
                ('fan_speed', 'fast'),
                ('ac_power', 'high')
            ]
        )

        engine = RuleEngine([rule])

        fuzzy_inputs = {
            'temperature': {
                'hot': 0.8
            }
        }

        output_variables = {
            'fan_speed': self.fan_speed_sets,
            'ac_power': {
                'low': FuzzySet('low', TriangularMF('low', 0, 0, 50)),
                'high': FuzzySet('high', TriangularMF('high', 50, 100, 100))
            }
        }

        results = engine.infer(fuzzy_inputs, output_variables)

        assert results['fan_speed']['fast'] == 0.8
        assert results['ac_power']['high'] == 0.8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
