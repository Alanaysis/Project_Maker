# 梯度下降家族

实现各种梯度下降优化算法，包括 SGD、Momentum、Adam、AdaGrad、Nadam 等，以及学习率调度策略。

## 项目概述

本项目是一个学习型项目，旨在深入理解和实现梯度下降家族的各种优化算法。通过实际实现和可视化分析，掌握这些算法的原理、特点和适用场景。

### 学习目标

- 理解梯度下降的基本原理
- 掌握 BGD、SGD、Mini-Batch GD 等基础优化算法
- 理解 Momentum、NAG 等动量优化方法
- 掌握 AdaGrad、RMSProp、Adam、AdamW、Nadam 等自适应学习率算法
- 学会学习率调度策略（StepLR、CosineAnnealing、Warmup）
- 能够可视化优化过程
- 了解不同优化算法的优缺点和适用场景

### 技术栈

- **主语言**: Python
- **框架**: 无（纯 NumPy 实现）
- **其他**: NumPy, Matplotlib

### 核心循环

```
参数 → 梯度计算 → 参数更新 → 收敛检查
```

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd gradient-descent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install numpy matplotlib
```

### 运行示例

```bash
# 基础优化示例
python examples/basic_optimization.py

# 优化器对比示例
python examples/compare_optimizers.py

# 学习率调度示例
python examples/learning_rate_schedule.py

# 可视化演示
python examples/visualization_demo.py

# 线性回归对比
python examples/linear_regression.py

# 神经网络训练
python examples/neural_network.py
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src

# 运行特定测试
pytest tests/test_optimizers.py
```

## 项目结构

```
gradient-descent/
├── README.md                    # 项目说明（本文件）
├── LEARNING_NOTES.md            # 学习笔记
├── requirements.txt             # 依赖说明
├── docs/
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发指南
├── src/
│   ├── __init__.py
│   ├── optimizer.py             # 优化工具函数
│   ├── optimizers/              # 优化器实现
│   │   ├── __init__.py
│   │   ├── base.py             # 基类
│   │   ├── bgd.py              # BGD, Mini-Batch GD
│   │   ├── sgd.py              # SGD
│   │   ├── momentum.py         # Momentum, NAG
│   │   ├── adagrad.py          # AdaGrad
│   │   ├── rmsprop.py          # RMSProp
│   │   ├── adam.py             # Adam, AdamW
│   │   └── nadam.py            # Nadam
│   ├── schedulers/             # 学习率调度器
│   │   ├── __init__.py
│   │   ├── base.py             # 基类
│   │   ├── step.py             # StepLR
│   │   ├── exponential.py      # ExponentialLR
│   │   ├── cosine.py           # CosineAnnealingLR
│   │   └── warmup.py           # WarmupScheduler
│   ├── functions/              # 测试函数
│   │   ├── __init__.py
│   │   ├── base.py             # 基类
│   │   ├── quadratic.py        # 二次函数
│   │   ├── rosenbrock.py       # Rosenbrock 函数
│   │   └── himmelblau.py       # Himmelblau 函数
│   └── visualizer/             # 可视化模块
│       ├── __init__.py
│       ├── contour.py          # 等高线图
│       ├── trajectory.py       # 轨迹图
│       └── comparison.py       # 对比图
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_optimizers.py      # 优化器测试
│   ├── test_schedulers.py      # 调度器测试
│   ├── test_functions.py       # 测试函数验证
│   └── test_integration.py     # 集成测试
└── examples/                   # 示例代码
    ├── basic_optimization.py   # 基础优化示例
    ├── compare_optimizers.py   # 优化器对比
    ├── learning_rate_schedule.py # 学习率调度
    └── visualization_demo.py   # 可视化演示
