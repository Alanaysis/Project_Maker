"""
去模糊化器测试
"""

import pytest
import numpy as np
from src.defuzzifier import Defuzzifier


class TestDefuzzifier:
    """去模糊化器测试"""

    def test_center_of_gravity(self):
        """测试重心法"""
        defuzzifier = Defuzzifier('cog')

        # 创建一个简单的隶属函数
        x = np.linspace(0, 10, 100)
        mf_values = np.zeros_like(x)

        # 三角形隶属函数，峰值在5
        mask = (x >= 2) & (x <= 8)
        mf_values[mask] = 1 - np.abs(x[mask] - 5) / 3

        result = defuzzifier.defuzzify(x, mf_values)
        assert abs(result - 5.0) < 0.1  # 应该接近5

    def test_mean_of_maximum(self):
        """测试最大隶属度法"""
        defuzzifier = Defuzzifier('mom')

        # 创建一个梯形隶属函数
        x = np.linspace(0, 10, 100)
        mf_values = np.zeros_like(x)

        # 平台区域在3-7
        mask = (x >= 3) & (x <= 7)
        mf_values[mask] = 1.0

        # 上升段
        mask_rise = (x >= 1) & (x < 3)
        mf_values[mask_rise] = (x[mask_rise] - 1) / 2

        # 下降段
        mask_fall = (x > 7) & (x <= 9)
        mf_values[mask_fall] = (9 - x[mask_fall]) / 2

        result = defuzzifier.defuzzify(x, mf_values)
        assert abs(result - 5.0) < 0.1  # 平台中心

    def test_weighted_average(self):
        """测试加权平均法"""
        defuzzifier = Defuzzifier('wa')

        x = np.array([0, 1, 2, 3, 4])
        mf_values = np.array([0, 0.5, 1, 0.5, 0])

        result = defuzzifier.defuzzify(x, mf_values)
        expected = np.sum(x * mf_values) / np.sum(mf_values)
        assert abs(result - expected) < 1e-10

    def test_zero_membership(self):
        """测试零隶属度情况"""
        defuzzifier = Defuzzifier('cog')

        x = np.linspace(0, 10, 100)
        mf_values = np.zeros_like(x)

        result = defuzzifier.defuzzify(x, mf_values)
        assert abs(result - 5.0) < 0.1  # 返回论域中心

    def test_symmetric_membership(self):
        """测试对称隶属函数"""
        defuzzifier = Defuzzifier('cog')

        x = np.linspace(0, 10, 100)
        mf_values = np.zeros_like(x)

        # 对称三角形，峰值在5
        mask = (x >= 2) & (x <= 8)
        mf_values[mask] = 1 - np.abs(x[mask] - 5) / 3

        result = defuzzifier.defuzzify(x, mf_values)
        assert abs(result - 5.0) < 0.1

    def test_asymmetric_membership(self):
        """测试非对称隶属函数"""
        defuzzifier = Defuzzifier('cog')

        x = np.linspace(0, 10, 100)
        mf_values = np.zeros_like(x)

        # 非对称三角形，峰值在3
        mask = (x >= 0) & (x <= 7)
        mf_values[mask] = np.where(x[mask] <= 3, x[mask] / 3, (7 - x[mask]) / 4)

        result = defuzzifier.defuzzify(x, mf_values)
        # 重心应该偏向左侧
        assert result < 5.0

    def test_invalid_method(self):
        """测试无效方法"""
        with pytest.raises(ValueError, match="不支持的方法"):
            Defuzzifier('invalid')

    def test_set_method(self):
        """测试设置方法"""
        defuzzifier = Defuzzifier('cog')
        defuzzifier.set_method('mom')
        assert defuzzifier.get_method() == 'mom'

    def test_set_invalid_method(self):
        """测试设置无效方法"""
        defuzzifier = Defuzzifier('cog')
        with pytest.raises(ValueError):
            defuzzifier.set_method('invalid')

    def test_defuzzify_multiple(self):
        """测试多变量去模糊化"""
        defuzzifier = Defuzzifier('cog')

        x = np.linspace(0, 10, 100)

        # 创建两个隶属函数
        mf1 = np.zeros_like(x)
        mask1 = (x >= 2) & (x <= 8)
        mf1[mask1] = 1 - np.abs(x[mask1] - 5) / 3

        mf2 = np.zeros_like(x)
        mask2 = (x >= 5) & (x <= 10)
        mf2[mask2] = (x[mask2] - 5) / 5

        fuzzy_outputs = {
            'output1': mf1,
            'output2': mf2
        }

        results = defuzzifier.defuzzify_multiple(x, fuzzy_outputs)

        assert 'output1' in results
        assert 'output2' in results
        assert abs(results['output1'] - 5.0) < 0.1
        assert results['output2'] > 5.0

    def test_mismatched_lengths(self):
        """测试长度不匹配"""
        defuzzifier = Defuzzifier('cog')

        x = np.array([0, 1, 2])
        mf_values = np.array([0, 1])

        with pytest.raises(ValueError, match="长度必须相同"):
            defuzzifier.defuzzify(x, mf_values)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
