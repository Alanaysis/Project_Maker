# 物理引擎实现文档

## 1. 实现概述

本文档详细描述物理引擎的实现细节，包括核心算法、数据结构和代码实现。

## 2. 向量数学实现 (`vector2d.h`)

### 基本数据结构

```cpp
struct Vector2D {
    double x = 0.0;
    double y = 0.0;
};
```

### 运算符重载

#### 加法和减法

```cpp
Vector2D operator+(const Vector2D& other) const {
    return {x + other.x, y + other.y};
}

Vector2D operator-(const Vector2D& other) const {
    return {x - other.x, y - other.y};
}
```

#### 标量乘法和除法

```cpp
Vector2D operator*(double scalar) const {
    return {x * scalar, y * scalar};
}

Vector2D operator/(double scalar) const {
    return {x / scalar, y / scalar};
}
```

#### 复合赋值运算符

```cpp
Vector2D& operator+=(const Vector2D& other) {
    x += other.x;
    y += other.y;
    return *this;
}
```

### 向量运算

#### 点积

```cpp
double dot(const Vector2D& other) const {
    return x * other.x + y * other.y;
}
```

#### 叉积

2D 叉积返回标量：

```cpp
double cross(const Vector2D& other) const {
    return x * other.y - y * other.x;
}
```

#### 长度和归一化

```cpp
double length_squared() const {
    return x * x + y * y;
}

double length() const {
    return std::sqrt(length_squared());
}

Vector2D normalized() const {
    double len = length();
    if (len < 1e-10) {
        return {0.0, 0.0};
    }
    return {x / len, y / len};
}
```

#### 旋转

```cpp
Vector2D rotated(double angle) const {
    double cos_a = std::cos(angle);
    double sin_a = std::sin(angle);
    return {
        x * cos_a - y * sin_a,
        x * sin_a + y * cos_a
    };
}
```

#### 投影

```cpp
Vector2D project_onto(const Vector2D& other) const {
    double other_len_sq = other.length_squared();
    if (other_len_sq < 1e-10) {
        return {0.0, 0.0};
    }
    return other * (dot(other) / other_len_sq);
}
```

#### 反射

```cpp
Vector2D reflect(const Vector2D& normal) const {
    return *this - normal * (2.0 * dot(normal));
}
```

#### 线性插值

```cpp
static Vector2D lerp(const Vector2D& a, const Vector2D& b, double t) {
    return a + (b - a) * t;
}
```

## 3. AABB 实现 (`aabb.h`)

### 基本数据结构

```cpp
struct AABB {
    Vector2D min;  // 左下角
    Vector2D max;  // 右上角
};
```

### 相交测试

```cpp
bool intersects(const AABB& other) const {
    return min.x <= other.max.x && max.x >= other.min.x &&
           min.y <= other.max.y && max.y >= other.min.y;
}
```

### 合并

```cpp
AABB merge(const AABB& other) const {
    return {
        std::min(min.x, other.min.x),
        std::min(min.y, other.min.y),
        std::max(max.x, other.max.x),
        std::max(max.y, other.max.y)
    };
}
```

### 扩展

```cpp
AABB expanded(double amount) const {
    return {
        min.x - amount,
        min.y - amount,
        max.x + amount,
        max.y + amount
    };
}
```

### 距离计算

```cpp
double distance_to(const AABB& other) const {
    double dx = std::max({0.0, min.x - other.max.x, other.min.x - max.x});
    double dy = std::max({0.0, min.y - other.max.y, other.min.y - max.y});
    return std::sqrt(dx * dx + dy * dy);
}
```

## 4. 刚体实现 (`rigid_body.h`, `rigid_body.cpp`)

### 刚体定义

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

### 构造函数