```

## 实现的功能

### 优化器

| 优化器 | 描述 | 特点 |
|--------|------|------|
| **BGD** | 批量梯度下降 | 收敛稳定、适合小数据集 |
| **Mini-Batch GD** | 小批量梯度下降 | 平衡效率和稳定性 |
| **SGD** | 随机梯度下降 | 简单、可解释 |
| **Momentum** | 动量法 | 加速收敛、减少震荡 |
| **NAG** | Nesterov 加速梯度 | 更准确的梯度估计 |
| **AdaGrad** | 自适应学习率 | 对稀疏特征友好 |
| **RMSProp** | 均方根传播 | 解决 AdaGrad 衰减问题 |
| **Adam** | 自适应矩估计 | 通用、收敛快 |
| **AdamW** | 解耦权重衰减的 Adam | 更好的泛化性能 |
| **Nadam** | Nesterov 加速 Adam | 结合 NAG 和 Adam 优点 |

### 学习率调度器

| 调度器 | 描述 | 特点 |
|--------|------|------|
| **StepLR** | 阶梯衰减 | 简单有效 |
| **ExponentialLR** | 指数衰减 | 平滑衰减 |
| **CosineAnnealingLR** | 余弦退火 | 周期性衰减 |
| **WarmupScheduler** | 热身调度 | 稳定训练初期 |

### 测试函数

| 函数 | 描述 | 特点 |
|------|------|------|
| **QuadraticFunction** | 二次函数 | 凸函数、唯一最小值 |
| **RosenbrockFunction** | Rosenbrock 函数 | 非凸、峡谷型地形 |
| **HimmelblauFunction** | Himmelblau 函数 | 非凸、多模态 |

### 可视化功能

- **等高线图**: 展示函数地形和优化轨迹
- **3D 表面图**: 直观展示函数形状
- **轨迹图**: 对比不同优化器的路径
- **收敛曲线**: 展示优化过程的收敛情况
- **梯度范数曲线**: 展示梯度的变化趋势
- **学习率曲线**: 展示学习率调度的效果

## 使用示例

### 基础用法

```python
from src.optimizers import Adam
from src.functions import QuadraticFunction
from src.optimizer import optimize

# 创建测试函数
func = QuadraticFunction(a=1.0, b=1.0)

# 创建优化器
optimizer = Adam(learning_rate=0.01)

# 运行优化
x0 = np.array([3.0, 3.0])
result = optimize(func, optimizer, x0, max_iter=1000, tol=1e-6)

print(f"最优解: {result['x']}")
print(f"最优值: {result['fun']}")
print(f"迭代次数: {result['niter']}")
```

### 对比多个优化器

```python
from src.optimizers import SGD, Momentum, Adam
from src.functions import RosenbrockFunction
from src.optimizer import compare_optimizers

# 创建测试函数
func = RosenbrockFunction()

# 创建优化器
optimizers = {
    'SGD': SGD(learning_rate=0.0001),
    'Momentum': Momentum(learning_rate=0.0001, momentum=0.9),
    'Adam': Adam(learning_rate=0.001)
}

# 对比优化器
results = compare_optimizers(func, optimizers, func.initial_point())

# 打印结果
for name, result in results.items():
    print(f"{name}: {result['niter']} iterations, f(x) = {result['fun']:.6e}")
```

### 使用学习率调度

```python
from src.optimizers import Adam
from src.schedulers import CosineAnnealingLR
from src.functions import QuadraticFunction

# 创建优化器和调度器
optimizer = Adam(learning_rate=0.01)
scheduler = CosineAnnealingLR(optimizer, T_max=500, eta_min=0.001)

# 手动运行优化
func = QuadraticFunction()
x = func.initial_point()

for i in range(500):
    grad = func.gradient(x)
    x = optimizer.step(x, grad)
    scheduler.step()
```

### 可视化优化过程

```python
from src.visualizer import ContourPlotter, TrajectoryPlotter

# 创建等高线图
plotter = ContourPlotter(func, x_range=(-4, 4), y_range=(-4, 4))
fig = plotter.plot(
    trajectories=[result['trajectory']],
    labels=['Adam'],
    title="Optimization Trajectory"
)
fig.savefig('optimization.png')

# 创建轨迹可视化器
trajectory_plotter = TrajectoryPlotter()

