# 学习笔记：约束求解器

## 1. 核心概念

### 1.1 什么是几何约束求解？

几何约束求解是确定几何实体位置和形状的过程，使得所有约束条件同时满足。

**例子**：
- 两个点之间的距离为 5
- 两条线平行
- 一条线与一个圆相切

### 1.2 约束的数学表示

每个约束可以表示为一个方程：

```
f(x) = 0
```

其中 x 是几何参数向量（如点的坐标）。

**距离约束**：
```
f(P1, P2) = (x1-x2)² + (y1-y2)² - d² = 0
```

**平行约束**：
```
f(L1, L2) = dx1·dy2 - dy1·dx2 = 0
```

### 1.3 约束系统

多个约束组成一个方程组：

```
F(x) = [f1(x), f2(x), ..., fm(x)] = 0
```

目标是找到 x 使得所有 fi(x) = 0。

## 2. 求解方法

### 2.1 Newton-Raphson 方法

**核心思想**：通过迭代逼近解。

**算法**：
1. 选择初始猜测 x⁰
2. 计算残差 r = F(x)
3. 计算雅可比矩阵 J = ∂F/∂x
4. 求解线性系统 J·Δx = -r
5. 更新 x = x + Δx
6. 重复直到收敛

**优点**：
- 收敛速度快（二次收敛）
- 实现相对简单

**缺点**：
- 需要初始猜测
- 可能不收敛
- 对奇异雅可比矩阵敏感

### 2.2 雅可比矩阵

雅可比矩阵是约束函数的一阶偏导数矩阵：

```
J[i][j] = ∂fi/∂xj
```

**例子**：

对于距离约束 f = (x1-x2)² + (y1-y2)² - d²

```
J = [∂f/∂x1, ∂f/∂y1, ∂f/∂x2, ∂f/∂y2]
  = [2(x1-x2), 2(y1-y2), -2(x1-x2), -2(y1-y2)]
```

### 2.3 线性系统求解

Newton 迭代需要求解线性系统：

```
J·Δx = -F
```

**方法**：
- **直接求逆**：Δx = -J⁻¹·F（数值不稳定）
- **正规方程**：(J^T·J)·Δx = -J^T·F（更稳定）
- **QR 分解**：更稳定但更慢

### 2.4 正则化

当雅可比矩阵奇异时，使用 Tikhonov 正则化：

```
(J^T·J + λI)·Δx = -J^T·F
```

其中 λ 是小正数（如 1e-12）。

## 3. 约束类型

### 3.1 几何约束

| 约束 | 公式 | 梯度 |
|------|------|------|
| 距离 | (x1-x2)² + (y1-y2)² - d² | [2dx, 2dy, -2dx, -2dy] |
| 水平 | y1 - y2 | [0, 1, 0, -1] |
| 垂直 | x1 - x2 | [1, 0, -1, 0] |
| 平行 | dx1·dy2 - dy1·dx2 | [dy2, -dx2, -dy1, dx1] |
| 垂直 | dx1·dx2 + dy1·dy2 | [-dx2, -dy2, dx1, dy1] |

### 3.2 圆约束

| 约束 | 公式 |
|------|------|
| 半径 | r - target |
| 同心 | (cx1-cx2)² + (cy1-cy2)² |
| 线圆相切 | dist(center, line)² - r² |
| 圆圆相切 | (cx1-cx2)² + (cy1-cy2)² - (r1±r2)² |

### 3.3 点约束

| 约束 | 公式 |
|------|------|
| 点在线上 | (px-sx)·(ey-sy) - (py-sy)·(ex-sx) |
| 点在圆上 | (px-cx)² + (py-cy)² - r² |

## 4. 实现细节

### 4.1 参数向量

所有几何参数展平为一个向量：

```
Point i:   [x_i, y_i]
Line i:    [sx_i, sy_i, ex_i, ey_i]
Circle i:  [cx_i, cy_i, r_i]
```

**优点**：
- 简化雅可比矩阵计算
- 便于线性代数运算

### 4.2 约束关联

每个约束存储关联的参数索引：

