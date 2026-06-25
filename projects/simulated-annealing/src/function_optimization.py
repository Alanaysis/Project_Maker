"""
函数优化模块

实现常见的测试函数和连续空间优化：
- Rastrigin函数（多模态）
- Rosenbrock函数（山谷形）
- Ackley函数（指数型）
- Griewank函数（振荡型）
- Sphere函数（简单凸函数）
"""

import numpy as np
from typing import Callable, Tuple, List, Dict
from dataclasses import dataclass


@dataclass
class FunctionSpec:
    """函数规格"""
    name: str
    func: Callable
    dim: int
    bounds: Tuple[float, float]
    global_minimum: float
    global_optimum: np.ndarray


class TestFunctions:
    """测试函数集合"""

    @staticmethod
    def rastrigin(x: np.ndarray) -> float:
        """
        Rastrigin函数

        特点：多模态，大量局部最小值
        全局最小值：f(0, ..., 0) = 0
        搜索范围：[-5.12, 5.12]
        """
        n = len(x)
        return 10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x))

    @staticmethod
    def rosenbrock(x: np.ndarray) -> float:
        """
        Rosenbrock函数（香蕉函数）

        特点：全局最小值在狭长山谷中
        全局最小值：f(1, ..., 1) = 0
        搜索范围：[-5, 10]
        """
        return np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)

    @staticmethod
    def ackley(x: np.ndarray) -> float:
        """
        Ackley函数

        特点：指数型，中心有大面积平坦区域
        全局最小值：f(0, ..., 0) = 0
        搜索范围：[-32.768, 32.768]
        """
        n = len(x)
        sum1 = np.sum(x ** 2)
        sum2 = np.sum(np.cos(2 * np.pi * x))
        return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e

    @staticmethod
    def griewank(x: np.ndarray) -> float:
        """
        Griewank函数

        特点：振荡型，大量局部最小值
        全局最小值：f(0, ..., 0) = 0
        搜索范围：[-600, 600]
        """
        sum_part = np.sum(x ** 2) / 4000
        prod_part = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
        return sum_part - prod_part + 1

    @staticmethod
    def sphere(x: np.ndarray) -> float:
        """
        Sphere函数

        特点：简单凸函数，单峰
        全局最小值：f(0, ..., 0) = 0
        搜索范围：[-5.12, 5.12]
        """
        return np.sum(x ** 2)

    @staticmethod
    def michalewicz(x: np.ndarray, m: int = 10) -> float:
        """
        Michalewicz函数

        特点：多模态，m控制山谷的陡峭程度
        全局最小值：依赖维度
        搜索范围：[0, pi]
        """
        n = len(x)
        i = np.arange(1, n + 1)
        return -np.sum(np.sin(x) * (np.sin(i * x ** 2 / np.pi)) ** (2 * m))

    @staticmethod
    def levy(x: np.ndarray) -> float:
        """
        Levy函数

        特点：多模态
        全局最小值：f(1, ..., 1) = 0
        搜索范围：[-10, 10]
        """
        n = len(x)
        w = 1 + (x - 1) / 4

        term1 = np.sin(np.pi * w[0]) ** 2
        term3 = (w[-1] - 1) ** 2 * (1 + np.sin(2 * np.pi * w[-1]) ** 2)
        term2 = np.sum((w[:-1] - 1) ** 2 * (1 + 10 * np.sin(np.pi * w[:-1] + 1) ** 2))

        return term1 + term2 + term3


