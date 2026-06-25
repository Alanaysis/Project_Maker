"""
粒子类测试
"""

import numpy as np
import pytest
from src.particle import Particle


class TestParticle:
    """粒子类单元测试"""

    def test_initialization(self):
        """测试粒子初始化"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)

        assert particle.dimensions == 2
        assert len(particle.position) == 2
        assert len(particle.velocity) == 2
        assert len(particle.personal_best) == 2
        assert particle.personal_best_fitness == float("inf")

    def test_initialization_bounds(self):
        """测试粒子初始化位置在边界内"""
        rng = np.random.default_rng(42)
        bounds = (-10.0, 10.0)

        for _ in range(100):
            particle = Particle(dimensions=2, bounds=bounds, rng=rng)
            assert np.all(particle.position >= bounds[0])
            assert np.all(particle.position <= bounds[1])

    def test_evaluate_sphere(self):
        """测试球面函数评估"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)

        # 手动设置位置
        particle.position = np.array([3.0, 4.0])
        fitness = particle.evaluate(lambda x: np.sum(x**2))

        assert fitness == pytest.approx(25.0)
        assert particle.personal_best_fitness == pytest.approx(25.0)
        np.testing.assert_array_almost_equal(particle.personal_best, [3.0, 4.0])

    def test_evaluate_updates_personal_best(self):
        """测试评估是否更新个体最佳"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)
        objective = lambda x: np.sum(x**2)

        # 第一次评估
        particle.position = np.array([5.0, 5.0])
        fitness1 = particle.evaluate(objective)
        assert particle.personal_best_fitness == pytest.approx(50.0)

        # 第二次评估（更好）
        particle.position = np.array([1.0, 1.0])
        fitness2 = particle.evaluate(objective)
        assert particle.personal_best_fitness == pytest.approx(2.0)

        # 第三次评估（更差）
        particle.position = np.array([10.0, 10.0])
        fitness3 = particle.evaluate(objective)
        # 个体最佳不应更新
        assert particle.personal_best_fitness == pytest.approx(2.0)

    def test_update_velocity(self):
        """测试速度更新"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-100.0, 100.0), rng=rng)

        # 设置当前位置
        particle.position = np.array([0.0, 0.0])
        particle.velocity = np.array([1.0, 1.0])
        particle.personal_best = np.array([5.0, 5.0])

        global_best = np.array([10.0, 10.0])

        # 记录旧速度
        old_velocity = particle.velocity.copy()

        # 更新速度
        particle.update_velocity(global_best=global_best, w=0.5, c1=1.0, c2=1.0)

        # 速度应该改变了
        assert not np.array_equal(particle.velocity, old_velocity)

    def test_update_position(self):
        """测试位置更新"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-100.0, 100.0), rng=rng)

        particle.position = np.array([0.0, 0.0])
        particle.velocity = np.array([1.0, -1.0])

        particle.update_position()

        np.testing.assert_array_almost_equal(particle.position, [1.0, -1.0])

    def test_update_position_with_bounds(self):
        """测试带边界约束的位置更新"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-100.0, 100.0), rng=rng)

        particle.position = np.array([95.0, -95.0])
        particle.velocity = np.array([10.0, -10.0])

        particle.update_position(bounds=(-100.0, 100.0))

        # 位置应该被裁剪到边界
        assert particle.position[0] == pytest.approx(100.0)
        assert particle.position[1] == pytest.approx(-100.0)

    def test_repr(self):
        """测试字符串表示"""
        rng = np.random.default_rng(42)
        particle = Particle(dimensions=2, bounds=(-10.0, 10.0), rng=rng)
        repr_str = repr(particle)

        assert "Particle" in repr_str
        assert "dimensions=2" in repr_str

    def test_different_dimensions(self):
        """测试不同维度"""
        rng = np.random.default_rng(42)

        for dim in [1, 2, 5, 10]:
            particle = Particle(dimensions=dim, bounds=(-10.0, 10.0), rng=rng)
            assert particle.dimensions == dim
            assert len(particle.position) == dim
            assert len(particle.velocity) == dim
