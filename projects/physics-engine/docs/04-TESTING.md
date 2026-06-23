# 物理引擎测试文档

## 1. 测试概述

### 测试目标

1. **功能验证**：验证所有功能按预期工作
2. **边界测试**：测试边界情况和错误处理
3. **性能测试**：验证性能满足要求
4. **集成测试**：验证各组件协同工作

### 测试策略

1. **单元测试**：测试单个组件的功能
2. **集成测试**：测试组件之间的交互
3. **系统测试**：测试完整的物理模拟
4. **回归测试**：确保修改不会引入新问题

### 测试工具

- **Google Test**：C++ 测试框架
- **CMake**：构建系统，集成测试

## 2. 单元测试

### 2.1 向量数学测试 (`test_vector2d.cpp`)

#### 基本运算测试

```cpp
TEST(Vector2DTest, Addition) {
    Vector2D a(1.0, 2.0);
    Vector2D b(3.0, 4.0);
    Vector2D c = a + b;
    EXPECT_DOUBLE_EQ(c.x, 4.0);
    EXPECT_DOUBLE_EQ(c.y, 6.0);
}

TEST(Vector2DTest, Subtraction) {
    Vector2D a(5.0, 7.0);
    Vector2D b(2.0, 3.0);
    Vector2D c = a - b;
    EXPECT_DOUBLE_EQ(c.x, 3.0);
    EXPECT_DOUBLE_EQ(c.y, 4.0);
}

TEST(Vector2DTest, ScalarMultiplication) {
    Vector2D v(2.0, 3.0);
    Vector2D result = v * 2.0;
    EXPECT_DOUBLE_EQ(result.x, 4.0);
    EXPECT_DOUBLE_EQ(result.y, 6.0);
}
```

#### 向量运算测试

```cpp
TEST(Vector2DTest, DotProduct) {
    Vector2D a(1.0, 2.0);
    Vector2D b(3.0, 4.0);
    double dot = a.dot(b);
    EXPECT_DOUBLE_EQ(dot, 11.0);  // 1*3 + 2*4
}

TEST(Vector2DTest, CrossProduct) {
    Vector2D a(1.0, 0.0);
    Vector2D b(0.0, 1.0);
    double cross = a.cross(b);
    EXPECT_DOUBLE_EQ(cross, 1.0);  // 1*1 - 0*0
}

TEST(Vector2DTest, Length) {
    Vector2D v(3.0, 4.0);
    EXPECT_DOUBLE_EQ(v.length_squared(), 25.0);
    EXPECT_DOUBLE_EQ(v.length(), 5.0);
}
```

#### 归一化测试

```cpp
TEST(Vector2DTest, Normalization) {
    Vector2D v(3.0, 4.0);
    Vector2D n = v.normalized();
    EXPECT_NEAR(n.x, 0.6, 1e-10);
    EXPECT_NEAR(n.y, 0.8, 1e-10);
    EXPECT_NEAR(n.length(), 1.0, 1e-10);
}

TEST(Vector2DTest, ZeroVectorNormalization) {
    Vector2D v(0.0, 0.0);
    Vector2D n = v.normalized();
    EXPECT_DOUBLE_EQ(n.x, 0.0);
    EXPECT_DOUBLE_EQ(n.y, 0.0);
}
```

#### 变换测试

```cpp
TEST(Vector2DTest, Rotation) {
    Vector2D v(1.0, 0.0);
    Vector2D rotated = v.rotated(M_PI / 2);  // 90度
    EXPECT_NEAR(rotated.x, 0.0, 1e-10);
    EXPECT_NEAR(rotated.y, 1.0, 1e-10);
}

TEST(Vector2DTest, Projection) {
    Vector2D a(2.0, 3.0);
    Vector2D b(1.0, 0.0);
    Vector2D proj = a.project_onto(b);
    EXPECT_DOUBLE_EQ(proj.x, 2.0);
    EXPECT_DOUBLE_EQ(proj.y, 0.0);
}

TEST(Vector2DTest, Reflection) {
    Vector2D v(1.0, -1.0);
    Vector2D normal(0.0, 1.0);
    Vector2D reflected = v.reflect(normal);
    EXPECT_DOUBLE_EQ(reflected.x, 1.0);
    EXPECT_DOUBLE_EQ(reflected.y, 1.0);
}
```

