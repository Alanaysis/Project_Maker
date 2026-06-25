# 02 - 设计文档：约束求解器架构

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口层                              │
│  (ConstraintSolver API, 实体创建, 约束定义, 求解触发)        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      约束管理层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  实体管理    │  │  约束管理    │  │  约束传播    │         │
│  │ (Points,    │  │ (Distance,  │  │ (Propagator)│         │
│  │  Lines,     │  │  Angle,     │  │             │         │
│  │  Circles)   │  │  Tangent)   │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      求解器层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Newton-Raphson 求解器                   │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────────┐   │   │
│  │  │残差计算  │→│雅可比矩阵 │→│线性系统求解      │   │   │
│  │  │F(x)     │  │J(x)      │  │J·Δx = -F       │   │   │
│  │  └─────────┘  └──────────┘  └─────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      数学基础层                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │向量运算   │  │矩阵运算   │  │几何计算   │  │数值方法   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
用户定义几何 → 用户定义约束 → 约束传播 → 数值求解 → 几何更新
     │              │            │          │          │
     ▼              ▼            ▼          ▼          ▼
  创建实体      添加约束     优化初始    Newton     更新坐标
  (Point,      (Distance,    猜测       迭代       返回结果
   Line,        Angle,
   Circle)      Tangent)
```

## 2. 核心数据结构

### 2.1 几何实体

```cpp
struct Point2D {
    double x, y;
    int id;  // 唯一标识符
};

struct Line2D {
    Point2D start, end;
    int id;
};

struct Circle2D {
    Point2D center;
    double radius;
    int id;
};
```

### 2.2 参数向量

所有几何实体的参数被展平为一个向量：

```
Point i:   params[2i] = x_i, params[2i+1] = y_i
Line i:    params[4i] = sx_i, params[4i+1] = sy_i,
           params[4i+2] = ex_i, params[4i+3] = ey_i
Circle i:  params[3i] = cx_i, params[3i+1] = cy_i,
           params[3i+2] = r_i
```

### 2.3 约束基类

```cpp
class Constraint {
public:
    ConstraintType type;
    std::vector<int> param_indices;  // 关联的参数索引
    double target;                    // 目标值

    virtual double residual(const std::vector<double>& params) = 0;
    virtual std::vector<double> gradient(const std::vector<double>& params) = 0;
};
```

## 3. 约束实现

### 3.1 距离约束

**数学公式**：
```
f(P1, P2) = ||P1 - P2||² - d² = 0
         = (x1-x2)² + (y1-y2)² - d²
```

**梯度**：
```
∂f/∂x1 = 2(x1 - x2)
∂f/∂y1 = 2(y1 - y2)
∂f/∂x2 = -2(x1 - x2)
∂f/∂y2 = -2(y1 - y2)
```

### 3.2 平行约束

**数学公式**：
```
f(L1, L2) = d1 × d2 = 0
         = dx1·dy2 - dy1·dx2
```

其中 d1, d2 是两线的方向向量。

### 3.3 垂直约束

**数学公式**：
```
f(L1, L2) = d1 · d2 = 0
         = dx1·dx2 + dy1·dy2
```

### 3.4 相切约束（线与圆）

**数学公式**：
```
f(line, circle) = dist(center, line)² - r² = 0
```

点到直线距离公式：
```
dist = |ax0 + by0 + c| / √(a² + b²)
```

### 3.5 相切约束（两圆）

**外切**：
```
f(C1, C2) = ||C1-C2||² - (r1+r2)² = 0
```

**内切**：
```
f(C1, C2) = ||C1-C2||² - (r1-r2)² = 0
```

## 4. 求解算法

### 4.1 Newton-Raphson 迭代

```
算法: NewtonRaphsonSolve(constraints, params, config)
输入: constraints - 约束列表
      params - 初始参数向量
      config - 配置（容差、最大迭代等）
输出: 求解结果

1. for iter = 1 to config.max_iterations:
2.     residuals = computeResiduals(constraints, params)
3.     norm = ||residuals||
4.     if norm < config.tolerance:
5.         return Converged(params, iter, norm)
6.
7.     J = computeJacobian(constraints, params)
8.     dx = solveLinearSystem(J, -residuals)
9.     params += config.damping * dx
10.
11. return MaxIterations(params, norm)
```

### 4.2 线性系统求解

使用正规方程 + Tikhonov 正则化：

```
(J^T J + λI) Δx = -J^T r
```

其中 λ 是正则化参数，防止奇异矩阵。

### 4.3 雅可比矩阵计算

对于每个约束，计算其对相关参数的偏导数：

```
J[i][j] = ∂f_i/∂x_j
```

对于复杂约束，使用数值微分：
```
∂f/∂x ≈ (f(x+ε) - f(x)) / ε
```

## 5. 求解器配置

```cpp
struct SolverConfig {
    double tolerance = 1e-10;       // 收敛容差
    int max_iterations = 100;       // 最大迭代次数
    double damping = 1.0;           // 阻尼系数 (1.0 = 完整 Newton)
    bool verbose = false;           // 打印迭代细节
    double regularization = 1e-12;  // 正则化参数
};
```

## 6. 约束传播

### 6.1 传播策略

简单的传播可以改善初始猜测：

1. **重合传播**：如果两点重合，设置它们坐标相同
2. **水平传播**：如果线段水平，设置 y 坐标相等
3. **垂直传播**：如果线段垂直，设置 x 坐标相等
4. **距离传播**：如果距离为 0，设置点重合

### 6.2 高级传播（未实现）

- 弧一致性 (Arc Consistency)
- 图分解 (Graph Decomposition)
- 自由度分析 (DOF Analysis)

## 7. 错误处理

### 7.1 求解状态

```cpp
enum class SolverStatus {
    Converged,       // 成功收敛
    MaxIterations,   // 达到最大迭代
    SingularMatrix,  // 雅可比矩阵奇异
    Failed           // 其他失败
};
```

### 7.2 错误场景

| 场景 | 状态 | 处理 |
|-----|------|------|
| 成功求解 | Converged | 返回解 |
| 迭代过多 | MaxIterations | 返回当前解，警告 |
| 矩阵奇异 | SingularMatrix | 可能过度约束 |
| 数值溢出 | Failed | 检查初始猜测 |

## 8. 性能考虑

### 8.1 计算复杂度

- 残差计算：O(m)，m 为约束数
- 雅可比计算：O(m·k)，k 为每约束参数数
- 线性求解：O(n³)，n 为参数数

### 8.2 优化方向

- 稀疏矩阵优化
- 增量雅可比更新
- 并行约束计算
- 图分解减少系统规模

## 9. 扩展性设计

### 9.1 添加新约束类型

1. 继承 `Constraint` 基类
2. 实现 `residual()` 和 `gradient()`
3. 在 `ConstraintSolver` 中添加工厂方法

### 9.2 添加 3D 支持

- 扩展几何实体（Point3D, Plane, etc.）
- 扩展约束类型（角度约束需要更多参数）
- 雅可比矩阵规模增大

### 9.3 添加符号求解

- 集成符号计算库
- 精确解而非数值近似
- 处理多解情况

## 10. 测试策略

### 10.1 单元测试

- 每个约束类型的残差计算
- 每个约束类型的梯度计算
- 几何实体的基本操作

### 10.2 集成测试

- 简单约束系统求解
- 复杂约束系统求解
- 边界情况（过度约束、欠约束）

### 10.3 性能测试

- 大规模约束系统
- 收敛速度
- 数值稳定性
