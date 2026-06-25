# 产品说明：模拟退火算法

## 1. 产品概述

模拟退火算法库是一个Python优化工具包，提供完整的模拟退火算法实现，支持多种优化问题类型。

## 2. 核心功能

### 2.1 算法引擎

- **温度调度**：指数、线性、对数三种冷却策略
- **Metropolis准则**：标准接受概率计算
- **通用优化器**：支持任意目标函数和邻域函数

### 2.2 邻域操作

| 操作 | 说明 | 适用场景 |
|------|------|---------|
| Swap | 交换两个元素 | 排列问题 |
| Reverse | 反转子序列 | 路径优化 |
| Insert | 移动元素位置 | 调度问题 |
| Or-opt | 移动连续片段 | TSP优化 |
| 2-opt Swap | 交换两段子序列 | 路径优化 |
| Mixed | 混合多种操作 | 通用场景 |

### 2.3 问题支持

#### TSP旅行商
- 欧几里得距离计算
- 距离矩阵预计算
- 多种邻域操作

#### 函数优化
- 6种标准测试函数
- 自适应步长调整
- 边界处理

#### 调度问题
- 作业车间调度
- 流水车间调度
- 单机调度

### 2.4 可视化

- 收敛曲线绘制
- TSP路径可视化
- 冷却策略对比图

## 3. 使用指南

### 3.1 安装

```bash
pip install numpy matplotlib pytest
```

### 3.2 基本使用

```python
from src import SimulatedAnnealing, SAConfig, CoolingSchedule

# 配置
config = SAConfig(
    initial_temp=100.0,
    final_temp=0.01,
    cooling_rate=0.99,
    max_iterations=1000,
    cooling_schedule=CoolingSchedule.EXPONENTIAL
)

# 优化
optimizer = SimulatedAnnealing(config, objective, neighbor, initial_solution)
best_solution, best_cost, history = optimizer.optimize()
```

### 3.3 TSP求解

```python
from src import TSP, SimulatedAnnealing, SAConfig

# 创建TSP实例
tsp = TSP.create_random_instance(20, seed=42)
initial_solution = tsp.generate_random_solution()

# 配置并优化
config = SAConfig(initial_temp=1000.0, final_temp=0.1, max_iterations=5000)
optimizer = SimulatedAnnealing(
    config, tsp.calculate_total_distance, tsp.random_neighbor, initial_solution
)
best_path, best_distance, _ = optimizer.optimize()
```

### 3.4 函数优化

```python
from src import TestFunctions, ContinuousNeighbor, SimulatedAnnealing, SAConfig

# 使用Rastrigin函数
neighbor = ContinuousNeighbor(bounds=(-5.12, 5.12), dim=2)
config = SAConfig(initial_temp=100.0, final_temp=0.001, max_iterations=5000)

optimizer = SimulatedAnnealing(
    config, TestFunctions.rastrigin, neighbor, initial_solution
)
best_x, best_value, _ = optimizer.optimize()
```

### 3.5 调度优化

```python
from src import JobShopScheduling, SimulatedAnnealing, SAConfig

# 创建调度实例
jsp = JobShopScheduling.create_random_instance(10, 5)
initial_solution = jsp.generate_random_solution()

# 优化
config = SAConfig(initial_temp=100.0, final_temp=0.01, max_iterations=3000)
optimizer = SimulatedAnnealing(
    config, jsp.evaluate, jsp.neighbor_swap, initial_solution
)
best_schedule, best_makespan, _ = optimizer.optimize()
```

## 4. API参考

### 4.1 SAConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| initial_temp | float | 100.0 | 初始温度 |
| final_temp | float | 0.01 | 终止温度 |
| cooling_rate | float | 0.99 | 冷却速率 |
| max_iterations | int | 1000 | 最大迭代次数 |
| cooling_schedule | CoolingSchedule | EXPONENTIAL | 冷却策略 |

### 4.2 SimulatedAnnealing

#### `__init__(config, objective_func, neighbor_func, initial_solution)`
创建优化器实例。

#### `optimize() -> Tuple[Any, float, dict]`
执行优化，返回(最优解, 最优成本, 历史记录)。

#### `step() -> Tuple[bool, float]`
执行单步迭代，返回(是否接受, 接受概率)。

#### `calculate_acceptance_probability(delta_cost, temperature) -> float`
计算Metropolis接受概率。

### 4.3 NeighborhoodOps

#### `swap(solution) -> List[int]`
交换两个随机位置。

#### `reverse(solution) -> List[int]`
反转随机子序列。

#### `insert(solution) -> List[int]`
将随机元素移动到随机位置。

#### `or_opt(solution, max_segment=3) -> List[int]`
移动连续片段到随机位置。

#### `create_mixed_neighbor(ops=None, weights=None) -> Callable`
创建混合邻域函数。

### 4.4 TSP

#### `__init__(cities: List[City])`
创建TSP实例。

#### `calculate_total_distance(path: List[int]) -> float`
计算路径总距离。

#### `create_random_instance(n_cities, seed=None) -> TSP`
创建随机TSP实例。

### 4.5 TestFunctions

提供6种标准测试函数：
- `sphere(x)` - Sphere函数
- `rastrigin(x)` - Rastrigin函数
- `rosenbrock(x)` - Rosenbrock函数
- `ackley(x)` - Ackley函数
- `griewank(x)` - Griewank函数
- `levy(x)` - Levy函数

### 4.6 调度问题类

#### JobShopScheduling
- `evaluate(permutation) -> float`
- `neighbor_swap(solution) -> List[int]`
- `neighbor_insert(solution) -> List[int]`
- `neighbor_reverse(solution) -> List[int]`
- `create_random_instance(n_jobs, n_machines, ...) -> JobShopScheduling`

#### FlowShopScheduling
- 类似JobShopScheduling接口

#### SingleMachineScheduling
- `evaluate(permutation) -> float` (加权总延迟)
- `neighbor_swap(solution) -> List[int]`
- `neighbor_insert(solution) -> List[int]`

## 5. 性能指标

### 5.1 收敛性

- 理论上能收敛到全局最优
- 实际收敛速度依赖参数设置
- 典型迭代次数：1000-10000

### 5.2 时间复杂度

- 单步迭代：O(f(n))，f(n)为目标函数复杂度
- 总复杂度：O(max_iterations * f(n))

### 5.3 空间复杂度

- O(n)存储当前解和最优解
- O(max_iterations)存储历史记录

## 6. 最佳实践

### 6.1 参数调优

1. **初始温度**：应该足够高，使得初始接受率约80%
2. **冷却速率**：通常0.95-0.999，越慢越精确
3. **终止温度**：应该足够低，使得几乎不接受差解
4. **迭代次数**：与问题规模成正比

### 6.2 邻域选择

- TSP：Reverse (2-opt) 效果最好
- 调度问题：Swap 或 Insert
- 连续优化：高斯扰动

### 6.3 多次运行

由于SA的随机性，建议多次运行取最优结果。

## 7. 常见问题

### Q1: 为什么结果不稳定？
A: SA是随机算法，每次运行结果不同。增加迭代次数或多次运行取最优。

### Q2: 如何选择初始温度？
A: 可以通过预实验确定，使得初始接受率在70-90%之间。

### Q3: 收敛太慢怎么办？
A: 尝试增大冷却速率、增加迭代次数、或改进邻域操作。

### Q4: 陷入局部最优怎么办？
A: 增大初始温度、使用更慢的冷却策略、或尝试重启策略。