#### 插值测试

```cpp
TEST(Vector2DTest, Lerp) {
    Vector2D a(0.0, 0.0);
    Vector2D b(10.0, 10.0);

    Vector2D mid = Vector2D::lerp(a, b, 0.5);
    EXPECT_DOUBLE_EQ(mid.x, 5.0);
    EXPECT_DOUBLE_EQ(mid.y, 5.0);

    Vector2D start = Vector2D::lerp(a, b, 0.0);
    EXPECT_DOUBLE_EQ(start.x, 0.0);
    EXPECT_DOUBLE_EQ(start.y, 0.0);

    Vector2D end = Vector2D::lerp(a, b, 1.0);
    EXPECT_DOUBLE_EQ(end.x, 10.0);
    EXPECT_DOUBLE_EQ(end.y, 10.0);
}
```

### 2.2 AABB 测试 (`test_aabb.cpp`)

#### 基本操作测试

```cpp
TEST(AABBTest, ContainsPoint) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);

    // 内部点
    EXPECT_TRUE(aabb.contains(Vector2D(5.0, 5.0)));

    // 边界点
    EXPECT_TRUE(aabb.contains(Vector2D(0.0, 0.0)));
    EXPECT_TRUE(aabb.contains(Vector2D(10.0, 10.0)));

    // 外部点
    EXPECT_FALSE(aabb.contains(Vector2D(-1.0, 5.0)));
    EXPECT_FALSE(aabb.contains(Vector2D(11.0, 5.0)));
}

TEST(AABBTest, Intersects) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);  // 重叠
    AABB aabb3(11.0, 11.0, 20.0, 20.0); // 分离

    EXPECT_TRUE(aabb1.intersects(aabb2));
    EXPECT_TRUE(aabb2.intersects(aabb1));
    EXPECT_FALSE(aabb1.intersects(aabb3));
    EXPECT_FALSE(aabb3.intersects(aabb1));
}
```

#### 合并和扩展测试

```cpp
TEST(AABBTest, Merge) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);

    AABB merged = aabb1.merge(aabb2);
    EXPECT_DOUBLE_EQ(merged.min.x, 0.0);
    EXPECT_DOUBLE_EQ(merged.min.y, 0.0);
    EXPECT_DOUBLE_EQ(merged.max.x, 15.0);
    EXPECT_DOUBLE_EQ(merged.max.y, 15.0);
}

TEST(AABBTest, Expanded) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    AABB expanded = aabb.expanded(2.0);

    EXPECT_DOUBLE_EQ(expanded.min.x, -2.0);
    EXPECT_DOUBLE_EQ(expanded.min.y, -2.0);
    EXPECT_DOUBLE_EQ(expanded.max.x, 12.0);
    EXPECT_DOUBLE_EQ(expanded.max.y, 12.0);
}
```

### 2.3 刚体测试 (`test_rigid_body.cpp`)

#### 创建测试

```cpp
TEST_F(RigidBodyTest, DefaultConstruction) {
    RigidBodyDef def;
    def.position = {5.0, 10.0};
    def.mass = 2.0;

    RigidBody body(def);

    EXPECT_DOUBLE_EQ(body.position().x, 5.0);
    EXPECT_DOUBLE_EQ(body.position().y, 10.0);
    EXPECT_DOUBLE_EQ(body.mass(), 2.0);
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.5);
    EXPECT_EQ(body.type(), BodyType::Dynamic);
}

TEST_F(RigidBodyTest, StaticBody) {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {0.0, 0.0};
    def.mass = 100.0;

    RigidBody body(def);

    EXPECT_TRUE(body.is_static());
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.0);
}
```

#### 力和冲量测试

