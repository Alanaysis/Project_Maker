# 04 - 产品文档

## 产品概述

2D 物理引擎是一个用 Python 实现的轻量级物理仿真库，用于游戏开发、教育演示和物理模拟。

## 目标用户

### 1. 游戏开发者
- 需要 2D 物理引擎的独立游戏开发者
- 学习游戏物理的学生
- 快速原型开发的程序员

### 2. 教育工作者
- 物理教师
- 编程教师
- 科学仿真研究者

### 3. 学习者
- 学习物理引擎原理的学生
- 学习 Python 编程的开发者
- 对游戏开发感兴趣的人

## 核心价值

### 1. 简单易用
- 清晰的 API 设计
- 详细的文档和示例
- 快速上手

### 2. 功能完整
- 支持刚体动力学
- 支持碰撞检测与响应
- 支持约束系统
- 支持多种积分方法

### 3. 高质量代码
- 模块化设计
- 完整的测试覆盖
- 清晰的代码注释

### 4. 可扩展性
- 易于添加新功能
- 易于集成到其他项目
- 支持自定义扩展

## 功能特性

### 核心功能

#### 1. 向量数学
- 2D 向量基本运算
- 点积、叉积
- 归一化、旋转
- 距离计算

#### 2. 刚体系统
- 质量、速度、加速度
- 力和冲量
- 静态和动态物体
- 旋转动力学

#### 3. 碰撞检测
- AABB 碰撞
- 圆形碰撞
- 多边形碰撞 (SAT)
- 碰撞信息（法线、穿透深度、接触点）

#### 4. 碰撞响应
- 弹性碰撞
- 非弹性碰撞
- 摩擦力
- 位置修正

#### 5. 约束系统
- 距离约束
- 弹簧约束
- 钉子约束
- 角度约束

#### 6. 积分方法
- 欧拉方法
- Verlet 积分
- RK4 方法

#### 7. 物理世界
- 重力模拟
- 物体管理
- 约束管理
- 碰撞回调

### 示例程序

#### 1. 弹球游戏
- 完整的弹球游戏实现
- 挡板控制
- 计分系统
- 物体碰撞

#### 2. 物理演示
- 多种物体类型
- 弹簧系统
- 约束演示
- 交互式添加物体

## 使用场景

### 1. 游戏开发

#### 弹球游戏
```python
# 创建弹球游戏
world = PhysicsWorld()
world.gravity = Vector2D(0, 500)

# 创建挡板
flipper = RigidBody(Vector2D(200, 500), is_static=True)
world.add_body(flipper, AABBCollider(flipper, 80, 15))

# 创建球
ball = RigidBody(Vector2D(370, 500), mass=1.0)
ball.apply_impulse(Vector2D(-300, -800))
world.add_body(ball, CircleCollider(ball, 10))
```

#### 物理模拟
```python
# 创建物理模拟
world = PhysicsWorld()
world.gravity = Vector2D(0, 9.81)

# 创建多个物体
for i in range(10):
    body = RigidBody(Vector2D(i * 50, 100), mass=1.0)
    world.add_body(body, CircleCollider(body, 20))

# 运行仿真
for _ in range(1000):
    world.step(1 / 60)
```

### 2. 教育演示

#### 物理实验
```python
# 演示弹性碰撞
world = PhysicsWorld()
world.gravity = Vector2D(0, 0)

body_a = RigidBody(Vector2D(0, 0), mass=1.0)
body_a.velocity = Vector2D(5, 0)

body_b = RigidBody(Vector2D(10, 0), mass=1.0)
body_b.velocity = Vector2D(-3, 0)

world.add_body(body_a, CircleCollider(body_a, 5))
world.add_body(body_b, CircleCollider(body_b, 5))

# 观察碰撞后的速度变化
for _ in range(100):
    world.step(1 / 60)
    print(f"A: {body_a.velocity}, B: {body_b.velocity}")
```

#### 约束演示
```python
# 演示弹簧系统
world = PhysicsWorld()
world.gravity = Vector2D(0, 9.81)

# 创建两个物体
body_a = RigidBody(Vector2D(0, 0), mass=1.0)
body_b = RigidBody(Vector2D(5, 0), mass=1.0)

world.add_body(body_a, CircleCollider(body_a, 10))
world.add_body(body_b, CircleCollider(body_b, 10))

# 添加弹簧约束
spring = SpringConstraint(body_a, body_b, stiffness=50.0, damping=5.0)
world.add_constraint(spring)

# 观察弹簧振荡
for _ in range(500):
    world.step(1 / 60)
```

### 3. 科学仿真

