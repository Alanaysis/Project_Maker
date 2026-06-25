# 02 - 需求分析

## 项目目标

实现一个功能完整的 2D 物理引擎，支持刚体动力学、碰撞检测与响应、约束系统和多种积分方法。

## 功能需求

### 1. 向量数学模块 (`Vector2D`)

#### 基本运算
- 向量加法 (`+`)
- 向量减法 (`-`)
- 标量乘法 (`*`)
- 标量除法 (`/`)
- 向量取反 (`-v`)

#### 高级运算
- 点积 (`dot`)
- 叉积 (`cross`)
- 向量长度 (`length`)
- 长度平方 (`length_squared`)
- 归一化 (`normalized`)
- 垂直向量 (`perpendicular`)
- 反射 (`reflect`)
- 距离计算 (`distance_to`)
- 角度计算 (`angle`)
- 从角度创建 (`from_angle`)

### 2. 刚体模块 (`RigidBody`)

#### 基本属性
- 位置 (`position`)
- 速度 (`velocity`)
- 加速度 (`acceleration`)
- 质量 (`mass`)
- 逆质量 (`inverse_mass`)
- 是否静态 (`is_static`)

#### 物理属性
- 恢复系数 (`restitution`) - 弹性程度
- 摩擦系数 (`friction`)
- 旋转角度 (`rotation`)
- 角速度 (`angular_velocity`)

#### 方法
- 施加力 (`apply_force`)
- 施加冲量 (`apply_impulse`)
- 清除力 (`clear_forces`)
- 更新状态 (`update`)
- 计算动能 (`kinetic_energy`)
- 计算动量 (`momentum`)

### 3. 碰撞器模块 (`Collider`)

#### 圆形碰撞器 (`CircleCollider`)
- 半径 (`radius`)
- 获取 AABB (`get_aabb`)
- 点包含测试 (`contains_point`)

#### AABB 碰撞器 (`AABBCollider`)
- 宽度 (`width`)
- 高度 (`height`)
- 获取 AABB (`get_aabb`)
- 点包含测试 (`contains_point`)
- 获取角点 (`get_corners`)

#### 多边形碰撞器 (`PolygonCollider`)
- 顶点列表 (`vertices`)
- 法线列表 (`normals`)
- 获取世界坐标顶点 (`get_world_vertices`)
- 获取 AABB (`get_aabb`)
- 点包含测试 (`contains_point`)
- 创建矩形 (`create_box`)

### 4. 碰撞检测模块 (`CollisionDetector`)

#### 检测算法
- AABB vs AABB
- 圆形 vs 圆形
- 圆形 vs AABB
- 多边形 vs 多边形 (SAT)

#### 碰撞信息 (`CollisionInfo`)
- 物体 A (`body_a`)
- 物体 B (`body_b`)
- 碰撞法线 (`normal`)
- 穿透深度 (`penetration`)
- 接触点 (`contact_point`)

### 5. 碰撞响应模块 (`CollisionResolver`)

#### 响应方法
- 弹性碰撞响应
- 非弹性碰撞响应
- 摩擦力计算
- 位置修正（分离重叠物体）

### 6. 约束模块 (`Constraint`)

#### 距离约束 (`DistanceConstraint`)
- 保持两点之间的距离
- 刚度参数 (`stiffness`)
- 可选的初始距离

#### 弹簧约束 (`SpringConstraint`)
- 弹性连接两点
- 刚度参数 (`stiffness`)
- 阻尼参数 (`damping`)
- 静止长度 (`rest_length`)

#### 钉子约束 (`PinConstraint`)
- 固定物体在世界坐标系中的位置
- 锚点 (`anchor`)
- 刚度参数 (`stiffness`)

#### 角度约束 (`AngleConstraint`)
- 保持三个物体之间的角度
- 刚度参数 (`stiffness`)

### 7. 积分器模块 (`Integrator`)

#### 欧拉积分器 (`EulerIntegrator`)
- 半隐式欧拉方法
- 先更新速度，再更新位置
- 简单但稳定性较差

#### Verlet 积分器 (`VerletIntegrator`)
- 基于位置的积分
- 无显式速度存储
- 更稳定，适合约束求解

#### RK4 积分器 (`RK4Integrator`)
- 四阶龙格-库塔方法
- 计算四个中间状态
- 更精确但计算量大

### 8. 物理世界模块 (`PhysicsWorld`)

#### 世界属性
- 重力 (`gravity`)
- 积分器 (`integrator`)
- 约束求解迭代次数 (`iterations`)

#### 物体管理
- 添加物体 (`add_body`)
- 移除物体 (`remove_body`)
- 添加约束 (`add_constraint`)
- 移除约束 (`remove_constraint`)

#### 模拟方法
- 步进 (`step`)
  - 应用重力
  - 碰撞检测
  - 碰撞响应
  - 约束求解
  - 积分更新

#### 查询方法
- 获取指定位置的物体 (`get_body_at`)

## 非功能需求

### 1. 性能要求
- 支持至少 100 个物体的实时仿真
- 60 FPS 的帧率目标
- 高效的碰撞检测算法

### 2. 代码质量
- 模块化设计
- 清晰的接口定义
- 完整的文档注释
- 类型提示

### 3. 可扩展性
- 易于添加新的碰撞器形状
- 易于添加新的约束类型
- 易于添加新的积分方法

### 4. 测试覆盖
- 单元测试覆盖所有核心功能
- 集成测试验证系统行为

## 技术栈

### 编程语言
- Python 3.10+

### 依赖库
- Pygame（可视化示例）
- Pytest（测试框架）

### 开发工具
- VS Code / PyCharm
- Git 版本控制
- pytest 测试运行

## 约束条件

### 1. 2D 限制
- 仅支持 2D 物理模拟
- 不支持 3D 物理

### 2. 凸形状限制
- SAT 算法仅支持凸多边形
- 不支持凹多边形

### 3. 简化处理
- 不考虑空气阻力
- 不考虑旋转摩擦
- 不支持连续碰撞检测 (CCD)

## 验收标准

### 1. 功能验证
- [x] 向量数学运算正确
- [x] 刚体动力学正确
- [x] 碰撞检测准确
- [x] 碰撞响应合理
- [x] 约束系统有效
- [x] 积分方法正确

### 2. 示例程序
- [x] 弹球游戏可运行
- [x] 物理演示可运行
- [x] 交互功能正常

### 3. 测试通过
- [x] 所有单元测试通过
- [x] 测试覆盖率达到 80% 以上

### 4. 文档完整
- [x] README 文档完整
- [x] 代码注释清晰
- [x] 使用示例明确
