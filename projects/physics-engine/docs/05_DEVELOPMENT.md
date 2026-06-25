# 05 - 开发文档

## 开发环境

### 系统要求
- Python 3.10+
- Git
- VS Code / PyCharm (推荐)

### 依赖安装
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install pygame pytest
```

## 项目结构

```
physics-engine/
├── src/                        # 源代码
│   ├── __init__.py            # 包初始化
│   ├── vector.py              # 向量数学
│   ├── rigidbody.py           # 刚体
│   ├── collider.py            # 碰撞器
│   ├── collision.py           # 碰撞检测
│   ├── resolver.py            # 碰撞响应
│   ├── constraint.py          # 约束系统
│   ├── integrator.py          # 积分器
│   └── world.py               # 物理世界
├── examples/                   # 示例程序
│   ├── pinball.py             # 弹球游戏
│   └── physics_demo.py        # 物理演示
├── tests/                      # 测试文件
│   ├── test_vector.py         # 向量测试
│   └── test_physics.py        # 物理测试
├── docs/                       # 文档
│   ├── 01_RESEARCH.md         # 研究文档
│   ├── 02_REQUIREMENTS.md     # 需求文档
│   ├── 03_DESIGN.md           # 设计文档
│   ├── 04_PRODUCT.md          # 产品文档
│   └── 05_DEVELOPMENT.md      # 开发文档
└── README.md                   # 项目说明
```

## 开发流程

### 1. 需求分析
- 确定项目目标
- 分析功能需求
- 制定技术方案

### 2. 设计阶段
- 模块划分
- 接口设计
- 数据结构设计

### 3. 实现阶段
- 逐步实现各模块
- 编写单元测试
- 代码审查

### 4. 测试阶段
- 运行所有测试
- 修复 bug
- 性能优化

### 5. 文档阶段
- 编写 README
- 编写 API 文档
- 编写示例代码

## 实现细节

### 1. 向量数学 (`vector.py`)

**关键实现**：

```python
@dataclass
class Vector2D:
    x: float = 0.0
    y: float = 0.0
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def dot(self, other: 'Vector2D') -> float:
        return self.x * other.x + self.y * other.y
    
    def cross(self, other: 'Vector2D') -> float:
        return self.x * other.y - self.y * other.x
    
    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self) -> 'Vector2D':
        length = self.length()
        if length == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / length, self.y / length)
```

**设计考虑**：
- 使用 `dataclass` 简化代码
- 运算符重载提高可读性
- 处理零向量的特殊情况
- 提供可变和不可变操作

### 2. 刚体 (`rigidbody.py`)

**关键实现**：

```python
class RigidBody:
    def __init__(self, position: Vector2D = None, mass: float = 1.0, is_static: bool = False):
        self.position = position or Vector2D.zero()
        self.velocity = Vector2D.zero()
        self.acceleration = Vector2D.zero()
        self.force = Vector2D.zero()
        
        self.mass = mass
        self.inverse_mass = 0.0 if is_static or mass == 0 else 1.0 / mass
        self.is_static = is_static
        
        self.restitution = 0.5
        self.friction = 0.2
    
    def apply_force(self, force: Vector2D) -> None:
        if not self.is_static:
            self.force += force
    
    def apply_impulse(self, impulse: Vector2D) -> None:
        if not self.is_static:
            self.velocity += impulse * self.inverse_mass
```

**设计考虑**：
- 使用逆质量避免除零
- 区分静态和动态物体
- 支持力和冲量
- 存储累积力，在积分后清除

### 3. 碰撞器 (`collider.py`)

**关键实现**：

```python
class Collider(ABC):
    @abstractmethod
    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        pass
    
    @abstractmethod
    def contains_point(self, point: Vector2D) -> bool:
        pass

