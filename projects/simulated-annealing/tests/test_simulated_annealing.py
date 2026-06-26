#!/usr/bin/env python3
"""
模拟退火算法库单元测试
"""

import sys
import os
import math
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.core import SimulatedAnnealing, SAResult
from src.temperature import (
    ExponentialScheduler,
    LinearScheduler,
    LogarithmicScheduler,
    AdaptiveScheduler,
)
from src.acceptance import metropolis_criterion, boltzmann_acceptance
from src.neighborhood import (
    swap_neighbor,
    insert_neighbor,
    reverse_neighbor,
    multi_switch_neighbor,
    continuous_neighbor,
)
from src.cooling import ExponentialCooling, LinearCooling, AdaptiveCooling, create_cooling_schedule
from src.convergence import ConvergenceDetector, EarlyStopDetector
from src.restart import RestartManager, DiversificationRestart


# ============================================================
# 辅助函数
# ============================================================

def sphere(x):
    """Sphere 目标函数"""
    return sum(xi ** 2 for xi in x)


def rastrigin(x):
    """Rastrigin 目标函数"""
    n = len(x)
    return 10 * n + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)


def objective_1d(x):
    """单变量目标函数"""
    return (x[0] - 3.0) ** 2


# ============================================================
# 核心算法测试
# ============================================================

class TestSimulatedAnnealing:
    """模拟退火核心算法测试"""

    def test_basic_optimization(self):
        """测试基本优化功能"""
        sa = SimulatedAnnealing(
            initial_temp=1000.0,
            min_temp=1e-10,
            cooling_rate=0.99,
            iterations_per_temp=50,
            seed=42,
        )

        initial_sol = [10.0, 10.0]

        def neighbor_gen(sol):
            return [sol[0] + random.gauss(0, 1), sol[1] + random.gauss(0, 1)]

        result = sa.optimize(
            objective=sphere,
            initial_solution=initial_sol,
            neighbor_generator=neighbor_gen,
            max_iterations=500,
        )

        assert result.best_energy < 1.0, f"最优能量 {result.best_energy} 应该小于 1.0"
        assert result.iteration_count > 0
        assert result.runtime > 0
        assert len(result.energy_history) > 0
        assert len(result.temperature_history) > 0

    def test_result_summary(self):
        """测试结果摘要输出"""
        sa = SimulatedAnnealing(seed=42)
        result = SAResult(
            best_solution=[1.0, 2.0],
            best_energy=5.0,
            iteration_count=100,
            runtime=1.5,
        )
        summary = result.summary()
        assert "最优能量值" in summary
        assert "100" in summary
        assert "1.5" in summary

    def test_optimization_finds_minimum(self):
        """测试优化是否找到最小值"""
        sa = SimulatedAnnealing(
            initial_temp=500.0,
            min_temp=1e-10,
            cooling_rate=0.995,
            iterations_per_temp=100,
            seed=42,
        )

        initial_sol = [5.0]
        result = sa.optimize(
            objective=objective_1d,
            initial_solution=initial_sol,
            neighbor_generator=lambda sol: [sol[0] + random.gauss(0, 0.5)],
            max_iterations=1000,
        )

        assert abs(result.best_solution[0] - 3.0) < 0.5, \
            f"最优解 {result.best_solution[0]} 应该接近 3.0"


# ============================================================
# 温度调度测试
# ============================================================