```cpp
class Constraint {
    std::vector<int> param_indices;  // 参数在向量中的位置
    double target;                    // 目标值
};
```

### 4.3 梯度计算

**解析梯度**：直接推导偏导数公式

```cpp
std::vector<double> DistanceConstraint::gradient(const std::vector<double>& p) {
    double dx = p[0] - p[2];
    double dy = p[1] - p[3];
    return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy};
}
```

**数值梯度**：有限差分近似

```cpp
std::vector<double> numericalGradient(const Constraint& c, const std::vector<double>& p) {
    double eps = 1e-8;
    double f0 = c.residual(p);
    std::vector<double> grad(p.size());

    for (size_t i = 0; i < p.size(); ++i) {
        std::vector<double> p_plus = p;
        p_plus[i] += eps;
        grad[i] = (c.residual(p_plus) - f0) / eps;
    }

    return grad;
}
```

## 5. 数值稳定性

### 5.1 常见问题

1. **奇异雅可比矩阵**：约束相关或过度约束
2. **数值溢出**：参数值过大
3. **精度损失**：浮点运算误差累积

### 5.2 解决方案

1. **正则化**：添加小对角元素
2. **阻尼**：控制步长大小
3. **缩放**：归一化参数范围
4. **双精度**：使用 double 而非 float

### 5.3 收敛准则

```cpp
bool converged(const std::vector<double>& residuals, double tolerance) {
    double norm = 0.0;
    for (double r : residuals) {
        norm += r * r;
    }
    return std::sqrt(norm) < tolerance;
}
```

## 6. 约束传播

### 6.1 什么是约束传播？

约束传播是在数值求解之前，通过逻辑推理简化约束系统的技术。

### 6.2 传播策略

1. **重合传播**：如果两点重合，设置坐标相同
2. **水平传播**：如果线段水平，设置 y 坐标相等
3. **垂直传播**：如果线段垂直，设置 x 坐标相等
4. **距离传播**：如果距离为 0，设置点重合

### 6.3 传播的好处

- 提供更好的初始猜测
- 减少迭代次数
- 提高收敛性

## 7. CAD 应用

### 7.1 参数化草图

参数化草图是 CAD 系统的核心功能：

1. 用户绘制几何形状
2. 添加约束（尺寸、几何关系）
3. 系统求解约束
4. 修改参数自动更新形状

### 7.2 约束类型

CAD 系统支持的约束类型：

**几何约束**：
- 重合、水平、垂直、平行、垂直、相切、同心

**尺寸约束**：
- 距离、角度、半径、直径

### 7.3 约束状态

- **完全约束**：自由度为 0，形状唯一确定
- **欠约束**：自由度 > 0，形状不唯一
- **过度约束**：约束过多，可能无解

## 8. 学习资源

### 8.1 书籍

- "Geometric Constraint Solving" - Christoph Hoffmann
- "Computer-Aided Design" - various authors
- "Numerical Methods" - various authors

### 8.2 在线资源

