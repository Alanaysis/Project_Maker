# 物理引擎开发文档

## 1. 开发概述

### 开发目标

实现一个简易的 2D 物理引擎，支持：
- 刚体动力学
- AABB 碰撞检测
- 简单的约束求解

### 开发环境

- **操作系统**：Linux
- **编译器**：GCC/Clang
- **构建系统**：CMake
- **测试框架**：Google Test
- **IDE**：VS Code / CLion

### 开发流程

1. **需求分析**：确定功能范围和目标
2. **设计阶段**：架构设计、接口设计
3. **实现阶段**：编码实现
4. **测试阶段**：单元测试、集成测试
5. **文档阶段**：编写文档
6. **优化阶段**：性能优化

## 2. 开发计划

### 阶段 1：基础数学库

**目标**：实现 2D 向量数学库

**任务**：
1. 创建 `Vector2D` 结构
2. 实现基本运算（加、减、乘、除）
3. 实现向量运算（点积、叉积、长度、归一化）
4. 实现变换（旋转、投影、反射）
5. 编写单元测试

**时间**：1 天

### 阶段 2：几何基础

**目标**：实现 AABB 碰撞检测

**任务**：
1. 创建 `AABB` 结构
2. 实现相交测试
3. 实现合并、扩展操作
4. 编写单元测试

**时间**：0.5 天

### 阶段 3：刚体系统

**目标**：实现刚体动力学

**任务**：
1. 定义 `RigidBodyDef` 结构
2. 实现 `RigidBody` 类
3. 实现力、冲量、扭矩
4. 实现积分方法
5. 编写单元测试

**时间**：1 天

### 阶段 4：碰撞检测

**目标**：实现碰撞检测系统

**任务**：
1. 定义碰撞信息结构
2. 实现 AABB 碰撞检测
3. 实现圆形碰撞检测
4. 实现 AABB 与圆形碰撞检测
5. 编写单元测试

**时间**：1 天

### 阶段 5：约束系统

**目标**：实现约束求解

**任务**：
1. 定义约束基类
2. 实现距离约束
3. 实现钉子约束
4. 实现约束求解器
5. 编写单元测试

**时间**：1 天

### 阶段 6：物理世界

**目标**：实现物理世界

**任务**：
1. 实现 `World` 类
2. 实现模拟循环
3. 实现碰撞响应
4. 实现位置修正
5. 编写集成测试

**时间**：1.5 天

### 阶段 7：示例和文档

**目标**：创建示例程序和文档

**任务**：
1. 创建基础示例
2. 创建碰撞示例
3. 创建约束示例
4. 编写 README
5. 编写学习笔记

**时间**：1 天

**总计**：7 天

## 3. 开发日志

### Day 1：基础数学库

**完成内容**：
- 创建 `Vector2D` 结构
- 实现基本运算
- 实现向量运算
- 实现变换
- 编写单元测试

**遇到的问题**：
1. 浮点数精度问题：使用 `EXPECT_NEAR` 而不是 `EXPECT_DOUBLE_EQ`
2. 零向量归一化：添加边界检查

**解决方案**：
1. 使用相对误差比较
2. 返回零向量

**代码统计**：
- 新增文件：2
- 新增代码行：约 300 行
- 测试用例：25 个

### Day 2：几何基础

**完成内容**：
- 创建 `AABB` 结构
- 实现相交测试
- 实现合并、扩展
- 编写单元测试

**遇到的问题**：
1. 边界情况：完全重叠、边界接触
2. 距离计算：分离 AABB 的距离

**解决方案**：
1. 使用 `<=` 和 `>=` 处理边界
2. 使用 `std::max` 计算分离距离

**代码统计**：
- 新增文件：2
- 新增代码行：约 200 行
- 测试用例：15 个

### Day 3：刚体系统

**完成内容**：
- 定义 `RigidBodyDef`
- 实现 `RigidBody` 类
- 实现力、冲量、扭矩
- 实现积分方法
- 编写单元测试

**遇到的问题**：
1. 静态物体的质量：设置 `inv_mass` 为 0
2. 转动惯量：简化为圆形近似
3. 积分稳定性：使用半隐式欧拉法

**解决方案**：
1. 检查物体类型
2. 使用简化公式
3. 先更新速度，再更新位置

**代码统计**：
- 新增文件：3
- 新增代码行：约 400 行
- 测试用例：20 个

### Day 4：碰撞检测

**完成内容**：
- 定义碰撞信息结构
- 实现 AABB 碰撞检测
- 实现圆形碰撞检测
- 实现 AABB 与圆形碰撞检测
- 编写单元测试

**遇到的问题**：
1. 碰撞法线方向：统一从 A 指向 B
2. 穿透深度计算：选择最小穿透方向
3. 接触点计算：使用中心点

