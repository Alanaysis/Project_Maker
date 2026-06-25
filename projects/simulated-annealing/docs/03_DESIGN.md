# 架构设计：模拟退火算法

## 1. 系统架构

### 1.1 模块划分

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
│   └── test_simulated_annealing.py
├── examples/
│   └── tsp_example.py
└── docs/
```

### 1.2 依赖关系

```
visualization ──┐
                 │
tsp ────────────┤
                 │
function_optimization ──┤
                        │
scheduling ─────────────┤
                        │
neighborhood ───────────┤
                        │
simulated_annealing ◄───┘
```

## 2. 核心类设计

### 2.1 SimulatedAnnealing

主优化器类，实现SA算法的核心逻辑。

```python
class SimulatedAnnealing:
    def __init__(self, config, objective_func, neighbor_func, initial_solution)
    def calculate_acceptance_probability(self, delta_cost, temperature) -> float
    def cooling_exponential(self) -> float
    def cooling_linear(self) -> float
    def cooling_logarithmic(self) -> float
    def update_temperature(self)
    def step(self) -> Tuple[bool, float]
    def should_stop(self) -> bool
    def optimize(self) -> Tuple[Any, float, dict]
```

**设计要点**：
- 泛型设计，支持任意类型的解
- 策略模式支持多种冷却策略
- 记录优化历史用于分析

### 2.2 SAConfig

配置数据类，封装算法参数。

```python
@dataclass
class SAConfig:
    initial_temp: float = 100.0
    final_temp: float = 0.01
    cooling_rate: float = 0.99
    max_iterations: int = 1000
    cooling_schedule: CoolingSchedule = CoolingSchedule.EXPONENTIAL
```

### 2.3 NeighborhoodOps

邻域操作工具类，提供多种邻域操作。

```python
class NeighborhoodOps:
    @staticmethod
    def swap(solution: List[int]) -> List[int]
    @staticmethod
    def reverse(solution: List[int]) -> List[int]
    @staticmethod
    def insert(solution: List[int]) -> List[int]
    @staticmethod
    def or_opt(solution: List[int], max_segment: int = 3) -> List[int]
    @staticmethod
    def two_opt_swap(solution: List[int]) -> List[int]
    @staticmethod
    def create_mixed_neighbor(ops, weights) -> Callable
```

**设计要点**：
- 所有操作都是静态方法，无状态
- 操作不修改原始解，返回新解
- 支持混合邻域策略

### 2.4 TSP

旅行商问题类，封装TSP的逻辑。

```python
class TSP:
    def __init__(self, cities: List[City])
    def calculate_total_distance(self, path: List[int]) -> float
    def random_neighbor(self, path: List[int]) -> List[int]
    def or_opt_neighbor(self, path: List[int]) -> List[int]
    def generate_random_solution(self) -> List[int]
    @staticmethod
    def create_random_instance(n_cities, seed) -> TSP
```

### 2.5 TestFunctions

测试函数集合，用于函数优化。

```python
class TestFunctions:
    @staticmethod
    def rastrigin(x: np.ndarray) -> float
    @staticmethod
    def rosenbrock(x: np.ndarray) -> float
    @staticmethod
    def ackley(x: np.ndarray) -> float
    @staticmethod
    def griewank(x: np.ndarray) -> float
    @staticmethod
    def sphere(x: np.ndarray) -> float
    @staticmethod
    def michalewicz(x: np.ndarray, m: int = 10) -> float
    @staticmethod
    def levy(x: np.ndarray) -> float
```

### 2.6 ContinuousNeighbor

连续空间邻域生成器。

```python
class ContinuousNeighbor:
    def __init__(self, bounds, dim, step_size=1.0, adaptive=True)
    def __call__(self, x: np.ndarray) -> np.ndarray
    def update_step_size(self, accepted: bool)
```

**设计要点**：
- 可调用对象，兼容SA框架
- 自适应步长调整
- 边界处理

### 2.7 调度问题类

```python
class JobShopScheduling:
    def __init__(self, jobs: List[Job], n_machines: int)
    def evaluate(self, permutation: List[int]) -> float
    def generate_random_solution(self) -> List[int]
    def neighbor_swap(self, solution) -> List[int]
    def neighbor_insert(self, solution) -> List[int]
    def neighbor_reverse(self, solution) -> List[int]
    @staticmethod
    def create_random_instance(n_jobs, n_machines, ...) -> JobShopScheduling

class FlowShopScheduling:
    def __init__(self, process_times: np.ndarray)
    def evaluate(self, permutation: List[int]) -> float
    # ... 类似接口

class SingleMachineScheduling:
    def __init__(self, process_times, due_dates, weights)
    def evaluate(self, permutation: List[int]) -> float
    # ... 类似接口
```

## 3. 数据流设计

### 3.1 优化流程

```
初始解
  │
  ▼
┌─────────────────┐
│  生成邻域解      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  计算目标函数值  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  计算接受概率    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  接受/拒绝决策   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  更新温度        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  检查终止条件    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
  继续      返回最优解
```

### 3.2 数据结构

#### 解的表示
- 排列问题：List[int]（如TSP、调度）
- 连续问题：np.ndarray（如函数优化）

#### 历史记录
```python
history = {
    'temperature': [],      # 温度历史
    'current_cost': [],     # 当前成本历史
    'best_cost': [],        # 最优成本历史
    'acceptance_rate': float # 总接受率
}
```

## 4. 接口设计

### 4.1 目标函数接口

```python
def objective(solution) -> float:
    """返回解的成本值（最小化）"""
    pass
```

### 4.2 邻域函数接口

```python
def neighbor(solution) -> solution_type:
    """返回一个新的候选解"""
    pass
```

### 4.3 使用示例

```python
# 1. 配置
config = SAConfig(
    initial_temp=1000.0,
    final_temp=0.1,
    cooling_rate=0.995,
    max_iterations=5000
)

# 2. 创建优化器
optimizer = SimulatedAnnealing(
    config=config,
    objective_func=my_objective,
    neighbor_func=my_neighbor,
    initial_solution=initial_solution
)

# 3. 执行优化
best_solution, best_cost, history = optimizer.optimize()
```

## 5. 扩展设计

### 5.1 自定义冷却策略

```python
class CustomCoolingSchedule(Enum):
    CUSTOM = "custom"

# 在SimulatedAnnealing中添加
def cooling_custom(self) -> float:
    # 自定义冷却逻辑
    pass
```

### 5.2 自定义邻域操作

```python
def my_custom_neighbor(solution: List[int]) -> List[int]:
    # 自定义邻域逻辑
    return new_solution

# 直接传入SA
optimizer = SimulatedAnnealing(
    config, objective, my_custom_neighbor, initial_solution
)
```

### 5.3 自定义接受准则

```python
class CustomSA(SimulatedAnnealing):
    def calculate_acceptance_probability(self, delta_cost, temperature):
        # 自定义接受逻辑
        return probability
```

## 6. 性能优化

### 6.1 距离矩阵预计算

TSP问题中，预先计算城市间距离矩阵，避免重复计算。

### 6.2 增量更新

对于某些问题，可以增量更新目标函数值，而不是重新计算。

### 6.3 并行化

- 多线程并行评估
- 岛屿模型并行搜索

## 7. 错误处理

### 7.1 参数验证

- 温度参数必须为正数
- 冷却速率必须在(0, 1)之间
- 最大迭代次数必须为正整数

### 7.2 边界处理

- 连续优化的边界裁剪
- 排列问题的合法性检查
