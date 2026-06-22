# 场景图系统 - 测试策略

## 1. 测试概述

### 1.1 测试目标

- 验证数学类型（Vec3, Mat4, Quaternion）的正确性
- 验证变换层级的正确传播
- 验证视锥裁剪算法的准确性
- 验证边界情况的处理
- 确保代码的健壮性

### 1.2 测试框架

使用 Google Test 框架：

```cpp
#include <gtest/gtest.h>

TEST(TestSuiteName, TestName) {
    EXPECT_EQ(1, 1);
    EXPECT_FLOAT_EQ(1.0f, 1.0f);
    EXPECT_NEAR(1.0f, 1.0f, 1e-5f);
}
```

### 1.3 测试运行

```bash
mkdir build && cd build
cmake .. -DBUILD_TESTS=ON
make -j$(nproc)
ctest --output-on-failure
```

---

## 2. 数学类型测试

### 2.1 Vec3 测试

```cpp
TEST(Vec3Test, Addition) {
    Vec3 a(1, 2, 3);
    Vec3 b(4, 5, 6);
    Vec3 c = a + b;
    EXPECT_FLOAT_EQ(c.x, 5.0f);
    EXPECT_FLOAT_EQ(c.y, 7.0f);
    EXPECT_FLOAT_EQ(c.z, 9.0f);
}

TEST(Vec3Test, DotProduct) {
    Vec3 a(1, 2, 3);
    Vec3 b(4, 5, 6);
    EXPECT_FLOAT_EQ(a.dot(b), 32.0f);  // 1*4 + 2*5 + 3*6
}

TEST(Vec3Test, CrossProduct) {
    Vec3 a(1, 0, 0);
    Vec3 b(0, 1, 0);
    Vec3 c = a.cross(b);
    EXPECT_FLOAT_EQ(c.x, 0.0f);
    EXPECT_FLOAT_EQ(c.y, 0.0f);
    EXPECT_FLOAT_EQ(c.z, 1.0f);
}

TEST(Vec3Test, Normalized) {
    Vec3 v(3, 4, 0);
    Vec3 n = v.normalized();
    EXPECT_NEAR(n.length(), 1.0f, 1e-5f);
    EXPECT_NEAR(n.x, 0.6f, 1e-5f);
    EXPECT_NEAR(n.y, 0.8f, 1e-5f);
}

TEST(Vec3Test, ZeroVectorNormalized) {
    Vec3 v(0, 0, 0);
    Vec3 n = v.normalized();
    EXPECT_FLOAT_EQ(n.x, 0.0f);
    EXPECT_FLOAT_EQ(n.y, 0.0f);
    EXPECT_FLOAT_EQ(n.z, 0.0f);
}
```

**测试要点**：
- 基本运算：加减乘除、点积、叉积
- 归一化：长度变为 1，方向不变
- 边界情况：零向量归一化

### 2.2 Mat4 测试

```cpp
TEST(Mat4Test, Identity) {
    Mat4 m;
    for (int r = 0; r < 4; ++r) {
        for (int c = 0; c < 4; ++c) {
            EXPECT_FLOAT_EQ(m.at(r, c), (r == c) ? 1.0f : 0.0f);
        }
    }
}

TEST(Mat4Test, Translation) {
    Mat4 m = Mat4::translation({1, 2, 3});
    Vec3 p = m.transform_point({0, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 1.0f);
    EXPECT_FLOAT_EQ(p.y, 2.0f);
    EXPECT_FLOAT_EQ(p.z, 3.0f);
}

TEST(Mat4Test, TransformDirection) {
    Mat4 m = Mat4::translation({1, 2, 3});
    Vec3 d = m.transform_direction({1, 0, 0});
    EXPECT_FLOAT_EQ(d.x, 1.0f);
    EXPECT_FLOAT_EQ(d.y, 0.0f);
    EXPECT_FLOAT_EQ(d.z, 0.0f);
}

TEST(Mat4Test, MatrixMultiply) {
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 s = Mat4::scaling({2, 2, 2});
    Mat4 ts = t * s;
    Vec3 p = ts.transform_point({1, 1, 1});
    EXPECT_FLOAT_EQ(p.x, 3.0f);  // 1*2 + 1
    EXPECT_FLOAT_EQ(p.y, 4.0f);  // 1*2 + 2
    EXPECT_FLOAT_EQ(p.z, 5.0f);  // 1*2 + 3
}

TEST(Mat4Test, Inverse) {
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 t_inv = t.inverse();
    Mat4 result = t * t_inv;
    for (int r = 0; r < 4; ++r) {
        for (int c = 0; c < 4; ++c) {
            EXPECT_NEAR(result.at(r, c), (r == c) ? 1.0f : 0.0f, 1e-5f);
        }
    }
}
```