class CircleCollider(Collider):
    def __init__(self, body: RigidBody, radius: float = 1.0):
        super().__init__(body)
        self.radius = radius
    
    def get_aabb(self) -> tuple[Vector2D, Vector2D]:
        min_point = self.body.position - Vector2D(self.radius, self.radius)
        max_point = self.body.position + Vector2D(self.radius, self.radius)
        return min_point, max_point
```

**设计考虑**：
- 抽象基类定义统一接口
- 每种形状实现自己的检测方法
- 支持 AABB 用于宽相检测
- 支持点包含测试

### 4. 碰撞检测 (`collision.py`)

**关键实现**：

```python
class CollisionDetector:
    @staticmethod
    def check_collision(a: Collider, b: Collider) -> CollisionInfo | None:
        if isinstance(a, CircleCollider) and isinstance(b, CircleCollider):
            return CollisionDetector.circle_vs_circle(a, b)
        elif isinstance(a, AABBCollider) and isinstance(b, AABBCollider):
            return CollisionDetector.aabb_vs_aabb(a, b)
        # ... 其他组合
    
    @staticmethod
    def circle_vs_circle(a: CircleCollider, b: CircleCollider) -> CollisionInfo | None:
        diff = b.body.position - a.body.position
        distance = diff.length()
        sum_radius = a.radius + b.radius
        
        if distance >= sum_radius:
            return None
        
        normal = diff.normalized()
        penetration = sum_radius - distance
        contact_point = a.body.position + normal * a.radius
        
        return CollisionInfo(
            body_a=a.body,
            body_b=b.body,
            normal=normal,
            penetration=penetration,
            contact_point=contact_point,
        )
```

**设计考虑**：
- 使用双分派处理不同形状组合
- 返回 `CollisionInfo` 或 `None`
- 计算碰撞法线、穿透深度、接触点
- 支持 AABB、圆形、多边形碰撞

### 5. 碰撞响应 (`resolver.py`)

**关键实现**：

```python
class CollisionResolver:
    @staticmethod
    def resolve(collision: CollisionInfo) -> None:
        body_a = collision.body_a
        body_b = collision.body_b
        normal = collision.normal
        
        # 计算相对速度
        relative_velocity = body_b.velocity - body_a.velocity
        velocity_along_normal = relative_velocity.dot(normal)
        
        # 不处理分离的物体
        if velocity_along_normal > 0:
            return
        
        # 计算恢复系数
        restitution = min(body_a.restitution, body_b.restitution)
        
        # 计算冲量大小
        impulse_scalar = -(1 + restitution) * velocity_along_normal
        impulse_scalar /= body_a.inverse_mass + body_b.inverse_mass
        
        # 应用冲量
        impulse = normal * impulse_scalar
        body_a.velocity -= impulse * body_a.inverse_mass
        body_b.velocity += impulse * body_b.inverse_mass
        
        # 应用摩擦力
        CollisionResolver._apply_friction(collision, impulse_scalar)
        
        # 位置修正
        CollisionResolver._positional_correction(collision)
```

**设计考虑**：
- 基于冲量的碰撞响应
- 支持弹性/非弹性碰撞
- 包含摩擦力计算
- 位置修正防止物体重叠

### 6. 约束系统 (`constraint.py`)

**关键实现**：

```python
class DistanceConstraint(Constraint):
    def __init__(self, body_a: RigidBody, body_b: RigidBody, 
                 distance: float = None, stiffness: float = 1.0):
        self.body_a = body_a
        self.body_b = body_b
        self.stiffness = stiffness
        
        if distance is None:
            self.distance = body_a.position.distance_to(body_b.position)
        else:
            self.distance = distance
    
    def solve(self, dt: float) -> None:
        diff = self.body_b.position - self.body_a.position
        current_distance = diff.length()
        
        if current_distance == 0:
            return
        
        error = current_distance - self.distance
        correction = diff.normalized() * error * self.stiffness
        
        total_inverse_mass = self.body_a.inverse_mass + self.body_b.inverse_mass
        if total_inverse_mass == 0:
            return
        
        correction_a = correction * (self.body_a.inverse_mass / total_inverse_mass)
        correction_b = correction * (self.body_b.inverse_mass / total_inverse_mass)
        
        self.body_a.position += correction_a
        self.body_b.position -= correction_b
