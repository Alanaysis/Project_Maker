# 物理引擎设计文档

## 1. 设计目标

### 功能目标

1. **刚体动力学**
   - 支持静态、动态、运动学三种刚体类型
   - 实现质量、速度、加速度、力、冲量
   - 支持旋转和角速度

2. **碰撞检测**
   - AABB 碰撞检测
   - 圆形碰撞检测
   - AABB 与圆形碰撞检测

3. **约束求解**
   - 距离约束
   - 钉子约束
   - 铰链约束
   - 焊接约束

4. **物理模拟**
   - 重力
   - 摩擦力
   - 弹性碰撞
   - 阻尼

### 非功能目标

1. **可扩展性**：易于添加新的碰撞形状和约束类型
2. **可维护性**：清晰的代码结构和文档
3. **性能**：满足基本的实时性要求
4. **易用性**：简洁的 API 接口

## 2. 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    物理世界 (World)                    │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   刚体管理   │  │  碰撞检测   │  │  约束求解   │  │
│  │  (Bodies)   │  │ (Collision) │  │(Constraints)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  向量数学   │  │    AABB     │  │   刚体定义   │  │
│  │ (Vector2D)  │  │             │  │(RigidBodyDef)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 模块划分

#### 1. 数学模块 (`vector2d.h`)
- 2D 向量类
- 基本运算（加、减、乘、除）
- 点积、叉积
- 长度、归一化
- 旋转、投影、反射

#### 2. 几何模块 (`aabb.h`)
- AABB 类
- 相交测试
- 合并、扩展
- 距离计算

#### 3. 刚体模块 (`rigid_body.h`)
- 刚体类
- 刚体定义
- 物理属性（质量、速度、力等）
- 积分方法

#### 4. 碰撞模块 (`collision.h`)
- 碰撞检测函数
- 碰撞信息结构
- 支持多种形状组合

#### 5. 约束模块 (`constraint.h`)
- 约束基类
- 距离约束
- 钉子约束
- 铰链约束
- 焊接约束
- 约束求解器

#### 6. 世界模块 (`world.h`)
- 物理世界类
- 实体管理
- 模拟循环
- 配置管理

## 3. 类设计

### Vector2D

```cpp
struct Vector2D {
    double x, y;

    // 构造函数
    Vector2D();
    Vector2D(double x, double y);

    // 运算符重载
    Vector2D operator+(const Vector2D& other) const;
    Vector2D operator-(const Vector2D& other) const;
    Vector2D operator*(double scalar) const;
    Vector2D operator/(double scalar) const;

    // 复合赋值
    Vector2D& operator+=(const Vector2D& other);
    Vector2D& operator-=(const Vector2D& other);
    Vector2D& operator*=(double scalar);
    Vector2D& operator/=(double scalar);

    // 向量运算
    double dot(const Vector2D& other) const;
    double cross(const Vector2D& other) const;
    double length() const;
    double length_squared() const;
    Vector2D normalized() const;
    void normalize();

    // 变换
    Vector2D rotated(double angle) const;
    Vector2D project_onto(const Vector2D& other) const;
    Vector2D reflect(const Vector2D& normal) const;

    // 插值
    static Vector2D lerp(const Vector2D& a, const Vector2D& b, double t);
};
```

### AABB

```cpp
struct AABB {
    Vector2D min, max;

    // 构造函数
    AABB();
    AABB(const Vector2D& min, const Vector2D& max);
    AABB(double min_x, double min_y, double max_x, double max_y);

    // 属性
    Vector2D center() const;
    Vector2D size() const;
    double area() const;

    // 测试
    bool contains(const Vector2D& point) const;
    bool contains(const AABB& other) const;
    bool intersects(const AABB& other) const;

    // 操作
    AABB intersection(const AABB& other) const;
    AABB merge(const AABB& other) const;
    AABB expanded(double amount) const;
    double distance_to(const AABB& other) const;
};
```

### RigidBody

```cpp
class RigidBody {
public:
    // 构造函数
    RigidBody(const RigidBodyDef& def);

    // 属性访问
    uint32_t id() const;
    BodyType type() const;
    const Vector2D& position() const;
    double rotation() const;
    const Vector2D& velocity() const;
    double angular_velocity() const;
    double mass() const;
    double inv_mass() const;

    // 设置器
    void set_position(const Vector2D& pos);
    void set_velocity(const Vector2D& vel);

    // 物理操作
    void apply_force(const Vector2D& force);
    void apply_force_at_point(const Vector2D& force, const Vector2D& point);
    void apply_impulse(const Vector2D& impulse);
    void apply_impulse_at_point(const Vector2D& impulse, const Vector2D& point);
    void apply_torque(double torque);

    // 积分
    void integrate(double dt);

    // 碰撞检测
    AABB compute_aabb() const;
    Vector2D velocity_at_point(const Vector2D& point) const;

private:
    // 物理属性
    uint32_t id_;
    BodyType type_;
    Vector2D position_;
    double rotation_;
    Vector2D velocity_;
    double angular_velocity_;
    double mass_;
    double inv_mass_;
    double inertia_;
    double inv_inertia_;
    double restitution_;
    double friction_;
    double linear_damping_;
    double angular_damping_;
    bool is_sensor_;
    void* user_data_;

    // 力和扭矩
    Vector2D force_;
    double torque_;

    // ID 生成
    static uint32_t next_id_;
};
```

