"""
模糊集合测试
"""

import pytest
import numpy as np
from src.fuzzy_set import (
    FuzzySet,
    MembershipFunction,
    TriangularMF,
    TrapezoidalMF,
    GaussianMF,
    BellShapedMF,
    create_triangular_set,
    create_trapezoidal_set,
    create_gaussian_set
)


class TestTriangularMF:
    """三角形隶属函数测试"""

    def test_basic_functionality(self):
        """测试基本功能"""
        mf = TriangularMF("test", 0, 5, 10)

        # 测试边界点
        assert mf(0) == 0.0
        assert mf(5) == 1.0
        assert mf(10) == 0.0

        # 测试中间点
        assert mf(2.5) == 0.5
        assert mf(7.5) == 0.5

    def test_outside_range(self):
        """测试范围外的点"""
        mf = TriangularMF("test", 0, 5, 10)

        assert mf(-1) == 0.0
        assert mf(11) == 0.0

    def test_numpy_array(self):
        """测试numpy数组输入"""
        mf = TriangularMF("test", 0, 5, 10)
        x = np.array([0, 2.5, 5, 7.5, 10])
        expected = np.array([0.0, 0.5, 1.0, 0.5, 0.0])

        np.testing.assert_array_almost_equal(mf(x), expected)

    def test_edge_case_equal_points(self):
        """测试边界情况：点重合"""
        mf = TriangularMF("test", 5, 5, 10)
        assert mf(5) == 1.0
        assert mf(10) == 0.0


class TestTrapezoidalMF:
    """梯形隶属函数测试"""

    def test_basic_functionality(self):
        """测试基本功能"""
        mf = TrapezoidalMF("test", 0, 5, 15, 20)

        # 测试边界点
        assert mf(0) == 0.0
        assert mf(5) == 1.0
        assert mf(15) == 1.0
        assert mf(20) == 0.0

        # 测试平台区域
        assert mf(10) == 1.0

        # 测试斜坡区域
        assert mf(2.5) == 0.5
        assert mf(17.5) == 0.5

    def test_numpy_array(self):
        """测试numpy数组输入"""
        mf = TrapezoidalMF("test", 0, 5, 15, 20)
        x = np.array([0, 2.5, 5, 10, 15, 17.5, 20])
        expected = np.array([0.0, 0.5, 1.0, 1.0, 1.0, 0.5, 0.0])

        np.testing.assert_array_almost_equal(mf(x), expected)


class TestGaussianMF:
    """高斯隶属函数测试"""

    def test_basic_functionality(self):
        """测试基本功能"""
        mf = GaussianMF("test", mean=5.0, sigma=2.0)

        # 测试均值点
        assert mf(5.0) == 1.0

        # 测试远离均值的点
        assert mf(5.0 + 2 * 2.0) < 0.5  # 2 sigma 外
        assert mf(5.0 - 2 * 2.0) < 0.5

    def test_symmetry(self):
        """测试对称性"""
        mf = GaussianMF("test", mean=0.0, sigma=1.0)

        assert abs(mf(1.0) - mf(-1.0)) < 1e-10
        assert abs(mf(2.0) - mf(-2.0)) < 1e-10

    def test_numpy_array(self):
        """测试numpy数组输入"""
        mf = GaussianMF("test", mean=0.0, sigma=1.0)
        x = np.array([-2, -1, 0, 1, 2])

        result = mf(x)
        assert result.shape == x.shape
        assert result[2] == 1.0  # 中心点


class TestBellShapedMF:
    """钟形隶属函数测试"""

    def test_basic_functionality(self):
        """测试基本功能"""
        mf = BellShapedMF("test", a=2.0, b=4.0, c=5.0)

        # 测试中心点
        assert mf(5.0) == 1.0

        # 测试远离中心的点
        assert mf(0.0) < 0.5
        assert mf(10.0) < 0.5


class TestFuzzySet:
    """模糊集合测试"""

    def test_membership(self):
        """测试隶属度计算"""
        fs = create_triangular_set("test", 0, 5, 10)

        assert fs.membership(5) == 1.0
        assert fs.membership(0) == 0.0

    def test_complement(self):
        """测试补集"""
        fs = create_triangular_set("test", 0, 5, 10)

        assert fs.complement(5) == 0.0
        assert fs.complement(0) == 1.0

    def test_intersect(self):
        """测试交集"""
        fs1 = create_triangular_set("set1", 0, 5, 10)
        fs2 = create_triangular_set("set2", 5, 10, 15)

        # 在交集区域
        result = fs1.intersect(fs2, 7.5)
        assert 0 <= result <= 1

    def test_union(self):
        """测试并集"""
        fs1 = create_triangular_set("set1", 0, 5, 10)
        fs2 = create_triangular_set("set2", 5, 10, 15)

        # 在并集区域
        result = fs1.union(fs2, 7.5)
        assert result >= 0

    def test_alpha_cut(self):
        """测试α-截集"""
        fs = create_triangular_set("test", 0, 5, 10)
        x = np.linspace(0, 10, 100)

        result = fs.alpha_cut(x, 0.5)
        assert len(result) > 0
        assert all(fs.membership(val) >= 0.5 for val in result)


class TestFactoryFunctions:
    """工厂函数测试"""

    def test_create_triangular_set(self):
        """测试创建三角形模糊集合"""
        fs = create_triangular_set("test", 0, 5, 10, (0, 10))

        assert fs.name == "test"
        assert fs.universe == (0, 10)
        assert fs.membership(5) == 1.0

    def test_create_trapezoidal_set(self):
        """测试创建梯形模糊集合"""
        fs = create_trapezoidal_set("test", 0, 5, 15, 20)

        assert fs.name == "test"
        assert fs.membership(10) == 1.0

    def test_create_gaussian_set(self):
        """测试创建高斯模糊集合"""
        fs = create_gaussian_set("test", 5.0, 2.0)

        assert fs.name == "test"
        assert fs.membership(5.0) == 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
