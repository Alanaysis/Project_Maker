"""
混沌 PSO 测试
"""

import numpy as np
import pytest
from src.chaos_pso import (
    ChaosSwarm,
    ChaosPSOConfig,
    logistic_map,
    tent_map,
    sinusoidal_map,
)
from src.functions import sphere, rastrigin


class TestChaosMaps:
    """混沌映射测试"""

    def test_logistic_map(self):
        """测试 Logistic 映射"""
        x = np.array([0.1, 0.5, 0.9])
        result = logistic_map(x)

        assert len(result) == 3
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_tent_map(self):
        """测试 Tent 映射"""
        x = np.array([0.1, 0.5, 0.9])
        result = tent_map(x)

        assert len(result) == 3
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_sinusoidal_map(self):
        """测试 Sinusoidal 映射"""
        x = np.array([0.1, 0.5, 0.9])
        result = sinusoidal_map(x)

        assert len(result) == 3
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_chaos_sequence_generation(self):
        """测试混沌序列生成"""
        x = np.array([0.3, 0.7])
        values = [x]

        for _ in range(10):
            x = logistic_map(x)
            values.append(x)

        # 混沌序列应该不重复
        values_array = np.array(values)
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                assert not np.array_equal(values_array[i], values_array[j])


class TestChaosPSOConfig:
    """混沌 PSO 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ChaosPSOConfig()

        assert config.n_particles == 30
        assert config.dimensions == 2
        assert config.chaos_map == "logistic"
        assert config.chaos_weight == 0.1

    def test_custom_config(self):
        """测试自定义配置"""
        config = ChaosPSOConfig(
            n_particles=50,
            chaos_map="tent",
            chaos_weight=0.2,
        )

        assert config.n_particles == 50
        assert config.chaos_map == "tent"
        assert config.chaos_weight == 0.2


class TestChaosSwarm:
    """混沌粒子群测试"""

    def test_initialization(self):
        """测试初始化"""
        config = ChaosPSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = ChaosSwarm(config)

        assert len(swarm.particles) == 10
        assert swarm.global_best is None

    def test_chaos_initialization(self):
        """测试混沌初始化"""
        config = ChaosPSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            random_seed=42,
        )
        swarm = ChaosSwarm(config)

        # 粒子位置应该在边界内
        for particle in swarm.particles:
            assert np.all(particle.position >= -10.0)
            assert np.all(particle.position <= 10.0)

    def test_optimize_sphere(self):
        """测试优化球面函数"""
        config = ChaosPSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            random_seed=42,
        )
        swarm = ChaosSwarm(config)
        result = swarm.optimize(sphere)

        assert result["best_fitness"] < 1.0
        assert len(result["convergence_history"]) > 0

    def test_different_chaos_maps(self):
        """测试不同混沌映射"""
        for chaos_map in ["logistic", "tent", "sinusoidal"]:
            config = ChaosPSOConfig(
                n_particles=10,
                dimensions=2,
                bounds=(-10.0, 10.0),
                max_iterations=20,
                chaos_map=chaos_map,
                random_seed=42,
            )
            swarm = ChaosSwarm(config)
            result = swarm.optimize(sphere)

            assert result["best_fitness"] < float("inf")

    def test_invalid_chaos_map(self):
        """测试无效的混沌映射"""
        config = ChaosPSOConfig(chaos_map="invalid")

        with pytest.raises(ValueError):
            ChaosSwarm(config)

    def test_chaos_perturbation(self):
        """测试混沌扰动"""
        config = ChaosPSOConfig(
            n_particles=10,
            dimensions=2,
            chaos_weight=0.2,
            random_seed=42,
        )
        swarm = ChaosSwarm(config)

        # 混沌扰动权重应该衰减
        initial_weight = swarm._current_chaos_weight
        swarm.optimize(sphere, verbose=False)
        final_weight = swarm._current_chaos_weight

        assert final_weight < initial_weight

    def test_reset(self):
        """测试重置功能"""
        config = ChaosPSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = ChaosSwarm(config)

        # 运行一次优化
        swarm.optimize(sphere)
        assert swarm.global_best is not None

        # 重置
        swarm.reset()
        assert swarm.global_best is None
        assert swarm.global_best_fitness == float("inf")

    def test_callback(self):
        """测试回调函数"""
        config = ChaosPSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=20,
            random_seed=42,
        )
        swarm = ChaosSwarm(config)

        callback_data = []

        def my_callback(iteration, fitness, position):
            callback_data.append((iteration, fitness))

        swarm.optimize(sphere, callback=my_callback)

        assert len(callback_data) > 0

    def test_track_trajectories(self):
        """测试轨迹追踪"""
        config = ChaosPSOConfig(
            n_particles=5,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=10,
            random_seed=42,
            track_trajectories=True,
        )
        swarm = ChaosSwarm(config)
        result = swarm.optimize(sphere)

        assert result["particle_trajectories"] is not None
        assert len(result["particle_trajectories"]) == 5