```cpp
TEST_F(RigidBodyTest, ApplyForce) {
    RigidBodyDef def;
    def.mass = 2.0;

    RigidBody body(def);

    body.apply_force({10.0, 20.0});
    EXPECT_DOUBLE_EQ(body.force().x, 10.0);
    EXPECT_DOUBLE_EQ(body.force().y, 20.0);
}

TEST_F(RigidBodyTest, ApplyImpulse) {
    RigidBodyDef def;
    def.mass = 2.0;

    RigidBody body(def);

    body.apply_impulse({10.0, 20.0});
    EXPECT_DOUBLE_EQ(body.velocity().x, 5.0);   // 10 / 2
    EXPECT_DOUBLE_EQ(body.velocity().y, 10.0);  // 20 / 2
}
```

#### 积分测试

```cpp
TEST_F(RigidBodyTest, Integration) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 0.0};

    RigidBody body(def);

    double dt = 0.1;
    body.integrate(dt);

    // 位置应该更新
    EXPECT_NEAR(body.position().x, 0.1, 1e-10);
    EXPECT_NEAR(body.position().y, 0.0, 1e-10);
}

TEST_F(RigidBodyTest, IntegrationWithForce) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};
    def.velocity = {0.0, 0.0};

    RigidBody body(def);

    body.apply_force({10.0, 0.0});

    double dt = 0.1;
    body.integrate(dt);

    // 速度应该增加（F * dt / m = 10 * 0.1 / 1 = 1.0）
    EXPECT_NEAR(body.velocity().x, 1.0, 1e-10);
}
```

### 2.4 碰撞检测测试 (`test_collision.cpp`)

#### AABB 碰撞测试

```cpp
TEST(CollisionTest, AABBvsAABB_NoCollision) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(15.0, 15.0, 20.0, 20.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_FALSE(result.collided);
}

TEST(CollisionTest, AABBvsAABB_OverlapX) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(5.0, 0.0, 15.0, 10.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);
    EXPECT_DOUBLE_EQ(result.normal.x, 1.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 0.0);
}
```

#### 圆形碰撞测试

```cpp
TEST(CollisionTest, CircleVsCircle_Collision) {
    Vector2D center_a(0.0, 0.0);
    Vector2D center_b(3.0, 0.0);
    double radius_a = 2.0;
    double radius_b = 2.0;

    CollisionResult result = circle_vs_circle(center_a, radius_a, center_b, radius_b);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 1.0, 1e-10);
}
```

### 2.5 约束测试 (`test_constraint.cpp`)

#### 距离约束测试

```cpp
TEST_F(ConstraintTest, DistanceConstraintInitialize) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 初始距离应该是 5.0
    EXPECT_NEAR(constraint->target_distance(), 5.0, 1e-10);
}

TEST_F(ConstraintTest, DistanceConstraintSolve) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();
    constraint->stiffness = 1.0;

    // 移动 body_b 使距离变为 10.0
    body_b->set_position({10.0, 0.0});

    constraint->solve(1.0 / 60.0);

    // 物体应该被拉近
    EXPECT_LT(body_b->position().x, 10.0);
    EXPECT_GT(body_a->position().x, 0.0);
}
```

#### 钉子约束测试

```cpp
TEST_F(ConstraintTest, PinConstraintSolve) {
    body_a->set_position({0.0, 0.0});
    auto constraint = std::make_shared<PinConstraint>(
        body_a, Vector2D(5.0, 5.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 移动物体
    body_a->set_position({2.0, 2.0});

    constraint->solve(1.0 / 60.0);

    // 物体应该被拉向固定点
    EXPECT_GT(body_a->position().x, 2.0);
    EXPECT_GT(body_a->position().y, 2.0);
}
```

### 2.6 世界测试 (`test_world.cpp`)

#### 基本功能测试

```cpp
TEST_F(WorldTest, CreateBody) {
    RigidBodyDef def;
    def.position = {5.0, 10.0};
    def.mass = 2.0;

    auto body = world->create_body(def);

    EXPECT_EQ(world->body_count(), 1);
    EXPECT_DOUBLE_EQ(body->position().x, 5.0);
    EXPECT_DOUBLE_EQ(body->position().y, 10.0);
}

TEST_F(WorldTest, StepSimulation) {
    RigidBodyDef def;
    def.position = {0.0, 10.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    // 模拟一步
    world->step(1.0 / 60.0);

    // 物体应该下落（重力）
    EXPECT_LT(body->position().y, 10.0);
    EXPECT_LT(body->velocity().y, 0.0);
}
```