```cpp
RigidBody::RigidBody(const RigidBodyDef& def)
    : type_(def.type)
    , position_(def.position)
    , rotation_(def.rotation)
    , velocity_(def.velocity)
    , angular_velocity_(def.angular_velocity)
    , mass_(def.mass)
    , restitution_(def.restitution)
    , friction_(def.friction)
    , linear_damping_(def.linear_damping)
    , angular_damping_(def.angular_damping)
    , is_sensor_(def.is_sensor)
    , user_data_(def.user_data)
    , id_(next_id_++)
{
    // 计算逆质量
    if (type_ == BodyType::Static || mass_ <= 0.0) {
        inv_mass_ = 0.0;
    } else {
        inv_mass_ = 1.0 / mass_;
    }

    // 计算转动惯量
    if (type_ == BodyType::Static) {
        inv_inertia_ = 0.0;
    } else {
        inertia_ = 0.5 * mass_ * 1.0;  // 简化：圆形近似
        inv_inertia_ = 1.0 / inertia_;
    }
}
```

### 施加力

```cpp
void RigidBody::apply_force(const Vector2D& force) {
    if (type_ != BodyType::Dynamic) return;
    force_ += force;
}

void RigidBody::apply_force_at_point(const Vector2D& force, const Vector2D& point) {
    if (type_ != BodyType::Dynamic) return;
    force_ += force;
    Vector2D r = point - position_;
    torque_ += r.cross(force);
}
```

### 施加冲量

```cpp
void RigidBody::apply_impulse(const Vector2D& impulse) {
    if (type_ != BodyType::Dynamic) return;
    velocity_ += impulse * inv_mass_;
}

void RigidBody::apply_impulse_at_point(const Vector2D& impulse, const Vector2D& point) {
    if (type_ != BodyType::Dynamic) return;
    velocity_ += impulse * inv_mass_;
    Vector2D r = point - position_;
    angular_velocity_ += r.cross(impulse) * inv_inertia_;
}
```

### 积分

```cpp
void RigidBody::integrate(double dt) {
    if (type_ == BodyType::Static) return;

    // 更新速度
    velocity_ += force_ * inv_mass_ * dt;
    angular_velocity_ += torque_ * inv_inertia_ * dt;

    // 应用阻尼
    velocity_ *= (1.0 - linear_damping_ * dt);
    angular_velocity_ *= (1.0 - angular_damping_ * dt);

    // 更新位置
    position_ += velocity_ * dt;
    rotation_ += angular_velocity_ * dt;

    // 清除力
    clear_forces();
}
```

### AABB 计算

```cpp
AABB RigidBody::compute_aabb() const {
    // 简化：假设物体大小为 1x1
    double half_size = 0.5;
    return {
        position_.x - half_size,
        position_.y - half_size,
        position_.x + half_size,
        position_.y + half_size
    };
}
```

### 速度计算

```cpp
Vector2D RigidBody::velocity_at_point(const Vector2D& point) const {
    Vector2D r = point - position_;
    return velocity_ + Vector2D(-r.y, r.x) * angular_velocity_;
}
```

### 静态成员初始化

```cpp
// rigid_body.cpp
uint32_t RigidBody::next_id_ = 0;
```

## 5. 碰撞检测实现 (`collision.h`)

### AABB 碰撞检测

```cpp
CollisionResult aabb_vs_aabb(const AABB& a, const AABB& b) {
    CollisionResult result;

    // 计算重叠
    double overlap_x = std::min(a.max.x, b.max.x) - std::max(a.min.x, b.min.x);
    double overlap_y = std::min(a.max.y, b.max.y) - std::max(a.min.y, b.min.y);

    if (overlap_x <= 0.0 || overlap_y <= 0.0) {
        return result;  // 没有碰撞
    }

    result.collided = true;

    // 选择最小穿透方向
    if (overlap_x < overlap_y) {
        double sign = (a.center().x < b.center().x) ? 1.0 : -1.0;
        result.normal = {sign, 0.0};
        result.penetration = overlap_x;
    } else {
        double sign = (a.center().y < b.center().y) ? 1.0 : -1.0;
        result.normal = {0.0, sign};
        result.penetration = overlap_y;
    }

    // 计算接触点
    result.contact_point = (a.center() + b.center()) * 0.5;

    return result;
}
```

### 圆形碰撞检测