### Constraint

```cpp
// 约束基类
class Constraint {
public:
    virtual ~Constraint() = default;
    virtual void initialize() = 0;
    virtual void solve(double dt) = 0;
    virtual ConstraintType type() const = 0;

    bool enabled = true;
    double stiffness = 1.0;
    double damping = 0.0;
};

// 距离约束
class DistanceConstraint : public Constraint {
public:
    DistanceConstraint(
        std::shared_ptr<RigidBody> body_a,
        std::shared_ptr<RigidBody> body_b,
        const Vector2D& anchor_a,
        const Vector2D& anchor_b,
        double distance = -1.0);

    void initialize() override;
    void solve(double dt) override;
    ConstraintType type() const override { return ConstraintType::Distance; }

private:
    std::shared_ptr<RigidBody> body_a_;
    std::shared_ptr<RigidBody> body_b_;
    Vector2D anchor_a_;
    Vector2D anchor_b_;
    double target_distance_;
};
```

### World

```cpp
class World {
public:
    World(const WorldConfig& config = WorldConfig{});

    // 实体管理
    std::shared_ptr<RigidBody> create_body(const RigidBodyDef& def);
    void destroy_body(std::shared_ptr<RigidBody> body);

    // 约束管理
    std::shared_ptr<DistanceConstraint> create_distance_constraint(...);
    std::shared_ptr<PinConstraint> create_pin_constraint(...);
    std::shared_ptr<HingeConstraint> create_hinge_constraint(...);
    std::shared_ptr<WeldConstraint> create_weld_constraint(...);
    void destroy_constraint(std::shared_ptr<Constraint> constraint);

    // 碰撞回调
    void set_collision_callback(CollisionCallback callback);

    // 模拟
    void step(double dt = -1.0);

    // 查询
    const std::vector<std::shared_ptr<RigidBody>>& bodies() const;
    size_t body_count() const;

    // 配置
    const WorldConfig& config() const;
    void set_config(const WorldConfig& config);

    // 清理
    void clear();

private:
    // 模拟步骤
    void apply_gravity(double dt);
    void integrate(double dt);
    std::vector<CollisionManifold> detect_collisions();
    void resolve_collisions(const std::vector<CollisionManifold>& collisions, double dt);
    void solve_constraints(double dt);
    void correct_positions(const std::vector<CollisionManifold>& collisions);
    void update_sleep();

    // 成员变量
    WorldConfig config_;
    std::vector<std::shared_ptr<RigidBody>> bodies_;
    ConstraintSolver solver_;
    CollisionCallback collision_callback_;
};
```

## 4. 数据流设计

### 模拟循环

```
输入：时间步长 dt
输出：更新后的物理状态

1. 施加重力
   for each body in world:
       if body.is_dynamic():
           body.apply_force(gravity * body.mass)

2. 积分
   for each body in world:
       body.integrate(dt)

3. 碰撞检测
   collisions = []
   for each pair (body_a, body_b):
       if aabb_intersects(body_a.aabb, body_b.aabb):
           collision = narrow_phase(body_a, body_b)
           if collision:
               collisions.append(collision)

4. 碰撞响应
   for each collision in collisions:
       apply_impulse(collision)

5. 约束求解
   for i in range(iterations):
       for each constraint in world.constraints:
           constraint.solve(dt)

6. 位置修正
   for each collision in collisions:
       correct_position(collision)
```

### 数据流向

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   力计算    │ ──▶ │   积分      │ ──▶ │  碰撞检测   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  重力/外力  │     │  速度/位置  │     │  碰撞信息   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
       ┌───────────────────────────────────────┘
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  碰撞响应   │ ──▶ │  约束求解   │ ──▶ │  位置修正   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  冲量应用   │     │  约束满足   │     │  穿透解决   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 5. 接口设计

### 创建物体

```cpp
// 创建物理世界
physics_engine::WorldConfig config;
config.gravity = {0.0, -9.81};
physics_engine::World world(config);

// 创建动态物体
physics_engine::RigidBodyDef def;
def.position = {0.0, 10.0};
def.mass = 1.0;
def.restitution = 0.5;
auto body = world.create_body(def);

// 创建静态物体
physics_engine::RigidBodyDef static_def;
static_def.type = physics_engine::BodyType::Static;
static_def.position = {0.0, -1.0};
auto ground = world.create_body(static_def);
```

