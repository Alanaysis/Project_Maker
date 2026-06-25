"""
个体类测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.individual import Individual


class TestIndividual:
    """个体类测试"""

    def test_creation(self):
        """测试个体创建"""
        ind = Individual([1, 2, 3])
        assert ind.chromosome == [1, 2, 3]
        assert ind.fitness == 0.0

    def test_evaluate(self):
        """测试适应度评估"""
        ind = Individual([1, 2, 3])
        fitness_func = lambda x: sum(x)
        ind.evaluate(fitness_func)
        assert ind.fitness == 6.0

    def test_copy(self):
        """测试深拷贝"""
        ind1 = Individual([1, 2, 3])
        ind1.fitness = 10.0
        ind2 = ind1.copy()

        assert ind2.chromosome == [1, 2, 3]
        assert ind2.fitness == 10.0

        # 修改副本不影响原件
        ind2.chromosome[0] = 99
        assert ind1.chromosome[0] == 1

    def test_len(self):
        """测试长度"""
        ind = Individual([1, 2, 3, 4, 5])
        assert len(ind) == 5

    def test_getitem(self):
        """测试索引访问"""
        ind = Individual([10, 20, 30])
        assert ind[0] == 10
        assert ind[1] == 20
        assert ind[2] == 30

    def test_setitem(self):
        """测试索引设置"""
        ind = Individual([1, 2, 3])
        ind[1] = 99
        assert ind[1] == 99

    def test_repr(self):
        """测试字符串表示"""
        ind = Individual([1, 2, 3])
        ind.fitness = 6.0
        repr_str = repr(ind)
        assert "Individual" in repr_str
        assert "6.0000" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
