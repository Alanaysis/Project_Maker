# 05 - 开发日志

## 项目概述

**项目名称**：约束求解器 (Constraint Solver)

**目标**：实现一个 CAD 几何约束求解器，理解约束求解原理、数值求解方法和约束传播。

**技术栈**：C++17, CMake

**开发周期**：2024

## 开发阶段

### 阶段 1：研究与设计 (Day 1)

#### 完成的工作

1. **市场调研**
   - 调研了 Solvespace、FreeCAD Sketcher 等开源实现
   - 了解了 D-Cubed/DCM 等商业实现
   - 阅读了相关学术论文

2. **技术选型**
   - 语言：C++（性能、内存控制、工业标准）
   - 算法：Newton-Raphson（直观、收敛性好）
   - 数据结构：参数向量 + 约束链表

3. **架构设计**
   - 设计了四层架构：用户接口、约束管理、求解器、数学基础
   - 定义了几何实体、约束、求解器的数据结构
   - 规划了测试策略

#### 关键决策

- **使用虚函数多态**：便于扩展新约束类型
- **参数向量展平**：简化雅可比矩阵计算
- **正规方程求解**：避免直接求逆，提高数值稳定性

#### 遇到的问题

- 如何处理奇异雅可比矩阵？
  - 解决：Tikhonov 正则化
- 如何计算复杂约束的梯度？
  - 解决：数值微分作为备选方案

### 阶段 2：核心实现 (Day 2)

#### 完成的工作

1. **几何实体** (geometry.h)
   - 实现了 Point2D、Line2D、Circle2D
   - 包含基本运算、向量运算、几何计算

2. **约束系统** (constraint.h)
   - 实现了 13 种约束类型
   - 每个约束包含残差和梯度计算
   - 支持解析梯度和数值梯度

3. **求解器** (solver.h / solver.cpp)
   - 实现了 Newton-Raphson 迭代
   - 包含雅可比矩阵计算
   - 实现了正规方程 + 正则化求解
   - 支持阻尼系数控制

#### 代码统计

- 头文件：3 个 (geometry.h, constraint.h, solver.h)
- 源文件：1 个 (solver.cpp)
- 总代码行数：约 1500 行

#### 关键实现

**距离约束**：
```cpp
double DistanceConstraint::residual(const std::vector<double>& p) const {
    double dx = p[param_indices[0]] - p[param_indices[2]];
    double dy = p[param_indices[1]] - p[param_indices[3]];
    return dx * dx + dy * dy - target * target;
}
```

**雅可比矩阵**：
```cpp
std::vector<std::vector<double>> ConstraintSolver::computeJacobian() const {
    int m = constraints_.size();
    int n = params_.size();

    std::vector<std::vector<double>> J(m, std::vector<double>(n, 0.0));

    for (int i = 0; i < m; ++i) {
        auto grad = constraints_[i]->gradient(params_);
        for (size_t j = 0; j < constraints_[i]->param_indices.size(); ++j) {
            int col = constraints_[i]->param_indices[j];
            J[i][col] = grad[j];
        }
    }

    return J;
}
```

#### 遇到的问题

- 如何映射实体 ID 到参数索引？
  - 解决：使用 EntityInfo 结构体存储映射关系
- 如何处理复杂约束的梯度？
  - 解决：提供数值微分作为备选

### 阶段 3：测试与验证 (Day 3)

#### 完成的工作

1. **单元测试** (test_constraints.cpp)
   - 测试了几何实体的基本运算
   - 测试了所有约束类型的残差计算
   - 测试了梯度计算（与数值微分对比）

2. **集成测试** (test_solver.cpp)
   - 测试了简单约束系统求解
   - 测试了复杂约束系统求解
   - 测试了边界情况（过度约束、退化几何）

3. **示例程序** (examples/)
   - basic_example.cpp：基础约束演示
   - cad_sketch.cpp：CAD 草图示例
   - tangent_demo.cpp：相切约束演示

#### 测试结果

- 单元测试：15/15 通过
- 集成测试：12/12 通过
- 示例程序：全部运行成功

#### 关键测试

**三角形约束测试**：
```cpp
TEST(triangle_with_constraints) {
    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 1.0, false});

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(10.0, 0.0);
    int p3 = solver.addPoint(5.0, 8.0);

    solver.addDistance(p1, p2, 10.0);
    solver.addDistance(p2, p3, 10.0);
    solver.addDistance(p1, p3, 10.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // 验证边长
    auto p1f = solver.getPoint(p1);
    auto p2f = solver.getPoint(p2);
    auto p3f = solver.getPoint(p3);

    ASSERT_NEAR(p1f.distanceTo(p2f), 10.0, 1e-4);
    ASSERT_NEAR(p2f.distanceTo(p3f), 10.0, 1e-4);
    ASSERT_NEAR(p1f.distanceTo(p3f), 10.0, 1e-4);
}
```