**解决方案**：
1. 约定法线方向
2. 比较 X 和 Y 方向的重叠
3. 使用 AABB 中心

**代码统计**：
- 新增文件：2
- 新增代码行：约 300 行
- 测试用例：18 个

### Day 5：约束系统

**完成内容**：
- 定义约束基类
- 实现距离约束
- 实现钉子约束
- 实现约束求解器
- 编写单元测试

**遇到的问题**：
1. 约束求解的稳定性：使用迭代方法
2. 有效质量计算：考虑两个物体
3. 阻尼应用：防止振荡

**解决方案**：
1. 使用多次迭代
2. 计算总逆质量
3. 添加速度阻尼

**代码统计**：
- 新增文件：2
- 新增代码行：约 350 行
- 测试用例：12 个

### Day 6：物理世界

**完成内容**：
- 实现 `World` 类
- 实现模拟循环
- 实现碰撞响应
- 实现位置修正
- 编写集成测试

**遇到的问题**：
1. 碰撞响应：冲量计算
2. 摩擦力：库仑摩擦模型
3. 位置修正：解决穿透

**解决方案**：
1. 使用冲量公式
2. 使用库仑摩擦定律
3. 使用位置修正百分比

**代码统计**：
- 新增文件：3
- 新增代码行：约 500 行
- 测试用例：15 个

### Day 7：示例和文档

**完成内容**：
- 创建基础示例
- 创建碰撞示例
- 创建约束示例
- 编写 README
- 编写学习笔记

**遇到的问题**：
1. 示例的可读性：添加详细注释
2. 文档的完整性：覆盖所有功能

**解决方案**：
1. 使用清晰的变量名
2. 分模块编写文档

**代码统计**：
- 新增文件：8
- 新增代码行：约 800 行
- 文档页数：约 50 页

## 4. 代码规范

### 命名规范

#### 变量命名

- **局部变量**：snake_case
  ```cpp
  double time_step;
  Vector2D velocity;
  ```

- **成员变量**：snake_case_（带下划线后缀）
  ```cpp
  double mass_;
  Vector2D position_;
  ```

- **常量**：UPPER_CASE 或 kCamelCase
  ```cpp
  constexpr double PI = 3.14159265358979323846;
  constexpr int kMaxIterations = 10;
  ```

#### 函数命名

- **普通函数**：snake_case
  ```cpp
  void apply_force(const Vector2D& force);
  double calculate_distance();
  ```

- **类方法**：snake_case
  ```cpp
  void RigidBody::integrate(double dt);
  AABB RigidBody::compute_aabb() const;
  ```

#### 类命名

- **类名**：CamelCase
  ```cpp
  class RigidBody;
  class ConstraintSolver;
  struct WorldConfig;
  ```

#### 枚举命名

- **枚举类型**：CamelCase
- **枚举值**：CamelCase
  ```cpp
  enum class BodyType {
      Static,
      Dynamic,
      Kinematic
  };
  ```

### 代码风格

#### 缩进

- 使用 4 个空格缩进
- 不使用 Tab

#### 大括号

- 函数和类：大括号另起一行
  ```cpp
  void function()
  {
      // ...
  }
  ```

- 控制语句：大括号另起一行
  ```cpp
  if (condition)
  {
      // ...
  }
  else
  {
      // ...
  }
  ```

#### 行长度

- 建议每行不超过 80 个字符
- 最长不超过 120 个字符

#### 空格

- 运算符两边加空格
  ```cpp
  int a = 1 + 2;
  ```

- 逗号后面加空格
  ```cpp
  function(a, b, c);
  ```

- 括号内部不加空格
  ```cpp
  function(a, b);
  ```

### 注释规范

#### 文件注释

```cpp
/**
 * @file vector2d.h
 * @brief 2D 向量数学库
 * @author Your Name
 * @date 2026-06-22
 */
```

#### 类注释

```cpp
/**
 * @brief 2D 向量类
 * 
 * 支持基本的向量运算，包括加法、减法、标量乘法、
 * 点积、叉积、长度、归一化等。
 */
struct Vector2D {
    // ...
};
```

#### 函数注释

```cpp
/**
 * @brief 计算两个向量的点积
 * 
 * @param other 另一个向量
 * @return 点积结果
 */
double dot(const Vector2D& other) const;
```

#### 行内注释

```cpp
// 计算逆质量
if (mass_ > 0.0) {
    inv_mass_ = 1.0 / mass_;
}
```

### 头文件规范

#### 头文件保护

