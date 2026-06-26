# 贝塞尔曲线引擎 (Bezier Curve Engine)

> 实现贝塞尔曲线编辑和渲染引擎的深度学习项目

## 项目简介 / Project Description

本项目是一个用于学习和理解贝塞尔曲线的交互式引擎。通过实现从基础数学到高级算法的完整技术栈，深入探索参数曲线的设计与渲染原理。

This project is an interactive engine for learning and understanding Bezier curves. By implementing a complete technology stack from foundational mathematics to advanced algorithms, it explores the principles of parametric curve design and rendering in depth.

## 学习目标 / Learning Objectives

### 数学基础 / Mathematical Foundation
- [x] 理解 Bernstein 多项式和基函数
- [x] 掌握贝塞尔曲线参数方程
- [x] 学习 De Casteljau 算法的递归原理
- [x] 理解切线、法向量和曲率的几何意义

### 算法实现 / Algorithm Implementation
- [x] 线性、二次、三次贝塞尔曲线的计算
- [x] 曲线细分（De Casteljau 分割）
- [x] 曲线相交检测
- [x] 曲线长度近似（多种数值积分方法）

### 工程实践 / Engineering Practice
- [x] 数值稳定性处理
- [x] 自适应算法设计
- [x] 交互式可视化
- [x] 单元测试覆盖

## 数学背景 / Mathematical Background

### Bernstein 多项式 / Bernstein Polynomials

n 次 Bernstein 基函数定义为:

```
B_i^n(t) = C(n,i) * (1-t)^(n-i) * t^i,  i = 0, 1, ..., n
```

其中 C(n,i) = n! / (i! * (n-i)!) 是二项式系数。

### 贝塞尔曲线公式 / Bezier Curve Formula

n 次贝塞尔曲线由 n+1 个控制点 P₀, P₁, ..., Pₙ 定义:

```
B(t) = Σ B_i^n(t) * P_i,  t ∈ [0, 1]
```

#### 线性曲线 (n=1) / Linear Curve (n=1)
```
B(t) = (1-t)·P₀ + t·P₁
```

#### 二次曲线 (n=2) / Quadratic Curve (n=2)
```
B(t) = (1-t)²·P₀ + 2(1-t)t·P₁ + t²·P₂
```

#### 三次曲线 (n=3) / Cubic Curve (n=3)
```
B(t) = (1-t)³·P₀ + 3(1-t)²t·P₁ + 3(1-t)t²·P₂ + t³·P₃
```

### De Casteljau 算法 / De Casteljau's Algorithm

递归线性插值算法:

```
P_i^0 = P_i
P_i^r(t) = (1-t)·P_i^(r-1) + t·P_(i+1)^(r-1)
```

最终结果: B(t) = P_0^n(t)

## 项目结构 / Project Structure

```
bezier-engine/
├── src/                          # 核心模块
│   ├── __init__.py
│   ├── linear_bezier.py         # 线性贝塞尔曲线
│   ├── quadratic_bezier.py      # 二次贝塞尔曲线
│   ├── cubic_bezier.py          # 三次贝塞尔曲线
│   ├── de_casteljau.py          # De Casteljau 算法
│   ├── subdivision.py           # 曲线细分
│   ├── curve_intersection.py    # 相交检测
│   ├── tangent_normal.py        # 切线和法向量
│   └── curve_length.py          # 曲线长度
├── examples/                     # 示例脚本
│   ├── interactive_bezier.py    # 交互式绘制
│   ├── subdivision_viz.py       # 细分可视化
│   ├── curve_fitting.py         # 曲线拟合
│   └── animated_rendering.py    # 动画渲染
├── tests/                        # 单元测试
│   ├── test_bezier_engine.py
│   └── run_tests.py
├── requirements.txt
└── README.md
```

## 快速开始 / Quick Start

### 安装 / Installation

```bash
pip install -r requirements.txt
```

### 运行测试 / Run Tests

```bash
# 方式 1: 直接运行
python -m tests.run_tests

# 方式 2: 使用 pytest
python -m pytest tests/ -v
```

### 运行示例 / Run Examples

```bash
# 交互式贝塞尔曲线绘制
python -m examples.interactive_bezier

# 曲线细分可视化
python -m examples.subdivision_viz

# 曲线拟合
python -m examples.curve_fitting

# 动画渲染
python -m examples.animated_rendering
```

## 核心算法 / Core Algorithms

### 1. 曲线计算 / Curve Evaluation

| 方法 | 描述 | 复杂度 |
|------|------|--------|
| Bernstein 直接计算 | 直接使用 Bernstein 多项式 | O(n) |
| De Casteljau | 递归线性插值 | O(n²) |
| 幂基转换 | 转换为多项式形式 | O(n) |

### 2. 曲线细分 / Curve Subdivision

| 方法 | 描述 | 适用场景 |
|------|------|----------|
| De Casteljau 细分 | 在参数 t 处分割 | 通用 |
| 自适应细分 | 根据弯曲程度自动细分 | 渲染优化 |
| 递归细分 | 多次细分 | 碰撞检测 |

### 3. 曲线长度 / Curve Length

| 方法 | 精度 | 速度 |
|------|------|------|
| 梯形法则 | 中等 | 快 |
| 辛普森法则 | 高 | 快 |
| 高斯求积 | 很高 | 快 |
| 自适应细分 | 最高 | 慢 |

## 学习资源 / Learning Resources

- **书籍**: "Curves and Surfaces for Computer Graphics" by Peter Rogers
- **论文**: "A History of Bezier Curves" by Joe Warren
- **在线课程**: Stanford CS148 - Interactive Geometry
- **参考实现**: [FontTools](https://github.com/fonttools/fonttools) 的 Bezier 模块

## 许可证 / License

MIT License
