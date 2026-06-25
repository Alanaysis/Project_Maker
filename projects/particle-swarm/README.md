# 粒子群优化 (Particle Swarm Optimization)

从零实现粒子群优化算法，深入理解群体智能的核心原理。

## 学习目标

- **理解粒子群原理**：模拟鸟群觅食行为的优化算法
- **掌握速度更新**：惯性权重 + 认知学习 + 社会学习
- **学会全局最优搜索**：通过群体协作找到最优解
- **掌握 PSO 变体**：自适应 PSO、混沌 PSO
- **实际应用**：神经网络训练、特征选择

## 核心循环

```
初始化粒子 → 适应度评估 → 速度更新 → 位置更新 → 全局最优
```

1. **初始化粒子**：在搜索空间中随机生成粒子群
2. **适应度评估**：计算每个粒子的目标函数值
3. **速度更新**：根据个体最佳和全局最佳调整速度
4. **位置更新**：根据速度更新粒子位置
5. **全局最优**：记录群体找到的最优解

## 项目结构

```
particle-swarm/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── particle.py             # 粒子类
│   ├── swarm.py                # 标准 PSO
│   ├── adaptive_pso.py         # 自适应 PSO
│   ├── chaos_pso.py            # 混沌 PSO
│   ├── functions.py            # 测试函数
│   ├── neural_network.py       # 神经网络训练
│   ├── feature_selection.py    # 特征选择
│   └── visualizer.py           # 可视化
├── tests/
│   ├── __init__.py
│   ├── test_particle.py        # 粒子测试
│   ├── test_swarm.py           # 标准 PSO 测试
│   ├── test_adaptive_pso.py    # 自适应 PSO 测试
│   ├── test_chaos_pso.py       # 混沌 PSO 测试
│   ├── test_neural_network.py  # 神经网络测试
│   ├── test_feature_selection.py # 特征选择测试
│   └── test_functions.py       # 测试函数测试
└── examples/
    ├── basic_pso.py            # 基础示例
    ├── function_optimization.py # 多函数优化
    ├── parameter_tuning.py     # 参数调优
    ├── adaptive_pso_example.py # 自适应 PSO 示例
    ├── chaos_pso_example.py    # 混沌 PSO 示例
    ├── neural_network_example.py # 神经网络训练示例
    └── feature_selection_example.py # 特征选择示例
```

## 快速开始

### 基本使用

```python
import numpy as np
from src import Swarm, PSOConfig, sphere

# 配置 PSO
config = PSOConfig(
    n_particles=30,           # 粒子数量
    dimensions=2,             # 搜索空间维度
    bounds=(-10.0, 10.0),     # 搜索边界
    w=0.7,                    # 惯性权重
    c1=1.5,                   # 认知系数
    c2=1.5,                   # 社会系数
    max_iterations=100,       # 最大迭代次数
    random_seed=42,           # 随机种子（可复现）
)

# 创建粒子群并优化
swarm = Swarm(config)
result = swarm.optimize(sphere, verbose=True)

print(f"最佳位置: {result.best_position}")
print(f"最佳适应度: {result.best_fitness:.6f}")
print(f"迭代次数: {result.iterations}")
```

### 使用线性递减惯性权重

```python
config = PSOConfig(
    n_particles=30,
    dimensions=2,
    bounds=(-10.0, 10.0),
    w_strategy="linear_decay",  # 线性递减策略
    w_max=0.9,                  # 初始惯性权重
    w_min=0.4,                  # 最终惯性权重
    max_iterations=100,
)

swarm = Swarm(config)
result = swarm.optimize(sphere)
```

### 自定义目标函数

```python
import numpy as np

def my_function(x):
    """自定义目标函数"""
    return np.sum(np.abs(x)) + np.prod(np.abs(x))

config = PSOConfig(
    n_particles=30,
    dimensions=2,
    bounds=(-10.0, 10.0),
)

swarm = Swarm(config)
result = swarm.optimize(my_function)
```

### 使用回调函数

```python
def my_callback(iteration, fitness, position):
    """每代结束后的回调"""
    if iteration % 10 == 0:
        print(f"代 {iteration}: 适应度 = {fitness:.6f}")

swarm = Swarm(config)
result = swarm.optimize(sphere, callback=my_callback)
```

### 追踪粒子轨迹

```python
config = PSOConfig(
    n_particles=5,
    dimensions=2,
    bounds=(-10.0, 10.0),
    max_iterations=50,
    track_trajectories=True,  # 启用轨迹追踪
)

swarm = Swarm(config)
result = swarm.optimize(sphere)

# 获取轨迹
trajectories = result.particle_trajectories
print(f"追踪了 {len(trajectories)} 个粒子的轨迹")
```

### 使用自适应 PSO

