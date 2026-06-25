"""
粒子群测试
"""

import numpy as np
import pytest
from src.swarm import Swarm, PSOConfig, PSOResult
from src.functions import sphere, rastrigin


class TestPSOConfig:
    """PSO 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = PSOConfig()

        assert config.n_particles == 30
        assert config.dimensions == 2
        assert config.bounds == (-100.0, 100.0)
        assert config.w == 0.7
        assert config.c1 == 1.5
        assert config.c2 == 1.5
        assert config.max_iterations == 100
        assert config.tolerance == 1e-6

    def test_custom_config(self):
        """测试自定义配置"""
        config = PSOConfig(
            n_particles=50,
            dimensions=5,
            bounds=(-10.0, 10.0),
            w=0.5,
            c1=2.0,
            c2=2.0,
            max_iterations=200,
        )

        assert config.n_particles == 50
        assert config.dimensions == 5
        assert config.bounds == (-10.0, 10.0)
        assert config.w == 0.5
        assert config.c1 == 2.0
        assert config.c2 == 2.0
        assert config.max_iterations == 200


class TestSwarm:
    """粒子群测试"""

    def test_initialization(self):
        """测试粒子群初始化"""
        config = PSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = Swarm(config)

        assert len(swarm.particles) == 10
        assert swarm.global_best is None
        assert swarm.global_best_fitness == float("inf")

    def test_optimize_sphere(self):
        """测试优化球面函数"""
        config = PSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=100,
            random_seed=42,
        )
        swarm = Swarm(config)
        result = swarm.optimize(sphere)

        assert isinstance(result, PSOResult)
        assert result.best_fitness < 1.0  # 应该找到接近最优的解
        assert len(result.convergence_history) > 0

    def test_optimize_reproducibility(self):
        """测试优化结果可复现"""
        config = PSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            random_seed=42,
        )

        # 两次运行
        swarm1 = Swarm(config)
        result1 = swarm1.optimize(sphere)

        swarm2 = Swarm(config)
        result2 = swarm2.optimize(sphere)

        # 结果应该相同
        np.testing.assert_array_almost_equal(
            result1.best_position, result2.best_position
        )
        assert result1.best_fitness == pytest.approx(result2.best_fitness)

    def test_convergence_history(self):
        """测试收敛历史记录"""
        config = PSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=20,
            random_seed=42,
        )
        swarm = Swarm(config)
        result = swarm.optimize(sphere)

        assert len(result.convergence_history) <= config.max_iterations

        # 收敛历史应该单调递减或相等
        for i in range(1, len(result.convergence_history)):
            assert result.convergence_history[i] <= result.convergence_history[i - 1] + 1e-10

    def test_reset(self):
        """测试重置功能"""
        config = PSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            random_seed=42,
        )
        swarm = Swarm(config)

        # 运行一次优化
        swarm.optimize(sphere)
        assert swarm.global_best is not None
        assert len(swarm.convergence_history) > 0

        # 重置
        swarm.reset()
        assert swarm.global_best is None
        assert swarm.global_best_fitness == float("inf")
        assert len(swarm.convergence_history) == 0

    def test_linear_decay_strategy(self):
        """测试线性递减惯性权重策略"""
        config = PSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            w_strategy="linear_decay",
            w_max=0.9,
            w_min=0.4,
            random_seed=42,
        )
        swarm = Swarm(config)

        # 测试惯性权重递减
        w_first = swarm._get_inertia_weight(0)
        w_middle = swarm._get_inertia_weight(25)
        w_last = swarm._get_inertia_weight(49)

        assert w_first > w_middle > w_last
        assert w_first == pytest.approx(0.9)
        assert w_last == pytest.approx(0.41, abs=0.01)

    def test_callback(self):
        """测试回调函数"""
        config = PSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=10,
            random_seed=42,
        )
        swarm = Swarm(config)

        callback_data = []

        def my_callback(iteration, fitness, position):
            callback_data.append((iteration, fitness))

        swarm.optimize(sphere, callback=my_callback)

        assert len(callback_data) > 0
        assert callback_data[0][0] == 0  # 第一次迭代

    def test_track_trajectories(self):
        """测试轨迹追踪"""
        config = PSOConfig(
            n_particles=5,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=10,
            random_seed=42,
            track_trajectories=True,
        )
        swarm = Swarm(config)
        result = swarm.optimize(sphere)

        assert result.particle_trajectories is not None
        assert len(result.particle_trajectories) == 5


class TestPSOResult:
    """PSO 结果测试"""

    def test_repr(self):
        """测试字符串表示"""
        result = PSOResult(
            best_position=np.array([0.0, 0.0]),
            best_fitness=0.0,
            iterations=100,
            convergence_history=[10.0, 5.0, 1.0],
        )

        repr_str = repr(result)
        assert "PSOResult" in repr_str
        assert "0.000000" in repr_str