```cpp
#pragma once

// 或者使用 include guards
#ifndef PHYSICS_ENGINE_VECTOR2D_H
#define PHYSICS_ENGINE_VECTOR2D_H
// ...
#endif // PHYSICS_ENGINE_VECTOR2D_H
```

#### 包含顺序

1. 对应的头文件（对于 .cpp 文件）
2. C 标准库
3. C++ 标准库
4. 第三方库
5. 项目内头文件

```cpp
#include "physics_engine/vector2d.h"

#include <cmath>
#include <iostream>

#include <gtest/gtest.h>
```

### 源文件规范

#### 文件结构

1. 包含对应的头文件
2. 命名空间
3. 静态成员定义
4. 函数实现

```cpp
#include "physics_engine/rigid_body.h"

namespace physics_engine {

// 静态成员定义
uint32_t RigidBody::next_id_ = 0;

// 函数实现
RigidBody::RigidBody(const RigidBodyDef& def)
    : type_(def.type)
    // ...
{
    // ...
}

} // namespace physics_engine
```

## 5. 调试技巧

### 常见问题

#### 1. 物体穿透

**症状**：物体穿过其他物体

**原因**：
- 时间步长太大
- 碰撞检测不准确
- 位置修正不足

**解决方案**：
```cpp
// 减小时间步长
config.time_step = 1.0 / 120.0;

// 增加位置修正
config.position_iterations = 5;

// 使用 CCD（连续碰撞检测）
```

#### 2. 约束不稳定

**症状**：约束振荡或爆炸

**原因**：
- 迭代次数不足
- 约束冲突
- 时间步长太大

**解决方案**：
```cpp
// 增加迭代次数
config.velocity_iterations = 16;

// 减小时间步长
config.time_step = 1.0 / 120.0;

// 添加阻尼
constraint->damping = 0.1;
```

#### 3. 能量不守恒

**症状**：物体速度无限增加

**原因**：
- 数值积分误差
- 碰撞响应不准确
- 阻尼不足

**解决方案**：
```cpp
// 添加阻尼
def.linear_damping = 0.01;
def.angular_damping = 0.01;

// 调整恢复系数
def.restitution = 0.5;

// 使用更稳定的积分方法
```

### 调试工具

#### 1. 日志输出

```cpp
// 添加调试日志
std::cout << "Position: " << body->position() << std::endl;
std::cout << "Velocity: " << body->velocity() << std::endl;
std::cout << "Force: " << body->force() << std::endl;
```

#### 2. 可视化

```cpp
// 绘制 AABB
void draw_aabb(const AABB& aabb) {
    // 绘制矩形
}

// 绘制速度向量
void draw_velocity(const RigidBody& body) {
    // 绘制箭头
}
```

#### 3. 断言检查

```cpp
// 检查数值有效性
assert(!std::isnan(body->position().x));
assert(!std::isinf(body->velocity().x));

// 检查物理约束
assert(body->mass() > 0.0);
assert(body->inv_mass() >= 0.0);
```

#### 4. 单元测试

```cpp
// 测试边界情况
TEST(RigidBodyTest, ZeroMass) {
    RigidBodyDef def;
    def.mass = 0.0;
    RigidBody body(def);
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.0);
}

// 测试数值稳定性
TEST(RigidBodyTest, LargeForce) {
    RigidBodyDef def;
    def.mass = 1.0;
    RigidBody body(def);
    body.apply_force({1e10, 0.0});
    body.integrate(1.0 / 60.0);
    EXPECT_FALSE(std::isnan(body->velocity().x));
}
```

### 性能分析

#### 1. 时间测量

```cpp
auto start = std::chrono::high_resolution_clock::now();

// 执行代码
world.step(dt);

auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

std::cout << "Step time: " << duration.count() << " microseconds" << std::endl;
```

#### 2. 热点分析

使用 `gprof` 或 `valgrind` 分析性能热点：

```bash
# 编译时启用性能分析
g++ -pg -o physics_engine ...

# 运行程序
./physics_engine

# 分析结果
gprof physics_engine gmon.out > analysis.txt
```

#### 3. 内存分析

使用 `valgrind` 检查内存问题：

```bash
# 检查内存泄漏
valgrind --leak-check=full ./physics_engine_tests

# 检查内存错误
valgrind --tool=memcheck ./physics_engine_tests
```

## 6. 版本控制

### Git 工作流

#### 分支策略

