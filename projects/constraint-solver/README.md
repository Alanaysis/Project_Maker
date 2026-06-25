# 约束求解器 (Constraint Solver)

一个用 C++ 实现的 CAD 几何约束求解器，用于求解 2D 几何约束系统。

## 项目简介

本项目实现了一个完整的几何约束求解器，支持多种几何约束类型，使用 Newton-Raphson 数值方法求解约束系统。

### 核心功能

- **几何实体**：点、线段、圆
- **约束类型**：距离、角度、相切、平行、垂直等
- **数值求解**：Newton-Raphson 方法
- **约束传播**：简单传播优化

### 技术栈

- **语言**：C++17
- **构建**：CMake 3.14+
- **依赖**：无（纯 C++ 实现）

## 快速开始

### 编译

```bash
cd projects/constraint-solver
mkdir build && cd build
cmake ..
make
```

### 运行示例

```bash
# 基础示例
./basic_example

# CAD 草图示例
./cad_sketch

# 相切约束演示
./tangent_demo
```

### 运行测试

```bash
ctest
```

## 使用示例

### 基本约束求解

```cpp
#include "solver.h"
using namespace cadsolver;

int main() {
    ConstraintSolver solver;

    // 创建两个点
    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(1.0, 0.0);

    // 添加距离约束
    solver.addDistance(p1, p2, 5.0);

    // 求解
    auto result = solver.solve();

    if (result.success()) {
        auto p2_final = solver.getPoint(p2);
        std::cout << "P2: " << p2_final.toString() << std::endl;
    }

    return 0;
}
```

### 约束类型

| 约束类型 | 描述 | 用法 |
|---------|------|------|
| Coincident | 两点重合 | `solver.addCoincident(p1, p2)` |
| Distance | 距离约束 | `solver.addDistance(p1, p2, 5.0)` |
| Horizontal | 水平约束 | `solver.addHorizontal(line)` |
| Vertical | 垂直约束 | `solver.addVertical(line)` |
| Parallel | 平行约束 | `solver.addParallel(l1, l2)` |
| Perpendicular | 垂直约束 | `solver.addPerpendicular(l1, l2)` |
| Angle | 角度约束 | `solver.addAngle(l1, l2, M_PI/4)` |
| Radius | 半径约束 | `solver.addRadius(circle, 5.0)` |
| Concentric | 同心约束 | `solver.addConcentric(c1, c2)` |
| Tangent | 相切约束 | `solver.addTangent(line, circle)` |
| PointOnLine | 点在线上 | `solver.addPointOnLine(p, line)` |
| PointOnCircle | 点在圆上 | `solver.addPointOnCircle(p, circle)` |
| Length | 长度约束 | `solver.addLength(line, 10.0)` |

### 求解器配置

```cpp
SolverConfig config;
config.tolerance = 1e-10;       // 收敛容差
config.max_iterations = 100;    // 最大迭代次数
config.damping = 1.0;           // 阻尼系数
config.verbose = false;         // 打印迭代细节

ConstraintSolver solver(config);
```

## 项目结构

```
constraint-solver/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── LEARNING_NOTES.md           # 学习笔记
├── include/
│   ├── geometry.h             # 几何实体定义
│   ├── constraint.h           # 约束定义
│   └── solver.h               # 求解器接口
├── src/
│   └── solver.cpp             # 求解器实现
├── tests/
│   ├── test_constraints.cpp   # 约束单元测试
│   └── test_solver.cpp        # 求解器集成测试
├── examples/
│   ├── basic_example.cpp      # 基础示例
│   ├── cad_sketch.cpp         # CAD 草图示例
│   └── tangent_demo.cpp       # 相切约束演示
└── docs/
    ├── 01-RESEARCH.md         # 研究报告
    ├── 02-DESIGN.md           # 设计文档
    ├── 03-IMPLEMENTATION.md   # 实现细节
    ├── 04-TESTING.md          # 测试文档
    └── 05-DEVELOPMENT.md      # 开发日志
```

## 算法说明

### Newton-Raphson 方法

1. 计算残差向量 F(x)
2. 计算雅可比矩阵 J = ∂F/∂x
3. 求解线性系统 J·Δx = -F
4. 更新参数 x = x + Δx
5. 重复直到收敛

### 正则化

使用 Tikhonov 正则化防止奇异矩阵：

```
(J^T·J + λI)·Δx = -J^T·F
```

## 学习目标

通过本项目，你可以学到：

1. **约束求解原理**：理解几何约束的数学表示
2. **数值求解方法**：掌握 Newton-Raphson 方法
3. **约束传播**：了解如何优化初始猜测
4. **CAD 系统**：理解参数化设计的核心功能

## 文档

- [研究报告](docs/01-RESEARCH.md)：背景知识和调研结果
- [设计文档](docs/02-DESIGN.md)：架构设计和数据结构
- [实现细节](docs/03-IMPLEMENTATION.md)：核心算法实现
- [测试文档](docs/04-TESTING.md)：测试策略和用例
- [开发日志](docs/05-DEVELOPMENT.md)：开发过程和经验
- [学习笔记](LEARNING_NOTES.md)：学习总结和收获

## 参考资源

### 开源项目

- [Solvespace](https://github.com/solvespace/solvespace) - 开源参数化 CAD
- [FreeCAD](https://github.com/FreeCAD/FreeCAD) - 开源 3D CAD
- [OpenCASCADE](https://github.com/Open-Cascade-SAS/OCCT) - CAD 内核

### 学术论文

- Fudos & Hoffmann, "A Graph-Constructive Approach to Solving Systems of Geometric Constraints" (1997)
- Joan-Arinyo et al., "Constructive Geometric Constraint Solving" (2003)

### 在线资源

- [OpenCASCADE 文档](https://dev.opencascade.org)
- [FreeCAD 开发者文档](https://wiki.freecad.org/Developer_hub)

## 未来改进

1. **图分解**：利用约束图结构提高效率
2. **增量求解**：支持增量约束添加
3. **3D 支持**：扩展到三维约束
4. **更多约束类型**：添加样条曲线、曲面约束
5. **性能优化**：稀疏矩阵、并行计算

## 许可证

本项目仅供学习使用。

## 作者

AI Assistant

## 致谢

感谢所有开源 CAD 项目的贡献者，特别是 Solvespace 和 FreeCAD 团队。