class TestTemperatureSchedulers:
    """温度调度器测试"""

    def test_exponential_scheduler(self):
        """测试指数冷却调度器"""
        scheduler = ExponentialScheduler(rate=0.9)
        temp = 1000.0

        for _ in range(10):
            temp = scheduler.next_temperature(temp)

        assert temp < 1000.0, "温度应该下降"
        assert temp > 0, "温度应该大于 0"
        assert abs(scheduler.get_rate() - 0.9) < 1e-10

    def test_exponential_scheduler_invalid_rate(self):
        """测试无效冷却率"""
        with pytest.raises(ValueError):
            ExponentialScheduler(rate=1.5)
        with pytest.raises(ValueError):
            ExponentialScheduler(rate=0.0)

    def test_linear_scheduler(self):
        """测试线性冷却调度器"""
        scheduler = LinearScheduler(delta=10.0)
        temp = 1000.0

        for _ in range(50):
            temp = scheduler.next_temperature(temp)

        assert temp == 0.0, "线性冷却应该达到 0"

    def test_linear_scheduler_negative_delta(self):
        """测试负降温步长"""
        with pytest.raises(ValueError):
            LinearScheduler(delta=-1.0)

    def test_logarithmic_scheduler(self):
        """测试对数冷却调度器"""
        scheduler = LogarithmicScheduler(initial_temp=1000.0)
        temp = scheduler.next_temperature(1000.0)
        assert temp > 0

        temp = scheduler.next_temperature(temp)
        assert temp < 1000.0, "温度应该下降"

    def test_adaptive_scheduler(self):
        """测试自适应调度器"""
        scheduler = AdaptiveScheduler(
            initial_rate=0.95,
            target_acceptance=0.44,
            adjustment_factor=0.01,
        )

        initial_rate = scheduler.get_rate()
        # 模拟高接受率
        for _ in range(50):
            scheduler.update(0.8)
        new_rate = scheduler.get_rate()
        assert new_rate >= initial_rate, "高接受率应该增加冷却速率"

    def test_adaptive_scheduler_reset(self):
        """测试自适应调度器重置"""
        scheduler = AdaptiveScheduler()
        scheduler.update(0.8)
        scheduler.reset()
        assert abs(scheduler.get_rate() - scheduler.initial_rate) < 1e-10


# ============================================================
# 接受准则测试
# ============================================================

class TestAcceptanceCriterion:
    """接受准则测试"""

    def test_metropolis_better_solution(self):
        """测试 Metropolis 准则：更好的解应该被接受"""
        random.seed(42)
        for _ in range(100):
            assert metropolis_criterion(delta_e=-1.0, temperature=100.0) is True

    def test_metropolis_worse_solution(self):
        """测试 Metropolis 准则：差解以概率接受"""
        random.seed(42)
        # 高温时差解也应该被接受
        probs = []
        for _ in range(1000):
            probs.append(metropolis_criterion(delta_e=10.0, temperature=1000.0))
        acceptance_rate = sum(probs) / len(probs)
        assert acceptance_rate > 0.01, "高温时应该有显著的接受率"

    def test_metropolis_zero_temperature(self):
        """测试零温度：差解不应该被接受"""
        random.seed(42)
        for _ in range(100):
            assert metropolis_criterion(delta_e=1.0, temperature=0.0) is False

    def test_boltzmann_acceptance_probability(self):
        """测试 Boltzmann 接受概率"""
        # ΔE < 0 时概率为 1
        assert boltzmann_acceptance(-1.0, 100.0) == 1.0

        # ΔE > 0 时概率在 (0, 1) 之间
        prob = boltzmann_acceptance(1.0, 100.0)
        assert 0.0 < prob < 1.0

    def test_boltzmann_zero_temperature(self):
        """测试 Boltzmann 零温度"""
        assert boltzmann_acceptance(1.0, 0.0) == 0.0


# ============================================================
# 邻域生成测试
# ============================================================

class TestNeighborhoodGeneration:
    """邻域生成测试"""

    def test_swap_neighbor(self):
        """测试交换邻域"""
        sol = [1, 2, 3, 4, 5]
        new_sol = swap_neighbor(sol)
        assert len(new_sol) == len(sol)
        assert new_sol != sol
        assert sorted(new_sol) == sorted(sol)

    def test_insert_neighbor(self):
        """测试插入邻域"""
        sol = [1, 2, 3, 4, 5]
        new_sol = insert_neighbor(sol)
        assert len(new_sol) == len(sol)
        assert new_sol != sol
        assert sorted(new_sol) == sorted(sol)

    def test_reverse_neighbor(self):
        """测试反转邻域"""
        sol = [1, 2, 3, 4, 5]
        new_sol = reverse_neighbor(sol)
        assert len(new_sol) == len(sol)
        assert new_sol != sol
        assert sorted(new_sol) == sorted(sol)

    def test_multi_switch_neighbor(self):
        """测试多交换邻域"""
        sol = [1, 2, 3, 4, 5]
        new_sol = multi_switch_neighbor(sol, num_switches=3)
        assert len(new_sol) == len(sol)
        assert sorted(new_sol) == sorted(sol)

    def test_continuous_neighbor_scalar(self):
        """测试连续邻域（标量）"""
        sol = 5.0
        new_sol = continuous_neighbor(sol, magnitude=0.1)
        assert isinstance(new_sol, float)
        assert new_sol != sol

    def test_continuous_neighbor_list(self):
        """测试连续邻域（列表）"""
        sol = [1.0, 2.0, 3.0]
        new_sol = continuous_neighbor(sol, magnitude=0.1)
        assert len(new_sol) == len(sol)
        assert new_sol != sol

    def test_neighborhood_generator_auto(self):
        """测试自动邻域生成"""
        from src.neighborhood import neighborhood_generator

        # 列表自动选择 swap
        sol = [1, 2, 3, 4, 5]
        new_sol = neighborhood_generator(sol, strategy="auto")
        assert len(new_sol) == len(sol)

        # 标量自动选择 continuous
        sol = 5.0
        new_sol = neighborhood_generator(sol, strategy="auto")
        assert isinstance(new_sol, float)

    def test_neighborhood_generator_invalid(self):
        """测试无效策略"""
        from src.neighborhood import neighborhood_generator
        with pytest.raises(ValueError):
            neighborhood_generator([1, 2, 3], strategy="invalid")


