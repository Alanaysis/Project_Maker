# 03 - 系统设计

## 架构概述

本物理引擎采用模块化设计，各组件职责明确，通过清晰的接口进行交互。

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      PhysicsWorld                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Bodies    │  │ Colliders   │  │ Constraints │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                │
│         ▼                ▼                ▼                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Collision Detection                    │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │  AABB   │  │ Circle  │  │   SAT   │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Collision Response                     │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │ Impulse │  │ Friction│  │Position │            │   │
│  │  │         │  │         │  │Correction│            │   │
│  │  └─────────┘  └─────────┘  └─────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Integration                            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │  Euler  │  │ Verlet  │  │   RK4   │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Vector2D 模块

**职责**：提供 2D 向量的数学运算。

**设计要点**：
- 使用 `dataclass` 实现值类型语义
- 支持运算符重载（`+`, `-`, `*`, `/`）
- 提供不可变操作（返回新对象）和可变操作（`+=`, `-=`）
- 包含常用的几何运算

**类图**：
```
Vector2D
├── x: float
├── y: float
├── __add__(other) -> Vector2D
├── __sub__(other) -> Vector2D
├── __mul__(scalar) -> Vector2D
├── __truediv__(scalar) -> Vector2D
├── __neg__() -> Vector2D
├── dot(other) -> float
├── cross(other) -> float
├── length() -> float
├── length_squared() -> float
├── normalized() -> Vector2D
├── perpendicular() -> Vector2D
├── reflect(normal) -> Vector2D
├── distance_to(other) -> float
├── angle() -> float
└── from_angle(angle, length) -> Vector2D
```

### 2. RigidBody 模块

**职责**：表示物理世界中的刚体对象。

**设计要点**：
- 区分静态和动态物体
- 使用逆质量避免除零错误
- 存储累积力，在积分后清除
- 支力力和冲量

**状态管理**：
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Forces    │ ──▶ │ Acceleration│ ──▶ │  Velocity   │
└─────────────┘     └─────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  Position   │
                                         └─────────────┘
```

**类图**：
```
RigidBody
├── position: Vector2D
├── velocity: Vector2D
├── acceleration: Vector2D
├── force: Vector2D
├── mass: float
├── inverse_mass: float
├── is_static: bool
├── restitution: float
├── friction: float
├── rotation: float
├── angular_velocity: float
├── apply_force(force)
├── apply_impulse(impulse)
├── clear_forces()
├── update(dt)
├── kinetic_energy: float
└── momentum: Vector2D
```

### 3. Collider 模块

**职责**：定义物体的碰撞形状。

**设计要点**：
- 抽象基类 `Collider`
- 每种形状实现自己的碰撞检测
- 支持获取 AABB 用于宽相检测
- 支持点包含测试

**继承层次**：
```
Collider (Abstract)
├── CircleCollider
│   ├── radius: float
│   ├── get_aabb() -> (min, max)
│   └── contains_point(point) -> bool
├── AABBCollider
│   ├── width: float
│   ├── height: float
│   ├── get_aabb() -> (min, max)
│   ├── contains_point(point) -> bool
│   └── get_corners() -> list[Vector2D]
└── PolygonCollider
    ├── vertices: list[Vector2D]
    ├── normals: list[Vector2D]
    ├── get_world_vertices() -> list[Vector2D]
    ├── get_aabb() -> (min, max)
    ├── contains_point(point) -> bool
    └── create_box(width, height) -> PolygonCollider
```

### 4. CollisionDetector 模块

**职责**：检测物体之间的碰撞。

**设计要点**：
- 使用双分派处理不同形状组合
- 返回 `CollisionInfo` 或 `None`
- 支持 AABB、圆形、多边形碰撞

**碰撞检测流程**：
```
check_collision(collider_a, collider_b)
    │
    ├─ Circle vs Circle ──▶ circle_vs_circle()
    ├─ AABB vs AABB ──▶ aabb_vs_aabb()
    ├─ Circle vs AABB ──▶ circle_vs_aabb()
    └─ Polygon vs Polygon ──▶ sat_polygon_vs_polygon()
```

**SAT 算法流程**：
```
sat_polygon_vs_polygon(a, b)
    │
    ├─ 1. 获取所有边法线
    ├─ 2. 投影两个多边形到每个法线
    ├─ 3. 检查是否有分离轴
    └─ 4. 如果没有分离轴，计算最小穿透
```

### 5. CollisionResolver 模块

**职责**：处理碰撞后的物体响应。

**设计要点**：
- 基于冲量的碰撞响应
- 支持弹性/非弹性碰撞
- 包含摩擦力计算
- 位置修正防止物体重叠

**碰撞响应流程**：
```
resolve(collision)
    │
    ├─ 1. 计算相对速度
    ├─ 2. 计算沿法线的速度分量
    ├─ 3. 计算冲量大小
    │     └─ j = -(1 + e) * v_rel·n / (1/m_a + 1/m_b)
    ├─ 4. 应用冲量
    ├─ 5. 应用摩擦力
    └─ 6. 位置修正
```

### 6. Constraint 模块

**职责**：限制物体之间的相对运动。

**设计要点**：
- 抽象基类 `Constraint`
- 每种约束实现自己的求解方法
- 支持迭代求解提高稳定性

**约束类型**：

#### DistanceConstraint
```
distance_constraint(a, b, distance)
    │
    ├─ 计算当前距离
    ├─ 计算距离误差
    ├─ 计算位置修正
    └─ 应用修正