**测试要点**：
- 单位矩阵
- 平移变换：transform_point 和 transform_direction 的区别
- 矩阵乘法：TRS 顺序
- 逆矩阵：M * M^-1 = I

### 2.3 Quaternion 测试

```cpp
TEST(QuaternionTest, FromAxisAngleIdentity) {
    Quaternion q = Quaternion::from_axis_angle({0, 1, 0}, 0);
    EXPECT_NEAR(q.w, 1.0f, 1e-5f);
}

TEST(QuaternionTest, Rotate90Degrees) {
    Quaternion q = Quaternion::from_axis_angle({0, 1, 0}, M_PI/2);
    Vec3 v = q.rotate({1, 0, 0});
    EXPECT_NEAR(v.x, 0.0f, 1e-5f);
    EXPECT_NEAR(v.y, 0.0f, 1e-5f);
    EXPECT_NEAR(v.z, -1.0f, 1e-5f);
}

TEST(QuaternionTest, Multiply) {
    Quaternion q1 = Quaternion::from_axis_angle({0, 1, 0}, M_PI/2);
    Quaternion q2 = Quaternion::from_axis_angle({0, 1, 0}, M_PI/2);
    Quaternion q3 = q1 * q2;
    Vec3 v = q3.rotate({1, 0, 0});
    EXPECT_NEAR(v.x, -1.0f, 1e-4f);
}
```

**测试要点**：
- 从轴角创建
- 旋转向量
- 四元数乘法（组合旋转）

---

## 3. 变换测试

### 3.1 Transform 测试

```cpp
TEST(TransformTest, DefaultConstructor) {
    Transform t;
    EXPECT_FLOAT_EQ(t.position.x, 0.0f);
    EXPECT_FLOAT_EQ(t.scale.x, 1.0f);
    EXPECT_FLOAT_EQ(t.rotation.w, 1.0f);
}

TEST(TransformTest, LocalMatrix) {
    Transform t;
    t.position = Vec3(1, 2, 3);
    t.scale = Vec3(2, 2, 2);
    Mat4 m = t.get_local_matrix();
    Vec3 p = m.transform_point({1, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 3.0f);  // 1*2 + 1
}

TEST(TransformTest, Forward) {
    Transform t;
    Vec3 fwd = t.forward();
    EXPECT_NEAR(fwd.x, 0.0f, 1e-5f);
    EXPECT_NEAR(fwd.y, 0.0f, 1e-5f);
    EXPECT_NEAR(fwd.z, -1.0f, 1e-5f);
}

TEST(TransformTest, RotateAxis) {
    Transform t;
    t.rotate_axis({0, 1, 0}, 90.0f);
    Vec3 fwd = t.forward();
    EXPECT_NEAR(fwd.x, -1.0f, 1e-4f);
}
```

**测试要点**：
- 默认构造
- 局部矩阵计算
- 方向向量
- 旋转操作

---

## 4. 包围盒测试

### 4.1 AABB 测试

```cpp
TEST(AABBTest, FromCenterSize) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    EXPECT_FLOAT_EQ(aabb.min.x, -1.0f);
    EXPECT_FLOAT_EQ(aabb.max.x, 1.0f);
}

TEST(AABBTest, Contains) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    EXPECT_TRUE(aabb.contains({0, 0, 0}));
    EXPECT_FALSE(aabb.contains({2, 0, 0}));
}

TEST(AABBTest, Intersects) {
    AABB a = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    AABB b = AABB::from_center_size({0.5f, 0, 0}, {1, 1, 1});
    EXPECT_TRUE(a.intersects(b));
}

TEST(AABBTest, Transform) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    Mat4 translation = Mat4::translation({10, 0, 0});
    AABB transformed = aabb.transform(translation);
    EXPECT_NEAR(transformed.min.x, 9.0f, 1e-5f);
    EXPECT_NEAR(transformed.max.x, 11.0f, 1e-5f);
}

TEST(AABBTest, Merge) {
    AABB a = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    AABB b = AABB::from_center_size({5, 5, 5}, {1, 1, 1});
    AABB merged = AABB::merge(a, b);
    EXPECT_FLOAT_EQ(merged.min.x, -1.0f);
    EXPECT_FLOAT_EQ(merged.max.x, 6.0f);
}
```

**测试要点**：
- 创建和访问
- 包含测试
- 相交测试
- 变换
- 合并

### 4.2 Frustum 测试

