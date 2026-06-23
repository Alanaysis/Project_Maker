# 物理引擎研究

## 1. 物理引擎概述

### 什么是物理引擎？

物理引擎是一种模拟物理现象的软件组件，主要用于：
- 游戏开发中的物理模拟
- 工程仿真
- 动画制作
- 科学计算

### 物理引擎的核心功能

1. **刚体动力学**：模拟物体的运动
2. **碰撞检测**：检测物体之间的接触
3. **碰撞响应**：处理碰撞后的物理反应
4. **约束求解**：限制物体的运动
5. **场景管理**：管理物理世界中的所有实体

## 2. 刚体动力学

### 基本概念

#### 质量 (Mass)
- 表示物体的惯性
- 影响加速度：a = F / m
- 单位：千克 (kg)

#### 位置 (Position)
- 物体在空间中的坐标
- 使用 2D 向量表示：(x, y)

#### 速度 (Velocity)
- 位置的变化率
- v = ds / dt
- 单位：米/秒 (m/s)

#### 加速度 (Acceleration)
- 速度的变化率
- a = dv / dt
- 单位：米/秒² (m/s²)

#### 力 (Force)
- 改变物体运动状态的原因
- F = ma
- 单位：牛顿 (N)

#### 冲量 (Impulse)
- 瞬间的力作用
- J = F * dt
- 直接改变速度：v += J / m

### 牛顿运动定律

1. **第一定律（惯性定律）**
   - 物体在没有外力作用下保持静止或匀速直线运动
   - 惯性：物体抵抗运动状态改变的性质

2. **第二定律**
   - F = ma
   - 力等于质量乘以加速度
   - 可以写成：a = F / m

3. **第三定律**
   - 作用力与反作用力大小相等、方向相反
   - 碰撞时双方受到的冲量相同

### 数值积分

#### 欧拉方法

最简单的数值积分方法：

```cpp
// 显式欧拉法
velocity += acceleration * dt;
position += velocity * dt;

// 半隐式欧拉法（更稳定）
velocity += acceleration * dt;
position += velocity * dt;  // 使用更新后的速度
```

#### Verlet 积分

直接基于位置计算：

```cpp
Vector2D new_position = 2 * position - old_position + acceleration * dt * dt;
old_position = position;
position = new_position;
```

#### RK4（四阶龙格-库塔法）

更高精度的积分方法：

```cpp
k1 = f(t, y);
k2 = f(t + dt/2, y + dt/2 * k1);
k3 = f(t + dt/2, y + dt/2 * k2);
k4 = f(t + dt, y + dt * k3);

y += dt/6 * (k1 + 2*k2 + 2*k3 + k4);
```

## 3. 碰撞检测

### 碰撞检测流程

```
宽相检测 → 窄相检测 → 碰撞信息计算
```

### 宽相检测 (Broad Phase)

快速排除不可能碰撞的物体对：

#### AABB 碰撞检测

轴对齐包围盒 (Axis-Aligned Bounding Box)：

```cpp
struct AABB {
    Vector2D min;  // 左下角
    Vector2D max;  // 右上角
};

bool intersects(const AABB& a, const AABB& b) {
    return a.min.x <= b.max.x && a.max.x >= b.min.x &&
           a.min.y <= b.max.y && a.max.y >= b.min.y;
}
```

#### 空间分区

- **网格**：将空间划分为均匀的网格
- **四叉树**：递归划分空间
- **BVH**：层次包围盒

### 窄相检测 (Narrow Phase)

精确检测碰撞：

#### 圆形碰撞

```cpp
bool circle_collision(Vector2D center_a, double radius_a,
                      Vector2D center_b, double radius_b) {
    double distance = (center_a - center_b).length();
    return distance < radius_a + radius_b;
}
```

#### 多边形碰撞

- **分离轴定理 (SAT)**：检测是否存在分离轴
- **GJK 算法**：基于闵可夫斯基差
- **EPA 算法**：计算穿透深度

### 碰撞信息

碰撞检测返回的信息：

```cpp
struct CollisionInfo {
    Vector2D normal;        // 碰撞法线
    double penetration;     // 穿透深度
    Vector2D contact_point; // 接触点
};
```

## 4. 碰撞响应

### 冲量方法

基于冲量的碰撞响应：