#### 分子动力学
```python
# 模拟分子运动
world = PhysicsWorld()
world.gravity = Vector2D(0, 0)  # 无重力

# 创建多个分子
molecules = []
for i in range(50):
    pos = Vector2D(random.uniform(0, 800), random.uniform(0, 600))
    vel = Vector2D(random.uniform(-100, 100), random.uniform(-100, 100))
    
    mol = RigidBody(pos, mass=1.0)
    mol.velocity = vel
    mol.restitution = 1.0  # 完全弹性碰撞
    
    world.add_body(mol, CircleCollider(mol, 10))
    molecules.append(mol)

# 运行仿真
for _ in range(1000):
    world.step(1 / 60)
```

## 技术规格

### 系统要求
- Python 3.10+
- Pygame（可视化示例）
- Pytest（测试）

### 性能指标
- 支持 100+ 物体实时仿真
- 60 FPS 帧率目标
- 低内存占用

### API 规范
- 清晰的函数命名
- 类型提示
- 详细的文档字符串
- 合理的默认参数

## 示例代码

### 基本使用

```python
from src import (
    Vector2D, RigidBody, CircleCollider,
    PhysicsWorld, EulerIntegrator
)

# 创建物理世界
world = PhysicsWorld(integrator=EulerIntegrator())
world.gravity = Vector2D(0, 9.81)

# 创建刚体
ball = RigidBody(Vector2D(0, 10), mass=1.0)
ball.velocity = Vector2D(5, 0)
ball.restitution = 0.8

# 添加碰撞器
collider = CircleCollider(ball, radius=1.0)
world.add_body(ball, collider)

# 运行仿真
for _ in range(100):
    world.step(1 / 60)
    print(f"Position: {ball.position}")
```

### 碰撞检测

```python
from src import CollisionDetector, AABBCollider

# 创建 AABB 碰撞器
box_a = AABBCollider(body_a, width=2, height=2)
box_b = AABBCollider(body_b, width=2, height=2)

# 检测碰撞
collision = CollisionDetector.check_collision(box_a, box_b)
if collision:
    print(f"Collision detected!")
    print(f"Normal: {collision.normal}")
    print(f"Penetration: {collision.penetration}")
```

### 约束系统

```python
from src import SpringConstraint, DistanceConstraint

# 创建两个物体
body_a = RigidBody(Vector2D(0, 0), mass=1.0)
body_b = RigidBody(Vector2D(5, 0), mass=1.0)

# 添加弹簧约束
spring = SpringConstraint(body_a, body_b, stiffness=50.0, damping=5.0)
world.add_constraint(spring)

# 添加距离约束
distance = DistanceConstraint(body_a, body_b, distance=3.0)
world.add_constraint(distance)
```

## 竞品分析

### 与 Box2D 比较

| 特性 | 本项目 | Box2D |
|------|--------|-------|
| 语言 | Python | C++ |
| 复杂度 | 简单 | 复杂 |
| 功能 | 基础 | 完整 |
| 性能 | 中等 | 高 |
| 学习曲线 | 平缓 | 陡峭 |
| 适用场景 | 教育、原型 | 生产环境 |

### 与 PyMunk 比较

| 特性 | 本项目 | PyMunk |
|------|--------|--------|
| 依赖 | 无外部依赖 | 依赖 Chipmunk |
| 功能 | 基础 | 完整 |
| 性能 | 中等 | 高 |
| 学习成本 | 低 | 中等 |
| 适用场景 | 学习、原型 | 游戏开发 |

## 发展路线

### 短期目标 (v1.0)
- [x] 核心物理功能
- [x] 基本碰撞检测
- [x] 约束系统
- [x] 示例程序
- [x] 单元测试

### 中期目标 (v2.0)
- [ ] 空间分区优化
- [ ] 更多碰撞形状
- [ ] 连续碰撞检测
- [ ] 性能优化

### 长期目标 (v3.0)
- [ ] 3D 物理支持
- [ ] 流体模拟
- [ ] 布料模拟
- [ ] GPU 加速

## 已知限制

### 1. 功能限制
- 仅支持 2D 物理
- 不支持凹多边形
- 不支持连续碰撞检测
- 不支持流体模拟

### 2. 性能限制
- 大量物体时性能下降
- 不支持多线程
- 无 GPU 加速

### 3. 兼容性限制
- 仅支持 Python 3.10+
- 可视化依赖 Pygame

## 支持与反馈

### 问题报告
- 使用 GitHub Issues 报告 bug
- 提供详细的复现步骤
- 包含错误信息和堆栈跟踪

### 功能请求
- 使用 GitHub Issues 提出功能建议
- 说明使用场景和需求
- 提供设计建议

### 贡献指南
- Fork 项目
- 创建功能分支
- 提交 Pull Request
- 遵循代码规范

## 许可证

MIT License

## 联系方式

- 项目地址: [GitHub Repository]
- 文档: [Documentation]
- 示例: [Examples]