def get_function_specs(dim: int = 2) -> Dict[str, FunctionSpec]:
    """
    获取所有测试函数的规格

    参数:
        dim: 问题维度

    返回:
        函数规格字典
    """
    specs = {
        'rastrigin': FunctionSpec(
            name='Rastrigin',
            func=TestFunctions.rastrigin,
            dim=dim,
            bounds=(-5.12, 5.12),
            global_minimum=0.0,
            global_optimum=np.zeros(dim)
        ),
        'rosenbrock': FunctionSpec(
            name='Rosenbrock',
            func=TestFunctions.rosenbrock,
            dim=dim,
            bounds=(-5.0, 10.0),
            global_minimum=0.0,
            global_optimum=np.ones(dim)
        ),
        'ackley': FunctionSpec(
            name='Ackley',
            func=TestFunctions.ackley,
            dim=dim,
            bounds=(-32.768, 32.768),
            global_minimum=0.0,
            global_optimum=np.zeros(dim)
        ),
        'griewank': FunctionSpec(
            name='Griewank',
            func=TestFunctions.griewank,
            dim=dim,
            bounds=(-600.0, 600.0),
            global_minimum=0.0,
            global_optimum=np.zeros(dim)
        ),
        'sphere': FunctionSpec(
            name='Sphere',
            func=TestFunctions.sphere,
            dim=dim,
            bounds=(-5.12, 5.12),
            global_minimum=0.0,
            global_optimum=np.zeros(dim)
        ),
        'levy': FunctionSpec(
            name='Levy',
            func=TestFunctions.levy,
            dim=dim,
            bounds=(-10.0, 10.0),
            global_minimum=0.0,
            global_optimum=np.ones(dim)
        ),
    }
    return specs


class ContinuousNeighbor:
    """
    连续空间邻域生成器

    用于连续优化问题的邻域解生成。
    """

    def __init__(
        self,
        bounds: Tuple[float, float],
        dim: int,
        step_size: float = 1.0,
        adaptive: bool = True
    ):
        """
        初始化邻域生成器

        参数:
            bounds: 搜索范围 (min, max)
            dim: 问题维度
            step_size: 初始步长
            adaptive: 是否自适应调整步长
        """
        self.bounds = bounds
        self.dim = dim
        self.step_size = step_size
        self.adaptive = adaptive
        self.accepted_count = 0
        self.total_count = 0

    def __call__(self, x: np.ndarray) -> np.ndarray:
        """
        生成邻域解

        参数:
            x: 当前解

        返回:
            新解
        """
        # 高斯扰动
        perturbation = np.random.randn(self.dim) * self.step_size
        new_x = x + perturbation

        # 边界处理：反射
        low, high = self.bounds
        new_x = np.clip(new_x, low, high)

        return new_x

    def update_step_size(self, accepted: bool):
        """
        自适应更新步长

        参数:
            accepted: 是否接受新解
        """
        if not self.adaptive:
            return

        self.total_count += 1
        if accepted:
            self.accepted_count += 1

        # 每100步调整一次
        if self.total_count % 100 == 0 and self.total_count > 0:
            rate = self.accepted_count / self.total_count
            if rate > 0.5:
                self.step_size *= 1.2  # 接受率高，增大步长
            elif rate < 0.2:
                self.step_size *= 0.8  # 接受率低，减小步长

            # 限制步长范围
            low, high = self.bounds
            max_step = (high - low) / 10
            self.step_size = np.clip(self.step_size, 0.01, max_step)

            # 重置计数
            self.accepted_count = 0
            self.total_count = 0


def demo_function_optimization():
    """演示函数优化"""
    print("函数优化演示")
    print("=" * 50)

    from .simulated_annealing import SimulatedAnnealing, SAConfig, CoolingSchedule

    # 获取测试函数
    dim = 2
    specs = get_function_specs(dim)

    for name, spec in specs.items():
        print(f"\n优化 {spec.name} 函数 (维度={dim})")
        print("-" * 40)

        # 配置
        config = SAConfig(
            initial_temp=100.0,
            final_temp=0.001,
            cooling_rate=0.995,
            max_iterations=5000,
            cooling_schedule=CoolingSchedule.EXPONENTIAL
        )

        # 邻域函数
        neighbor = ContinuousNeighbor(spec.bounds, dim, step_size=0.5)

        # 初始解
        low, high = spec.bounds
        initial_solution = np.random.uniform(low, high, dim)

        # 优化
        optimizer = SimulatedAnnealing(
            config,
            spec.func,
            neighbor,
            initial_solution
        )

        best_solution, best_cost, history = optimizer.optimize()

        print(f"  初始解: {initial_solution}")
        print(f"  最优解: {best_solution}")
        print(f"  最优值: {best_cost:.6f}")
        print(f"  理论最优: {spec.global_minimum}")
        print(f"  误差: {abs(best_cost - spec.global_minimum):.6f}")

    print("\n演示完成!")


if __name__ == "__main__":
    demo_function_optimization()