```

**设计考虑**：
- 抽象基类定义统一接口
- 支持刚度参数控制约束强度
- 支持迭代求解提高稳定性
- 处理静态物体的特殊情况

### 7. 积分器 (`integrator.py`)

**关键实现**：

```python
class EulerIntegrator(Integrator):
    def integrate(self, body: RigidBody, dt: float) -> None:
        if body.is_static:
            return
        
        # 半隐式欧拉：先更新速度
        body.velocity += body.acceleration * dt
        body.velocity *= 0.999  # 阻尼
        
        # 再更新位置
        body.position += body.velocity * dt
        
        # 更新旋转
        body.angular_velocity += body.torque * body.inverse_inertia * dt
        body.angular_velocity *= 0.999
        body.rotation += body.angular_velocity * dt
        
        # 清除力
        body.clear_forces()

class VerletIntegrator(Integrator):
    def __init__(self):
        self._positions: dict[int, Vector2D] = {}
    
    def integrate(self, body: RigidBody, dt: float) -> None:
        if body.is_static:
            return
        
        body_id = id(body)
        
        if body_id not in self._positions:
            self._positions[body_id] = body.position - body.velocity * dt
        
        acceleration = body.force * body.inverse_mass
        
        # Verlet 积分
        new_position = (
            2 * body.position
            - self._positions[body_id]
            + acceleration * dt * dt
        )
        
        body.velocity = (new_position - self._positions[body_id]) / (2 * dt)
        body.velocity *= 0.999
        
        self._positions[body_id] = body.position
        body.position = new_position
        
        body.clear_forces()
```

**设计考虑**：
- 半隐式欧拉提高稳定性
- Verlet 积分适合约束求解
- 添加阻尼防止振荡
- 处理静态物体的特殊情况

### 8. 物理世界 (`world.py`)

**关键实现**：

```python
class PhysicsWorld:
    def __init__(self, integrator: Integrator = None):
        self.bodies: list[RigidBody] = []
        self.colliders: dict[int, Collider] = {}
        self.constraints: list[Constraint] = []
        self.gravity = Vector2D(0, 9.81)
        self.integrator = integrator or EulerIntegrator()
        self.iterations = 10
    
    def step(self, dt: float) -> None:
        # 1. 应用重力
        self._apply_gravity()
        
        # 2. 碰撞检测
        collisions = self._detect_collisions()
        
        # 3. 碰撞响应
        self._resolve_collisions(collisions)
        
        # 4. 约束求解
        self._solve_constraints(dt)
        
        # 5. 积分更新
        self._integrate(dt)
```

**设计考虑**：
- 管理所有物体和约束
- 实现完整的物理循环
- 支持重力设置
- 提供查询接口

## 测试策略

### 单元测试

**测试覆盖**：
- 向量数学运算
- 刚体属性和方法
- 碰撞检测算法
- 碰撞响应计算
- 约束求解
- 积分方法

**测试示例**：
```python
class TestVector2D:
    def test_addition(self):
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1 + v2
        assert result.x == 4
        assert result.y == 6
    
    def test_dot_product(self):
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        assert v1.dot(v2) == 11
    
    def test_length(self):
        v = Vector2D(3, 4)
        assert v.length() == 5.0
