# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────┐
│           系统测试 (examples/)          │
│    完整约束系统的端到端测试              │
├─────────────────────────────────────────┤
│           集成测试 (test_solver.cpp)    │
│    多约束组合求解测试                   │
├─────────────────────────────────────────┤
│           单元测试 (test_constraints.cpp)│
│    单个约束的残差和梯度测试             │
└─────────────────────────────────────────┘
```

### 1.2 测试覆盖目标

- **约束残差**：100% 覆盖所有约束类型
- **梯度计算**：100% 覆盖，与数值微分对比
- **求解器**：覆盖主要求解场景
- **边界情况**：过度约束、欠约束、退化几何

## 2. 单元测试

### 2.1 几何实体测试

#### 测试用例：点距离计算

```cpp
TEST(point_distance) {
    Point2D p1(0, 0), p2(3, 4);
    ASSERT_NEAR(p1.distanceTo(p2), 5.0, 1e-10);
    ASSERT_NEAR(p1.distanceSquaredTo(p2), 25.0, 1e-10);
}
```

**验证**：距离公式 `√(x² + y²)` 正确性

#### 测试用例：点向量运算

```cpp
TEST(point_operations) {
    Point2D p1(1, 2), p2(3, 4);

    auto sum = p1 + p2;
    ASSERT_NEAR(sum.x, 4.0, 1e-10);
    ASSERT_NEAR(sum.y, 6.0, 1e-10);

    auto diff = p2 - p1;
    ASSERT_NEAR(diff.x, 2.0, 1e-10);
    ASSERT_NEAR(diff.y, 2.0, 1e-10);
}
```

#### 测试用例：线段角度计算

```cpp
TEST(line_angle) {
    Line2D l1(Point2D(0, 0), Point2D(1, 0));  // 水平
    Line2D l2(Point2D(0, 0), Point2D(0, 1));  // 垂直

    ASSERT_NEAR(l1.angleWith(l2), M_PI / 2.0, 1e-10);

    Line2D l3(Point2D(0, 0), Point2D(1, 1));  // 45度
    ASSERT_NEAR(l1.angleWith(l3), M_PI / 4.0, 1e-10);
}
```

#### 测试用例：线段最近点

```cpp
TEST(line_closest_point) {
    Line2D line(Point2D(0, 0), Point2D(10, 0));
    Point2D p(5, 5);

    auto closest = line.closestPointTo(p);
    ASSERT_NEAR(closest.x, 5.0, 1e-10);
    ASSERT_NEAR(closest.y, 0.0, 1e-10);
    ASSERT_NEAR(line.distanceToPoint(p), 5.0, 1e-10);
}
```

### 2.2 约束残差测试

#### 测试用例：距离约束

```cpp
TEST(distance_constraint) {
    // 距离为 5 的两点
    std::vector<double> params = {0.0, 0.0, 3.0, 4.0};
    DistanceConstraint c(0, 2, 5.0);

    // 正确距离，残差应为 0
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // 错误距离，残差应非零
    params = {0.0, 0.0, 1.0, 0.0};
    ASSERT_NEAR(c.residual(params), 1.0 - 25.0, 1e-10);
}
```

**验证**：
- (3,4) 到 (0,0) 距离 = 5，残差 = 25 - 25 = 0
- (1,0) 到 (0,0) 距离 = 1，残差 = 1 - 25 = -24

#### 测试用例：水平约束

```cpp
TEST(horizontal_constraint) {
    // 水平线段
    std::vector<double> params = {0.0, 5.0, 10.0, 5.0};
    HorizontalConstraint c(0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // 非水平线段
    params = {0.0, 0.0, 10.0, 5.0};
    ASSERT_NEAR(c.residual(params), -5.0, 1e-10);
}
```

**验证**：残差 = y1 - y2

#### 测试用例：平行约束

```cpp
TEST(parallel_constraint) {
    // 两条水平线（平行）
    std::vector<double> params = {0.0, 0.0, 10.0, 0.0,
                                  0.0, 5.0, 10.0, 5.0};
    ParallelConstraint c(0, 4);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // 两条垂直线（平行）
    params = {0.0, 0.0, 0.0, 10.0,
              5.0, 0.0, 5.0, 10.0};
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // 不平行的线
    params = {0.0, 0.0, 10.0, 0.0,
              0.0, 0.0, 0.0, 10.0};
    ASSERT_NEAR(c.residual(params), 100.0, 1e-10);
}
```

**验证**：残差 = dx1·dy2 - dy1·dx2（叉积）

#### 测试用例：垂直约束

```cpp
TEST(perpendicular_constraint) {
    // 水平线和垂直线（垂直）
    std::vector<double> params = {0.0, 0.0, 10.0, 0.0,
                                  0.0, 0.0, 0.0, 10.0};
    PerpendicularConstraint c(0, 4);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // 两条水平线（不垂直）
    params = {0.0, 0.0, 10.0, 0.0,
              0.0, 5.0, 10.0, 5.0};
    ASSERT_NEAR(c.residual(params), 100.0, 1e-10);
}
```

**验证**：残差 = dx1·dx2 + dy1·dy2（点积）

### 2.3 梯度测试

#### 测试方法：数值微分对比

```cpp
TEST(distance_gradient) {
    std::vector<double> params = {0.0, 0.0, 3.0, 4.0};
    DistanceConstraint c(0, 2, 5.0);

    auto grad = c.gradient(params);
    double eps = 1e-8;
    double f0 = c.residual(params);

    // 与数值微分对比
    for (size_t i = 0; i < params.size(); ++i) {
        std::vector<double> p_plus = params;
        p_plus[i] += eps;
        double numerical = (c.residual(p_plus) - f0) / eps;
        ASSERT_NEAR(grad[i], numerical, 1e-5);
    }
}
```

**验证**：解析梯度与数值梯度误差 < 1e-5

## 3. 集成测试

### 3.1 简单约束系统

#### 测试用例：两点距离

```cpp
TEST(simple_distance) {
    ConstraintSolver solver;

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(1.0, 0.0);

    solver.addDistance(p1, p2, 5.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // p2 应该在距离 p1 为 5 的位置
    auto p2_final = solver.getPoint(p2);
    double dist = p2_final.distanceTo(Point2D(0, 0));
    ASSERT_NEAR(dist, 5.0, 1e-6);
}
```

#### 测试用例：重合点

```cpp
TEST(coincident_points) {
    ConstraintSolver solver;

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(10.0, 10.0);

    solver.addCoincident(p1, p2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto p1_final = solver.getPoint(p1);
    auto p2_final = solver.getPoint(p2);
    ASSERT_NEAR(p1_final.x, p2_final.x, 1e-6);
    ASSERT_NEAR(p1_final.y, p2_final.y, 1e-6);
}
```

### 3.2 线段约束

#### 测试用例：水平线段

```cpp
TEST(horizontal_line) {
    ConstraintSolver solver;

    int line = solver.addLine(0.0, 0.0, 10.0, 5.0);

    solver.addHorizontal(line);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto line_final = solver.getLine(line);
    ASSERT_NEAR(line_final.start.y, line_final.end.y, 1e-6);
}
```

#### 测试用例：垂直线段

```cpp
TEST(vertical_line) {
    ConstraintSolver solver;

    int line = solver.addLine(0.0, 0.0, 5.0, 10.0);

    solver.addVertical(line);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto line_final = solver.getLine(line);
    ASSERT_NEAR(line_final.start.x, line_final.end.x, 1e-6);
}
```

#### 测试用例：平行线段

```cpp
TEST(parallel_lines) {
    ConstraintSolver solver;

    int line1 = solver.addLine(0.0, 0.0, 10.0, 0.0);
    int line2 = solver.addLine(0.0, 5.0, 10.0, 8.0);  // 不平行

    solver.addParallel(line1, line2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // 检查平行：方向向量叉积应为 0
    auto l1 = solver.getLine(line1);
    auto l2 = solver.getLine(line2);
    double dx1 = l1.end.x - l1.start.x;
    double dy1 = l1.end.y - l1.start.y;
    double dx2 = l2.end.x - l2.start.x;
    double dy2 = l2.end.y - l2.start.y;
    double cross = dx1 * dy2 - dy1 * dx2;
    ASSERT_NEAR(cross, 0.0, 1e-4);
}
```

### 3.3 圆约束

#### 测试用例：固定半径

```cpp
TEST(fixed_radius) {
    ConstraintSolver solver;

    int circle = solver.addCircle(5.0, 5.0, 1.0);  // 初始半径 1

    solver.addRadius(circle, 10.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto c = solver.getCircle(circle);
    ASSERT_NEAR(c.radius, 10.0, 1e-6);
}
```

#### 测试用例：同心圆

```cpp
TEST(concentric_circles) {
    ConstraintSolver solver;

    int c1 = solver.addCircle(0.0, 0.0, 5.0);
    int c2 = solver.addCircle(10.0, 10.0, 3.0);  // 不同心

    solver.addConcentric(c1, c2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto circle1 = solver.getCircle(c1);
    auto circle2 = solver.getCircle(c2);

    ASSERT_NEAR(circle1.center.x, circle2.center.x, 1e-4);
    ASSERT_NEAR(circle1.center.y, circle2.center.y, 1e-4);
}
```

### 3.4 复合约束

#### 测试用例：三角形约束

```cpp
TEST(triangle_with_constraints) {
    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 1.0, false});

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(10.0, 0.0);
    int p3 = solver.addPoint(5.0, 8.0);

    // 固定三边长度
    solver.addDistance(p1, p2, 10.0);
    solver.addDistance(p2, p3, 10.0);
    solver.addDistance(p1, p3, 10.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // 验证边长
    auto p1f = solver.getPoint(p1);
    auto p2f = solver.getPoint(p2);
    auto p3f = solver.getPoint(p3);

    ASSERT_NEAR(p1f.distanceTo(p2f), 10.0, 1e-4);
    ASSERT_NEAR(p2f.distanceTo(p3f), 10.0, 1e-4);
    ASSERT_NEAR(p1f.distanceTo(p3f), 10.0, 1e-4);
}
```

#### 测试用例：矩形约束

```cpp
TEST(multiple_constraints) {
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    int l1 = solver.addLine(0.0, 0.0, 10.5, 0.3);  // 底边
    int l2 = solver.addLine(10.5, 0.3, 10.2, 5.8);  // 右边
    int l3 = solver.addLine(10.2, 5.8, 0.3, 5.5);   // 顶边
    int l4 = solver.addLine(0.3, 5.5, 0.0, 0.0);    // 左边

    solver.addHorizontal(l1);
    solver.addVertical(l2);
    solver.addHorizontal(l3);
    solver.addVertical(l4);
    solver.addLength(l1, 10.0);
    solver.addLength(l2, 5.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // 验证几何性质
    auto line1 = solver.getLine(l1);
    auto line2 = solver.getLine(l2);

    ASSERT_NEAR(line1.start.y, line1.end.y, 1e-4);  // 水平
    ASSERT_NEAR(line2.start.x, line2.end.x, 1e-4);  // 垂直
    ASSERT_NEAR(line1.length(), 10.0, 1e-4);          // 宽度
    ASSERT_NEAR(line2.length(), 5.0, 1e-4);           // 高度
}
```

## 4. 边界情况测试

### 4.1 过度约束系统

```cpp
TEST(overconstrained_system) {
    ConstraintSolver solver;

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(1.0, 0.0);

    // 不一致的约束
    solver.addDistance(p1, p2, 5.0);
    solver.addDistance(p1, p2, 10.0);

    auto result = solver.solve();
    // 不应该收敛到零残差
    ASSERT_TRUE(!result.success() || result.residual_norm > 1e-6);
}
```

### 4.2 退化几何

```cpp
TEST(degenerate_line) {
    // 零长度线段
    Line2D line(Point2D(0, 0), Point2D(0, 0));
    Point2D p(5, 5);

    // 应该返回起点
    auto closest = line.closestPointTo(p);
    ASSERT_NEAR(closest.x, 0.0, 1e-10);
    ASSERT_NEAR(closest.y, 0.0, 1e-10);
}
```

## 5. 性能测试

### 5.1 大规模系统

```cpp
TEST(large_system_performance) {
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.8, false});

    // 创建 100 个点的链式约束
    std::vector<int> points;
    for (int i = 0; i < 100; ++i) {
        points.push_back(solver.addPoint(i * 10.0, 0.0));
    }

    // 添加距离约束
    for (int i = 0; i < 99; ++i) {
        solver.addDistance(points[i], points[i + 1], 10.0);
    }

    auto start = std::chrono::high_resolution_clock::now();
    auto result = solver.solve();
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "Solve time: " << duration.count() << " ms" << std::endl;

    ASSERT_TRUE(result.success());
}
```

## 6. 测试运行

### 6.1 编译测试

```bash
cd projects/constraint-solver
mkdir build && cd build
cmake ..
make
```

### 6.2 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
./constraint_tests
./solver_tests

# 运行示例
./basic_example
./cad_sketch
./tangent_demo
```

### 6.3 测试输出示例

```
=== Constraint Tests ===
Running point_distance... PASSED
Running point_operations... PASSED
Running line_angle... PASSED
Running coincident_constraint... PASSED
Running distance_constraint... PASSED
...
15/15 tests passed

=== Solver Tests ===
Running simple_distance... PASSED
Running coincident_points... PASSED
Running horizontal_line... PASSED
...
12/12 tests passed
```

## 7. 测试覆盖率

### 7.1 覆盖的约束类型

- [x] Coincident (重合)
- [x] Distance (距离)
- [x] Horizontal (水平)
- [x] Vertical (垂直)
- [x] Parallel (平行)
- [x] Perpendicular (垂直)
- [x] Angle (角度)
- [x] Radius (半径)
- [x] Concentric (同心)
- [x] Tangent (相切)
- [x] PointOnLine (点在线上)
- [x] PointOnCircle (点在圆上)
- [x] Length (长度)

### 7.2 覆盖的求解场景

- [x] 单约束求解
- [x] 多约束求解
- [x] 过度约束检测
- [x] 收敛性验证
- [x] 梯度正确性

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: |
          mkdir build && cd build
          cmake ..
          make
      - name: Test
        run: |
          cd build
          ctest --output-on-failure
```

### 8.2 测试报告

测试结果以 JUnit XML 格式输出，便于 CI 系统解析。
