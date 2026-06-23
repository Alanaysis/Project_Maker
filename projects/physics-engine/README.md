# 物理引擎

一个简易的 2D 物理引擎，支持刚体动力学、碰撞检测和约束求解。

## 项目概述

本项目实现了一个基础的 2D 物理引擎，用于学习物理模拟的核心概念。引擎支持：

- **刚体动力学**：质量、速度、加速度、力、冲量
- **碰撞检测**：AABB 碰撞检测、圆形碰撞检测
- **约束求解**：距离约束、钉子约束、铰链约束、焊接约束
- **物理模拟**：重力、摩擦力、弹性碰撞

## 核心循环

```
物理状态 → 力计算 → 积分 → 碰撞检测 → 约束求解 → 状态更新
```

## 技术栈

- **语言**：C++17
- **构建系统**：CMake
- **测试框架**：Google Test
- **依赖**：无外部依赖

## 项目结构

```
physics-engine/
├── include/                    # 头文件
│   └── physics_engine/
│       ├── vector2d.h         # 2D 向量数学库
│       ├── aabb.h             # 轴对齐包围盒
│       ├── rigid_body.h       # 刚体
│       ├── collision.h        # 碰撞检测
│       ├── constraint.h       # 约束求解
│       ├── world.h            # 物理世界
│       └── physics_engine.h   # 主头文件
├── src/                        # 源文件
│   └── rigid_body.cpp
├── tests/                      # 测试文件
│   ├── test_vector2d.cpp
│   ├── test_aabb.cpp
│   ├── test_rigid_body.cpp
│   ├── test_collision.cpp
│   ├── test_constraint.cpp
│   ├── test_world.cpp
│   └── test_integration.cpp
├── examples/                   # 示例程序
│   ├── example_basic.cpp
│   ├── example_collision.cpp
│   ├── example_constraints.cpp
│   └── example_pendulum.cpp
├── docs/                       # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── LEARNING_NOTES.md           # 学习笔记
├── CMakeLists.txt              # 构建配置
└── README.md                   # 本文件
```

## 快速开始

### 构建项目

```bash
# 创建构建目录
mkdir build && cd build

# 配置 CMake
cmake ..

# 编译
make

# 运行测试
make test

# 运行示例
./examples/example_basic
```

### 使用示例

```cpp
#include "physics_engine/physics_engine.h"

int main() {
    // 创建物理世界
    physics_engine::WorldConfig config;
    config.gravity = {0.0, -9.81};
    physics_engine::World world(config);

    // 创建刚体
    physics_engine::RigidBodyDef def;
    def.position = {0.0, 10.0};
    def.mass = 1.0;
    auto body = world.create_body(def);

    // 模拟循环
    double dt = 1.0 / 60.0;
    for (int i = 0; i < 60; ++i) {
        world.step(dt);
        std::cout << "位置: " << body->position() << std::endl;
    }

    return 0;
}
```

## 核心功能

### 1. 向量数学 (`Vector2D`)

支持 2D 向量的基本运算：
- 加法、减法、标量乘法、标量除法
- 点积、叉积
- 长度、归一化
- 旋转、投影、反射
- 线性插值

### 2. AABB 碰撞检测 (`AABB`)

轴对齐包围盒：
- 点包含测试
- AABB 相交测试
- 合并、扩展
- 距离计算

### 3. 刚体 (`RigidBody`)

支持三种刚体类型：
- **Static**：不受力影响，不移动
- **Dynamic**：受力影响，完全模拟
- **Kinematic**：不受力影响，但可手动设置速度

功能：
- 施加力、冲量、扭矩
- 积分（更新位置和速度）
- 阻尼
- 传感器标记

### 4. 碰撞检测

支持多种碰撞检测：
- AABB vs AABB
- Circle vs Circle
- AABB vs Circle

返回碰撞信息：
- 碰撞法线
- 穿透深度
- 接触点

### 5. 约束求解

支持多种约束类型：
- **距离约束**：保持两点之间的距离
- **钉子约束**：固定物体在世界坐标系中的位置
- **铰链约束**：允许旋转但限制位置
- **焊接约束**：完全固定相对位置和角度

### 6. 物理世界 (`World`)

管理所有物理实体：
- 创建和销毁刚体
- 创建和销毁约束
- 设置碰撞回调
- 模拟步进
- 重力、碰撞响应、约束求解

## 学习目标

通过本项目，你将学习：

1. **物理模拟原理**
   - 牛顿运动定律
   - 数值积分方法（欧拉积分）
   - 力和冲量的区别

2. **碰撞检测算法**
   - 宽相检测（AABB）
   - 窄相检测（精确碰撞）
   - 碰撞响应（冲量、摩擦）

3. **约束求解**
   - 约束的数学表示
   - 迭代求解方法
   - 稳定性和收敛性

## 示例程序

### 基础示例 (`example_basic`)
演示基本的自由落体和碰撞。

### 碰撞示例 (`example_collision`)
演示多个物体的碰撞检测和响应。

### 约束示例 (`example_constraints`)
演示链条和摆锤的约束求解。

### 摆链示例 (`example_pendulum`)
演示单摆的物理模拟和能量守恒。

## 测试

运行所有测试：

```bash
cd build
ctest --output-on-failure
```

测试覆盖：
- 向量数学运算
- AABB 碰撞检测
- 刚体动力学
- 约束求解
- 集成测试（完整物理模拟）

## 文档

详细文档位于 `docs/` 目录：

1. **01-RESEARCH.md**：物理引擎研究和背景知识
2. **02-DESIGN.md**：系统设计和架构
3. **03-IMPLEMENTATION.md**：实现细节和算法
4. **04-TESTING.md**：测试策略和用例
5. **05-DEVELOPMENT.md**：开发过程和经验总结

## 学习笔记

`LEARNING_NOTES.md` 记录了开发过程中的学习心得和关键概念。

## 扩展方向

可以进一步扩展的功能：

1. **更多形状支持**：多边形、凸包
2. **更高效的碰撞检测**：空间分区（四叉树、BVH）
3. **更复杂的约束**：滑轮、齿轮
4. **性能优化**：并行计算、休眠机制
5. **3D 支持**：扩展到三维空间

## 参考资源

- [Game Physics Engine Development](https://www.amazon.com/Game-Physics-Engine-Development-Commercial-Grade/dp/0123819768)
- [Real-Time Collision Detection](https://www.amazon.com/Real-Time-Collision-Detection-Interactive-Technology/dp/1558607323)
- [Box2D 物理引擎](https://box2d.org/)
- [Bullet 物理引擎](https://pybullet.org/)

## 许可证

本项目仅用于学习目的。
