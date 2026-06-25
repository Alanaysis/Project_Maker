"""
模糊控制器测试
"""

import pytest
import numpy as np
from src.fuzzy_set import FuzzySet, TriangularMF, TrapezoidalMF
from src.rule_engine import FuzzyRule
from src.controller import FuzzyController


class TestFuzzyController:
    """模糊控制器测试"""

    def setup_method(self):
        """测试前准备"""
        # 创建温度控制器示例
        self.controller = FuzzyController(defuzzify_method='cog')

        # 定义输入变量：温度
        temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }
        self.controller.add_input_variable('temperature', temperature_sets)

        # 定义输出变量：风扇转速
        fan_speed_sets = {
            'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
            'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
            'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
        }
        self.controller.add_output_variable('fan_speed', fan_speed_sets, universe=(0, 100))

        # 添加规则
        rules = [
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
        self.controller.add_rules(rules)

    def test_add_input_variable(self):
        """测试添加输入变量"""
        variables = self.controller.get_input_variables()
        assert 'temperature' in variables

    def test_add_output_variable(self):
        """测试添加输出变量"""
        variables = self.controller.get_output_variables()
        assert 'fan_speed' in variables

    def test_add_rule(self):
        """测试添加规则"""
        rules = self.controller.get_rules()
        assert len(rules) == 3

    def test_control_cold(self):
        """测试冷温度控制"""
        output = self.controller.control({'temperature': 5})
        assert 'fan_speed' in output
        assert output['fan_speed'] < 30  # 应该是低速

    def test_control_warm(self):
        """测试温暖温度控制"""
        output = self.controller.control({'temperature': 20})
        assert 'fan_speed' in output
        assert 30 < output['fan_speed'] < 70  # 应该是中速

    def test_control_hot(self):
        """测试热温度控制"""
        output = self.controller.control({'temperature': 35})
        assert 'fan_speed' in output
        assert output['fan_speed'] > 50  # 应该是高速

    def test_control_step_by_step(self):
        """测试逐步控制"""
        results = self.controller.control_step_by_step({'temperature': 25})

        assert 'fuzzy_inputs' in results
        assert 'rule_activations' in results
        assert 'fuzzy_outputs' in results
        assert 'crisp_outputs' in results

        # 检查模糊输入
        assert 'temperature' in results['fuzzy_inputs']

        # 检查规则激活
        assert len(results['rule_activations']) == 3

        # 检查精确输出
        assert 'fan_speed' in results['crisp_outputs']

    def test_different_defuzzify_methods(self):
        """测试不同的去模糊化方法"""
        for method in ['cog', 'mom']:
            self.controller.set_defuzzify_method(method)
            output = self.controller.control({'temperature': 25})
            assert 'fan_speed' in output
            assert 0 <= output['fan_speed'] <= 100

    def test_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError):
            self.controller.control({'pressure': 100})

    def test_repr(self):
        """测试字符串表示"""
        repr_str = repr(self.controller)
        assert 'FuzzyController' in repr_str
        assert 'temperature' in repr_str
        assert 'fan_speed' in repr_str


class TestTemperatureControlExample:
    """温度控制示例测试"""

    def test_complete_example(self):
        """测试完整的温度控制示例"""
        # 创建控制器
        controller = FuzzyController()

        # 定义温度模糊集合
        temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }
        controller.add_input_variable('temperature', temperature_sets)

        # 定义风扇转速模糊集合
        fan_speed_sets = {
            'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
            'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
            'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
        }
        controller.add_output_variable('fan_speed', fan_speed_sets, universe=(0, 100))

        # 添加规则
        rules = [
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
        controller.add_rules(rules)

        # 测试不同温度
        # 注意：由于模糊逻辑的连续性，边界值可能在两个类别之间
        test_cases = [
            (5, 'slow'),      # 冷：风扇慢速
            (15, 'slow_to_medium'),  # 冷偏温：在慢速和中速之间
            (20, 'medium'),   # 温暖：风扇中速
            (25, 'medium'),   # 温暖偏热：中速
            (30, 'fast'),     # 热：风扇快速
            (35, 'fast')      # 很热：风扇快速
        ]

        for temp, expected_category in test_cases:
            output = controller.control({'temperature': temp})
            fan_speed = output['fan_speed']

            # 验证输出在有效范围内
            assert 0 <= fan_speed <= 100, f"温度 {temp}°C: 风扇转速 {fan_speed} 超出范围"

            # 验证趋势正确
            if expected_category == 'slow':
                assert fan_speed < 35, f"温度 {temp}°C: 预期低速，实际 {fan_speed}"
            elif expected_category == 'slow_to_medium':
                # 在冷和温暖之间，输出应该在低速到中速范围内
                assert 20 < fan_speed < 55, f"温度 {temp}°C: 预期低中速，实际 {fan_speed}"
            elif expected_category == 'medium':
                assert 30 < fan_speed < 70, f"温度 {temp}°C: 预期中速，实际 {fan_speed}"
            elif expected_category == 'fast':
                assert fan_speed > 50, f"温度 {temp}°C: 预期高速，实际 {fan_speed}"

    def test_monotonicity(self):
        """测试输出的单调性"""
        controller = FuzzyController()

        # 定义模糊集合
        temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }
        controller.add_input_variable('temperature', temperature_sets)

        fan_speed_sets = {
            'slow': FuzzySet('slow', TriangularMF('slow', 0, 0, 50)),
            'medium': FuzzySet('medium', TriangularMF('medium', 25, 50, 75)),
            'fast': FuzzySet('fast', TriangularMF('fast', 50, 100, 100))
        }
        controller.add_output_variable('fan_speed', fan_speed_sets, universe=(0, 100))

        rules = [
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
        controller.add_rules(rules)

        # 测试单调性：温度越高，风扇转速应该越高
        temperatures = [5, 10, 15, 20, 25, 30, 35]
        outputs = []

        for temp in temperatures:
            output = controller.control({'temperature': temp})
            outputs.append(output['fan_speed'])

        # 验证趋势：输出应该随温度增加而增加
        for i in range(len(outputs) - 1):
            # 允许小的波动，但整体趋势应该是上升的
            assert outputs[i] <= outputs[i + 1] + 5, \
                f"温度从 {temperatures[i]}°C 到 {temperatures[i+1]}°C，" \
                f"风扇转速从 {outputs[i]} 降到 {outputs[i+1]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