```python
from src import AdaptiveSwarm, AdaptivePSOConfig

config = AdaptivePSOConfig(
    n_particles=30,
    dimensions=2,
    bounds=(-10.0, 10.0),
    w_init=0.9,                # 初始惯性权重
    c1_init=2.0,               # 初始认知系数
    c2_init=2.0,               # 初始社会系数
    w_min=0.4,                 # 最小惯性权重
    w_max=0.9,                 # 最大惯性权重
    adaptation_rate=0.1,       # 参数调整速率
    max_iterations=100,
)

swarm = AdaptiveSwarm(config)
result = swarm.optimize(sphere, verbose=True)

# 查看参数变化历史
for params in result['parameter_history'][::10]:
    print(f"w={params['w']:.3f}, c1={params['c1']:.3f}, c2={params['c2']:.3f}")
```

### 使用混沌 PSO

```python
from src import ChaosSwarm, ChaosPSOConfig

config = ChaosPSOConfig(
    n_particles=30,
    dimensions=2,
    bounds=(-10.0, 10.0),
    chaos_map="logistic",      # 混沌映射类型: logistic, tent, sinusoidal
    chaos_weight=0.1,          # 混沌扰动权重
    chaos_decay=0.99,          # 混沌扰动衰减系数
    max_iterations=100,
)

swarm = ChaosSwarm(config)
result = swarm.optimize(sphere, verbose=True)

print(f"最佳位置: {result['best_position']}")
print(f"最佳适应度: {result['best_fitness']:.6f}")
```

### 训练神经网络

```python
from src import NeuralNetworkTrainer, NeuralNetworkConfig
from src.neural_network import create_xor_dataset

# 创建数据集
X, y = create_xor_dataset()

# 配置神经网络
config = NeuralNetworkConfig(
    layer_sizes=[2, 10, 1],    # 网络结构
    hidden_activation="sigmoid",
    output_activation="sigmoid",
    n_particles=30,
    max_iterations=100,
)

# 训练
trainer = NeuralNetworkTrainer(config)
result = trainer.train(X, y, loss_type="binary_crossentropy", verbose=True)

print(f"最终损失: {result['best_loss']:.6f}")
print(f"训练准确率: {result['accuracy']:.2%}")
```

### 特征选择

```python
from src import FeatureSelector, FeatureSelectionConfig
from src.feature_selection import simple_cross_validation_accuracy, create_sample_dataset

# 创建数据集
X, y = create_sample_dataset(n_samples=100, n_features=10, n_informative=5)

# 配置特征选择
config = FeatureSelectionConfig(
    n_features=10,
    n_particles=30,
    max_iterations=50,
    min_features=1,
    max_features=10,
    accuracy_weight=0.9,       # 准确率权重
    feature_weight=0.1,        # 特征数量惩罚权重
)

# 执行特征选择
selector = FeatureSelector(config)
result = selector.select(X, y, evaluator=simple_cross_validation_accuracy, verbose=True)

print(f"选择特征数: {result['n_selected_features']}")
print(f"选择特征索引: {result['selected_feature_indices']}")
print(f"最终准确率: {result['final_accuracy']:.2%}")
```

### 可视化

```python
from src.visualizer import PSOVisualizer

# 收敛曲线
PSOVisualizer.plot_convergence(result.convergence_history)

# 2D 搜索空间
PSOVisualizer.plot_2d_search_space(
    swarm.particles,
    bounds=(-10.0, 10.0),
    objective_function=sphere,
    global_best=result.best_position,
)

# 粒子轨迹
PSOVisualizer.plot_trajectory(
    result.particle_trajectories,
    bounds=(-10.0, 10.0),
    objective_function=sphere,
)
```

## 核心算法

### 1. 速度更新公式

```python
v_new = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
```

其中：
- `w * v`：**惯性部分**，保持原有运动趋势
- `c1 * r1 * (pbest - x)`：**认知部分**，向个体最佳移动
- `c2 * r2 * (gbest - x)`：**社会部分**，向全局最佳移动

### 2. 位置更新公式

```python
x_new = x + v_new
```

### 3. 惯性权重策略

| 策略 | 公式 | 特点 |
|------|------|------|
| 固定权重 | w = const | 简单，但难以平衡 |
| 线性递减 | w = w_max - (w_max - w_min) * t/T | 经典，效果好 |
| 自适应 | 根据收敛情况动态调整 | 智能，但复杂 |

## 测试函数

### Sphere 函数
```python
f(x) = sum(x_i^2)
```
- 特点：单峰、凸函数
- 最优解：f(0, 0, ..., 0) = 0
- 搜索范围：[-100, 100]

### Rosenbrock 函数
```python
f(x) = sum(100 * (x_{i+1} - x_i^2)^2 + (1 - x_i)^2)
```
- 特点：单峰但有狭窄的全局最优谷
- 最优解：f(1, 1, ..., 1) = 0
- 搜索范围：[-30, 30]

