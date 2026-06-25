# 光线追踪技术调研

## 1. 光线追踪技术历史

### 1.1 早期发展（1968-1980）

- **1968年**：Arthur Appel 提出光线投射（Ray Casting）算法
- **1971年**：Goldstein 和 Nagel 提出光线追踪概念
- **1979年**：Turner Whitted 提出递归光线追踪算法，成为现代光线追踪的基础

### 1.2 经典时期（1980-2000）

- **1984年**：Cook 提出分布式光线追踪（Distributed Ray Tracing），支持软阴影、景深、运动模糊
- **1986年**：Kajiya 提出渲染方程（Rendering Equation），统一了各种渲染算法
- **1993年**：Veach 提出双向路径追踪（Bidirectional Path Tracing）
- **1997年**：Veach 和 Guibas 提出 Metropolis 光传输（MLT）

### 1.3 现代发展（2000-至今）

- **2002年**：Jensen 提出光子映射（Photon Mapping）
- **2003年**：Pharr 和 Humphreys 出版《Physically Based Rendering》
- **2009年**：NVIDIA 推出 OptiX 光线追踪引擎
- **2018年**：NVIDIA RTX 系列 GPU 支持硬件光线追踪
- **2020年**：DirectX Raytracing (DXR) 和 Vulkan Ray Tracing 成为标准

## 2. 光线追踪原理

### 2.1 基本概念

光线追踪是一种基于物理的渲染算法，模拟光线在场景中的传播。基本思想是：

1. 从相机发射光线穿过每个像素
2. 计算光线与场景中物体的交点
3. 在交点处计算光照和材质效果
4. 递归追踪反射和折射光线

### 2.2 渲染方程

渲染方程描述了光线在场景中的传播：

```
Lo(x, wo) = Le(x, wo) + ∫ fr(x, wi, wo) Li(x, wi) (wi · n) dwi
```

其中：
- `Lo(x, wo)`：从点 x 沿方向 wo 出射的光线
- `Le(x, wo)`：点 x 自身发射的光线
- `fr(x, wi, wo)`：双向反射分布函数（BRDF）
- `Li(x, wi)`：从方向 wi 入射的光线
- `(wi · n)`：入射角余弦

### 2.3 光线-物体相交

#### 光线-球体相交

球体方程：`(p - c)² = r²`
光线方程：`p(t) = o + t·d`

代入求解二次方程：
```
a·t² + 2b·t + c = 0
其中：
a = d·d
b = (o - c)·d
c = (o - c)·(o - c) - r²
```

#### 光线-三角形相交

使用 Moller-Trumbore 算法：
```
t = (edge2 · q) / (edge1 · p)
其中：
edge1 = v1 - v0
edge2 = v2 - v0
p = d × edge2
a = edge1 · p
```

#### 光线-平面相交

平面方程：`(p - p0) · n = 0`
光线方程：`p(t) = o + t·d`

求解：
```
t = (p0 - o) · n / (d · n)
```

## 3. 材质模型

### 3.1 Lambertian 漫反射

最简单的材质模型，光线在表面随机散射：
```
fr(wi, wo) = albedo / π
```

### 3.2 金属反射

镜面反射，支持模糊：
```
fr(wi, wo) = reflect(wi, n) + fuzz * random()
```

### 3.3 电介质折射

使用 Snell 定律和 Schlick 近似：
```
n1 * sin(θ1) = n2 * sin(θ2)
R(θ) = R0 + (1 - R0) * (1 - cos(θ))^5
```

### 3.4 微表面模型

PBR 材质的基础：
```
fr(wi, wo) = D(h) * G(wi, wo) * F(wo · h) / (4 * (wi · n) * (wo · n))
```

其中：
- D(h)：法线分布函数
- G(wi, wo)：几何遮蔽函数
- F(wo · h)：菲涅尔函数

## 4. 加速结构

### 4.1 包围盒层次结构（BVH）

将物体组织成树形结构，每个节点有一个包围盒：
- 构建时间：O(n log n)
- 查询时间：O(log n)
- 内存使用：O(n)

### 4.2 KD-Tree

空间分割结构，递归地将空间分成两半：
- 构建时间：O(n log n)
- 查询时间：O(log n)
- 适合静态场景