#### 约束创建测试

```cpp
TEST_F(WorldTest, CreateDistanceConstraint) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    auto body_b = world->create_body(def2);

    auto constraint = world->create_distance_constraint(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_NE(constraint, nullptr);
    EXPECT_EQ(constraint->type(), ConstraintType::Distance);
}
```

## 3. 集成测试 (`test_integration.cpp`)

### 3.1 自由落体测试

```cpp
TEST_F(IntegrationTest, FreeFall) {
    RigidBodyDef def;
    def.position = {0.0, 100.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;
    double total_time = 1.0;
    int steps = static_cast<int>(total_time / dt);

    for (int i = 0; i < steps; ++i) {
        world->step(dt);
    }

    // 使用运动学公式验证：y = y0 + v0*t + 0.5*g*t^2
    double expected_y = 100.0 + 0.5 * (-9.81) * total_time * total_time;

    // 由于数值积分的误差，允许一定的容差
    EXPECT_NEAR(body->position().y, expected_y, 1.0);
}
```

### 3.2 抛物运动测试

```cpp
TEST_F(IntegrationTest, ProjectileMotion) {
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.velocity = {10.0, 20.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;
    double total_time = 2.0;
    int steps = static_cast<int>(total_time / dt);

    for (int i = 0; i < steps; ++i) {
        world->step(dt);
    }

    // x = v0x * t = 10 * 2 = 20
    double expected_x = 10.0 * total_time;
    EXPECT_NEAR(body->position().x, expected_x, 1.0);

    // y = v0y * t + 0.5 * g * t^2 = 20 * 2 + 0.5 * (-9.81) * 4 = 20.38
    double expected_y = 20.0 * total_time + 0.5 * (-9.81) * total_time * total_time;
    EXPECT_NEAR(body->position().y, expected_y, 1.0);
}
```

### 3.3 碰撞响应测试

```cpp
TEST_F(IntegrationTest, TwoBodyCollision) {
    RigidBodyDef def1;
    def1.position = {-5.0, 0.0};
    def1.velocity = {5.0, 0.0};
    def1.mass = 1.0;
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    def2.velocity = {-5.0, 0.0};
    def2.mass = 1.0;
    auto body_b = world->create_body(def2);

    double dt = 1.0 / 60.0;

    // 模拟碰撞
    for (int i = 0; i < 60; ++i) {
        world->step(dt);
    }

    // 两个物体应该已经碰撞并反弹
    EXPECT_LT(body_a->velocity().x, 0.0);
    EXPECT_GT(body_b->velocity().x, 0.0);
}
```

### 3.4 约束系统测试

```cpp
TEST_F(IntegrationTest, Pendulum) {
    RigidBodyDef anchor_def;
    anchor_def.type = BodyType::Static;
    anchor_def.position = {0.0, 10.0};
    auto anchor = world->create_body(anchor_def);

    RigidBodyDef bob_def;
    bob_def.position = {5.0, 10.0};
    bob_def.mass = 1.0;
    auto bob = world->create_body(bob_def);

    auto constraint = world->create_distance_constraint(
        anchor, bob, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->stiffness = 1.0;

    double dt = 1.0 / 60.0;

    // 模拟摆锤运动
    for (int i = 0; i < 300; ++i) {
        world->step(dt);
    }

    // 摆锤应该在锚点附近摆动
    double distance = anchor->position().distance_to(bob->position());
    EXPECT_NEAR(distance, 5.0, 1.0);
}
```

### 3.5 能量守恒测试