# 绘制收敛曲线
fig = trajectory_plotter.plot_convergence(
    {'Adam': result['values']},
    title="Convergence Curve"
)
fig.savefig('convergence.png')
```

## 算法对比

### 收敛速度

| 算法 | 收敛速度 | 稳定性 | 内存开销 |
|------|---------|--------|---------|
| BGD | 慢 | 高 | 低 |
| SGD | 慢 | 高 | 低 |
| Mini-Batch | 中 | 中 | 低 |
| Momentum | 中 | 高 | 低 |
| NAG | 中 | 高 | 低 |
| AdaGrad | 中 | 中 | 中 |
| RMSProp | 快 | 中 | 中 |
| Adam | 快 | 中 | 中 |
| AdamW | 快 | 中 | 中 |
| Nadam | 快 | 中 | 中 |

### 适用场景

| 场景 | 推荐算法 |
|------|---------|
| 小数据集、凸优化 | BGD |
| 简单问题 | SGD + Momentum |
| 稀疏数据 | AdaGrad, Adam |
| 快速原型 | Adam, Nadam |
| 追求泛化 | SGD + 学习率调度 |
| 大规模训练 | AdamW |

## 学习资源

### 文档

- [市场调研](docs/01-RESEARCH.md) - 梯度下降算法概述
- [架构设计](docs/02-ARCHITECTURE.md) - 项目架构设计
- [实现细节](docs/03-IMPLEMENTATION.md) - 核心算法实现
- [测试文档](docs/04-TESTING.md) - 测试策略和用例
- [开发指南](docs/05-DEVELOPMENT.md) - 开发环境和规范

### 学习笔记

- [学习笔记](LEARNING_NOTES.md) - 学习过程和关键洞察

### 示例代码

- [基础优化](examples/basic_optimization.py) - 基本的优化流程
- [优化器对比](examples/compare_optimizers.py) - 对比不同优化器
- [学习率调度](examples/learning_rate_schedule.py) - 学习率调度策略
- [可视化演示](examples/visualization_demo.py) - 可视化功能演示
- [线性回归](examples/linear_regression.py) - 线性回归优化对比
- [神经网络](examples/neural_network.py) - 神经网络训练对比

## 开发指南

### 添加新优化器

1. 在 `src/optimizers/` 创建新文件
2. 继承 `BaseOptimizer`
3. 实现 `step` 方法
4. 在 `src/optimizers/__init__.py` 注册
5. 编写测试

### 添加新测试函数

1. 在 `src/functions/` 创建新文件
2. 继承 `TestFunction`
3. 实现函数值和梯度计算
4. 在 `src/functions/__init__.py` 注册
5. 编写测试

### 添加新调度器

1. 在 `src/schedulers/` 创建新文件
2. 继承 `BaseScheduler`
3. 实现 `get_lr` 方法
4. 在 `src/schedulers/__init__.py` 注册
5. 编写测试

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 运行并显示覆盖率
pytest --cov=src --cov-report=term-missing

# 运行特定测试文件
pytest tests/test_optimizers.py

# 运行特定测试类
pytest tests/test_optimizers.py::TestAdam

# 运行特定测试方法
pytest tests/test_optimizers.py::TestAdam::test_bias_correction
```

### 测试覆盖率

```bash
# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-optimizer`)
3. 提交更改 (`git commit -m 'feat: 添加新优化器'`)
4. 推送到分支 (`git push origin feature/new-optimizer`)
5. 创建 Pull Request

## 许可证

MIT License

## 致谢

- NumPy 团队提供的优秀数值计算库
- Matplotlib 团队提供的可视化库
- PyTorch 团队提供的优化器实现参考
- 所有开源社区的贡献者

## 联系方式

如有问题或建议，请通过以下方式联系:

- 提交 Issue
- 发送邮件到 [your-email@example.com]

## 更新日志

### v0.2.0 (2026-06-24)

- 新增 BGD、Mini-Batch GD 优化器
- 新增 NesterovMomentum 优化器
- 新增 Nadam 优化器
- 新增线性回归示例
- 新增神经网络训练示例
- 更新文档和测试用例

### v0.1.0 (2026-06-22)

- 初始版本
- 实现 SGD、Momentum、AdaGrad、RMSProp、Adam、AdamW 优化器
- 实现 StepLR、ExponentialLR、CosineAnnealingLR、WarmupScheduler 调度器
- 实现 QuadraticFunction、RosenbrockFunction、HimmelblauFunction 测试函数
- 实现等高线图、轨迹图、对比图可视化
- 添加完整的测试套件
- 添加详细的文档和示例