- **main**：稳定版本
- **develop**：开发分支
- **feature/***：功能分支
- **bugfix/***：修复分支

#### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`：新功能
- `fix`：修复
- `docs`：文档
- `style`：格式
- `refactor`：重构
- `test`：测试
- `chore`：构建

**示例**：
```
feat(collision): add AABB vs Circle collision detection

- Implement AABB vs Circle collision detection
- Add unit tests for new collision type
- Update documentation

Closes #123
```

### 代码审查

#### 审查清单

1. **功能正确性**
   - 代码是否按预期工作？
   - 是否有边界情况未处理？

2. **代码质量**
   - 是否符合代码规范？
   - 是否有重复代码？
   - 是否易于理解？

3. **性能**
   - 是否有性能问题？
   - 是否可以优化？

4. **测试**
   - 是否有足够的测试？
   - 测试是否覆盖边界情况？

5. **文档**
   - 是否有必要的注释？
   - 是否更新了文档？

## 7. 持续集成

### GitHub Actions

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure
      run: cmake -B build -DCMAKE_BUILD_TYPE=Release
    
    - name: Build
      run: cmake --build build
    
    - name: Test
      run: cd build && ctest --output-on-failure
```

### 测试矩阵

- **操作系统**：Ubuntu, macOS, Windows
- **编译器**：GCC, Clang, MSVC
- **CMake 版本**：3.14, 3.20, 3.25

## 8. 发布流程

### 版本号

使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的 API 修改
- **MINOR**：向下兼容的功能性新增
- **PATCH**：向下兼容的问题修正

### 发布步骤

1. 更新版本号
2. 更新 CHANGELOG
3. 创建发布分支
4. 运行测试
5. 创建 Git 标签
6. 发布到 GitHub

### 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 没有已知的严重问题

## 9. 经验总结

### 成功经验

1. **模块化设计**：每个组件独立，易于理解和维护
2. **测试驱动开发**：先写测试，再写实现
3. **渐进式开发**：从简单到复杂，逐步完善
4. **文档同步**：边开发边写文档

### 教训

1. **数值精度**：浮点数运算需要特别注意
2. **边界情况**：需要充分测试边界情况
3. **性能优化**：过早优化是万恶之源
4. **代码规范**：统一的代码规范很重要

### 改进建议

1. **更多测试**：增加边界情况测试
2. **性能优化**：使用空间分区优化碰撞检测
3. **更多功能**：支持更多形状和约束
4. **文档完善**：添加更多示例和教程

## 10. 未来规划

### 短期目标（1-3 个月）

1. 支持多边形碰撞检测
2. 实现空间分区（四叉树）
3. 添加更多约束类型
4. 性能优化

### 中期目标（3-6 个月）

1. 支持 3D 物理
2. 实现更高级的碰撞检测算法（GJK、EPA）
3. 添加布娃娃物理
4. GPU 加速

### 长期目标（6-12 个月）

1. 完整的物理引擎
2. 商业级质量
3. 广泛的应用场景
4. 开源社区

## 11. 开发总结

### 项目统计

- **总开发时间**：7 天
- **代码行数**：约 3000 行
- **测试用例**：约 100 个
- **文档页数**：约 100 页

### 技术收获

1. **物理模拟**：理解了刚体动力学、碰撞检测、约束求解
2. **数值方法**：学习了数值积分、迭代求解
3. **软件工程**：实践了模块化设计、测试驱动开发
4. **C++ 编程**：提高了 C++ 编程能力

### 个人成长

1. **问题解决能力**：学会了分析和解决复杂问题
2. **学习能力**：掌握了快速学习新技术的方法
3. **项目管理**：实践了项目规划和进度管理
4. **团队协作**：提高了代码规范和文档能力

### 致谢

感谢所有为本项目提供帮助和建议的人。

## 12. 附录

### 参考资源

1. **书籍**
   - 《Game Physics Engine Development》
   - 《Real-Time Collision Detection》
   - 《Physics for Game Developers》

2. **网站**
   - [Box2D](https://box2d.org/)
   - [Bullet Physics](https://pybullet.org/)
   - [Game Physics](https://gafferongames.com/)

3. **开源项目**
   - [Box2D](https://github.com/erincatto/box2d)
   - [Bullet](https://github.com/bulletphysics/bullet3)
   - [Chipmunk](https://github.com/slembcke/Chipmunk2D)

### 术语表

- **刚体**：不会变形的物体
- **冲量**：瞬间的力作用
- **约束**：限制物体运动的条件
- **穿透**：两个物体重叠的程度
- **恢复系数**：碰撞弹性的度量
- **阻尼**：减少振荡的力

### 常见问题

1. **Q：为什么使用半隐式欧拉法？**
   A：比显式欧拉法更稳定，计算量增加不多。

2. **Q：如何处理物体穿透？**
   A：使用位置修正，将物体推开。

3. **Q：如何提高约束求解的稳定性？**
   A：增加迭代次数，添加阻尼。

4. **Q：如何优化碰撞检测？**
   A：使用宽相检测（AABB）快速排除，使用空间分区减少检测次数。