```cpp
TEST_F(IntegrationTest, EnergyConservation) {
    RigidBodyDef def;
    def.position = {0.0, 10.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    double initial_energy = body->mass() * 9.81 * body->position().y;

    double dt = 1.0 / 60.0;
    for (int i = 0; i < 60; ++i) {
        world->step(dt);
    }

    double kinetic_energy = 0.5 * body->mass() * body->velocity().length_squared();
    double potential_energy = body->mass() * 9.81 * body->position().y;
    double final_energy = kinetic_energy + potential_energy;

    // 能量应该近似守恒（允许数值误差）
    EXPECT_NEAR(initial_energy, final_energy, 10.0);
}
```

## 4. 测试配置

### CMake 配置

```cmake
# tests/CMakeLists.txt

find_package(GTest QUIET)

if(NOT GTest_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG release-1.12.1
    )
    FetchContent_MakeAvailable(googletest)
endif()

set(TEST_SOURCES
    test_vector2d.cpp
    test_aabb.cpp
    test_rigid_body.cpp
    test_collision.cpp
    test_constraint.cpp
    test_world.cpp
    test_integration.cpp
)

add_executable(physics_engine_tests ${TEST_SOURCES})

target_link_libraries(physics_engine_tests
    PRIVATE
        physics_engine
        GTest::gtest
        GTest::gtest_main
)

add_test(NAME physics_engine_tests COMMAND physics_engine_tests)
```

### 运行测试

```bash
# 构建项目
mkdir build && cd build
cmake ..

# 编译
make

# 运行测试
ctest --output-on-failure

# 或者直接运行测试可执行文件
./tests/physics_engine_tests
```

## 5. 测试覆盖率

### 覆盖率目标

1. **代码覆盖率**：> 80%
2. **分支覆盖率**：> 70%
3. **功能覆盖率**：100%

### 覆盖率工具

使用 `gcov` 和 `lcov` 生成覆盖率报告：

```bash
# 编译时启用覆盖率
cmake -DCMAKE_BUILD_TYPE=Coverage ..
make

# 运行测试
ctest

# 生成覆盖率报告
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 6. 测试最佳实践

### 测试命名

- 使用描述性的测试名称
- 格式：`TestSuite.TestName` 或 `Feature_Scenario_ExpectedResult`

### 测试组织

- 每个源文件对应一个测试文件
- 使用测试夹具（Fixture）共享设置
- 将相关测试分组

### 断言选择

- `EXPECT_*`：非致命断言，测试继续执行
- `ASSERT_*`：致命断言，测试立即停止
- 使用 `EXPECT_NEAR` 进行浮点数比较

### 测试数据

- 使用有意义的测试数据
- 测试边界情况
- 测试错误情况

## 7. 常见问题

### 浮点数精度问题

```cpp
// 错误
EXPECT_DOUBLE_EQ(a, b);

// 正确
EXPECT_NEAR(a, b, 1e-10);
```

### 测试隔离

- 每个测试应该独立
- 使用 `SetUp()` 和 `TearDown()` 进行设置和清理
- 避免测试之间的依赖

### 性能测试

```cpp
TEST(PerformanceTest, ManyBodies) {
    World world;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    // 创建大量物体
    for (int i = 0; i < 1000; ++i) {
        RigidBodyDef def;
        def.position = {static_cast<double>(i), 0.0};
        world.create_body(def);
    }
    
    // 模拟
    for (int i = 0; i < 100; ++i) {
        world.step(1.0 / 60.0);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    // 验证性能
    EXPECT_LT(duration.count(), 1000);  // 应该在 1 秒内完成
}
```

## 8. 测试总结

### 测试覆盖

1. **向量数学**：基本运算、向量运算、变换、插值
2. **AABB**：相交测试、合并、扩展
3. **刚体**：创建、属性、力、冲量、积分
4. **碰撞检测**：AABB 碰撞、圆形碰撞
5. **约束**：距离约束、钉子约束
6. **世界**：创建、模拟、约束
7. **集成**：自由落体、抛物运动、碰撞、约束、能量守恒

### 测试结果

所有测试应该通过，验证：
1. 功能正确性
2. 数值稳定性
3. 边界处理
4. 性能满足要求

### 持续改进

1. 增加更多边界情况测试
2. 添加性能基准测试
3. 提高测试覆盖率
4. 自动化测试流程