# ============================================================
# 冷却方案测试
# ============================================================

class TestCoolingSchedules:
    """冷却方案测试"""

    def test_exponential_cooling(self):
        """测试指数冷却"""
        schedule = ExponentialCooling(alpha=0.9)
        temp = schedule.compute_temperature(1000.0, 0)
        assert temp == 1000.0

        temp = schedule.compute_temperature(1000.0, 10)
        assert temp < 1000.0
        assert abs(temp - 1000.0 * (0.9 ** 10)) < 1e-10

    def test_exponential_cooling_invalid_alpha(self):
        """测试无效 alpha"""
        with pytest.raises(ValueError):
            ExponentialCooling(alpha=1.5)

    def test_linear_cooling(self):
        """测试线性冷却"""
        schedule = LinearCooling()
        temp = schedule.compute_temperature(1000.0, 0, 100)
        assert temp == 1000.0

        temp = schedule.compute_temperature(1000.0, 50, 100)
        assert abs(temp - 500.0) < 1e-10

        temp = schedule.compute_temperature(1000.0, 100, 100)
        assert temp < 1e-9

    def test_adaptive_cooling_update(self):
        """测试自适应冷却更新"""
        schedule = AdaptiveCooling()
        alpha = schedule.update(improved=False)
        assert alpha >= schedule.base_alpha - 0.001

    def test_adaptive_cooling_reset(self):
        """测试自适应冷却重置"""
        schedule = AdaptiveCooling()
        for _ in range(20):
            schedule.update(improved=False)
        schedule.reset()
        assert schedule._current_alpha == schedule.base_alpha

    def test_create_cooling_schedule(self):
        """测试工厂函数"""
        s1 = create_cooling_schedule("exponential", alpha=0.95)
        assert isinstance(s1, ExponentialCooling)

        s2 = create_cooling_schedule("linear")
        assert isinstance(s2, LinearCooling)

        s3 = create_cooling_schedule("adaptive")
        assert isinstance(s3, AdaptiveCooling)

    def test_create_cooling_schedule_invalid(self):
        """测试无效方案类型"""
        with pytest.raises(ValueError):
            create_cooling_schedule("invalid")


# ============================================================
# 收敛检测测试
# ============================================================

class TestConvergenceDetection:
    """收敛检测测试"""

    def test_energy_convergence(self):
        """测试能量收敛检测"""
        detector = ConvergenceDetector(
            energy_threshold=1e-6,
            window_size=20,
            min_iterations=25,
        )

        # 模拟能量收敛
        for i in range(30):
            converged = detector.update(
                current_energy=0.0001 if i > 10 else i * 0.1,
                acceptance_rate=0.5 if i < 10 else 0.001,
                improved=i < 10,
                iteration=i,
            )

        # 应该检测到收敛
        assert detector.is_converged or detector.convergence_iteration is not None

    def test_acceptance_convergence(self):
        """测试接受率收敛检测"""
        detector = ConvergenceDetector(
            acceptance_threshold=0.01,
            window_size=20,
            min_iterations=25,
        )

        for i in range(30):
            converged = detector.update(
                current_energy=i * 0.1,
                acceptance_rate=0.5 if i < 10 else 0.001,
                improved=i < 10,
                iteration=i,
            )

        assert detector.is_converged or detector.convergence_iteration is not None

    def test_no_improve_convergence(self):
        """测试连续未改进检测"""
        detector = ConvergenceDetector(
            no_improve_threshold=10,
            min_iterations=5,
        )

        for i in range(15):
            detector.update(
                current_energy=i * 0.1,
                acceptance_rate=0.5,
                improved=False,
                iteration=i,
            )

        assert detector.is_converged or detector.convergence_iteration is not None

    def test_early_stop_detector(self):
        """测试早停检测器"""
        detector = EarlyStopDetector(patience=5, min_iterations=3)

        # 前 3 次不应该停止
        for i in range(3):
            assert not detector.update(current_energy=i * 0.1, iteration=i)

        # 连续 5 次未改进应该停止
        for i in range(5, 10):
            should_stop = detector.update(current_energy=i * 0.1, iteration=i)
            if i >= 9:
                assert should_stop

    def test_convergence_detector_reset(self):
        """测试收敛检测器重置"""
        detector = ConvergenceDetector()
        detector.update(current_energy=0.1, acceptance_rate=0.5, improved=True, iteration=10)
        detector.reset()
        assert not detector.is_converged
        assert detector.convergence_iteration is None


