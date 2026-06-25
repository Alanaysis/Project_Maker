# 模拟退火算法实现

> 模拟退火（Simulated Annealing, SA）是一种通用的随机搜索算法，用于求解优化问题。

## 项目简介

本项目实现了完整的模拟退火优化算法框架，支持多种优化问题类型：
- **TSP旅行商问题**：路径优化
- **函数优化**：连续空间多模态函数优化
- **调度问题**：作业车间、流水车间、单机调度

## 学习目标

- 理解模拟退火算法的基本原理
- 掌握温度调度策略（指数衰减、线性衰减、对数衰减）
- 学会Metropolis接受准则
- 掌握多种邻域操作（交换、逆序、插入）
- 应用模拟退火求解实际优化问题

## 算法原理

模拟退火来源于金属退火的物理过程：
1. **初始状态**：从高温开始，系统处于高能态
2. **邻域搜索**：在当前解的邻域中随机选择新解
3. **接受判断**：
   - 如果新解更优，总是接受
   - 如果新解较差，以一定概率接受（概率随温度降低而减小）
4. **温度降低**：按照调度策略降低温度
5. **终止条件**：温度足够低或达到最大迭代次数

核心公式：
```
P(accept) = exp(-ΔE / T)
```
其中 ΔE 是能量差，T 是当前温度。

## 项目结构

```
simulated-annealing/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖列表
├── src/                         # 源代码
│   ├── __init__.py              # 包入口
│   ├── simulated_annealing.py   # 核心算法
│   ├── neighborhood.py          # 邻域操作
│   ├── tsp.py                   # TSP问题
│   ├── function_optimization.py # 函数优化
│   ├── scheduling.py            # 调度问题
│   └── visualization.py         # 可视化工具
├── tests/                       # 测试代码
│   └── test_simulated_annealing.py
├── examples/                    # 示例代码
│   └── tsp_example.py
└── docs/                        # 文档
    ├── 01_RESEARCH.md           # 市场调研
    ├── 02_REQUIREMENTS.md       # 需求分析
    ├── 03_DESIGN.md             # 架构设计
    ├── 04_PRODUCT.md            # 产品说明
    └── 05_DEVELOPMENT.md        # 开发指南
```

## 核心特性

### 1. 多种冷却策略

| 策略 | 公式 | 特点 |
|------|------|------|
| 指数冷却 | T(t) = T0 * α^t | 最常用，衰减平滑 |
| 线性冷却 | T(t) = T0 - (T0-Tf)*t/max | 简单直观 |
| 对数冷却 | T(t) = T0 / (1+α*log(1+t)) | 衰减最慢 |

### 2. 丰富的邻域操作

| 操作 | 说明 | 适用场景 |
|------|------|---------|
| Swap | 交换两个元素 | 排列问题 |
| Reverse | 反转子序列 | 路径优化 |
| Insert | 移动元素位置 | 调度问题 |
| Or-opt | 移动连续片段 | TSP优化 |
| Mixed | 混合多种操作 | 通用场景 |

### 3. 多种问题支持

- **TSP旅行商**：路径规划、物流配送
- **函数优化**：参数调优、模型拟合
- **调度问题**：生产调度、资源分配

### 4. 可视化支持

- 收敛曲线绘制
- TSP路径可视化
- 冷却策略对比图

## 快速开始

### 1. 安装依赖

```bash
pip install numpy matplotlib pytest
```

### 2. 基本使用

```python
from src import SimulatedAnnealing, SAConfig, CoolingSchedule
import numpy as np

# 定义目标函数
def objective(x):
    return x ** 2

# 定义邻域函数
def neighbor(x):
    return x + np.random.randn() * 2

# 配置
config = SAConfig(
    initial_temp=100.0,
    final_temp=0.01,
    cooling_rate=0.99,
    max_iterations=1000,
    cooling_schedule=CoolingSchedule.EXPONENTIAL
)

# 初始解
initial_solution = np.random.randn() * 10

# 优化
optimizer = SimulatedAnnealing(config, objective, neighbor, initial_solution)
best_solution, best_cost, history = optimizer.optimize()

print(f"最优解: {best_solution:.4f}")
print(f"最优值: {best_cost:.6f}")
```

### 3. TSP求解

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

print(f"最优距离: {best_distance:.2f}")
```

### 4. 函数优化

```python
from src import TestFunctions, ContinuousNeighbor, SimulatedAnnealing, SAConfig
import numpy as np

# 使用Rastrigin函数
neighbor = ContinuousNeighbor(bounds=(-5.12, 5.12), dim=2)
config = SAConfig(initial_temp=100.0, final_temp=0.001, max_iterations=5000)

initial_solution = np.random.uniform(-5.12, 5.12, 2)
optimizer = SimulatedAnnealing(
    config, TestFunctions.rastrigin, neighbor, initial_solution
)
best_x, best_value, _ = optimizer.optimize()

print(f"最优解: {best_x}")
print(f"最优值: {best_value:.6f}")
```

### 5. 调度优化

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

print(f"最优Makespan: {best_makespan}")
```

### 6. 运行测试

```bash
cd tests
python -m pytest test_simulated_annealing.py -v
```

### 7. 运行示例

```bash
cd examples
python tsp_example.py
```

## 技术栈

- **主语言**：Python 3.8+
- **依赖库**：numpy, matplotlib
- **测试框架**：pytest

## 应用场景

模拟退火算法适用于：
- 组合优化问题（TSP、调度问题）
- 函数优化（多模态、非凸函数）
- 特征选择
- 参数调优
- 资源分配

## 参考资料

- [Simulated Annealing - Wikipedia](https://en.wikipedia.org/wiki/Simulated_annealing)
- [Kirkpatrick et al., 1983](https://science.sciencemag.org/content/220/4598/671)
- [Černý, 1985](https://link.springer.com/article/10.1007/BF00400755)

## 许可证

MIT License
