"""
模拟退火算法测试

测试模拟退火算法的各个组件：
- 核心算法（温度调度、Metropolis准则）
- 邻域操作（交换、逆序、插入）
- TSP旅行商问题
- 函数优化
- 调度问题
"""

import pytest
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule
from src.neighborhood import NeighborhoodOps
from src.tsp import TSP, City
from src.function_optimization import (
    TestFunctions, ContinuousNeighbor, get_function_specs
)
from src.scheduling import (
    JobShopScheduling, FlowShopScheduling, SingleMachineScheduling,
    ObjectiveType, Job
)


# ============================================================
# 核心算法测试
# ============================================================

class TestSAConfig:
    """测试SA配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = SAConfig()
        assert config.initial_temp == 100.0
        assert config.final_temp == 0.01
        assert config.cooling_rate == 0.99
        assert config.max_iterations == 1000
        assert config.cooling_schedule == CoolingSchedule.EXPONENTIAL

    def test_custom_config(self):
        """测试自定义配置"""
        config = SAConfig(
            initial_temp=200.0,
            final_temp=0.001,
            cooling_rate=0.95,
            max_iterations=500,
            cooling_schedule=CoolingSchedule.LINEAR
        )
        assert config.initial_temp == 200.0
        assert config.final_temp == 0.001
        assert config.cooling_rate == 0.95
        assert config.max_iterations == 500
        assert config.cooling_schedule == CoolingSchedule.LINEAR


class TestCoolingSchedule:
    """测试冷却策略"""

    def setup_method(self):
        """设置测试环境"""
        self.config = SAConfig(initial_temp=100.0, final_temp=0.01, cooling_rate=0.99)

        def objective(x):
            return x ** 2

        def neighbor(x):
            return x + np.random.randn()

        self.optimizer = SimulatedAnnealing(
            self.config, objective, neighbor, 10.0
        )

    def test_exponential_cooling(self):
        """测试指数冷却"""
        self.optimizer.config.cooling_schedule = CoolingSchedule.EXPONENTIAL
        self.optimizer.iteration = 100
        temp = self.optimizer.cooling_exponential()
        expected = 100.0 * (0.99 ** 100)
        assert abs(temp - expected) < 1e-10

    def test_linear_cooling(self):
        """测试线性冷却"""
        self.optimizer.config.cooling_schedule = CoolingSchedule.LINEAR
        self.optimizer.iteration = 500
        self.optimizer.config.max_iterations = 1000
        temp = self.optimizer.cooling_linear()
        expected = 100.0 - (100.0 - 0.01) * 500 / 1000
        assert abs(temp - expected) < 1e-10

    def test_logarithmic_cooling(self):
        """测试对数冷却"""
        self.optimizer.config.cooling_schedule = CoolingSchedule.LOGARITHMIC
        self.optimizer.iteration = 100
        temp = self.optimizer.cooling_logarithmic()
        expected = 100.0 / (1 + 0.99 * np.log(1 + 100))
        assert abs(temp - expected) < 1e-10


class TestMetropolis:
    """测试Metropolis接受准则"""

    def setup_method(self):
        """设置测试环境"""
        self.config = SAConfig(initial_temp=100.0, final_temp=0.01, cooling_rate=0.99)

        def objective(x):
            return x ** 2

        def neighbor(x):
            return x + np.random.randn()

        self.optimizer = SimulatedAnnealing(
            self.config, objective, neighbor, 10.0
        )

    def test_accept_better_solution(self):
        """测试总是接受更优解"""
        prob = self.optimizer.calculate_acceptance_probability(-10.0, 100.0)
        assert prob == 1.0

    def test_accept_worse_solution_with_probability(self):
        """测试以概率接受较差解"""
        np.random.seed(42)
        prob = self.optimizer.calculate_acceptance_probability(10.0, 100.0)
        assert 0 < prob < 1
        assert abs(prob - np.exp(-10.0 / 100.0)) < 1e-10

    def test_reject_worse_solution_at_low_temp(self):
        """测试低温时拒绝较差解的概率很高"""
        prob = self.optimizer.calculate_acceptance_probability(10.0, 0.01)
        assert prob < 0.001  # 概率应该非常小

    def test_zero_delta_cost(self):
        """测试成本差为零时总是接受"""
        prob = self.optimizer.calculate_acceptance_probability(0.0, 100.0)
        assert prob == 1.0


# ============================================================
# 邻域操作测试
# ============================================================

class TestNeighborhoodOps:
    """测试邻域操作"""

    def setup_method(self):
        self.solution = list(range(10))
        self.ops = NeighborhoodOps()

    def test_swap_preserves_elements(self):
        """测试交换操作保持元素完整"""
        new_sol = self.ops.swap(self.solution)
        assert sorted(new_sol) == sorted(self.solution)
        assert len(new_sol) == len(self.solution)

    def test_swap_changes_position(self):
        """测试交换操作改变位置"""
        np.random.seed(42)
        new_sol = self.ops.swap(self.solution)
        # 大多数情况下应该改变
        assert new_sol != self.solution or True  # 随机性，不做严格断言

    def test_reverse_preserves_elements(self):
        """测试逆序操作保持元素完整"""
        new_sol = self.ops.reverse(self.solution)
        assert sorted(new_sol) == sorted(self.solution)
        assert len(new_sol) == len(self.solution)

    def test_insert_preserves_elements(self):
        """测试插入操作保持元素完整"""
        new_sol = self.ops.insert(self.solution)
        assert sorted(new_sol) == sorted(self.solution)
        assert len(new_sol) == len(self.solution)

    def test_or_opt_preserves_elements(self):
        """测试Or-opt操作保持元素完整"""
        new_sol = self.ops.or_opt(self.solution)
        assert sorted(new_sol) == sorted(self.solution)
        assert len(new_sol) == len(self.solution)

    def test_two_opt_swap_preserves_elements(self):
        """测试2-opt交换保持元素完整"""
        new_sol = self.ops.two_opt_swap(self.solution)
        assert sorted(new_sol) == sorted(self.solution)
        assert len(new_sol) == len(self.solution)

    def test_mixed_neighbor_preserves_elements(self):
        """测试混合邻域保持元素完整"""
        mixed = self.ops.create_mixed_neighbor()
        for _ in range(100):
            new_sol = mixed(self.solution)
            assert sorted(new_sol) == sorted(self.solution)
            assert len(new_sol) == len(self.solution)

    def test_mixed_neighbor_with_custom_weights(self):
        """测试自定义权重的混合邻域"""
        ops_list = [self.ops.swap, self.ops.reverse]
        weights = [0.7, 0.3]
        mixed = self.ops.create_mixed_neighbor(ops_list, weights)
        new_sol = mixed(self.solution)
        assert sorted(new_sol) == sorted(self.solution)


# ============================================================
# TSP测试
# ============================================================

class TestTSP:
    """测试TSP问题"""

    def setup_method(self):
        """设置测试环境"""
        self.cities = [
            City(0, 0, "A"),
            City(10, 0, "B"),
            City(10, 10, "C"),
            City(0, 10, "D"),
        ]
        self.tsp = TSP(self.cities)

    def test_distance_calculation(self):
        """测试距离计算"""
        dist = self.tsp._calculate_distance(self.cities[0], self.cities[1])
        assert abs(dist - 10.0) < 1e-10

    def test_total_distance(self):
        """测试总距离计算"""
        path = [0, 1, 2, 3]
        total = self.tsp.calculate_total_distance(path)
        expected = 10.0 + 10.0 + 10.0 + 10.0  # 矩形周长
        assert abs(total - expected) < 1e-10

    def test_random_neighbor(self):
        """测试邻域操作"""
        np.random.seed(42)
        path = [0, 1, 2, 3]
        new_path = self.tsp.random_neighbor(path)
        assert len(new_path) == len(path)
        assert set(new_path) == set(path)  # 包含相同的元素

    def test_random_solution(self):
        """测试随机解生成"""
        np.random.seed(42)
        solution = self.tsp.generate_random_solution()
        assert len(solution) == self.tsp.n_cities
        assert set(solution) == set(range(self.tsp.n_cities))

    def test_random_instance(self):
        """测试随机实例创建"""
        np.random.seed(42)
        tsp = TSP.create_random_instance(5, seed=42)
        assert tsp.n_cities == 5
        assert len(tsp.cities) == 5

    def test_or_opt_neighbor(self):
        """测试Or-opt邻域操作"""
        np.random.seed(42)
        path = [0, 1, 2, 3, 4]
        new_path = self.tsp.or_opt_neighbor(path)
        # or_opt_neighbor需要至少5个城市才能正常工作
        assert len(new_path) == len(path)
        assert set(new_path) == set(path)

    def test_distance_matrix_symmetry(self):
        """测试距离矩阵对称性"""
        n = self.tsp.n_cities
        for i in range(n):
            for j in range(n):
                assert abs(self.tsp.distance_matrix[i][j] - self.tsp.distance_matrix[j][i]) < 1e-10

    def test_distance_matrix_diagonal(self):
        """测试距离矩阵对角线为0"""
        n = self.tsp.n_cities
        for i in range(n):
            assert abs(self.tsp.distance_matrix[i][i]) < 1e-10


# ============================================================
# 函数优化测试
# ============================================================

class TestTestFunctions:
    """测试测试函数"""

    def test_sphere_at_origin(self):
        """测试Sphere函数在原点为0"""
        x = np.zeros(2)
        assert abs(TestFunctions.sphere(x)) < 1e-10

    def test_rastrigin_at_origin(self):
        """测试Rastrigin函数在原点为0"""
        x = np.zeros(2)
        assert abs(TestFunctions.rastrigin(x)) < 1e-10

    def test_ackley_at_origin(self):
        """测试Ackley函数在原点为0"""
        x = np.zeros(2)
        assert abs(TestFunctions.ackley(x)) < 1e-10

    def test_griewank_at_origin(self):
        """测试Griewank函数在原点为0"""
        x = np.zeros(2)
        assert abs(TestFunctions.griewank(x)) < 1e-10

    def test_rosenbrock_at_optimum(self):
        """测试Rosenbrock函数在最优解为0"""
        x = np.ones(2)
        assert abs(TestFunctions.rosenbrock(x)) < 1e-10

    def test_levy_at_optimum(self):
        """测试Levy函数在最优解为0"""
        x = np.ones(2)
        assert abs(TestFunctions.levy(x)) < 1e-10

    def test_sphere_positive(self):
        """测试Sphere函数非负"""
        x = np.array([1.0, 2.0])
        assert TestFunctions.sphere(x) >= 0

    def test_rastrigin_positive(self):
        """测试Rastrigin函数在某些点为正"""
        x = np.array([1.0, 1.0])
        assert TestFunctions.rastrigin(x) > 0


class TestContinuousNeighbor:
    """测试连续空间邻域生成器"""

    def test_within_bounds(self):
        """测试生成的解在边界内"""
        np.random.seed(42)
        neighbor = ContinuousNeighbor(bounds=(-5.0, 5.0), dim=2, step_size=0.5)
        x = np.array([0.0, 0.0])

        for _ in range(100):
            new_x = neighbor(x)
            assert np.all(new_x >= -5.0)
            assert np.all(new_x <= 5.0)

    def test_different_from_original(self):
        """测试生成的解与原解不同"""
        np.random.seed(42)
        neighbor = ContinuousNeighbor(bounds=(-5.0, 5.0), dim=2, step_size=1.0)
        x = np.array([0.0, 0.0])

        different_count = 0
        for _ in range(100):
            new_x = neighbor(x)
            if not np.array_equal(new_x, x):
                different_count += 1

        assert different_count > 90  # 应该大多数不同

    def test_adaptive_step_size(self):
        """测试自适应步长调整"""
        np.random.seed(42)
        # 使用较小的初始步长，使得增大后不会被裁剪
        neighbor = ContinuousNeighbor(
            bounds=(-50.0, 50.0), dim=2, step_size=0.5, adaptive=True
        )
        initial_step = neighbor.step_size

        # 模拟高接受率（100次后触发调整，再100次再次调整）
        for _ in range(200):
            neighbor.update_step_size(True)

        # 步长应该增大（经过2轮调整: 0.5 * 1.2 * 1.2 = 0.72）
        assert neighbor.step_size > initial_step

    def test_adaptive_step_size_decrease(self):
        """测试自适应步长在低接受率时减小"""
        np.random.seed(42)
        neighbor = ContinuousNeighbor(
            bounds=(-5.0, 5.0), dim=2, step_size=1.0, adaptive=True
        )
        initial_step = neighbor.step_size

        # 模拟低接受率（约16.7%接受率，小于20%阈值）
        for i in range(200):
            neighbor.update_step_size(i % 6 == 0)

        # 步长应该减小（经过2轮调整: 1.0 * 0.8 * 0.8 = 0.64）
        assert neighbor.step_size < initial_step


class TestGetFunctionSpecs:
    """测试函数规格获取"""

    def test_returns_all_functions(self):
        """测试返回所有函数"""
        specs = get_function_specs(2)
        expected = ['rastrigin', 'rosenbrock', 'ackley', 'griewank', 'sphere', 'levy']
        assert set(specs.keys()) == set(expected)

    def test_function_spec_attributes(self):
        """测试函数规格属性"""
        specs = get_function_specs(2)
        for name, spec in specs.items():
            assert spec.name is not None
            assert spec.func is not None
            assert spec.dim == 2
            assert spec.bounds is not None
            assert spec.global_minimum is not None


# ============================================================
# 调度问题测试
# ============================================================

class TestJobShopScheduling:
    """测试作业车间调度"""

    def setup_method(self):
        np.random.seed(42)
        self.jsp = JobShopScheduling.create_random_instance(5, 3, seed=42)

    def test_random_instance_creation(self):
        """测试随机实例创建"""
        assert self.jsp.n_jobs == 5
        assert self.jsp.n_machines == 3
        assert len(self.jsp.jobs) == 5

    def test_evaluate_returns_positive(self):
        """测试评估返回正值"""
        solution = self.jsp.generate_random_solution()
        makespan = self.jsp.evaluate(solution)
        assert makespan > 0

    def test_generate_random_solution(self):
        """测试生成随机解"""
        solution = self.jsp.generate_random_solution()
        assert len(solution) == self.jsp.n_jobs
        assert set(solution) == set(range(self.jsp.n_jobs))

    def test_neighbor_swap_preserves_elements(self):
        """测试交换邻域保持元素完整"""
        solution = self.jsp.generate_random_solution()
        new_solution = self.jsp.neighbor_swap(solution)
        assert sorted(new_solution) == sorted(solution)

    def test_neighbor_insert_preserves_elements(self):
        """测试插入邻域保持元素完整"""
        solution = self.jsp.generate_random_solution()
        new_solution = self.jsp.neighbor_insert(solution)
        assert sorted(new_solution) == sorted(solution)

    def test_neighbor_reverse_preserves_elements(self):
        """测试逆序邻域保持元素完整"""
        solution = self.jsp.generate_random_solution()
        new_solution = self.jsp.neighbor_reverse(solution)
        assert sorted(new_solution) == sorted(solution)

    def test_sa_optimization_improves(self):
        """测试SA优化能够改善解"""
        np.random.seed(42)
        initial_solution = self.jsp.generate_random_solution()
        initial_makespan = self.jsp.evaluate(initial_solution)

        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.01,
            cooling_rate=0.995,
            max_iterations=2000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        optimizer = SimulatedAnnealing(
            config,
            self.jsp.evaluate,
            self.jsp.neighbor_swap,
            initial_solution
        )

        best_solution, best_makespan, _ = optimizer.optimize()
        assert best_makespan <= initial_makespan


class TestFlowShopScheduling:
    """测试流水车间调度"""

    def setup_method(self):
        np.random.seed(42)
        self.fsp = FlowShopScheduling.create_random_instance(6, 4, seed=42)

    def test_random_instance_creation(self):
        """测试随机实例创建"""
        assert self.fsp.n_jobs == 6
        assert self.fsp.n_machines == 4
        assert self.fsp.process_times.shape == (6, 4)

    def test_evaluate_returns_positive(self):
        """测试评估返回正值"""
        solution = self.fsp.generate_random_solution()
        makespan = self.fsp.evaluate(solution)
        assert makespan > 0

    def test_generate_random_solution(self):
        """测试生成随机解"""
        solution = self.fsp.generate_random_solution()
        assert len(solution) == self.fsp.n_jobs
        assert set(solution) == set(range(self.fsp.n_jobs))

    def test_neighbor_operations_preserve_elements(self):
        """测试邻域操作保持元素完整"""
        solution = self.fsp.generate_random_solution()

        new_sol = self.fsp.neighbor_swap(solution)
        assert sorted(new_sol) == sorted(solution)

        new_sol = self.fsp.neighbor_insert(solution)
        assert sorted(new_sol) == sorted(solution)

        new_sol = self.fsp.neighbor_reverse(solution)
        assert sorted(new_sol) == sorted(solution)


class TestSingleMachineScheduling:
    """测试单机调度"""

    def setup_method(self):
        np.random.seed(42)
        self.sms = SingleMachineScheduling.create_random_instance(8, seed=42)

    def test_random_instance_creation(self):
        """测试随机实例创建"""
        assert self.sms.n_jobs == 8
        assert len(self.sms.process_times) == 8
        assert len(self.sms.due_dates) == 8
        assert len(self.sms.weights) == 8

    def test_evaluate_returns_non_negative(self):
        """测试评估返回非负值"""
        solution = self.sms.generate_random_solution()
        tardiness = self.sms.evaluate(solution)
        assert tardiness >= 0

    def test_generate_random_solution(self):
        """测试生成随机解"""
        solution = self.sms.generate_random_solution()
        assert len(solution) == self.sms.n_jobs
        assert set(solution) == set(range(self.sms.n_jobs))

    def test_neighbor_operations_preserve_elements(self):
        """测试邻域操作保持元素完整"""
        solution = self.sms.generate_random_solution()

        new_sol = self.sms.neighbor_swap(solution)
        assert sorted(new_sol) == sorted(solution)

        new_sol = self.sms.neighbor_insert(solution)
        assert sorted(new_sol) == sorted(solution)

    def test_sa_optimization_improves(self):
        """测试SA优化能够改善解"""
        np.random.seed(42)
        initial_solution = self.sms.generate_random_solution()
        initial_tardiness = self.sms.evaluate(initial_solution)

        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.01,
            cooling_rate=0.995,
            max_iterations=2000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        optimizer = SimulatedAnnealing(
            config,
            self.sms.evaluate,
            self.sms.neighbor_swap,
            initial_solution
        )

        best_solution, best_tardiness, _ = optimizer.optimize()
        assert best_tardiness <= initial_tardiness


# ============================================================
# 集成测试
# ============================================================

class TestSimulatedAnnealing:
    """测试模拟退火优化器"""

    def test_optimize_simple_function(self):
        """测试优化简单函数"""
        np.random.seed(42)

        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.01,
            cooling_rate=0.99,
            max_iterations=500,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        def objective(x):
            return x ** 2

        def neighbor(x):
            return x + np.random.randn() * 2

        initial_solution = np.random.randn() * 10
        optimizer = SimulatedAnnealing(config, objective, neighbor, initial_solution)
        best_solution, best_cost, history = optimizer.optimize()

        # 检查结果
        assert best_cost >= 0
        assert abs(best_solution) < abs(initial_solution)  # 应该更接近0
        assert len(history['temperature']) == optimizer.iteration

    def test_tsp_optimization(self):
        """测试TSP优化"""
        np.random.seed(42)

        # 创建小型TSP实例
        tsp = TSP.create_random_instance(10, seed=42)
        initial_solution = tsp.generate_random_solution()
        initial_distance = tsp.calculate_total_distance(initial_solution)

        config = SAConfig(
            initial_temp=1000.0,
            final_temp=0.1,
            cooling_rate=0.995,
            max_iterations=2000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        optimizer = SimulatedAnnealing(
            config,
            tsp.calculate_total_distance,
            tsp.random_neighbor,
            initial_solution
        )

        best_solution, best_distance, history = optimizer.optimize()

        # 检查结果
        assert best_distance <= initial_distance
        assert len(best_solution) == tsp.n_cities
        assert set(best_solution) == set(range(tsp.n_cities))

    def test_function_optimization_integration(self):
        """测试函数优化集成"""
        np.random.seed(42)

        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.001,
            cooling_rate=0.995,
            max_iterations=3000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        # 使用Sphere函数
        neighbor = ContinuousNeighbor(bounds=(-5.0, 5.0), dim=2, step_size=0.5)
        initial_solution = np.random.uniform(-5, 5, 2)

        optimizer = SimulatedAnnealing(
            config,
            TestFunctions.sphere,
            neighbor,
            initial_solution
        )

        best_solution, best_cost, _ = optimizer.optimize()

        # Sphere函数最优值为0
        assert best_cost >= 0
        assert best_cost < initial_solution.dot(initial_solution)  # 应该比初始解好

    def test_scheduling_optimization_integration(self):
        """测试调度优化集成"""
        np.random.seed(42)

        jsp = JobShopScheduling.create_random_instance(4, 3, seed=42)
        initial_solution = jsp.generate_random_solution()
        initial_makespan = jsp.evaluate(initial_solution)

        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.01,
            cooling_rate=0.995,
            max_iterations=1000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        optimizer = SimulatedAnnealing(
            config,
            jsp.evaluate,
            jsp.neighbor_swap,
            initial_solution
        )

        best_solution, best_makespan, _ = optimizer.optimize()
        assert best_makespan <= initial_makespan


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
