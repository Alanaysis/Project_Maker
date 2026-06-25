"""
模糊化器测试
"""

import pytest
import numpy as np
from src.fuzzy_set import FuzzySet, TriangularMF, TrapezoidalMF
from src.fuzzifier import Fuzzifier


class TestFuzzifier:
    """模糊化器测试"""

    def setup_method(self):
        """测试前准备"""
        # 创建温度模糊集合
        self.temperature_sets = {
            'cold': FuzzySet('cold', TriangularMF('cold', 0, 0, 20)),
            'warm': FuzzySet('warm', TriangularMF('warm', 10, 20, 30)),
            'hot': FuzzySet('hot', TriangularMF('hot', 20, 40, 40))
        }

        # 创建湿度模糊集合
        self.humidity_sets = {
            'dry': FuzzySet('dry', TrapezoidalMF('dry', 0, 0, 20, 40)),
            'normal': FuzzySet('normal', TrapezoidalMF('normal', 20, 40, 60, 80)),
            'humid': FuzzySet('humid', TrapezoidalMF('humid', 60, 80, 100, 100))
        }

        # 创建模糊化器
        self.fuzzifier = Fuzzifier({
            'temperature': self.temperature_sets,
            'humidity': self.humidity_sets
        })

    def test_fuzzify_single_variable(self):
        """测试单变量模糊化"""
        result = self.fuzzifier.fuzzify({'temperature': 25})

        assert 'temperature' in result
        assert 'cold' in result['temperature']
        assert 'warm' in result['temperature']
        assert 'hot' in result['temperature']

        # 25度的隶属度：
        # cold(25): TriangularMF(0,0,20) -> 25>20, 所以cold=0
        # warm(25): TriangularMF(10,20,30) -> (30-25)/(30-20) = 0.5
        # hot(25): TriangularMF(20,40,40) -> (25-20)/(40-20) = 0.25
        assert result['temperature']['cold'] == 0.0
        assert abs(result['temperature']['warm'] - 0.5) < 1e-10
        assert abs(result['temperature']['hot'] - 0.25) < 1e-10

    def test_fuzzify_multiple_variables(self):
        """测试多变量模糊化"""
        result = self.fuzzifier.fuzzify({
            'temperature': 25,
            'humidity': 50
        })

        assert 'temperature' in result
        assert 'humidity' in result

        # 检查温度
        assert result['temperature']['cold'] == 0.0

        # 检查湿度
        assert abs(result['humidity']['normal'] - 1.0) < 1e-10

    def test_fuzzify_single(self):
        """测试单变量模糊化方法"""
        result = self.fuzzifier.fuzzify_single('temperature', 15)

        assert 'cold' in result
        assert 'warm' in result
        assert 'hot' in result

        # 15度：cold=0.25, warm=0.5, hot=0
        assert abs(result['cold'] - 0.25) < 1e-10
        assert abs(result['warm'] - 0.5) < 1e-10
        assert result['hot'] == 0.0

    def test_undefined_variable(self):
        """测试未定义的变量"""
        with pytest.raises(ValueError, match="未定义的输入变量"):
            self.fuzzifier.fuzzify({'pressure': 100})

    def test_get_variable_names(self):
        """测试获取变量名"""
        names = self.fuzzifier.get_variable_names()

        assert 'temperature' in names
        assert 'humidity' in names
        assert len(names) == 2

    def test_get_set_names(self):
        """测试获取模糊集合名"""
        names = self.fuzzifier.get_set_names('temperature')

        assert 'cold' in names
        assert 'warm' in names
        assert 'hot' in names
        assert len(names) == 3

    def test_add_variable(self):
        """测试添加变量"""
        new_fuzzifier = Fuzzifier()
        new_fuzzifier.add_variable('temperature', self.temperature_sets)

        assert 'temperature' in new_fuzzifier.get_variable_names()

    def test_boundary_values(self):
        """测试边界值"""
        result = self.fuzzifier.fuzzify_single('temperature', 0)
        assert result['cold'] == 1.0

        result = self.fuzzifier.fuzzify_single('temperature', 40)
        assert result['hot'] == 1.0

    def test_out_of_range(self):
        """测试超出范围的值"""
        # -10度：在冷的范围内（TriangularMF(0,0,20)在x<0时为0）
        # 但TriangularMF(0,0,20)只在[0,20]有定义，所以-10度的cold隶属度为0
        result = self.fuzzifier.fuzzify_single('temperature', -10)
        assert result['cold'] == 0.0  # x<0 不在 [0,20] 范围内
        assert result['warm'] == 0.0
        assert result['hot'] == 0.0

        # 50度：超出hot的范围，但TriangularMF(20,40,40)在x>40时为0
        result = self.fuzzifier.fuzzify_single('temperature', 50)
        assert result['cold'] == 0.0
        assert result['warm'] == 0.0
        assert result['hot'] == 0.0  # x>40 不在 [20,40] 范围内


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
