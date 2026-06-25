"""
自适应 PSO 测试
"""

import numpy as np
import pytest
from src.adaptive_pso import AdaptiveSwarm, AdaptivePSOConfig
from src.functions import sphere, rastrigin


class TestAdaptivePSOConfig:
    """自适应 PSO 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AdaptivePSOConfig()

        assert config.n_particles == 30
        assert config.dimensions == 2
        assert config.w_init == 0.9
        assert config.c1_init == 2.0
        assert config.c2_init == 2.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = AdaptivePSOConfig(
            n_particles=50,
            dimensions=5,
            w_init=0.7,
            c1_init=1.5,
            c2_init=1.5,
        )

        assert config.n_particles == 50
        assert config.dimensions == 5
        assert config.w_init == 0.7


class TestAdaptiveSwarm:
    """自适应粒子群测试"""

    def test_initialization(self):
        """测试初始化"""
        config = AdaptivePSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = AdaptiveSwarm(config)

        assert len(swarm.particles) == 10
        assert swarm.global_best is None
        assert swarm.global_best_fitness == float("inf")

    def test_optimize_sphere(self):
        """测试优化球面函数"""
        config = AdaptivePSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            random_seed=42,
        )
        swarm = AdaptiveSwarm(config)
        result = swarm.optimize(sphere)

        assert result["best_fitness"] < 1.0
        assert len(result["convergence_history"]) > 0

    def test_parameter_adaptation(self):
        """测试参数自适应调整"""
        config = AdaptivePSOConfig(
            n_particles=20,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=50,
            random_seed=42,
        )
        swarm = AdaptiveSwarm(config)
        result = swarm.optimize(sphere)

        # 参数应该被记录
        assert len(result["parameter_history"]) > 0

        # 检查参数范围
        for params in result["parameter_history"]:
            assert config.w_min <= params["w"] <= config.w_max
            assert config.c_min <= params["c1"] <= config.c_max
            assert config.c_min <= params["c2"] <= config.c_max

    def test_diversity_calculation(self):
        """测试多样性计算"""
        config = AdaptivePSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = AdaptiveSwarm(config)

        diversity = swarm._calculate_diversity()
        assert diversity > 0

    def test_reset(self):
        """测试重置功能"""
        config = AdaptivePSOConfig(n_particles=10, dimensions=2, random_seed=42)
        swarm = AdaptiveSwarm(config)

        # 运行一次优化
        swarm.optimize(sphere)
        assert swarm.global_best is not None

        # 重置
        swarm.reset()
        assert swarm.global_best is None
        assert swarm.global_best_fitness == float("inf")

    def test_callback(self):
        """测试回调函数"""
        config = AdaptivePSOConfig(
            n_particles=10,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=20,
            random_seed=42,
        )
        swarm = AdaptiveSwarm(config)

        callback_data = []

        def my_callback(iteration, fitness, position):
            callback_data.append((iteration, fitness))

        swarm.optimize(sphere, callback=my_callback)

        assert len(callback_data) > 0

    def test_track_trajectories(self):
        """测试轨迹追踪"""
        config = AdaptivePSOConfig(
            n_particles=5,
            dimensions=2,
            bounds=(-10.0, 10.0),
            max_iterations=10,
            random_seed=42,
            track_trajectories=True,
        )
        swarm = AdaptiveSwarm(config)
        result = swarm.optimize(sphere)

        assert result["particle_trajectories"] is not None
        assert len(result["particle_trajectories"]) == 5