```cpp
CollisionResult circle_vs_circle(
    const Vector2D& center_a, double radius_a,
    const Vector2D& center_b, double radius_b)
{
    CollisionResult result;

    Vector2D diff = center_b - center_a;
    double dist_sq = diff.length_squared();
    double radius_sum = radius_a + radius_b;

    if (dist_sq > radius_sum * radius_sum) {
        return result;  // 没有碰撞
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
        result.normal = {1.0, 0.0};
        dist = 0.0;
    }

    result.penetration = radius_sum - dist;
    result.contact_point = center_a + result.normal * radius_a;

    return result;
}
```

### AABB 与圆形碰撞检测

```cpp
CollisionResult aabb_vs_circle(
    const AABB& aabb,
    const Vector2D& circle_center,
    double circle_radius)
{
    CollisionResult result;

    // 找到 AABB 上最近的点
    double closest_x = std::max(aabb.min.x, std::min(circle_center.x, aabb.max.x));
    double closest_y = std::max(aabb.min.y, std::min(circle_center.y, aabb.max.y));
    Vector2D closest = {closest_x, closest_y};

    Vector2D diff = circle_center - closest;
    double dist_sq = diff.length_squared();
    double radius_sq = circle_radius * circle_radius;

    if (dist_sq > radius_sq) {
        return result;  // 没有碰撞
    }

    double dist = std::sqrt(dist_sq);
    result.collided = true;

    if (dist > 1e-10) {
        result.normal = diff / dist;
    } else {
        // 圆心在 AABB 内部
        double dx_left = circle_center.x - aabb.min.x;
        double dx_right = aabb.max.x - circle_center.x;
        double dy_bottom = circle_center.y - aabb.min.y;
        double dy_top = aabb.max.y - circle_center.y;

        double min_dist = std::min({dx_left, dx_right, dy_bottom, dy_top});

        if (min_dist == dx_left) result.normal = {-1.0, 0.0};
        else if (min_dist == dx_right) result.normal = {1.0, 0.0};
        else if (min_dist == dy_bottom) result.normal = {0.0, -1.0};
        else result.normal = {0.0, 1.0};

        dist = 0.0;
    }

    result.penetration = circle_radius - dist;
    result.contact_point = closest;

    return result;
}
```

## 6. 约束实现 (`constraint.h`)

### 距离约束

```cpp
class DistanceConstraint : public Constraint {
public:
    void initialize() override {
        if (target_distance_ < 0.0) {
            Vector2D world_a = body_a_->position() + anchor_a_;
            Vector2D world_b = body_b_->position() + anchor_b_;
            target_distance_ = world_a.distance_to(world_b);
        }
    }

    void solve(double dt) override {
        if (!enabled) return;

        Vector2D world_a = body_a_->position() + anchor_a_;
        Vector2D world_b = body_b_->position() + anchor_b_;

        Vector2D diff = world_b - world_a;
        double current_distance = diff.length();

        if (current_distance < 1e-10) return;

        // 计算误差
        double error = current_distance - target_distance_;

        // 计算约束方向
        Vector2D normal = diff / current_distance;

        // 计算有效质量
        double inv_mass_sum = body_a_->inv_mass() + body_b_->inv_mass();
        if (inv_mass_sum < 1e-10) return;

        // 计算冲量
        double lambda = -error / inv_mass_sum * stiffness;

        // 应用阻尼
        Vector2D relative_velocity = body_b_->velocity() - body_a_->velocity();
        double velocity_along_normal = relative_velocity.dot(normal);
        lambda -= velocity_along_normal * damping / inv_mass_sum;

        // 应用冲量
        Vector2D impulse = normal * lambda;
        body_a_->apply_impulse(-impulse);
        body_b_->apply_impulse(impulse);
    }
};
```

### 钉子约束

```cpp
class PinConstraint : public Constraint {
public:
    void solve(double dt) override {
        if (!enabled) return;
        if (body_->is_static()) return;

        Vector2D current_world = body_->position() + local_anchor_;
        Vector2D error = world_point_ - current_world;

        double inv_mass = body_->inv_mass();
        if (inv_mass < 1e-10) return;

        // 计算冲量
        Vector2D impulse = error * (stiffness / inv_mass);

        // 应用阻尼
        Vector2D velocity = body_->velocity();
        impulse -= velocity * damping;

        // 应用冲量
        body_->apply_impulse(impulse);
    }
};
```

