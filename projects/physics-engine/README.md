# 2D 物理引擎 (Python)

一个用 Python 实现的 2D 物理引擎，支持刚体动力学、碰撞检测与响应、约束系统和多种积分方法。

## 功能特性

### 核心组件

- **向量数学** (`Vector2D`) - 2D 向量运算
- **刚体** (`RigidBody`) - 质量、速度、加速度
- **碰撞器** (`Collider`) - 圆形、AABB、多边形
- **碰撞检测** (`CollisionDetector`) - AABB、圆形、SAT
- **碰撞响应** (`CollisionResolver`) - 弹性/非弹性碰撞、摩擦力
- **约束系统** (`Constraint`) - 距离约束、弹簧
- **积分器** (`Integrator`) - 欧拉、Verlet、RK4
- **物理世界** (`PhysicsWorld`) - 主仿真循环

### 碰撞检测算法

1. **AABB 碰撞** - 轴对齐包围盒检测
2. **圆形碰撞** - 圆形之间的碰撞检测
3. **分离轴定理 (SAT)** - 凸多边形碰撞检测

### 碰撞响应

- **弹性碰撞** - 动量守恒
- **非弹性碰撞** - 能量损失
- **摩擦力** - 库仑摩擦模型

### 积分方法

1. **欧拉方法** - 半隐式欧拉积分
2. **Verlet 积分** - 位置积分，更好的稳定性
3. **RK4** - 四阶龙格-库塔方法

## 项目结构

```
physics-engine/
├── src/
│   ├── __init__.py
│   ├── vector.py          # 向量数学
│   ├── rigidbody.py       # 刚体
│   ├── collider.py        # 碰撞器形状
│   ├── collision.py       # 碰撞检测
│   ├── resolver.py        # 碰撞响应
│   ├── constraint.py      # 约束系统
│   ├── integrator.py      # 积分器
│   └── world.py           # 物理世界
├── examples/
│   ├── pinball.py         # 弹球游戏
│   └── physics_demo.py    # 物理演示
├── tests/
│   ├── test_vector.py     # 向量测试
│   └── test_physics.py    # 物理测试
└── docs/
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

## 快速开始

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

### 添加约束

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

### 碰撞检测

```python
from src import CollisionDetector, AABBCollider

# 创建 AABB 碰撞器
box_a = AABBCollider(body_a, width=2, height=2)
box_b = AABBCollider(body_b, width=2, height=2)

# 检测碰撞
collision = CollisionDetector.check_collision(box_a, box_b)
if collision:
    print(f"Collision detected! Penetration: {collision.penetration}")
```

## 运行示例

### 弹球游戏

```bash
python examples/pinball.py
```

操作说明：
- 左/右箭头键：控制挡板
- 空格键：发射新球
- ESC：退出

### 物理演示

```bash
python examples/physics_demo.py
```

操作说明：
- 鼠标点击：添加随机物体
- R 键：重置场景
- ESC：退出

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_vector.py -v
pytest tests/test_physics.py -v
```

## 技术细节

### 碰撞检测

#### AABB 碰撞
轴对齐包围盒碰撞检测是最简单的方法，适用于快速粗略检测。

#### 圆形碰撞
通过计算圆心距离与半径之和来判断碰撞。

#### 分离轴定理 (SAT)
用于凸多边形碰撞检测。如果存在一条轴使得两个多边形的投影不重叠，则它们不相交。

### 碰撞响应

#### 弹性碰撞
使用动量守恒和能量守恒计算碰撞后的速度。

#### 摩擦力
使用库仑摩擦模型，在切线方向上施加摩擦力。

### 积分方法

#### 欧拉方法
半隐式欧拉积分，先更新速度再更新位置。

#### Verlet 积分
基于位置的积分方法，更适合约束求解。

#### RK4
四阶龙格-库塔方法，提供更高的精度。

## 依赖

- Python 3.10+
- Pygame（用于可视化示例）

## 安装

```bash
pip install pygame pytest
```

## 许可证

MIT License