# ============================================================
# 重启机制测试
# ============================================================

class TestRestartMechanism:
    """重启机制测试"""

    def test_restart_trigger(self):
        """测试重启触发"""
        manager = RestartManager(max_restarts=5, restart_threshold=10)

        # 连续未改进触发重启
        for i in range(15):
            should_restart = manager.check_restart(
                current_energy=100.0,
                best_energy=50.0,
                iteration=i,
            )
            if i >= 10:
                assert should_restart is True

    def test_restart_limit(self):
        """测试重启次数限制"""
        manager = RestartManager(max_restarts=2, restart_threshold=1)

        for _ in range(5):
            manager.check_restart(current_energy=100.0, best_energy=50.0, iteration=0)
            manager.trigger_restart()

        assert manager.restart_count == 2

    def test_restart_manager_record(self):
        """测试结果记录"""
        manager = RestartManager()
        manager.record_result([1.0, 2.0], 5.0)
        assert len(manager._history) == 1

    def test_diversification_restart(self):
        """测试多样化重启"""
        restart = DiversificationRestart()
        history = [([1.0, 2.0], 5.0), ([3.0, 4.0], 3.0)]
        new_sol = restart.generate_restart_point(history, [0.0, 0.0], 0.0)
        assert new_sol is not None

    def test_restart_manager_reset(self):
        """测试重启管理器重置"""
        manager = RestartManager()
        manager.trigger_restart()
        manager.record_result([1.0], 1.0)
        manager.reset()
        assert manager.restart_count == 0
        assert len(manager._history) == 0


# ============================================================
# 集成测试
# ============================================================

class TestIntegration:
    """集成测试"""

    def test_full_sa_workflow(self):
        """测试完整的 SA 工作流"""
        random.seed(42)

        sa = SimulatedAnnealing(
            initial_temp=1000.0,
            min_temp=1e-10,
            cooling_rate=0.99,
            iterations_per_temp=50,
            seed=42,
        )

        initial_sol = [5.0, 5.0]
        result = sa.optimize(
            objective=sphere,
            initial_solution=initial_sol,
            neighbor_generator=lambda sol: [
                sol[0] + random.gauss(0, 1),
                sol[1] + random.gauss(0, 1),
            ],
            max_iterations=1000,
        )

        assert result.best_energy < 1.0
        assert result.iteration_count > 0
        assert len(result.energy_history) > 0
        assert len(result.temperature_history) > 0
        assert len(result.acceptance_history) > 0

    def test_temperature_scheduler_integration(self):
        """测试温度调度器集成"""
        scheduler = ExponentialScheduler(rate=0.95)
        sa = SimulatedAnnealing(
            initial_temp=1000.0,
            cooling_rate=0.99,
            seed=42,
        )

        result = sa.optimize(
            objective=sphere,
            initial_solution=[5.0, 5.0],
            neighbor_generator=lambda sol: [
                sol[0] + random.gauss(0, 0.1),
                sol[1] + random.gauss(0, 0.1),
            ],
            max_iterations=100,
            temperature_scheduler=scheduler,
        )

        assert result.best_energy < 10.0

    def test_convergence_integration(self):
        """测试收敛检测集成"""
        detector = ConvergenceDetector(
            energy_threshold=1e-4,
            min_iterations=10,
        )

        converged = False
        for i in range(50):
            e = 0.001 if i > 20 else i * 0.1
            converged = detector.update(
                current_energy=e,
                acceptance_rate=0.5 if i < 20 else 0.0001,
                improved=i < 20,
                iteration=i,
            )
            if converged:
                break

        assert converged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
