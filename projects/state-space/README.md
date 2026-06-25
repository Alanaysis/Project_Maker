# 状态空间模型

## 项目简介

实现状态空间模型和状态估计，包括连续/离散系统表示、系统分析（可控性/可观性/稳定性）、状态反馈控制（极点配置/LQR）、状态观测器以及实际应用案例（倒立摆/电机控制）。

## 学习目标

- 理解连续时间和离散时间状态空间表示
- 掌握系统离散化方法（零阶保持器/双线性变换/欧拉法）
- 学会可控性、可观性和稳定性分析
- 掌握极点配置和 LQR 最优控制
- 理解全阶/降阶观测器设计
- 掌握卡尔曼滤波算法
- 应用状态空间方法解决实际工程问题

## 技术栈

- **主语言**: Python 3.8+
- **依赖库**: numpy, scipy, matplotlib
- **测试框架**: pytest

## 项目结构

```
state-space/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── requirements.txt          # 依赖列表
├── setup.py                  # 包安装配置
├── src/                      # 源代码
│   ├── __init__.py
│   ├── state_space_model.py  # 连续/离散状态空间模型
│   ├── kalman_filter.py      # 卡尔曼滤波器
│   ├── analysis.py           # 可控性/可观性/稳定性分析
│   ├── controller.py         # 状态反馈/LQR/LQG控制器
│   ├── observer.py           # 全阶/降阶观测器
│   └── applications.py       # 实际应用（倒立摆/电机）
├── tests/                    # 测试代码
│   └── test_state_space.py
├── examples/                 # 示例代码
│   ├── basic_example.py      # 基本示例
│   ├── kalman_example.py     # 卡尔曼滤波示例
│   ├── control_example.py    # 控制示例
│   ├── inverted_pendulum_example.py  # 倒立摆控制
│   └── motor_control_example.py      # 电机控制
└── docs/                     # 文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 核心功能

### 1. 连续时间系统

```
ContinuousStateSpace:
  状态方程: dx/dt = A*x + B*u
  输出方程: y = C*x + D*u

  支持:
  - 传递函数转换 G(s) = C*(sI-A)^(-1)*B + D
  - 稳定性判断（特征值实部 < 0）
  - 系统离散化
```

### 2. 离散时间系统

```
StateSpaceModel:
  状态方程: x(k+1) = A*x(k) + B*u(k)
  输出方程: y(k) = C*x(k) + D*u(k)

  支持:
  - 离散传递函数 H(z)
  - 阶跃响应/脉冲响应
  - 稳定性判断（特征值模 < 1）
  - 逆离散化（连续化）
```

### 3. 系统分析

```
analysis.py:
  - 可控性矩阵: C = [B, AB, A²B, ..., A^(n-1)B]
  - 可观性矩阵: O = [C; CA; CA²; ...; CA^(n-1)]
  - 稳定性检查（连续/离散）
  - 稳定性裕度计算
  - 可控性/可观性格拉姆矩阵
  - 可控性分解
```

### 4. 状态反馈控制

```
controller.py:
  - 极点配置（Ackermann公式）
  - LQR控制器（Riccati方程）
  - LQG控制器（LQR + 卡尔曼滤波）

  控制律: u = -K*x + r
```

### 5. 状态观测器

```
observer.py:
  - 全阶观测器: x̂(k+1) = (A-LC)*x̂(k) + B*u(k) + L*y(k)
  - 降阶观测器: 仅估计不可直接测量的状态

  设计方法: 极点配置（利用对偶性）
```

### 6. 卡尔曼滤波

```
kalman_filter.py:
  预测: x̂(k|k-1) = A*x̂(k-1) + B*u(k)
  更新: x̂(k|k) = x̂(k|k-1) + K*(y(k) - C*x̂(k|k-1))

  支持: RTS平滑、估计误差分析
```

### 7. 实际应用

```
applications.py:
  - 倒立摆: 线性化模型、LQR控制、非线性仿真
  - 直流电机: 位置控制、速度控制、状态估计
```

## 快速开始

### 安装依赖

```bash
pip install numpy scipy matplotlib pytest
```

### 运行示例

```bash
# 基本示例
python examples/basic_example.py

# 卡尔曼滤波示例
python examples/kalman_example.py

# 控制示例
python examples/control_example.py

# 倒立摆控制
python examples/inverted_pendulum_example.py

# 电机控制
python examples/motor_control_example.py
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码示例

#### 连续系统离散化

```python
from src.state_space_model import ContinuousStateSpace

# 定义连续系统
A_c = [[0, 1], [-4, -2]]
B_c = [[0], [1]]
C = [[1, 0]]
D = [[0]]

cs = ContinuousStateSpace(A_c, B_c, C, D)
print(f"连续系统稳定: {cs.is_stable()}")

# 离散化
model_d = cs.discretize(dt=0.01, method="zoh")
print(f"离散系统稳定: {model_d.is_stable()}")
```

#### LQR控制

```python
from src.controller import LQRController
import numpy as np

A = np.array([[0.9, 0.1], [-0.1, 0.8]])
B = np.array([[1.0], [0.5]])
Q = np.eye(2)
R = np.array([[1.0]])

lqr = LQRController(A, B, Q, R)
x0 = np.array([1.0, 0.0])
states, controls = lqr.simulate(x0, n_steps=50)
```

#### 倒立摆控制

```python
from src.applications import InvertedPendulum

ip = InvertedPendulum(M=0.5, m=0.2, l=0.3)
lqr = ip.design_lqr(dt=0.01)
model = ip.discretize(dt=0.01)

x0 = [0, 0, 0.1, 0]  # 初始偏角0.1弧度
states, controls = lqr.simulate(x0, n_steps=200)
```

## 核心循环

```
连续系统 → 离散化 → 可控/可观分析 → 控制器设计 → 观测器设计 → 闭环仿真
```

## 应用场景

| 应用 | 系统模型 | 控制方法 |
|------|----------|----------|
| 倒立摆 | 四阶非线性系统 | LQR + 观测器 |
| 电机控制 | 三阶线性系统 | LQR + 卡尔曼滤波 |
| 机器人 | 多自由度系统 | 极点配置 |
| 导航系统 | 惯性导航模型 | 卡尔曼滤波 |
| 温度控制 | 一阶/二阶系统 | PID/状态反馈 |

## 参考资料

- Ogata, K. "Modern Control Engineering"
- Astrom, K.J. & Murray, R.M. "Feedback Systems"
- Franklin, G.F. et al. "Digital Control of Dynamic Systems"
- Kalman, R.E. "A New Approach to Linear Filtering and Prediction Problems" (1960)