### 施加力

```cpp
// 施加力
body->apply_force({10.0, 0.0});

// 施加冲量
body->apply_impulse({5.0, 0.0});

// 施加扭矩
body->apply_torque(1.0);

// 在指定点施加力
body->apply_force_at_point({0.0, 10.0}, {1.0, 0.0});
```

### 创建约束

```cpp
// 距离约束
auto constraint = world.create_distance_constraint(
    body_a, body_b,
    physics_engine::Vector2D(0.0, 0.0),  // 锚点 A
    physics_engine::Vector2D(0.0, 0.0),  // 锚点 B
    5.0);  // 目标距离

// 钉子约束
auto pin = world.create_pin_constraint(
    body,
    physics_engine::Vector2D(5.0, 5.0),  // 世界坐标
    physics_engine::Vector2D(0.0, 0.0)); // 局部坐标
```

### 碰撞回调

```cpp
world.set_collision_callback([](const physics_engine::CollisionManifold& manifold) {
    std::cout << "碰撞发生！" << std::endl;
    std::cout << "法线: " << manifold.normal << std::endl;
    std::cout << "穿透: " << manifold.contacts[0].penetration << std::endl;
});
```

### 模拟循环

```cpp
double dt = 1.0 / 60.0;
while (running) {
    world.step(dt);
    // 渲染...
}
```

## 6. 配置设计

### WorldConfig

```cpp
struct WorldConfig {
    Vector2D gravity = {0.0, -9.81};  // 重力加速度
    int velocity_iterations = 8;       // 速度求解迭代次数
    int position_iterations = 3;       // 位置求解迭代次数
    double time_step = 1.0 / 60.0;    // 固定时间步长
    bool allow_sleep = true;           // 是否允许休眠
    double sleep_linear_threshold = 0.01;  // 线性速度休眠阈值
    double sleep_angular_threshold = 0.01; // 角速度休眠阈值
};
```

### RigidBodyDef

```cpp
struct RigidBodyDef {
    BodyType type = BodyType::Dynamic;
    Vector2D position = {0.0, 0.0};
    double rotation = 0.0;
    Vector2D velocity = {0.0, 0.0};
    double angular_velocity = 0.0;
    double mass = 1.0;
    double restitution = 0.5;
    double friction = 0.3;
    double linear_damping = 0.01;
    double angular_damping = 0.01;
    bool is_sensor = false;
    void* user_data = nullptr;
};
```

## 7. 错误处理

### 异常情况

1. **无效质量**：质量为零或负数
   - 解决：设置 inv_mass 为 0，使其成为静态物体

2. **零向量归一化**：对零向量进行归一化
   - 解决：返回零向量

3. **除零错误**：除以零
   - 解决：检查除数，避免除零

4. **约束冲突**：多个约束相互冲突
   - 解决：使用迭代求解，允许一定误差

### 错误处理策略

1. **防御性编程**：检查输入参数
2. **优雅降级**：出错时使用默认值
3. **日志记录**：记录错误信息
4. **断言检查**：在调试模式下检查

## 8. 性能设计

### 时间复杂度

1. **碰撞检测**：O(n²) - 简单实现
2. **约束求解**：O(c * i) - c 为约束数，i 为迭代次数
3. **积分**：O(n) - n 为物体数

### 空间复杂度

1. **物体存储**：O(n)
2. **约束存储**：O(c)
3. **碰撞信息**：O(k) - k 为碰撞对数

### 优化策略

1. **宽相检测**：减少碰撞检测次数
2. **空间分区**：使用四叉树或网格
3. **休眠机制**：处理静止物体
4. **内存池**：减少内存分配

## 9. 测试设计

### 单元测试

1. **向量数学测试**
   - 基本运算
   - 点积、叉积
   - 长度、归一化

2. **AABB 测试**
   - 相交测试
   - 合并、扩展

3. **刚体测试**
   - 创建、属性访问
   - 力、冲量应用
   - 积分

4. **碰撞检测测试**
   - AABB 碰撞
   - 圆形碰撞

5. **约束测试**
   - 距离约束
   - 钉子约束

### 集成测试

1. **自由落体**
2. **抛物运动**
3. **碰撞响应**
4. **约束系统**
5. **能量守恒**

## 10. 设计总结

### 设计原则

1. **单一职责**：每个模块只负责一个功能
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置**：依赖抽象而非具体实现
4. **接口隔离**：提供最小化的接口

### 设计权衡

1. **简单性 vs 功能性**：选择简单实现，易于理解
2. **性能 vs 可读性**：优先可读性，必要时优化
3. **灵活性 vs 复杂度**：提供基本功能，易于扩展

### 未来改进

1. **更多形状支持**：多边形、凸包
2. **更高效算法**：GJK、BVH
3. **并行计算**：多线程优化
4. **3D 支持**：扩展到三维空间
