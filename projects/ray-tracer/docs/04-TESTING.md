# 04-TESTING.md - 光线追踪渲染器测试文档

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**：测试各个组件的正确性
2. **集成测试**：测试组件间的协作
3. **可视化测试**：渲染测试图像，人工验证

### 1.2 测试覆盖

- Vec3 运算
- Ray 构造和求值
- 光线-球体求交
- 光线-平面求交
- 材质散射
- 颜色计算
- 渲染输出

## 2. 单元测试

### 2.1 Vec3 测试

**文件**：`tests/test_vec3.cpp`

**测试用例**：

1. **构造函数测试**
   - 默认构造：x=0, y=0, z=0
   - 参数构造：正确设置 x, y, z

2. **加法测试**
   - (1,2,3) + (4,5,6) = (5,7,9)

3. **减法测试**
   - (4,5,6) - (1,2,3) = (3,3,3)

4. **标量乘法测试**
   - (1,2,3) * 2 = (2,4,6)
   - 3 * (1,2,3) = (3,6,9)

5. **点积测试**
   - (1,2,3) · (4,5,6) = 32

6. **叉积测试**
   - (1,0,0) × (0,1,0) = (0,0,1)

7. **长度测试**
   - (3,4,0) 的长度为 5
   - (3,4,0) 的长度平方为 25

8. **单位化测试**
   - (3,4,0) 单位化后长度为 1
   - 零向量单位化返回零向量

9. **反射测试**
   - (1,-1,0) 关于 (0,1,0) 的反射为 (1,1,0)

**运行测试**：
```bash
cd build
./test_vec3
```

**预期输出**：
```
Running Vec3 tests...
  [PASS] Constructor
  [PASS] Addition
  [PASS] Subtraction
  [PASS] Scalar Multiplication
  [PASS] Dot Product
  [PASS] Cross Product
  [PASS] Length
  [PASS] Normalize
  [PASS] Reflect
All Vec3 tests passed!
```

### 2.2 Ray 测试

**文件**：`tests/test_ray.cpp`

**测试用例**：

1. **构造函数测试**
   - 起点正确设置
   - 方向自动单位化

2. **at() 方法测试**
   - at(0) 返回起点
   - at(5) 返回正确点
   - at(-3) 返回反向点

3. **对角线方向测试**
   - 方向 (1,1,0) 单位化后长度为 1
   - at(sqrt(2)) 返回 (1,1,0)

**运行测试**：
```bash
./test_ray
```

**预期输出**：
```
Running Ray tests...
  [PASS] Constructor
  [PASS] At
  [PASS] Diagonal Direction
All Ray tests passed!
```

### 2.3 Sphere 测试

**文件**：`tests/test_sphere.cpp`

**测试用例**：

1. **球体命中测试**
   - 光线指向球体，应命中
   - 命中点在球体表面

2. **球体未命中测试**
   - 光线偏离球体，不应命中

3. **法线方向测试**
   - 正面命中，法线朝外
   - 法线 z 分量为正

4. **内部命中测试**
   - 光线从球体内部发射
   - front_face 为 false

5. **切线命中测试**
   - 光线刚好切过球体
   - 应该命中

6. **平面命中测试**
   - 光线从上往下打到平面
   - 应该命中

7. **平面平行测试**
   - 光线平行于平面
   - 不应命中

**运行测试**：
```bash
./test_sphere
```

**预期输出**：
```
Running Sphere tests...
  [PASS] Sphere Hit
  [PASS] Sphere Miss
  [PASS] Sphere Normal
  [PASS] Sphere Inside
  [PASS] Sphere Tangent
  [PASS] Plane Hit
  [PASS] Plane Miss Parallel
All Sphere tests passed!
```

### 2.4 Renderer 测试

**文件**：`tests/test_renderer.cpp`

**测试用例**：

1. **背景颜色测试**
   - 向上发射光线
   - 应该得到天空颜色

2. **物体颜色测试**
   - 向红色球体发射光线
   - 应该有红色分量

3. **深度限制测试**
   - 深度为 0 时返回黑色

4. **缓冲区渲染测试**
   - 检查缓冲区大小
   - 检查颜色值范围

**运行测试**：
```bash
./test_renderer
```

**预期输出**：
```
Running Renderer tests...
  [PASS] Ray Color Background
  [PASS] Ray Color Object
  [PASS] Ray Color Max Depth
  [PASS] Render To Buffer
All Renderer tests passed!
```

## 3. 集成测试

### 3.1 完整渲染测试

**测试方法**：
1. 渲染一个简单场景
2. 检查输出文件是否存在
3. 检查文件格式是否正确

**运行测试**：
```bash
./ray-tracer --scene test --output test_output.ppm
```

**验证方法**：
- 文件存在
- 文件头为 "P3"
- 文件大小合理

### 3.2 场景工厂测试

**测试方法**：
1. 创建各种场景
2. 检查物体数量

## 4. 可视化测试

### 4.1 默认场景

**渲染命令**：
```bash
./ray-tracer --scene default --output default.ppm
```

**预期效果**：
- 三个球体（蓝色漫反射、金属、玻璃）
- 灰色地面
- 天空渐变背景
- 金属球有模糊反射
- 玻璃球有折射效果

### 4.2 复杂场景

**渲染命令**：
```bash
./ray-tracer --scene complex --output complex.ppm
```

**预期效果**：
- 多个随机球体
- 不同材质（漫反射、金属、玻璃）
- 地面反射

### 4.3 测试场景

**渲染命令**：
```bash
./ray-tracer --scene test --output test.ppm
```

**预期效果**：
- 两个红色和蓝色球体
- 简单背景

## 5. 测试自动化

### 5.1 CTest 集成

在 CMakeLists.txt 中添加测试：
```cmake
enable_testing()
add_test(NAME test_vec3 COMMAND test_vec3)
add_test(NAME test_ray COMMAND test_ray)
add_test(NAME test_sphere COMMAND test_sphere)
add_test(NAME test_renderer COMMAND test_renderer)
```

运行所有测试：
```bash
cd build
ctest
```

### 5.2 持续集成

可以在 CI 中运行：
```bash
mkdir build && cd build
cmake ..
make
ctest --output-on-failure
```

## 6. 测试覆盖率

### 6.1 覆盖的组件

- [x] Vec3 运算
- [x] Ray 构造和求值
- [x] Sphere 求交
- [x] Plane 求交
- [x] HitableList 遍历
- [x] Lambertian 材质
- [x] Metal 材质
- [x] Dielectric 材质
- [x] Camera 光线生成
- [x] Renderer 颜色计算
- [x] 场景工厂

### 6.2 未覆盖的部分

- [ ] 边界情况（极小/极大值）
- [ ] 性能测试
- [ ] 内存泄漏测试
- [ ] 并发测试

## 7. 测试最佳实践

1. **测试命名清晰**：使用描述性的测试名称
2. **测试独立**：每个测试独立运行
3. **测试可重复**：使用固定种子保证可重复性
4. **测试快速**：单元测试应该快速运行
5. **测试覆盖**：覆盖正常路径和边界情况

## 8. 调试技巧

### 8.1 可视化调试

- 渲染小图像快速验证
- 使用测试场景隔离问题

### 8.2 数值调试

- 打印中间值
- 使用 epsilon 比较浮点数

### 8.3 常见问题

- 自相交：使用 t_min 避免
- 数值溢出：检查除法
- 递归过深：设置深度限制