```

#### SpringConstraint
```
spring_constraint(a, b, rest_length, stiffness, damping)
    │
    ├─ 计算当前长度
    ├─ 计算弹簧力 (胡克定律)
    │     └─ F = -k * (length - rest_length)
    ├─ 计算阻尼力
    │     └─ F = -d * velocity
    └─ 应用力
```

### 7. Integrator 模块

**职责**：将加速度积分到速度，将速度积分到位置。

**设计要点**：
- 抽象基类 `Integrator`
- 每种积分器实现自己的积分方法
- 支持可变时间步长

#### EulerIntegrator
```
integrate(body, dt)
    │
    ├─ v += a * dt  (半隐式)
    ├─ x += v * dt
    └─ 清除力
```

#### VerletIntegrator
```
integrate(body, dt)
    │
    ├─ x_new = 2*x - x_old + a*dt²
    ├─ v = (x_new - x_old) / (2*dt)
    └─ 清除力
```

#### RK4Integrator
```
integrate(body, dt)
    │
    ├─ k1 = f(t, y)
    ├─ k2 = f(t + dt/2, y + k1*dt/2)
    ├─ k3 = f(t + dt/2, y + k2*dt/2)
    ├─ k4 = f(t + dt, y + k3*dt)
    └─ y_new = y + (k1 + 2*k2 + 2*k3 + k4) * dt / 6
```

### 8. PhysicsWorld 模块

**职责**：管理整个物理仿真。

**设计要点**：
- 管理所有物体和约束
- 实现物理循环
- 支持重力设置
- 提供查询接口

**物理循环**：
```
step(dt)
    │
    ├─ 1. 应用外力 (重力)
    ├─ 2. 碰撞检测
    │     └─ 对所有物体对进行碰撞检测
    ├─ 3. 碰撞响应
    │     └─ 对所有碰撞进行响应
    ├─ 4. 约束求解
    │     └─ 迭代求解所有约束
    └─ 5. 积分更新
          └─ 对所有物体进行积分
```

## 数据流

### 完整仿真循环

```
┌─────────────────────────────────────────────────────────────┐
│                    PhysicsWorld.step(dt)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Apply Gravity                                           │
│     for body in bodies:                                     │
│         body.apply_force(gravity * body.mass)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Detect Collisions                                       │
│     for i, j in body_pairs:                                 │
│         collision = detect(collider_i, collider_j)          │
│         if collision: collisions.append(collision)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Resolve Collisions                                      │
│     for collision in collisions:                            │
│         resolve(collision)                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Solve Constraints                                       │
│     for _ in range(iterations):                             │
│         for constraint in constraints:                      │
│             constraint.solve(dt)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Integrate                                               │
│     for body in bodies:                                     │
│         integrator.integrate(body, dt)                      │
└─────────────────────────────────────────────────────────────┘
```

## 接口设计

### 主要接口

```python
class PhysicsWorld:
    def add_body(self, body: RigidBody, collider: Collider = None) -> None
    def remove_body(self, body: RigidBody) -> None
    def add_constraint(self, constraint: Constraint) -> None
    def remove_constraint(self, constraint: Constraint) -> None
    def step(self, dt: float) -> None
    def get_body_at(self, point: Vector2D) -> RigidBody | None
    def clear(self) -> None
```

### 扩展接口

```python
class Collider(ABC):
    @abstractmethod
    def get_aabb(self) -> tuple[Vector2D, Vector2D]
    @abstractmethod
    def contains_point(self, point: Vector2D) -> bool

class Constraint(ABC):
    @abstractmethod
    def solve(self, dt: float) -> None

class Integrator(ABC):
    @abstractmethod
    def integrate(self, body: RigidBody, dt: float) -> None
```

## 设计模式

### 1. 策略模式
- 积分器作为策略
- 可以在运行时切换积分方法

### 2. 组合模式
- PhysicsWorld 包含多个组件
- 组件之间松耦合

### 3. 访问者模式
- 碰撞检测使用双分派
- 根据类型选择不同的检测算法

### 4. 工厂模式
- PolygonCollider.create_box() 静态方法
- 简化常见形状的创建

## 性能考虑

### 1. 碰撞检测优化
- 使用 AABB 进行宽相检测
- 空间分区减少检测次数

### 2. 内存管理
- 使用逆质量避免除零
- 对象池减少内存分配

### 3. 计算优化
- 使用 length_squared() 避免开方
- 批量处理相似操作

### 4. 数值稳定性
- 位置修正防止重叠
- 阻尼防止振荡

## 错误处理

### 1. 输入验证
- 检查质量不为零
- 检查向量有效性

### 2. 边界情况
- 处理零距离向量
- 处理静态物体

### 3. 异常处理
- 捕获除零错误
- 提供有意义的错误信息

## 测试策略

### 1. 单元测试
- 测试每个模块的核心功能
- 测试边界情况和异常

### 2. 集成测试
- 测试模块之间的交互
- 测试完整的物理循环

### 3. 性能测试
- 测试大量物体的性能
- 测试长时间运行的稳定性

## 未来扩展

### 1. 功能扩展
- 3D 物理支持
- 连续碰撞检测 (CCD)
- 更多约束类型
- 流体模拟

### 2. 性能优化
- 空间分区 (四叉树/BVH)
- 多线程支持
- GPU 加速

### 3. 工具支持
- 可视化调试工具
- 性能分析工具
- 场景编辑器
