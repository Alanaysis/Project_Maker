# 01 - 研究报告：CAD 几何约束求解器

## 1. 背景与动机

### 1.1 什么是几何约束求解？

几何约束求解是 CAD（计算机辅助设计）系统的核心功能之一。它允许用户通过指定几何约束关系（如距离、角度、相切等）来定义形状，而不是手动计算每个点的精确坐标。

### 1.2 应用场景

- **参数化草图**：用户绘制草图时，系统自动求解约束
- **装配约束**：定义零件之间的位置关系
- **运动仿真**：在约束条件下模拟机构运动
- **尺寸驱动**：修改一个尺寸自动更新相关几何

## 2. 约束类型

### 2.1 几何约束

| 约束类型 | 描述 | 数学表达 |
|---------|------|---------|
| 重合 (Coincident) | 两点重合 | `||P1 - P2||² = 0` |
| 距离 (Distance) | 两点间固定距离 | `||P1 - P2||² = d²` |
| 水平 (Horizontal) | 线段水平 | `y1 - y2 = 0` |
| 垂直 (Vertical) | 线段垂直 | `x1 - x2 = 0` |
| 平行 (Parallel) | 两线段平行 | `d1 × d2 = 0` |
| 垂直 (Perpendicular) | 两线段垂直 | `d1 · d2 = 0` |
| 角度 (Angle) | 两线段固定角度 | `cos(θ) = d1·d2 / (|d1|·|d2|)` |

### 2.2 圆约束

| 约束类型 | 描述 | 数学表达 |
|---------|------|---------|
| 半径 (Radius) | 固定半径 | `r = target` |
| 同心 (Concentric) | 两圆同心 | `||C1 - C2||² = 0` |
| 相切 (Tangent) | 线与圆相切 | `dist(line, center) = r` |
| 相切 (Tangent) | 两圆相切 | `||C1-C2|| = r1 + r2` |

### 2.3 点约束

| 约束类型 | 描述 | 数学表达 |
|---------|------|---------|
| 点在线上 | 点在线段上 | `(P-S) × (E-S) = 0` |
| 点在圆上 | 点在圆周上 | `||P-C||² = r²` |

## 3. 求解算法

### 3.1 Newton-Raphson 方法

最常用的数值求解方法，通过迭代逼近解：

```
给定约束系统 F(x) = 0
1. 计算残差 r = F(x)
2. 计算雅可比矩阵 J = ∂F/∂x
3. 求解线性系统 J·Δx = -r
4. 更新 x = x + Δx
5. 重复直到 ||r|| < tolerance
```

**优点**：
- 收敛速度快（二次收敛）
- 实现相对简单

**缺点**：
- 需要初始猜测
- 可能不收敛
- 对奇异雅可比矩阵敏感

### 3.2 图论方法

基于约束图的结构分析：

1. **Laman 定理**：判断 2D 几何结构是否刚性
2. **自由度分析**：跟踪约束与自由度的关系
3. **分解策略**：将大系统分解为可求解的子系统

### 3.3 混合方法

结合图论和数值方法：
1. 图分析确定求解顺序
2. 数值方法求解每个子系统
3. 传播结果到全局系统

## 4. 现有实现

### 4.1 开源实现

| 项目 | 语言 | 特点 |
|-----|------|------|
| [Solvespace](https://github.com/solvespace/solvespace) | C++ | 完整的参数化 CAD |
| [FreeCAD Sketcher](https://github.com/FreeCAD/FreeCAD) | C++/Python | 基于 OpenCASCADE |
| [LibreCAD](https://github.com/LibreCAD/LibreCAD) | C++ | 2D CAD |

### 4.2 商业实现

- **D-Cubed/DCM** (Siemens)：行业标准
- **ACIS** (Spatial)：几何内核
- **Parasolid** (Siemens)：实体建模

### 4.3 学术研究

关键论文：
- Fudos & Hoffmann, "A Graph-Constructive Approach to Solving Systems of Geometric Constraints" (1997)
- Joan-Arinyo et al., "Constructive Geometric Constraint Solving" (2003)
- Li, Suzuki & Cao, "A Two-Phase Graph Based Algorithm for 2D Geometric Constraint Solving"

## 5. 技术选型

### 5.1 语言选择：C++

**理由**：
- 性能关键：约束求解涉及大量矩阵运算
- 内存控制：精细的内存管理
- 生态成熟：Eigen、BLAS 等数学库支持
- 工业标准：大多数 CAD 系统使用 C++

### 5.2 算法选择：Newton-Raphson

**理由**：
- 实现直观
- 收敛性好（对初始猜测敏感，但可通过传播缓解）
- 可扩展性好

### 5.3 数据结构

```
未知参数向量: [x0, y0, x1, y1, ..., xn, yn]
               ↓
约束系统: F(x) = [f1(x), f2(x), ..., fm(x)]
               ↓
雅可比矩阵: J[i][j] = ∂fi/∂xj
```

## 6. 挑战与解决方案

### 6.1 奇异雅可比矩阵

**问题**：过度约束或约束相关导致矩阵奇异

**解决**：
- Tikhonov 正则化
- QR 分解而非直接求逆
- 约束相关性检测

### 6.2 收敛性

**问题**：初始猜测不好导致不收敛

**解决**：
- 约束传播提供更好的初始猜测
- 阻尼 Newton 法
- 线搜索策略

### 6.3 多解问题

**问题**：约束系统可能有多个解

**解决**：
- 选择最接近初始猜测的解
- 用户交互选择
- 全局优化方法

## 7. 学习资源

### 7.1 书籍

- "Geometric Constraint Solving" - Christoph Hoffmann
- "Computer-Aided Design" - various authors

### 7.2 在线资源

- [Solvespace 源码](https://github.com/solvespace/solvespace)
- [OpenCASCADE 文档](https://dev.opencascade.org)
- [FreeCAD 开发者文档](https://wiki.freecad.org/Developer_hub)

### 7.3 课程

- 计算机图形学
- 数值分析
- 计算机辅助几何设计 (CAGD)

## 8. 项目目标

基于以上研究，本项目将实现：

1. **基本几何约束**：距离、角度、相切等
2. **数值求解器**：Newton-Raphson 方法
3. **约束传播**：简单传播优化
4. **CAD 示例**：参数化草图演示

目标是理解约束求解原理，掌握数值求解方法，为深入学习 CAD 系统打下基础。