### Rastrigin 函数
```python
f(x) = 10n + sum(x_i^2 - 10 * cos(2 * pi * x_i))
```
- 特点：多峰，大量局部最优
- 最优解：f(0, 0, ..., 0) = 0
- 搜索范围：[-5.12, 5.12]

### Ackley 函数
```python
f(x) = -20 * exp(-0.2 * sqrt(1/n * sum(x_i^2))) - exp(1/n * sum(cos(2*pi*x_i))) + 20 + e
```
- 特点：多峰，指数函数
- 最优解：f(0, 0, ..., 0) = 0
- 搜索范围：[-32, 32]

### Griewank 函数
```python
f(x) = 1 + sum(x_i^2 / 4000) - prod(cos(x_i / sqrt(i+1)))
```
- 特点：多峰，乘积结构
- 最优解：f(0, 0, ..., 0) = 0
- 搜索范围：[-600, 600]

## 关键概念

### 探索与开发

- **探索 (Exploration)**：在搜索空间中广泛搜索，发现新的有希望区域
- **开发 (Exploitation)**：在已知的有希望区域中精细搜索，找到最优解
- **惯性权重 w**：控制探索与开发的平衡
  - w 大：探索能力强，但可能发散
  - w 小：开发能力强，但可能陷入局部最优

### 个体学习与社会学习

- **个体学习 (c1)**：粒子向自己的历史最佳位置学习
- **社会学习 (c2)**：粒子向群体的历史最佳位置学习
- **平衡**：c1 = c2 = 2.0 是经典设置

### 收敛性

- PSO 不保证收敛到全局最优
- 通过合理设置参数可以提高找到全局最优的概率
- 线性递减惯性权重策略可以平衡探索和开发

## PSO 变体

### 自适应 PSO

自适应 PSO 根据搜索过程中的收敛情况和种群多样性，动态调整惯性权重和学习因子。

**自适应策略**：
1. **惯性权重自适应**：收敛慢时增大（探索），收敛快时减小（开发）
2. **学习因子自适应**：根据个体和群体表现平衡 c1 和 c2
3. **多样性控制**：当种群多样性过低时，增加探索性

**优势**：
- 无需手动调参
- 自动平衡探索和开发
- 适应不同优化问题

### 混沌 PSO

混沌 PSO 引入混沌序列替代随机数，增强搜索能力和跳出局部最优的能力。

**混沌映射**：
- **Logistic 映射**：x_{n+1} = r * x_n * (1 - x_n)
- **Tent 映射**：分段线性映射
- **Sinusoidal 映射**：x_{n+1} = sin(pi * x_n)

**应用场景**：
- 多峰函数优化
- 容易陷入局部最优的问题
- 需要更强探索能力的问题

## 实际应用

### 神经网络训练

使用 PSO 训练神经网络权重，替代传统的梯度下降方法。

**优势**：
- 全局优化：避免梯度下降陷入局部最优
- 无需梯度：适用于不可微的激活函数
- 并行评估：可以同时评估多个网络

**适用场景**：
- 小型网络训练
- 不可微激活函数
- 全局最优重要的问题

### 特征选择

使用 PSO 选择最优特征子集，提高机器学习模型性能。

**特点**：
- 二进制 PSO：粒子位置表示特征选择（0/1）
- 多目标优化：平衡特征数量和模型性能
- 适用于高维数据

**优势**：
- 自动选择最优特征子集
- 减少过拟合风险
- 提高模型可解释性

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行粒子测试
pytest tests/test_particle.py -v

# 运行粒子群测试
pytest tests/test_swarm.py -v

# 运行自适应 PSO 测试
pytest tests/test_adaptive_pso.py -v

# 运行混沌 PSO 测试
pytest tests/test_chaos_pso.py -v

# 运行神经网络测试
pytest tests/test_neural_network.py -v

# 运行特征选择测试
pytest tests/test_feature_selection.py -v

# 运行测试函数测试
pytest tests/test_functions.py -v
```

## 运行示例

```bash
# 基础示例
python examples/basic_pso.py

# 多函数优化
python examples/function_optimization.py

# 参数调优
python examples/parameter_tuning.py

# 自适应 PSO 示例
python examples/adaptive_pso_example.py

# 混沌 PSO 示例
python examples/chaos_pso_example.py

# 神经网络训练示例
python examples/neural_network_example.py

# 特征选择示例
python examples/feature_selection_example.py
```

## 参考资料

- [Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.](https://ieeexplore.ieee.org/document/488968)
- [Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer.](https://ieeexplore.ieee.org/document/699146)
- [Poli, R., Kennedy, J., & Blackwell, T. (2007). Particle swarm optimization.](https://link.springer.com/article/10.1007/s11721-007-0002-0)
- [Wikipedia: Particle swarm optimization](https://en.wikipedia.org/wiki/Particle_swarm_optimization)

## License

This project is for educational purposes.

---

[返回 AI 模块](../AI_README.md) | [返回主目录](../../README.md)
