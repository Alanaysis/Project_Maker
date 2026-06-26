"""
重启机制模块 (Restart Mechanism)

当模拟退火算法陷入局部最优时，重启机制可以帮助算法跳出当前区域，
继续搜索更好的解。

重启策略：
1. 完全重启：重新开始搜索，使用新的初始解
2. 部分重启：在当前解附近重新开始
3. 多样化重启：使用历史最优解作为新起点
4. 自适应重启：根据收敛状态决定何时重启
"""

import random
import copy
from typing import Optional, Callable, Any, List, Tuple


class RestartManager:
    """
    重启管理器

    管理模拟退火算法的重启策略。
    """

    def __init__(
        self,
        max_restarts: int = 5,
        restart_threshold: int = 1000,
        diversification_probability: float = 0.3,
    ):
        """
        Args:
            max_restarts: 最大重启次数
            restart_threshold: 连续未改进次数超过此值触发重启
            diversification_probability: 多样化重启的概率
        """
        self.max_restarts = max_restarts
        self.restart_threshold = restart_threshold
        self.diversification_probability = diversification_probability

        self._restart_count = 0
        self._no_improve_count = 0
        self._history: List[Tuple[Any, float]] = []

    def check_restart(
        self,
        current_energy: float,
        best_energy: float,
        iteration: int,
    ) -> bool:
        """
        检查是否需要重启

        Args:
            current_energy: 当前能量
            best_energy: 历史最优能量
            iteration: 当前迭代次数

        Returns:
            True 如果需要重启
        """
        if best_energy < current_energy:
            self._no_improve_count = 0
        else:
            self._no_improve_count += 1

        if self._restart_count >= self.max_restarts:
            return False

        return self._no_improve_count >= self.restart_threshold

    def record_result(self, solution: Any, energy: float):
        """记录当前结果"""
        self._history.append((copy.deepcopy(solution), energy))

    def get_restart_solution(
        self,
        initial_solution_generator: Callable,
        best_solution: Any,
        best_energy: float,
    ) -> Any:
        """
        生成重启解

        以一定概率使用多样化策略，否则使用初始解生成器。

        Args:
            initial_solution_generator: 初始解生成函数
            best_solution: 当前最优解
            best_energy: 当前最优能量

        Returns:
            新的初始解
        """
        # 多样化重启：基于历史最优解
        if (
            len(self._history) > 0
            and random.random() < self.diversification_probability
        ):
            # 从历史记录中随机选择一个解，在其附近扰动
            history_sol, _ = random.choice(self._history)
            return self._perturb_solution(history_sol, magnitude=1.0)

        # 标准重启：使用初始解生成器
        return initial_solution_generator()

    def _perturb_solution(self, solution: Any, magnitude: float = 1.0) -> Any:
        """对解进行扰动"""
        if isinstance(solution, list):
            return [x + random.gauss(0, magnitude) for x in solution]
        elif isinstance(solution, (int, float)):
            return solution + random.gauss(0, magnitude)
        else:
            # 尝试作为列表处理
            arr = list(solution)
            return [x + random.gauss(0, magnitude) for x in arr]

    @property
    def restart_count(self) -> int:
        return self._restart_count

    def trigger_restart(self):
        """触发一次重启"""
        self._restart_count += 1
        self._no_improve_count = 0

    def reset(self):
        """重置管理器状态"""
        self._restart_count = 0
        self._no_improve_count = 0
        self._history = []


class DiversificationRestart:
    """
    多样化重启策略

    提供多种多样化策略来生成新的搜索起点：
    1. 随机扰动：在最优解附近随机扰动
    2. 历史混合：从历史解中混合生成新解
    3. 跳跃重启：跳到历史最优解附近
    """

    def __init__(self, strategies: Optional[List[str]] = None):
        if strategies is None:
            strategies = ["perturbation", "mixing", "jump"]
        self.strategies = strategies

    def generate_restart_point(
        self,
        history: List[Tuple[Any, float]],
        best_solution: Any,
        best_energy: float,
    ) -> Any:
        """
        生成重启点

        Args:
            history: 历史解列表 (解, 能量)
            best_solution: 当前最优解
            best_energy: 当前最优能量

        Returns:
            新的搜索起点
        """
        if not history:
            return best_solution

        strategy = random.choice(self.strategies)

        if strategy == "perturbation":
            return self._perturbation(history, best_solution, best_energy)
        elif strategy == "mixing":
            return self._mixing(history)
        elif strategy == "jump":
            return self._jump(history, best_solution, best_energy)
        else:
            return best_solution

    def _perturbation(
        self, history: List[Tuple[Any, float]], best_sol: Any, best_energy: float
    ) -> Any:
        """在最优解附近扰动"""
        if isinstance(best_sol, list):
            return [x + random.gauss(0, 0.1 * max(abs(x), 1.0)) for x in best_sol]
        else:
            return best_sol + random.gauss(0, 0.1 * max(abs(best_sol), 1.0))

    def _mixing(self, history: List[Tuple[Tuple[Any, float]]]) -> Any:
        """从历史解中混合生成新解"""
        if len(history) < 2:
            return history[0][0] if history else None

        # 选择两个历史解进行混合
        s1, _ = random.choice(history)
        s2, _ = random.choice(history)

        if isinstance(s1, list) and isinstance(s2, list):
            lam = random.random()
            return [lam * a + (1 - lam) * b for a, b in zip(s1, s2)]

        return s1

    def _jump(
        self, history: List[Tuple[Any, float]], best_sol: Any, best_energy: float
    ) -> Any:
        """跳到历史最优解附近"""
        # 找到历史中最好的解（可能比当前最优更好）
        best_history_sol = min(history, key=lambda x: x[1])[0]

        if isinstance(best_history_sol, list):
            return [x + random.gauss(0, 0.05 * max(abs(x), 1.0)) for x in best_history_sol]
        else:
            return best_history_sol + random.gauss(0, 0.05 * max(abs(best_history_sol), 1.0))