```cpp
TEST(FrustumTest, PointInside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    EXPECT_TRUE(frustum.test_point({0, 0, 0}));
}

TEST(FrustumTest, PointOutside) {
    Frustum frustum = ...;
    EXPECT_FALSE(frustum.test_point({100, 0, 0}));
}

TEST(FrustumTest, AABBInside) {
    Frustum frustum = ...;
    AABB aabb = AABB::from_center_size({0, 0, 0}, {0.5f, 0.5f, 0.5f});
    EXPECT_TRUE(frustum.test_aabb(aabb));
}

TEST(FrustumTest, AABBOutside) {
    Frustum frustum = ...;
    AABB aabb = AABB::from_center_size({100, 0, 0}, {1, 1, 1});
    EXPECT_FALSE(frustum.test_aabb(aabb));
}

TEST(FrustumTest, SphereTest) {
    Frustum frustum = ...;
    EXPECT_TRUE(frustum.test_sphere({0, 0, 0}, 0.5f));
    EXPECT_FALSE(frustum.test_sphere({100, 0, 0}, 1.0f));
}
```

**测试要点**：
- 点测试
- AABB 测试
- 球体测试
- 内部和外部情况

---

## 5. 场景图测试

### 5.1 SceneNode 测试

```cpp
TEST_F(SceneNodeTest, AddChild) {
    auto child = std::make_shared<SceneNode>("Child");
    root->add_child(child);
    EXPECT_EQ(root->child_count(), 1);
    EXPECT_EQ(child->get_parent(), root);
}

TEST_F(SceneNodeTest, WorldTransformHierarchy) {
    root->get_transform().position = Vec3(1, 0, 0);
    auto child = std::make_shared<SceneNode>("Child");
    child->get_transform().position = Vec3(0, 2, 0);
    root->add_child(child);

    root->update_transforms();

    Vec3 wp = child->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 1.0f);
    EXPECT_FLOAT_EQ(wp.y, 2.0f);
    EXPECT_FLOAT_EQ(wp.z, 0.0f);
}

TEST_F(SceneNodeTest, WorldTransformWithScale) {
    root->get_transform().scale = Vec3(2, 2, 2);
    auto child = std::make_shared<SceneNode>("Child");
    child->get_transform().position = Vec3(1, 0, 0);
    root->add_child(child);

    root->update_transforms();

    Vec3 wp = child->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 2.0f);
}

TEST_F(SceneNodeTest, WorldBoundsIncludesChildren) {
    // 添加子节点后，父节点的包围盒应该包含子节点
    ...
    root->update_transforms();

    const AABB& bounds = root->get_world_bounds();
    EXPECT_NEAR(bounds.min.x, -11.0f, 1e-5f);
    EXPECT_NEAR(bounds.max.x, 11.0f, 1e-5f);
}

TEST_F(SceneNodeTest, TraverseDfs) {
    // 验证深度优先遍历顺序
    std::vector<std::string> names;
    root->traverse_dfs([&names](const SceneNodePtr& node) {
        names.push_back(node->get_name());
    });
    EXPECT_EQ(names[0], "Root");
    EXPECT_EQ(names[1], "Child1");
    EXPECT_EQ(names[2], "GrandChild");
    EXPECT_EQ(names[3], "Child2");
}
```

**测试要点**：
- 添加/移除子节点
- 变换层级传播
- 缩放传播
- 包围盒层级
- 遍历顺序

### 5.2 SceneGraph 裁剪测试

```cpp
TEST_F(SceneGraphTest, CullAllVisible) {
    auto node = std::make_shared<SceneNode>("Visible");
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 1);
    EXPECT_EQ(graph->get_visible_nodes().size(), 1);
}

TEST_F(SceneGraphTest, CullBehindCamera) {
    auto node = std::make_shared<SceneNode>("Behind");
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 20}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 0);
    EXPECT_EQ(result.culled_nodes, 1);
}

TEST_F(SceneGraphTest, CullHierarchy) {
    // 父节点被裁剪时，子节点也被裁剪
    auto parent = std::make_shared<SceneNode>("Parent");
    parent->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 20}, {1, 1, 1})
    ));
    auto child = std::make_shared<SceneNode>("Child");
    child->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    parent->add_child(child);
    graph->get_root()->add_child(parent);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.early_exits, 1);
    EXPECT_EQ(graph->get_visible_nodes().size(), 0);
}

TEST_F(SceneGraphTest, CullInvisibleNode) {
    auto node = std::make_shared<SceneNode>("Invisible");
    node->set_visible(false);
    node->set_renderable(std::make_shared<TestRenderable>(...));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 0);
}
```

