# 物理引擎学习笔记

## 学习目标

- 理解物理模拟原理
- 掌握碰撞检测算法
- 学会约束求解

## 核心概念

### 1. 刚体动力学

刚体是物理引擎中最基本的实体，具有以下属性：

- **质量 (Mass)**：物体的惯性，影响加速度
- **位置 (Position)**：物体在空间中的位置
- **速度 (Velocity)**：位置的变化率
- **加速度 (Acceleration)**：速度的变化率
- **旋转 (Rotation)**：物体的朝向
- **角速度 (Angular Velocity)**：旋转的变化率

#### 牛顿运动定律

1. **第一定律（惯性定律）**：物体在没有外力作用下保持静止或匀速直线运动
2. **第二定律**：F = ma（力 = 质量 × 加速度）
3. **第三定律**：作用力与反作用力大小相等、方向相反

#### 数值积分

使用欧拉方法进行数值积分：

```cpp
// 速度更新
velocity += force / mass * dt;

// 位置更新
position += velocity * dt;
```

更精确的方法：
- **半隐式欧拉法**：先更新速度，再用新速度更新位置
- **Verlet 积分**：直接基于位置计算
- **RK4（四阶龙格-库塔法）**：更高精度

### 2. 碰撞检测

碰撞检测分为两个阶段：

#### 宽相检测 (Broad Phase)

快速排除不可能碰撞的物体对：
- **AABB 碰撞检测**：轴对齐包围盒
- **空间分区**：四叉树、网格、BVH

```cpp
bool aabb_intersects(const AABB& a, const AABB& b) {
    return a.min.x <= b.max.x && a.max.x >= b.min.x &&
           a.min.y <= b.max.y && a.max.y >= b.min.y;
}
```

#### 窄相检测 (Narrow Phase)

精确检测碰撞：
- **圆形碰撞**：距离 < 半径之和
- **多边形碰撞**：分离轴定理 (SAT)
- **GJK 算法**：通用凸多边形碰撞检测

#### 碰撞信息

碰撞检测返回：
- **碰撞法线**：从物体 A 指向物体 B 的方向
- **穿透深度**：两个物体重叠的程度
- **接触点**：碰撞发生的位置

### 3. 碰撞响应

基于冲量的方法：

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

#### 摩擦力

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

### 4. 约束求解

约束限制物体的运动：

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

#### 迭代求解

使用 Gauss-Seidel 迭代：

```cpp
for (int i = 0; i < iterations; ++i) {
    for (auto& constraint : constraints) {
        constraint->solve(dt);
    }
}
```

### 5. 物理世界

物理世界管理所有实体和模拟步骤：

```
1. 施加重力
2. 积分（更新速度和位置）
3. 碰撞检测
4. 碰撞响应
5. 约束求解
6. 位置修正（解决穿透）
```

## 实现细节

### 向量数学

实现 2D 向量类，支持：
- 基本运算（加、减、乘、除）
- 点积、叉积
- 长度、归一化
- 旋转、投影、反射
- 线性插值

### AABB

轴对齐包围盒：
- 快速相交测试
- 合并、扩展
- 距离计算

### 刚体

支持三种类型：
- **Static**：不受力影响
- **Dynamic**：完全模拟
- **Kinematic**：可手动设置速度

### 约束

支持四种约束：
- **距离约束**：保持距离
- **钉子约束**：固定位置
- **铰链约束**：允许旋转
- **焊接约束**：完全固定

## 学习心得

### 1. 数值稳定性

- 使用半隐式欧拉法提高稳定性
- 添加阻尼防止能量无限累积
- 位置修正解决穿透问题

### 2. 性能优化

- 宽相检测快速排除
- 空间分区减少检测次数
- 休眠机制处理静止物体

### 3. 约束求解

- 迭代次数影响精度和性能
- 约束顺序影响收敛
- 松弛因子可以加速收敛

### 4. 碰撞响应

- 冲量方法简单有效
- 摩擦力模型影响真实感
- 恢复系数控制弹性

## 常见问题

### 1. 物体穿透

原因：积分步长太大，碰撞检测不准确

解决方案：
- 减小时间步长
- 添加位置修正
- 使用 CCD（连续碰撞检测）

### 2. 约束不稳定

原因：迭代次数不足，约束冲突

解决方案：
- 增加迭代次数
- 调整约束顺序
- 使用更稳定的求解器

### 3. 能量不守恒

原因：数值积分误差，碰撞响应不准确

解决方案：
- 使用更高阶积分方法
- 调整恢复系数
- 添加能量修正

## 扩展学习

### 进阶主题

1. **多边形碰撞检测**
   - 分离轴定理 (SAT)
   - GJK 算法
   - EPA 算法

2. **空间分区**
   - 四叉树
   - BVH（层次包围盒）
   - 网格

3. **高级约束**
   - 滑轮
   - 齿轮
   - 弹簧

4. **性能优化**
   - 并行计算
   - SIMD 指令
   - GPU 加速

### 参考资源

- 《Game Physics Engine Development》
- 《Real-Time Collision Detection》
- Box2D 源代码
- Bullet 物理引擎文档

## 总结

通过实现这个物理引擎，我深入理解了：

1. **物理模拟的基本原理**：牛顿运动定律、数值积分
2. **碰撞检测算法**：宽相/窄相检测、碰撞信息计算
3. **约束求解方法**：迭代求解、约束类型
4. **工程实践**：模块化设计、测试驱动开发

这个项目为理解更复杂的物理引擎（如 Box2D、Bullet）打下了坚实的基础。