- [Solvespace 源码](https://github.com/solvespace/solvespace)
- [FreeCAD 开发者文档](https://wiki.freecad.org/Developer_hub)
- [OpenCASCADE 文档](https://dev.opencascade.org)

### 8.3 课程

- 计算机图形学
- 数值分析
- 计算机辅助几何设计 (CAGD)

## 9. 实践建议

### 9.1 开始简单

1. 先实现基本几何实体
2. 再实现简单约束（距离、水平、垂直）
3. 最后实现复杂约束（相切、角度）

### 9.2 测试驱动

1. 先写测试用例
2. 再实现功能
3. 确保测试通过

### 9.3 数值验证

1. 使用已知解验证
2. 与数值微分对比梯度
3. 检查边界情况

### 9.4 性能优化

1. 先保证正确性
2. 再优化性能
3. 使用性能分析工具

## 10. 常见陷阱

### 10.1 初始猜测

**问题**：初始猜测不好导致不收敛

**解决**：
- 使用约束传播提供更好的猜测
- 尝试多个初始猜测
- 使用阻尼系数

### 10.2 奇异矩阵

**问题**：雅可比矩阵奇异

**解决**：
- 检查约束是否相关
- 使用正则化
- 移除冗余约束

### 10.3 数值精度

**问题**：浮点运算误差

**解决**：
- 使用双精度
- 调整容差参数
- 避免大数吃小数

### 10.4 多解问题

**问题**：约束系统有多个解

**解决**：
- 选择最接近初始猜测的解
- 使用全局优化方法
- 用户交互选择

## 11. 进阶主题

### 11.1 图论方法

- Laman 定理判断刚性
- 自由度分析
- 图分解策略

### 11.2 符号求解

- Groebner 基
- Wu 方法
- 精确解

### 11.3 全局优化

- 模拟退火
- 遗传算法
- 粒子群优化

### 11.4 3D 约束

- 点、线、面约束
- 刚体运动
- 装配约束

## 12. 总结

### 12.1 关键知识点

1. 约束可以表示为非线性方程
2. Newton-Raphson 是标准求解方法
3. 雅可比矩阵是关键计算
4. 正则化提高数值稳定性
5. 约束传播改善初始猜测

### 12.2 技能收获

1. 理解约束求解原理
2. 掌握数值求解方法
3. 学会约束传播技术
4. 了解 CAD 系统核心功能

### 12.3 下一步

1. 学习图论方法
2. 研究符号求解
3. 探索 3D 约束
4. 阅读 Solvespace 源码

## 13. 代码片段

### 13.1 创建约束系统

```cpp
ConstraintSolver solver;

// 创建几何实体
int p1 = solver.addPoint(0.0, 0.0);
int p2 = solver.addPoint(10.0, 0.0);
int line = solver.addLine(0.0, 0.0, 10.0, 5.0);

// 添加约束
solver.addDistance(p1, p2, 5.0);
solver.addHorizontal(line);

// 求解
auto result = solver.solve();
if (result.success()) {
    auto p2_final = solver.getPoint(p2);
    std::cout << "P2: " << p2_final.toString() << std::endl;
}
```

### 13.2 自定义约束

```cpp
class MyConstraint : public Constraint {
public:
    MyConstraint(int p_idx, double target) {
        param_indices = {p_idx, p_idx + 1};
        this->target = target;
    }

    double residual(const std::vector<double>& p) const override {
        // 实现残差计算
        return p[param_indices[0]] - target;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        // 实现梯度计算
        return {1.0, 0.0};
    }
};
```

### 13.3 配置求解器

```cpp
SolverConfig config;
config.tolerance = 1e-10;
config.max_iterations = 200;
config.damping = 0.8;
config.verbose = true;

ConstraintSolver solver(config);
```

## 14. 调试技巧

### 14.1 打印中间结果

```cpp
SolverConfig config;
config.verbose = true;  // 打印每次迭代

auto result = solver.solve();
std::cout << "Iterations: " << result.iterations << std::endl;
std::cout << "Residual: " << result.residual_norm << std::endl;
```

### 14.2 检查梯度

```cpp
auto grad = constraint.gradient(params);
double eps = 1e-8;
double f0 = constraint.residual(params);

for (size_t i = 0; i < params.size(); ++i) {
    std::vector<double> p_plus = params;
    p_plus[i] += eps;
    double numerical = (constraint.residual(p_plus) - f0) / eps;
    std::cout << "Grad[" << i << "]: " << grad[i]
              << " vs " << numerical
              << " diff: " << std::abs(grad[i] - numerical) << std::endl;
}
```

### 14.3 可视化约束

```cpp
auto descriptions = solver.getConstraintDescriptions();
for (const auto& desc : descriptions) {
    std::cout << desc << std::endl;
}
```

## 15. 扩展阅读

### 15.1 相关领域

- 计算机图形学
- 机器人学
- 物理仿真
- 优化理论

### 15.2 高级主题

- 稀疏矩阵优化
- 并行计算
- 符号计算
- 全局优化

### 15.3 工业应用

- CAD/CAM 系统
- 3D 建模软件
- 游戏引擎
- 虚拟现实
