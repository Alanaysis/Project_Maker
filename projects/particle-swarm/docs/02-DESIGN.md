# 02 - 架构设计

## 1. 整体架构

```
particle-swarm/
├── src/                         # 源代码
│   ├── __init__.py             # 包初始化
│   ├── particle.py             # 粒子类
│   ├── swarm.py                # 粒子群类（核心算法）
│   ├── functions.py            # 测试函数
│   └── visualizer.py           # 可视化
├── tests/                       # 测试
│   ├── test_particle.py        # 粒子测试
│   ├── test_swarm.py           # 粒子群测试
│   └── test_functions.py       # 测试函数测试
├── examples/                    # 示例
│   ├── basic_pso.py            # 基础示例
│   ├── function_optimization.py # 多函数优化
│   └── parameter_tuning.py     # 参数调优
└── docs/                        # 文档
```

## 2. 核心类设计

### 2.1 Particle 类

**职责**：表示搜索空间中的单个粒子

**属性**：
- `position`: 当前位置向量 (np.ndarray)
- `velocity`: 当前速度向量 (np.ndarray)
- `personal_best`: 个体历史最佳位置 (np.ndarray)
- `personal_best_fitness`: 个体历史最佳适应度 (float)
- `dimensions`: 搜索空间维度 (int)

**方法**：
- `evaluate(objective_function)`: 评估当前位置
- `update_velocity(global_best, w, c1, c2)`: 更新速度
- `update_position(bounds)`: 更新位置

### 2.2 Swarm 类

**职责**：管理粒子群，执行 PSO 算法

**属性**：
- `particles`: 粒子列表
- `global_best`: 全局最佳位置
- `global_best_fitness`: 全局最佳适应度
- `convergence_history`: 收敛历史

**方法**：
- `optimize(objective_function)`: 执行优化
- `reset()`: 重置状态

### 2.3 PSOConfig 类

**职责**：存储 PSO 配置参数

**参数**：
- `n_particles`: 粒子数量
- `dimensions`: 维度
- `bounds`: 搜索边界
- `w, c1, c2`: 速度更新参数
- `w_strategy`: 惯性权重策略
- `max_iterations`: 最大迭代次数
- `tolerance`: 收敛阈值
- `random_seed`: 随机种子

### 2.4 PSOResult 类

**职责**：存储优化结果

**属性**：
- `best_position`: 最佳位置
- `best_fitness`: 最佳适应度
- `iterations`: 迭代次数
- `convergence_history`: 收敛历史
- `particle_trajectories`: 粒子轨迹（可选）

## 3. 设计模式

### 3.1 策略模式

惯性权重策略使用策略模式：
- `fixed`: 固定权重
- `linear_decay`: 线性递减
- `adaptive`: 自适应

### 3.2 数据类

使用 `@dataclass` 装饰器简化配置和结果类的定义。

### 3.3 回调机制

`optimize()` 方法支持回调函数，允许用户在每代结束后执行自定义操作。

## 4. 接口设计

### 4.1 基本使用

```python
from src import Swarm, PSOConfig, sphere

config = PSOConfig(n_particles=30, dimensions=2)
swarm = Swarm(config)
result = swarm.optimize(sphere)
```

### 4.2 高级使用

```python
config = PSOConfig(
    n_particles=50,
    dimensions=10,
    bounds=(-100, 100),
    w_strategy="linear_decay",
    max_iterations=500,
    track_trajectories=True,
)

def my_callback(iteration, fitness, position):
    print(f"代 {iteration}: {fitness}")

swarm = Swarm(config)
result = swarm.optimize(sphere, callback=my_callback)
```

## 5. 扩展性设计

### 5.1 添加新的测试函数

在 `functions.py` 中添加新函数并注册到 `BENCHMARK_FUNCTIONS`：

```python
def my_function(x):
    return float(np.sum(x**2))

BENCHMARK_FUNCTIONS["my_function"] = {
    "function": my_function,
    "bounds": (-100.0, 100.0),
    "optimal": 0.0,
    "optimal_position": lambda d: np.zeros(d),
    "description": "我的测试函数",
}
```

### 5.2 添加新的惯性权重策略

在 `Swarm._get_inertia_weight()` 中添加新策略。

### 5.3 添加新的拓扑结构

可以扩展 `Swarm` 类以支持环形、星形等拓扑结构。

## 6. 依赖关系

```
numpy (核心计算)
   ↓
matplotlib (可视化，可选)
   ↓
pytest (测试，开发依赖)
```

## 7. 性能考虑

- 使用 NumPy 向量化操作
- 避免不必要的数组复制
- 支持随机种子以复现结果
- 可选的轨迹追踪以节省内存
