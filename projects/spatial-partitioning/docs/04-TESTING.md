# 空间划分算法测试指南

## 1. 测试策略

### 测试层次

1. **单元测试**：测试各个算法的基本功能
2. **集成测试**：测试算法组合使用
3. **性能测试**：测试算法性能

### 测试覆盖

- 功能测试：验证算法正确性
- 边界测试：测试边界条件
- 性能测试：验证性能指标

## 2. 单元测试

### AABB 测试

```cpp
TEST(AABBTest, Intersection) {
    AABB a({0,0,0}, {1,1,1});
    AABB b({0.5,0.5,0.5}, {1.5,1.5,1.5});
    AABB c({2,2,2}, {3,3,3});
    
    EXPECT_TRUE(a.intersects(b));
    EXPECT_FALSE(a.intersects(c));
}

TEST(AABBTest, SurfaceArea) {
    AABB box({0,0,0}, {1,1,1});
    EXPECT_FLOAT_EQ(box.surfaceArea(), 6.0f);
}
```

### BVH 测试

```cpp
TEST(BVHTest, BuildAndQuery) {
    BVH bvh;
    
    // 添加物体
    for (int i = 0; i < 100; i++) {
        float x = i * 2.0f;
        bvh.addObject(AABB({x, 0, 0}, {x+1, 1, 1}));
    }
    
    bvh.build();
    
    // 查询
    std::vector<int> results;
    bvh.query(AABB({5, 0, 0}, {10, 1, 1}), results);
    
    EXPECT_FALSE(results.empty());
}

TEST(BVHTest, RayCast) {
    BVH bvh;
    bvh.addObject(AABB({0,0,0}, {1,1,1}));
    bvh.build();
    
    Ray ray({-1, 0.5, 0.5}, {1, 0, 0});
    auto results = bvh.rayCast(ray);
    
    EXPECT_FALSE(results.empty());
}
```

### Octree 测试

```cpp
TEST(OctreeTest, InsertAndQuery) {
    Octree octree(AABB({-100,-100,-100}, {100,100,100}));
    
    // 添加物体
    for (int i = 0; i < 1000; i++) {
        float x = (rand() % 200) - 100;
        float y = (rand() % 200) - 100;
        float z = (rand() % 200) - 100;
        octree.addObject(AABB({x,y,z}, {x+1,y+1,z+1}));
    }
    
    // 查询
    std::vector<int> results;
    octree.query(AABB({-10,-10,-10}, {10,10,10}), results);
    
    EXPECT_GT(results.size(), 0);
}
```

### BSP 测试

```cpp
TEST(BSPTest, BuildAndQuery) {
    BSP bsp;
    
    // 添加三角形
    bsp.addTriangle({{0,0,0}, {1,0,0}, {0,1,0}});
    bsp.addTriangle({{1,0,0}, {1,1,0}, {0,1,0}});
    
    bsp.build();
    
    // 查询
    std::vector<int> results;
    bsp.query(AABB({0,0,-1}, {1,1,1}), results);
    
    EXPECT_EQ(results.size(), 2);
}
```

## 3. 集成测试

### 碰撞检测系统测试

```cpp
TEST(CollisionSystemTest, FullPipeline) {
    CollisionSystem system;
    
    // 添加物体
    for (int i = 0; i < 100; i++) {
        float x = i * 3.0f;
        system.addObject(AABB({x,0,0}, {x+2,2,2}));
    }
    
    // 添加一些重叠的物体
    system.addObject(AABB({5,0,0}, {7,2,2}));
    system.addObject(AABB({6,0,0}, {8,2,2}));
    
    // 检测碰撞
    auto pairs = system.detectCollisions();
    
    EXPECT_GT(pairs.size(), 0);
}
```

## 4. 性能测试

### 构建性能

```cpp
TEST(PerformanceTest, BVHBuildTime) {
    auto start = std::chrono::high_resolution_clock::now();
    
    BVH bvh;
    for (int i = 0; i < 100000; i++) {
        float x = (rand() % 1000) - 500;
        float y = (rand() % 1000) - 500;
        float z = (rand() % 1000) - 500;
        bvh.addObject(AABB({x,y,z}, {x+1,y+1,z+1}));
    }
    bvh.build();
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << "BVH build time: " << duration.count() << " ms" << std::endl;
    EXPECT_LT(duration.count(), 1000);  // 应该在 1 秒内完成
}
```

### 查询性能

```cpp
TEST(PerformanceTest, QueryTime) {
    BVH bvh;
    // 添加 100000 个物体
    // ...
    
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int i = 0; i < 10000; i++) {
        std::vector<int> results;
        bvh.query(AABB({-10,-10,-10}, {10,10,10}), results);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << "10000 queries time: " << duration.count() << " ms" << std::endl;
    EXPECT_LT(duration.count(), 100);  // 10000 次查询应该在 100ms 内完成
}
```

## 5. 测试运行

### 使用 CMake

```bash
mkdir build && cd build
cmake .. -DBUILD_TESTS=ON
make
./tests/spatial_tests
```

### 使用 CTest

```bash
cd build
ctest --output-on-failure
```

## 6. 测试覆盖率

```bash
# 使用 gcov
g++ -fprofile-arcs -ftest-coverage -o tests tests.cpp
./tests
gcov tests.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

## 7. 常见问题

### 浮点精度问题

```cpp
// 使用 epsilon 比较
EXPECT_NEAR(a, b, 1e-6f);
```

### 边界条件

```cpp
// 测试空场景
BVH bvh;
bvh.build();  // 不应该崩溃

// 测试单个物体
bvh.addObject(AABB({0,0,0}, {1,1,1}));
bvh.build();
```