```

### 集成测试

**测试场景**：
- 完整的物理循环
- 多物体交互
- 约束系统行为
- 长时间运行稳定性

**测试示例**：
```python
class TestPhysicsWorld:
    def test_gravity(self):
        world = PhysicsWorld()
        world.gravity = Vector2D(0, 10)
        
        body = RigidBody(Vector2D(0, 0), mass=1.0)
        world.add_body(body)
        
        world.step(1.0)
        
        assert body.position.y > 0
    
    def test_collision(self):
        world = PhysicsWorld()
        world.gravity = Vector2D(0, 0)
        
        body_a = RigidBody(Vector2D(0, 0), mass=1.0)
        body_b = RigidBody(Vector2D(2, 0), mass=1.0)
        
        collider_a = CircleCollider(body_a, 1.5)
        collider_b = CircleCollider(body_b, 1.5)
        
        world.add_body(body_a, collider_a)
        world.add_body(body_b, collider_b)
        
        body_a.velocity = Vector2D(5, 0)
        body_b.velocity = Vector2D(-5, 0)
        
        world.step(1 / 60)
        
        assert body_a.position.x < body_b.position.x
```

## 性能优化

### 1. 碰撞检测优化

**宽相检测**：
- 使用 AABB 进行快速筛选
- 空间分区减少检测次数

**窄相检测**：
- 仅对宽相筛选出的物体对进行精确检测
- 使用高效的算法（SAT、GJK）

### 2. 内存优化

**对象池**：
- 重用频繁创建的对象
- 减少内存分配和垃圾回收

**数据局部性**：
- 相关数据放在一起
- 提高缓存命中率

### 3. 计算优化

**批量处理**：
- 批量处理相似操作
- 函数调用开销

**数值优化**：
- 使用 `length_squared()` 避免开方
- 使用逆质量避免除法

## 已知问题

### 1. 数值稳定性
- 高速物体可能穿透
- 长时间运行可能能量漂移

**解决方案**：
- 添加阻尼
- 使用位置修正
- 限制最大速度

### 2. 性能瓶颈
- 大量物体时碰撞检测慢
- 约束求解迭代次数多

**解决方案**：
- 空间分区
- 减少迭代次数
- 使用更高效的算法

### 3. 功能限制
- 不支持凹多边形
- 不支持连续碰撞检测
- 不支持 3D 物理

**解决方案**：
- 分割凹多边形
- 实现 CCD
- 扩展到 3D

## 扩展建议

### 1. 功能扩展
- 添加更多碰撞形状（椭圆、胶囊）
- 添加更多约束类型（滑轮、齿轮）
- 添加关节系统
- 添加布料模拟

### 2. 性能优化
- 实现空间分区（四叉树、BVH）
- 添加多线程支持
- 使用 C 扩展加速关键路径
- 实现物体休眠机制

### 3. 工具支持
- 可视化调试工具
- 性能分析工具
- 场景编辑器
- 物理参数调优工具

## 调试技巧

### 1. 可视化调试
- 绘制碰撞法线
- 绘制接触点
- 绘制速度向量
- 绘制包围盒

### 2. 数值调试
- 打印物理状态
- 检查能量守恒
- 验证碰撞响应
- 测试边界情况

### 3. 性能调试
- 使用性能分析工具
- 记录帧时间
- 统计物体数量
- 监控内存使用

## 部署指南

### 1. 打包
```bash
# 创建 setup.py
# 打包为 wheel
python setup.py bdist_wheel
```

### 2. 发布
```bash
# 上传到 PyPI
twine upload dist/*
```

### 3. 文档
```bash
# 生成 API 文档
pdoc --html src/
```

## 贡献指南

### 1. 代码规范
- 遵循 PEP 8
- 使用类型提示
- 编写文档字符串
- 保持函数简短

### 2. 提交规范
- 使用语义化提交信息
- 每个提交解决一个问题
- 保持提交历史清晰

### 3. 测试要求
- 新功能必须有测试
- 修复 bug 必须有测试
- 保持测试覆盖率

## 总结

本物理引擎项目实现了一个完整的 2D 物理仿真系统，涵盖了物理引擎的核心功能。通过模块化设计和清晰的接口，使得代码易于理解和扩展。完整的测试覆盖和详细的文档保证了代码质量。

这个项目不仅是一个实用的物理引擎库，也是一个学习物理引擎原理的良好教材。通过阅读和修改代码，可以深入理解物理仿真的核心概念和实现技巧。