```cpp
// 计算相对速度
Vector2D relative_velocity = body_b.velocity - body_a.velocity;

// 计算法线方向的相对速度
double velocity_along_normal = relative_velocity.dot(normal);

// 如果物体正在分离，不处理
if (velocity_along_normal > 0) return;

// 计算恢复系数
double restitution = min(body_a.restitution, body_b.restitution);

// 计算冲量标量
double j = -(1 + restitution) * velocity_along_normal / inv_mass_sum;

// 应用冲量
Vector2D impulse = normal * j;
body_a.velocity -= impulse * body_a.inv_mass;
body_b.velocity += impulse * body_b.inv_mass;
```

### 摩擦力

库仑摩擦模型：

```cpp
// 计算切线方向
Vector2D tangent = relative_velocity - normal * velocity_along_normal;
tangent.normalize();

// 计算摩擦冲量
double jt = -relative_velocity.dot(tangent) / inv_mass_sum;

// 库仑摩擦定律
double friction = sqrt(body_a.friction * body_b.friction);
Vector2D friction_impulse;
if (abs(jt) < j * friction) {
    friction_impulse = tangent * jt;
} else {
    friction_impulse = tangent * (-j * friction);
}
```

### 位置修正

解决穿透问题：

```cpp
// 计算修正量
Vector2D correction = normal * max(penetration - slop, 0.0) / inv_mass_sum * percent;

// 应用修正
body_a.position -= correction * body_a.inv_mass;
body_b.position += correction * body_b.inv_mass;
```

## 5. 约束求解

### 约束类型

#### 距离约束

保持两点之间的距离：

```cpp
// 计算当前距离
Vector2D diff = point_b - point_a;
double current_distance = diff.length();

// 计算误差
double error = current_distance - target_distance;

// 计算冲量
Vector2D normal = diff.normalized();
double lambda = -error / inv_mass_sum;

// 应用冲量
body_a.position -= normal * lambda * body_a.inv_mass;
body_b.position += normal * lambda * body_b.inv_mass;
```

#### 钉子约束

固定物体在世界坐标系中的位置：

```cpp
// 计算误差
Vector2D error = target_position - body.position;

// 计算冲量
Vector2D impulse = error / body.inv_mass;

// 应用冲量
body.position += impulse * body.inv_mass;
```

### 迭代求解

使用 Gauss-Seidel 迭代：

```cpp
for (int i = 0; i < iterations; ++i) {
    for (auto& constraint : constraints) {
        constraint->solve(dt);
    }
}
```

## 6. 物理世界

### 模拟循环

```
1. 施加重力
2. 积分（更新速度和位置）
3. 碰撞检测
4. 碰撞响应
5. 约束求解
6. 位置修正
```

### 时间步长

- **固定时间步长**：每次模拟步的时间相同
- **可变时间步长**：根据帧率调整
- **插值**：在固定步长和可变帧率之间插值

## 7. 性能优化

### 宽相检测优化

- 空间分区减少检测次数
- 休眠机制处理静止物体
- 增量更新 AABB

### 约束求解优化

- 减少迭代次数
- 使用更高效的求解器
- 并行求解

### 内存优化

- 对象池减少分配
- 紧凑的数据结构
- 缓存友好的访问模式

## 8. 参考资源

### 书籍

1. **《Game Physics Engine Development》**
   - 作者：Ian Millington
   - 内容：完整的物理引擎开发指南

2. **《Real-Time Collision Detection》**
   - 作者：Ericson
   - 内容：碰撞检测算法详解

3. **《Physics for Game Developers》**
   - 作者：Bourg
   - 内容：游戏物理基础

### 开源引擎

1. **Box2D**
   - 网站：https://box2d.org/
   - 特点：2D 物理引擎，广泛使用

2. **Bullet**
   - 网站：https://pybullet.org/
   - 特点：3D 物理引擎，功能强大

3. **Chipmunk**
   - 网站：https://chipmunk-physics.net/
   - 特点：轻量级 2D 物理引擎

### 在线资源

- [Game Physics - Glenn Fiedler](https://gafferongames.com/)
- [Physics for Game Programmers](http://www.randygaul.net/)
- [Erin Catto's Presentations](https://box2d.org/publications/)

## 9. 研究总结

通过研究，我了解了物理引擎的核心概念：

1. **刚体动力学**：牛顿运动定律、数值积分
2. **碰撞检测**：宽相/窄相检测、碰撞信息计算
3. **碰撞响应**：冲量方法、摩擦力模型
4. **约束求解**：迭代方法、约束类型
5. **性能优化**：空间分区、休眠机制

这些知识为实现一个简易的物理引擎奠定了坚实的基础。
