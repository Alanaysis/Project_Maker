# Gradient Descent Optimization Family / 梯度下降家族

> 从零实现梯度下降优化算法家族，包含 SGD、Adam、AdaGrad 等经典优化器及学习率调度策略。

---

## English Description

A learning project implementing the gradient descent optimization algorithm family from scratch using NumPy. Covers vanilla SGD, momentum methods, adaptive learning rate methods (AdaGrad, RMSprop, Adam, AdamW), learning rate schedulers, gradient clipping, and convergence monitoring.

## 中文描述

从零实现梯度下降优化算法家族的学习项目。包含基础 SGD、动量法、自适应学习率方法（AdaGrad、RMSprop、Adam、AdamW）、学习率调度策略、梯度裁剪和收敛监测。

---

## Learning Objectives / 学习目标

- **理解梯度下降原理** - 掌握梯度下降的数学基础和几何直觉
- **掌握 SGD、Adam、AdaGrad 等** - 实现并对比多种优化算法
- **学会学习率调度** - 实现步长衰减、余弦退火、指数衰减、warmup 等策略
- **掌握收敛检测** - 实现梯度阈值、早停、损失方差等收敛判据

---

## Optimizer Comparison Table / 优化器对比表

| 优化器 | 学习率 | 动量 | 自适应 | 适用场景 |
|--------|--------|------|--------|----------|
| **SGD** | 固定/调度 | 无 | 否 | 简单问题，凸优化 |
| **SGD+Momentum** | 固定/调度 | 有 (0.9) | 否 | 缓解震荡，加速收敛 |
| **Nesterov** | 固定/调度 | 有 (0.9) | 否 | 比 Momentum 更精确 |
| **AdaGrad** | 自适应 | 无 | 是 | 稀疏数据 |
| **RMSprop** | 自适应 | 无 | 是 | RNN，非平稳目标 |
| **Adam** | 自适应 | 有 | 是 | 通用首选，鲁棒 |
| **AdamW** | 自适应 | 有 | 是 | 深度学习，解耦权重衰减 |

---

## Math Derivations / 数学推导

### Vanilla SGD

$$\theta_{t+1} = \theta_t - \eta \cdot \nabla_\theta \mathcal{L}(\theta_t)$$

### Momentum

$$v_t = \mu v_{t-1} - \eta \nabla_\theta \mathcal{L}(\theta_t)$$
$$\theta_{t+1} = \theta_t + v_t$$

### Nesterov Momentum

$$v_t = \mu v_{t-1} - \eta \nabla_\theta \mathcal{L}(\theta_t - \mu v_{t-1})$$
$$\theta_{t+1} = \theta_t + v_t$$

### AdaGrad

$$G_t = G_{t-1} + \nabla_\theta \mathcal{L}(\theta_t) \odot \nabla_\theta \mathcal{L}(\theta_t)$$
$$\theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{G_t + \epsilon}} \odot \nabla_\theta \mathcal{L}(\theta_t)$$

### RMSprop

$$E[g^2]_t = \rho E[g^2]_{t-1} + (1-\rho) \nabla_\theta \mathcal{L}(\theta_t)^2$$
$$\theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{E[g^2]_t + \epsilon}} \odot \nabla_\theta \mathcal{L}(\theta_t)$$

### Adam

$$m_t = \beta_1 m_{t-1} + (1-\beta_1) \nabla_\theta \mathcal{L}(\theta_t)$$
$$v_t = \beta_2 v_{t-1} + (1-\beta_2) \nabla_\theta \mathcal{L}(\theta_t)^2$$
$$\hat{m}_t = \frac{m_t}{1-\beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1-\beta_2^t}$$
$$\theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{\hat{v}_t} + \epsilon} \odot \hat{m}_t$$

### AdamW (Decoupled Weight Decay)

$$\theta_{t+1} = \theta_t(1-\eta w_d) - \frac{\eta}{\sqrt{\hat{v}_t} + \epsilon} \odot \hat{m}_t$$

---

## Project Structure / 项目结构

```
gradient-descent/
├── src/
│   ├── __init__.py              # Package init
│   ├── sgd.py                   # SGD, Mini-batch SGD, Momentum, Nesterov
│   ├── adapters.py              # AdaGrad, RMSprop, Adam, AdamW
│   ├── schedulers.py            # Step, Cosine, Exponential, Warmup schedulers
│   ├── gradient_clipping.py     # Gradient clipping utilities
│   ├── convergence.py           # Convergence monitoring and early stopping
│   ├── test_functions.py        # Benchmark functions (Sphere, Rosenbrock, etc.)
│   └── utils.py                 # Numerical gradient, loss utilities
├── examples/
│   ├── compare_optimizers.py    # Compare all optimizers on test functions
│   ├── train_synthetic.py       # Training on synthetic datasets
│   ├── lr_visualization.py      # Learning rate schedule visualization
│   ├── convergence_chart.py     # Convergence comparison chart
│   └── demo.py                  # Interactive optimization demo
├── tests/
│   ├── test_optimizers.py       # Optimizer unit tests
│   └── test_utils.py            # Scheduler, clipping, convergence tests
├── README.md                    # This file
└── requirements.txt             # Dependencies
```

---

## How to Run Examples / 运行示例

### Prerequisites / 前置条件

```bash
pip install numpy matplotlib
```

### Run Examples / 运行示例

```bash
# 1. Interactive demo
python examples/demo.py

# 2. Compare all optimizers
python examples/compare_optimizers.py

# 3. Train on synthetic data
python examples/train_synthetic.py

# 4. Visualize learning rate schedules
python examples/lr_visualization.py

# 5. Convergence comparison chart
python examples/convergence_chart.py
```

### Run Tests / 运行测试

```bash
python -m pytest tests/ -v
```

---

## Optimizer Implementation Details / 优化器实现细节

### Core Loop / 核心循环

```
参数 → 梯度计算 → 参数更新 → 收敛检查
```

### Key Design Decisions / 关键设计决策

1. **参数以列表传递** - 支持多参数（如神经网络中的权重和偏置）
2. **不原地修改参数** - 优化器返回新参数列表，避免副作用
3. **学习率缩放通过梯度** - 统一通过 `grad * lr / base_lr` 应用学习率
4. **状态可序列化** - 所有优化器支持 `get_state()` / `set_state()`

---

## Test Functions / 测试函数

| 函数 | 最小值 | 特点 |
|------|--------|------|
| Sphere | f(0)=0 | 凸函数，单模态 |
| Rosenbrock | f(1,1)=0 | 非凸，窄谷 |
| Rastrigin | f(0)=0 | 多模态，周期性 |
| Ackley | f(0)=0 | 多模态 |
| Beale | f(3,0.5)=0 | 多模态 |
| Himmelblau | 4个最小值 | 多模态 |

---

## References / 参考资料

- SGD: Robbins & Monro (1951)
- Momentum: Polyak (1964)
- Nesterov: Nesterov (1983)
- AdaGrad: Duchi et al. (2011)
- RMSprop: Hinton (2012)
- Adam: Kingma & Ba (2015)
- AdamW: Loshchilov & Hutter (2019)

---

## License / 许可

MIT License