### 4.3 八叉树

将空间递归分成 8 个子空间：
- 构建时间：O(n)
- 查询时间：O(log n)
- 适合均匀分布的场景

### 4.4 均匀网格

将空间分成规则的网格：
- 构建时间：O(n)
- 查询时间：O(1)
- 适合均匀分布的场景

## 5. 渲染算法

### 5.1 路径追踪（Path Tracing）

从相机发射光线，在交点处随机选择方向继续追踪：
- 优点：简单、物理准确
- 缺点：收敛慢、噪声大

### 5.2 双向路径追踪（Bidirectional Path Tracing）

同时从相机和光源发射光线，然后连接：
- 优点：对某些场景（如焦散）更高效
- 缺点：实现复杂

### 5.3 Metropolis 光传输（MLT）

使用 Metropolis-Hastings 算法采样路径空间：
- 优点：对复杂光路（如焦散）高效
- 缺点：难以并行化

### 5.4 光子映射（Photon Mapping）

从光源发射光子，存储在光子图中：
- 优点：高效渲染焦散
- 缺点：需要额外存储

### 5.5 辐射度（Radiosity）

计算表面之间的能量交换：
- 优点：适合漫反射场景
- 缺点：不支持镜面反射

## 6. 应用场景

### 6.1 电影和动画

- 皮克斯、梦工厂等使用光线追踪渲染动画电影
- 用于全局光照、软阴影、景深等效果

### 6.2 游戏

- NVIDIA RTX 支持实时光线追踪
- 用于反射、阴影、全局光照

### 6.3 建筑可视化

- 用于真实的光照模拟
- 支持材质和光照设计

### 6.4 产品设计

- 用于产品渲染和可视化
- 支持材质和光照测试

### 6.5 科学可视化

- 用于体积渲染（如医学图像）
- 支持复杂光照效果

## 7. 优缺点分析

### 7.1 优点

1. **物理准确**：基于物理的渲染，结果真实
2. **统一框架**：可以处理各种光照效果
3. **简单实现**：核心算法简单易懂
4. **可扩展性**：容易添加新效果

### 7.2 缺点

1. **计算密集**：需要大量计算资源
2. **收敛慢**：需要大量采样才能减少噪声
3. **难以实时**：传统上难以实时渲染
4. **内存消耗**：需要存储场景和加速结构

## 8. 发展趋势

### 8.1 硬件加速

- NVIDIA RTX 系列 GPU
- 专用光线追踪硬件
- 实时光线追踪成为可能

### 8.2 混合渲染

- 光线追踪 + 光栅化
- 选择性使用光线追踪效果
- 平衡质量和性能

### 8.3 降噪技术

- AI 降噪（如 NVIDIA OptiX AI Denoiser）
- 时间累积
- 空间滤波

### 8.4 实时光线追踪

- 游戏引擎支持（如 Unreal Engine、Unity）
- 有限效果（如反射、阴影）
- 混合渲染管线

## 9. 学习资源

### 9.1 书籍

- [Ray Tracing in One Weekend](https://raytracing.github.io/) - 入门书籍
- [Physically Based Rendering](http://www.pbr-book.org/) - 进阶书籍
- [Ray Tracing from the Ground Up](https://www.amazon.com/Ray-Tracing-Ground-Up-Kevin/dp/1568812728) - 综合书籍

### 9.2 在线资源

- [Scratchapixel](https://www.scratchapixel.com/) - 详细教程
- [smallpt](http://www.kevinbeason.com/smallpt/) - 99 行代码的光线追踪器
- [NVIDIA OptiX](https://developer.nvidia.com/optix) - 光线追踪引擎

### 9.3 开源项目

- [PBRT](https://github.com/mmp/pbrt-v3) - 物理渲染器
- [Mitsuba](https://github.com/mitsuba-renderer/mitsuba) - 研究渲染器
- [LuxCoreRender](https://github.com/LuxCoreRender/LuxCore) - 生产渲染器

## 10. 总结

光线追踪是一种强大的渲染技术，能够产生物理准确的图像。虽然计算密集，但随着硬件加速和算法优化，实时光线追踪已经成为可能。学习光线追踪不仅有助于理解计算机图形学，还能为游戏开发、电影制作等领域打下基础。
