# 开发指南：模拟退火算法

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pip 或 conda

### 1.2 依赖安装

```bash
pip install numpy matplotlib pytest
```

### 1.3 项目结构

```
simulated-annealing/
├── src/
│   ├── __init__.py              # 包入口
│   ├── simulated_annealing.py   # 核心算法
│   ├── neighborhood.py          # 邻域操作
│   ├── tsp.py                   # TSP问题
│   ├── function_optimization.py # 函数优化
│   ├── scheduling.py            # 调度问题
│   └── visualization.py         # 可视化
├── tests/
│   ├── __init__.py
│   └── test_simulated_annealing.py
├── examples/
│   └── tsp_example.py
├── docs/
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 2. 编码规范

### 2.1 Python规范

- 遵循PEP 8
- 使用类型注解
- 编写文档字符串

### 2.2 命名规范

- 类名：PascalCase
- 函数名：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有方法：_leading_underscore

### 2.3 文档字符串

```python
def function_name(param1: int, param2: str) -> bool:
    """
    函数简短描述

    详细描述（如果需要）。

    参数:
        param1: 参数1说明
        param2: 参数2说明

    返回:
        返回值说明

    异常:
        ValueError: 异常说明
    """
    pass
```

## 3. 测试指南

### 3.1 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试类
pytest tests/test_simulated_annealing.py::TestSAConfig -v

# 运行带覆盖率
pytest tests/ -v --cov=src
```

### 3.2 测试结构

```python
class TestClassName:
    """测试类说明"""

    def setup_method(self):
        """测试前设置"""
        pass

    def test_method_name(self):
        """测试方法说明"""
        # Arrange - 准备
        # Act - 执行
        # Assert - 断言
        pass
```

### 3.3 测试覆盖

- 核心算法：温度调度、接受准则
- 邻域操作：所有操作的正确性
- 问题求解：TSP、函数优化、调度问题
- 边界条件：异常输入、极端参数

## 4. 开发流程

### 4.1 添加新功能

1. 在`src/`中添加新模块
2. 在`__init__.py`中导出
3. 编写单元测试
4. 更新文档
5. 运行测试确认通过

### 4.2 添加新的邻域操作

```python
# 在 neighborhood.py 中添加
@staticmethod
def my_new_operation(solution: List[int]) -> List[int]:
    """
    新操作说明

    参数:
        solution: 当前解

    返回:
        新解
    """
    new_solution = solution.copy()
    # 操作逻辑
    return new_solution
```

### 4.3 添加新的测试函数

```python
# 在 function_optimization.py 中添加
@staticmethod
def my_new_function(x: np.ndarray) -> float:
    """
    新函数说明

    参数:
        x: 输入向量

    返回:
        函数值
    """
    # 函数逻辑
    return value
```

### 4.4 添加新的调度问题

```python
# 在 scheduling.py 中添加
class MySchedulingProblem:
    """自定义调度问题"""

    def __init__(self, ...):
        # 初始化
        pass

    def evaluate(self, permutation: List[int]) -> float:
        """评估调度方案"""
        pass

    def generate_random_solution(self) -> List[int]:
        """生成随机解"""
        pass

    def neighbor_swap(self, solution: List[int]) -> List[int]:
        """交换邻域"""
        pass
```

## 5. 调试技巧

### 5.1 打印优化过程

```python
optimizer = SimulatedAnnealing(config, objective, neighbor, initial_solution)

while not optimizer.should_stop():
    accepted, prob = optimizer.step()
    if optimizer.iteration % 100 == 0:
        print(f"Iter {optimizer.iteration}: "
              f"Temp={optimizer.temperature:.4f}, "
              f"Cost={optimizer.current_cost:.4f}, "
              f"Best={optimizer.best_cost:.4f}")
```

### 5.2 可视化调试

```python
from src.visualization import plot_convergence

best_solution, best_cost, history = optimizer.optimize()
fig = plot_convergence(history)
plt.show()
```

### 5.3 参数实验

```python
# 对比不同参数
for cooling_rate in [0.95, 0.99, 0.999]:
    config = SAConfig(cooling_rate=cooling_rate)
    optimizer = SimulatedAnnealing(config, objective, neighbor, initial)
    _, cost, _ = optimizer.optimize()
    print(f"Rate={cooling_rate}: Cost={cost:.4f}")
```

## 6. 性能优化

### 6.1 目标函数优化

- 使用numpy向量化操作
- 预计算可重用的中间结果
- 避免重复计算

### 6.2 邻域函数优化

- 减少内存分配
- 使用原地操作
- 批量生成候选解

### 6.3 并行化

```python
from concurrent.futures import ProcessPoolExecutor

def parallel_sa(problem, n_runs=10):
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(run_sa, problem)
            for _ in range(n_runs)
        ]
        results = [f.result() for f in futures]
    return min(results, key=lambda x: x[1])
```

## 7. 扩展开发

### 7.1 自定义冷却策略

```python
class CoolingSchedule(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    CUSTOM = "custom"  # 新增

class SimulatedAnnealing:
    def cooling_custom(self) -> float:
        """自定义冷却逻辑"""
        # 实现
        pass

    def update_temperature(self):
        if self.config.cooling_schedule == CoolingSchedule.CUSTOM:
            self.temperature = self.cooling_custom()
        # ...
```

### 7.2 自定义接受准则

```python
class CustomSimulatedAnnealing(SimulatedAnnealing):
    def calculate_acceptance_probability(self, delta_cost, temperature):
        """自定义接受逻辑"""
        if delta_cost <= 0:
            return 1.0
        # 使用不同的公式
        return 1.0 / (1.0 + delta_cost / temperature)
```

### 7.3 添加重启策略

```python
class RestartSimulatedAnnealing(SimulatedAnnealing):
    def optimize_with_restart(self, n_restarts=10):
        """带重启的优化"""
        best_overall = None
        best_cost_overall = float('inf')

        for i in range(n_restarts):
            # 重新初始化
            self.current_solution = self.generate_initial_solution()
            self.temperature = self.config.initial_temp
            self.iteration = 0

            # 运行SA
            solution, cost, history = self.optimize()

            if cost < best_cost_overall:
                best_overall = solution
                best_cost_overall = cost

        return best_overall, best_cost_overall
```

## 8. 版本管理

### 8.1 版本号规则

- 主版本.次版本.修订号
- 例如：2.0.0

### 8.2 更新日志

#### v2.0.0
- 新增邻域操作模块
- 新增函数优化模块
- 新增调度问题模块
- 完善测试覆盖

#### v1.0.0
- 初始版本
- 核心算法实现
- TSP问题支持
- 基本可视化

## 9. 贡献指南

### 9.1 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

### 9.2 Pull Request

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request
5. 等待审核

### 9.3 代码审核

- 测试通过
- 文档完整
- 代码风格一致
- 无明显性能问题