### 约束求解器

```cpp
class ConstraintSolver {
public:
    void add_constraint(std::shared_ptr<Constraint> constraint) {
        constraints_.push_back(constraint);
    }

    void initialize() {
        for (auto& constraint : constraints_) {
            if (constraint->enabled) {
                constraint->initialize();
            }
        }
    }

    void solve(double dt, int iterations = 10) {
        for (int i = 0; i < iterations; ++i) {
            for (auto& constraint : constraints_) {
                if (constraint->enabled) {
                    constraint->solve(dt);
                }
            }
        }
    }
};
```

## 7. 物理世界实现 (`world.h`)

### 创建刚体

```cpp
std::shared_ptr<RigidBody> World::create_body(const RigidBodyDef& def) {
    auto body = std::make_shared<RigidBody>(def);
    bodies_.push_back(body);
    return body;
}
```

### 模拟步进

```cpp
void World::step(double dt) {
    if (dt < 0.0) {
        dt = config_.time_step;
    }

    // 1. 施加重力
    apply_gravity(dt);

    // 2. 积分
    integrate(dt);

    // 3. 碰撞检测
    auto collisions = detect_collisions();

    // 4. 碰撞响应
    resolve_collisions(collisions, dt);

    // 5. 约束求解
    solve_constraints(dt);

    // 6. 位置修正
    correct_positions(collisions);

    // 7. 睡眠处理
    if (config_.allow_sleep) {
        update_sleep();
    }
}
```

### 施加重力

```cpp
void World::apply_gravity(double dt) {
    for (auto& body : bodies_) {
        if (body->is_dynamic()) {
            body->apply_force(config_.gravity * body->mass());
        }
    }
}
```

### 碰撞检测

```cpp
std::vector<CollisionManifold> World::detect_collisions() {
    std::vector<CollisionManifold> collisions;

    // 简单的 O(n^2) 碰撞检测
    for (size_t i = 0; i < bodies_.size(); ++i) {
        for (size_t j = i + 1; j < bodies_.size(); ++j) {
            auto& body_a = bodies_[i];
            auto& body_b = bodies_[j];

            // 跳过两个静态物体
            if (body_a->is_static() && body_b->is_static()) {
                continue;
            }

            // AABB 宽相检测
            AABB aabb_a = body_a->compute_aabb();
            AABB aabb_b = body_b->compute_aabb();

            if (!aabb_a.intersects(aabb_b)) {
                continue;
            }

            // 窄相检测
            CollisionResult result = detect_collision(*body_a, *body_b);

            if (result.collided) {
                CollisionManifold manifold;
                manifold.body_a = body_a.get();
                manifold.body_b = body_b.get();
                manifold.normal = result.normal;

                ContactPoint contact;
                contact.position = result.contact_point;
                contact.normal = result.normal;
                contact.penetration = result.penetration;
                contact.r_a = contact.position - body_a->position();
                contact.r_b = contact.position - body_b->position();

                manifold.contacts.push_back(contact);
                collisions.push_back(manifold);

                // 调用回调
                if (collision_callback_) {
                    collision_callback_(manifold);
                }
            }
        }
    }

    return collisions;
}
```

### 碰撞响应