**测试要点**：
- 可见物体
- 不可见物体（在视锥体外）
- 层级裁剪（父节点裁剪 → 子节点裁剪）
- 可见性标志

---

## 6. 边界情况测试

### 6.1 空场景

```cpp
TEST(SceneGraphTest, EmptyScene) {
    SceneGraph scene;
    Camera camera;
    camera.set_position({0, 0, 5});
    camera.set_target({0, 0, 0});
    camera.set_fov(60.0f);
    camera.set_near_far(0.1f, 100.0f);
    scene.set_camera(camera);

    scene.update();
    auto result = scene.cull();

    EXPECT_EQ(result.total_nodes, 1);  // 根节点
    EXPECT_EQ(result.visible_nodes, 1);
}
```

### 6.2 零大小包围盒

```cpp
TEST(AABBTest, ZeroSize) {
    AABB aabb({0, 0, 0}, {0, 0, 0});
    EXPECT_TRUE(aabb.contains({0, 0, 0}));
    EXPECT_FALSE(aabb.contains({0.1f, 0, 0}));
}
```

### 6.3 反向变换

```cpp
TEST(Mat4Test, NegativeScale) {
    Mat4 s = Mat4::scaling({-1, -1, -1});
    Vec3 p = s.transform_point({1, 1, 1});
    EXPECT_FLOAT_EQ(p.x, -1.0f);
    EXPECT_FLOAT_EQ(p.y, -1.0f);
    EXPECT_FLOAT_EQ(p.z, -1.0f);
}
```

### 6.4 深层嵌套

```cpp
TEST_F(SceneNodeTest, DeepHierarchy) {
    auto current = root;
    for (int i = 0; i < 100; ++i) {
        auto child = std::make_shared<SceneNode>("Node" + std::to_string(i));
        child->get_transform().position = Vec3(1, 0, 0);
        current->add_child(child);
        current = child;
    }

    root->update_transforms();

    Vec3 wp = current->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 100.0f);
}
```

---

## 7. 性能测试

### 7.1 大量节点更新

```cpp
TEST(PerformanceTest, UpdateManyNodes) {
    SceneGraph scene;
    auto root = scene.get_root();

    // 创建 10000 个节点
    for (int i = 0; i < 10000; ++i) {
        auto node = std::make_shared<SceneNode>("Node" + std::to_string(i));
        node->get_transform().position = Vec3(i, 0, 0);
        root->add_child(node);
    }

    auto start = std::chrono::high_resolution_clock::now();
    scene.update();
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    std::cout << "Update 10000 nodes: " << duration.count() << " microseconds" << std::endl;

    EXPECT_LT(duration.count(), 10000);  // 应该在 10ms 内完成
}
```

### 7.2 裁剪效率

```cpp
TEST(PerformanceTest, CullingEfficiency) {
    SceneGraph scene;
    // 创建大量物体，部分在视锥体内，部分在外
    ...

    scene.update();
    auto start = std::chrono::high_resolution_clock::now();
    auto result = scene.cull();
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    std::cout << "Culling: " << duration.count() << " microseconds" << std::endl;
    std::cout << "Visible: " << result.visible_nodes << "/" << result.total_nodes << std::endl;
}
```

---

## 8. 测试覆盖率检查清单

### 8.1 数学类型

- [ ] Vec3 基本运算（+, -, *, /）
- [ ] Vec3 点积、叉积
- [ ] Vec3 归一化（包括零向量）
- [ ] Mat4 构造（单位矩阵、平移、缩放、旋转）
- [ ] Mat4 乘法
- [ ] Mat4 逆矩阵
- [ ] Mat4 transform_point vs transform_direction
- [ ] Quaternion 创建（轴角、欧拉角）
- [ ] Quaternion 旋转
- [ ] Quaternion 乘法

### 8.2 变换

- [ ] 默认构造
- [ ] 局部矩阵计算
- [ ] TRS 顺序
- [ ] 方向向量

### 8.3 包围盒

- [ ] AABB 创建
- [ ] AABB 包含测试
- [ ] AABB 相交测试
- [ ] AABB 变换
- [ ] AABB 合并
- [ ] Frustum 点测试
- [ ] Frustum AABB 测试
- [ ] Frustum 球体测试

### 8.4 场景图

- [ ] 添加/移除子节点
- [ ] 查找节点
- [ ] 变换层级传播
- [ ] 缩放传播
- [ ] 包围盒层级
- [ ] 可见性标志
- [ ] 遍历顺序

### 8.5 裁剪

- [ ] 所有可见
- [ ] 所有不可见
- [ ] 混合可见性
- [ ] 层级裁剪
- [ ] 不可见标志
- [ ] 空场景