#### 遇到的问题

- 某些测试初始猜测不好导致不收敛？
  - 解决：调整初始猜测，使用阻尼系数
- 数值精度问题？
  - 解决：调整容差参数，使用双精度

### 阶段 4：文档与完善 (Day 4)

#### 完成的工作

1. **技术文档**
   - 01-RESEARCH.md：研究报告
   - 02-DESIGN.md：设计文档
   - 03-IMPLEMENTATION.md：实现细节
   - 04-TESTING.md：测试文档
   - 05-DEVELOPMENT.md：开发日志（本文件）

2. **学习笔记**
   - LEARNING_NOTES.md：学习总结

3. **项目文档**
   - README.md：项目说明

#### 文档结构

```
docs/
├── 01-RESEARCH.md      # 研究报告
├── 02-DESIGN.md        # 设计文档
├── 03-IMPLEMENTATION.md # 实现细节
├── 04-TESTING.md       # 测试文档
└── 05-DEVELOPMENT.md   # 开发日志
```

## 技术亮点

### 1. 清晰的架构设计

四层架构分离关注点：
- 用户接口层：简洁的 API
- 约束管理层：灵活的约束定义
- 求解器层：高效的数值求解
- 数学基础层：可靠的数学运算

### 2. 灵活的约束系统

- 使用虚函数实现多态
- 支持 13 种约束类型
- 易于扩展新约束

### 3. 数值稳定性

- Tikhonov 正则化防止奇异矩阵
- 阻尼系数控制步长
- 数值微分作为梯度备选

### 4. 完整的测试覆盖

- 单元测试覆盖所有约束类型
- 集成测试覆盖主要求解场景
- 边界情况测试

## 学到的经验

### 1. 约束求解原理

- 约束可以表示为非线性方程
- Newton-Raphson 方法是求解的标准方法
- 雅可比矩阵是关键计算

### 2. 数值方法

- 正规方程 + 正则化是求解线性系统的稳定方法
- 数值微分可以作为解析梯度的备选
- 阻尼可以提高收敛性

### 3. 软件工程

- 良好的架构设计是项目成功的关键
- 完整的测试覆盖提高代码质量
- 详细的文档便于维护和扩展

### 4. CAD 领域知识

- 几何约束是参数化设计的基础
- 约束求解是 CAD 系统的核心功能
- 理解约束求解有助于理解 CAD 系统

## 未来改进方向

### 1. 算法改进

- **图分解**：利用约束图结构提高效率
- **增量求解**：支持增量约束添加
- **全局优化**：处理多解情况

### 2. 功能扩展

- **3D 支持**：扩展到三维约束
- **更多约束类型**：添加样条曲线、曲面约束
- **参数化表达式**：支持参数化尺寸

### 3. 性能优化

- **稀疏矩阵**：优化大规模系统
- **并行计算**：利用多核加速
- **缓存优化**：减少重复计算

### 4. 用户体验

- **图形界面**：可视化约束系统
- **交互编辑**：支持拖拽修改
- **实时反馈**：显示约束状态

## 总结

本项目成功实现了 CAD 几何约束求解器的核心功能：

1. ✅ 基本几何约束（距离、角度、相切）
2. ✅ 数值求解器（Newton-Raphson）
3. ✅ 约束传播（简单传播）
4. ✅ CAD 示例（参数化草图）

通过这个项目，我深入理解了：
- 约束求解的基本原理
- 数值求解方法的应用
- CAD 系统的核心功能

这为深入学习 CAD 系统和几何建模打下了坚实的基础。

## 参考资源

### 开源项目

- [Solvespace](https://github.com/solvespace/solvespace)
- [FreeCAD](https://github.com/FreeCAD/FreeCAD)
- [OpenCASCADE](https://github.com/Open-Cascade-SAS/OCCT)

### 学术论文

- Fudos & Hoffmann, "A Graph-Constructive Approach to Solving Systems of Geometric Constraints" (1997)
- Joan-Arinyo et al., "Constructive Geometric Constraint Solving" (2003)
- Li, Suzuki & Cao, "A Two-Phase Graph Based Algorithm for 2D Geometric Constraint Solving"

### 在线资源

- [OpenCASCADE 文档](https://dev.opencascade.org)
- [FreeCAD 开发者文档](https://wiki.freecad.org/Developer_hub)
- [Wikipedia: Geometric Constraint Solving](https://en.wikipedia.org/wiki/Geometric_constraint_solving)