```cpp
void World::resolve_collisions(const std::vector<CollisionManifold>& collisions, double dt) {
    for (const auto& manifold : collisions) {
        for (const auto& contact : manifold.contacts) {
            RigidBody* body_a = manifold.body_a;
            RigidBody* body_b = manifold.body_b;

            // 跳过传感器
            if (body_a->is_sensor() || body_b->is_sensor()) {
                continue;
            }

            // 计算相对速度
            Vector2D vel_a = body_a->velocity_at_point(contact.position);
            Vector2D vel_b = body_b->velocity_at_point(contact.position);
            Vector2D relative_velocity = vel_b - vel_a;

            // 计算相对速度在法线方向的分量
            double velocity_along_normal = relative_velocity.dot(contact.normal);

            // 如果物体正在分离，不需要处理
            if (velocity_along_normal > 0.0) {
                continue;
            }

            // 计算恢复系数
            double restitution = std::min(body_a->restitution(), body_b->restitution());

            // 计算冲量标量
            double r_a_cross_n = contact.r_a.cross(contact.normal);
            double r_b_cross_n = contact.r_b.cross(contact.normal);

            double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass() +
                r_a_cross_n * r_a_cross_n * body_a->inv_inertia() +
                r_b_cross_n * r_b_cross_n * body_b->inv_inertia();

            double j = -(1.0 + restitution) * velocity_along_normal / inv_mass_sum;

            // 应用冲量
            Vector2D impulse = contact.normal * j;
            body_a->apply_impulse_at_point(-impulse, contact.position);
            body_b->apply_impulse_at_point(impulse, contact.position);

            // 摩擦力
            Vector2D tangent = relative_velocity - contact.normal * velocity_along_normal;
            double tangent_length = tangent.length();
            if (tangent_length > 1e-10) {
                tangent = tangent / tangent_length;

                double friction = std::sqrt(
                    body_a->friction() * body_b->friction());

                double jt = -relative_velocity.dot(tangent) / inv_mass_sum;

                // 库仑摩擦
                Vector2D friction_impulse;
                if (std::abs(jt) < j * friction) {
                    friction_impulse = tangent * jt;
                } else {
                    friction_impulse = tangent * (-j * friction);
                }

                body_a->apply_impulse_at_point(-friction_impulse, contact.position);
                body_b->apply_impulse_at_point(friction_impulse, contact.position);
            }
        }
    }
}
```

### 位置修正

```cpp
void World::correct_positions(const std::vector<CollisionManifold>& collisions) {
    const double percent = 0.8;
    const double slop = 0.01;

    for (const auto& manifold : collisions) {
        for (const auto& contact : manifold.contacts) {
            RigidBody* body_a = manifold.body_a;
            RigidBody* body_b = manifold.body_b;

            if (body_a->is_sensor() || body_b->is_sensor()) {
                continue;
            }

            double inv_mass_sum = body_a->inv_mass() + body_b->inv_mass();
            if (inv_mass_sum < 1e-10) continue;

            Vector2D correction = contact.normal *
                (std::max(contact.penetration - slop, 0.0) / inv_mass_sum * percent);

            body_a->set_position(body_a->position() - correction * body_a->inv_mass());
            body_b->set_position(body_b->position() + correction * body_b->inv_mass());
        }
    }
}
```

## 8. 构建系统 (`CMakeLists.txt`)

### 项目配置

```cmake
cmake_minimum_required(VERSION 3.14)
project(physics_engine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
```

### 库目标

```cmake
set(SOURCES
    src/rigid_body.cpp
)

add_library(physics_engine ${SOURCES})

target_include_directories(physics_engine
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)
```

### 编译选项

```cmake
target_compile_options(physics_engine PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)
```

### 测试配置

```cmake
if(PHYSICS_ENGINE_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

## 9. 实现总结

### 实现要点

1. **模块化设计**：每个组件独立，易于理解和维护
2. **清晰的接口**：简洁的 API，易于使用
3. **数值稳定性**：使用半隐式欧拉法，添加阻尼
4. **可扩展性**：易于添加新的形状和约束类型

### 实现挑战

1. **数值精度**：浮点数运算的精度问题
2. **稳定性**：约束求解的收敛性
3. **性能**：碰撞检测的效率
4. **边界情况**：处理各种特殊情况

### 代码质量

1. **可读性**：清晰的命名和注释
2. **可维护性**：模块化设计，职责分离
3. **可测试性**：单元测试覆盖
4. **文档**：详细的实现文档

## 10. 未来改进

### 短期改进

1. **更多形状**：支持多边形、凸包
2. **更高效的碰撞检测**：空间分区
3. **更多约束类型**：滑轮、齿轮

### 长期改进

1. **3D 支持**：扩展到三维空间
2. **并行计算**：多线程优化
3. **GPU 加速**：利用 GPU 进行计算
4. **更高级的算法**：GJK、BVH、CCD
