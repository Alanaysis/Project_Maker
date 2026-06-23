# LEARNING_NOTES.md - 光线追踪渲染器学习笔记

## 学习目标回顾

1. 理解光线追踪算法
2. 掌握光线-物体求交
3. 学会材质和光照模型

---

## 第一阶段：理论学习

### 1.1 光线追踪基础

**什么是光线追踪？**

光线追踪是一种通过模拟光线传播来生成图像的渲染技术。基本思想是：

1. 从相机发射光线穿过每个像素
2. 计算光线与场景中物体的交点
3. 根据材质和光照计算交点颜色
4. 递归处理反射和折射光线

**与光栅化的区别**

| 特性 | 光栅化 | 光线追踪 |
|------|--------|----------|
| 速度 | 快 | 慢 |
| 全局光照 | 难 | 易 |
| 阴影 | 需要额外处理 | 自然实现 |
| 反射/折射 | 需要额外处理 | 自然实现 |
| 质量 | 中等 | 高 |

**核心方程**

光线方程：`P(t) = O + t * D`

- P(t)：光线上参数为 t 的点
- O：起点（origin）
- D：方向（direction）
- t：参数

### 1.2 光线-球体求交

**数学推导**

给定球心 C，半径 r，光线 P(t) = O + tD：

```
|P(t) - C|² = r²
|(O + tD) - C|² = r²
|(O - C) + tD|² = r²
(O - C)·(O - C) + 2t(O - C)·D + t²D·D = r²
```

令：
- a = D·D
- b = 2D·(O - C)
- c = (O - C)·(O - C) - r²

得到二次方程：`at² + bt + c = 0`

解：`t = (-b ± sqrt(b² - 4ac)) / 2a`

**判别式分析**

- discriminant > 0：两个交点（光线穿过球体）
- discriminant = 0：一个交点（光线切过球体）
- discriminant < 0：无交点（光线未命中）

**实现要点**

```cpp
double discriminant = half_b * half_b - a * c;
if (discriminant < 0) return false;

double sqrtd = std::sqrt(discriminant);
double root = (-half_b - sqrtd) / a;

if (root < t_min || t_max < root) {
    root = (-half_b + sqrtd) / a;
    if (root < t_min || t_max < root) return false;
}
```

### 1.3 光线-平面求交

**数学推导**

给定平面上一点 P₀，法线 N，光线 P(t) = O + tD：

平面方程：`(P - P₀)·N = 0`

代入光线方程：`((O + tD) - P₀)·N = 0`

解得：`t = (P₀ - O)·N / (D·N)`

**特殊情况**

- D·N = 0：光线平行于平面
- t < 0：交点在光线起点后面

---

## 第二阶段：材质模型

### 2.1 Lambertian（漫反射）

**原理**

Lambertian 材质是最简单的材质模型，假设光线在交点处随机散射。

**数学模型**

散射方向 = 法线 + 随机单位向量

颜色 = 反照率 × 入射光颜色

**实现**

```cpp
class Lambertian : public Material {
    Vec3 albedo;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const {
        Vec3 scatter_direction = rec.normal + random_unit_vector();
        scattered = Ray(rec.point, scatter_direction);
        attenuation = albedo;
        return true;
    }
};
```

**学习要点**

- 反照率（albedo）表示材质的颜色
- 随机散射方向在法线半球内
- 需要处理退化情况（散射方向为零向量）

### 2.2 Metal（金属）

**原理**

金属材质按反射定律反射光线，可以添加模糊度模拟粗糙表面。

**数学模型**

反射方向 = 入射方向 - 2(入射方向·法线)法线

**实现**

```cpp
class Metal : public Material {
    Vec3 albedo;
    double fuzz;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const {
        Vec3 reflected = ray_in.direction.reflect(rec.normal);
        scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
        attenuation = albedo;
        return scattered.direction.dot(rec.normal) > 0;
    }
};
```

**学习要点**

- 反射公式：`R = D - 2(D·N)N`
- 模糊度（fuzz）控制反射的模糊程度
- 需要检查反射方向是否在法线半球内

### 2.3 Dielectric（电介质）

**原理**

电介质材质（玻璃、水等）会折射光线，使用 Snell 定律计算折射方向。

**Snell 定律**

`η₁ sin θ₁ = η₂ sin θ₂`

其中：
- η₁, η₂：两种介质的折射率
- θ₁, θ₂：入射角和折射角

**全内反射**

当光线从高折射率介质进入低折射率介质时，如果入射角大于临界角，会发生全内反射。

**Schlick 近似**

计算反射率的近似公式：

```
R(θ) = R₀ + (1 - R₀)(1 - cos θ)⁵
R₀ = ((η₁ - η₂)/(η₁ + η₂))²
```

**实现**

```cpp
class Dielectric : public Material {
    double ir;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const {
        attenuation = Vec3(1.0, 1.0, 1.0);
        double refraction_ratio = rec.front_face ? (1.0 / ir) : ir;

        Vec3 unit_direction = ray_in.direction.normalize();
        double cos_theta = std::fmin((-unit_direction).dot(rec.normal), 1.0);
        double sin_theta = std::sqrt(1.0 - cos_theta * cos_theta);

        bool cannot_refract = refraction_ratio * sin_theta > 1.0;
        Vec3 direction;

        if (cannot_refract || reflectance(cos_theta, refraction_ratio) > random_double()) {
            direction = unit_direction.reflect(rec.normal);
        } else {
            direction = unit_direction.refract(rec.normal, refraction_ratio);
        }

        scattered = Ray(rec.point, direction);
        return true;
    }
};
```

**学习要点**

- 折射率（ir）表示材质的折射率
- 全内反射的判断
- Schlick 近似用于计算反射率
- 需要处理正面和背面

---

## 第三阶段：相机系统

### 3.1 相机坐标系

**坐标系定义**

- w：从相机位置指向观察点
- u：右方向（vup × w）
- v：上方向（w × u）

**实现**

```cpp
w = (lookfrom - lookat).normalize();
u = vup.cross(w).normalize();
v = w.cross(u);
```

### 3.2 视角（FOV）

**数学模型**

视角决定可见范围：

```
viewport_height = 2 * tan(fov/2)
viewport_width = aspect_ratio * viewport_height
```

**实现**

```cpp
double theta = vfov * M_PI / 180.0;
double h = std::tan(theta / 2.0);
double viewport_height = 2.0 * h;
double viewport_width = aspect_ratio * viewport_height;
```

### 3.3 景深

**原理**

景深效果模拟真实相机的光圈：

- 光圈越大，景深越浅
- 焦距决定清晰范围

**实现**

```cpp
Ray get_ray(double s, double t) const {
    Vec3 rd = random_in_unit_disk() * lens_radius;
    Vec3 offset = u * rd.x + v * rd.y;

    return Ray(
        origin + offset,
        lower_left_corner + horizontal * s + vertical * t - origin - offset
    );
}
```

---

## 第四阶段：渲染技术

### 4.1 多重采样抗锯齿

**原理**

对每个像素多次采样，取平均值作为最终颜色。

**实现**

```cpp
Color pixel_color(0, 0, 0);
for (int s = 0; s < samples_per_pixel; ++s) {
    double u = (i + random_double()) / width;
    double v = (j + random_double()) / height;
    Ray ray = camera.get_ray(u, v);
    pixel_color += ray_color(ray, max_depth);
}
pixel_color /= samples_per_pixel;
```

**学习要点**

- 采样数越多，图像越平滑
- 随机采样可以减少规律性锯齿
- 计算量与采样数成正比

### 4.2 伽马校正

**原理**

显示器使用伽马空间，需要将线性颜色转换为伽马空间。

**简单伽马校正**

`c' = sqrt(c)`

**实现**

```cpp
double linear_to_gamma(double linear) {
    if (linear > 0) return std::sqrt(linear);
    return 0;
}
```

### 4.3 PPM 格式

**格式说明**

```
P3
width height
max_color
r g b
r g b
...
```

**实现**

```cpp
file << "P3\n" << width << " " << height << "\n255\n";
for (int j = height - 1; j >= 0; --j) {
    for (int i = 0; i < width; ++i) {
        int r = color_to_int(pixel_color.x);
        int g = color_to_int(pixel_color.y);
        int b = color_to_int(pixel_color.z);
        file << r << " " << g << " " << b << "\n";
    }
}
```

---

## 第五阶段：调试经验

### 5.1 自相交问题

**问题**

光线命中物体后，反射光线可能再次命中同一物体。

**解决**

使用 t_min = 0.001，忽略太近的交点。

```cpp
if (world->hit(ray, 0.001, infinity, rec)) {
    // ...
}
```

### 5.2 数值溢出

**问题**

除以零或极小值导致数值溢出。

**解决**

检查分母，使用 epsilon。

```cpp
if (std::fabs(denom) < 1e-10) return false;
```

### 5.3 递归过深

**问题**

递归过深导致栈溢出。

**解决**

设置最大递归深度。

```cpp
if (depth <= 0) return Color(0, 0, 0);
```

### 5.4 颜色溢出

**问题**

颜色值超出 [0, 1] 范围。

**解决**

使用 std::clamp。

```cpp
c = std::clamp(c, 0.0, 0.999);
```

---

## 学习总结

### 核心收获

1. **光线追踪算法**
   - 理解了光线追踪的基本原理
   - 掌握了光线-物体求交算法
   - 学会了递归光线追踪

2. **几何数学**
   - 掌握了向量运算
   - 理解了点积和叉积的几何意义
   - 学会了光线-球体和平面求交

3. **材质模型**
   - 理解了 Lambertian 漫反射
   - 理解了金属反射
   - 理解了电介质折射

4. **相机系统**
   - 理解了相机坐标系
   - 学会了视角和景深控制

5. **渲染技术**
   - 掌握了多重采样抗锯齿
   - 理解了伽马校正
   - 学会了 PPM 格式输出

### 难点和解决方案

1. **难点**：光线-球体求交的数学推导
   - **解决**：通过二次方程求解，理解判别式的几何意义

2. **难点**：电介质材质的折射计算
   - **解决**：理解 Snell 定律和全内反射

3. **难点**：自相交问题
   - **解决**：使用 t_min 避免

4. **难点**：数值稳定性
   - **解决**：使用 epsilon 和边界检查

### 未来学习方向

1. **空间划分**
   - BVH（Bounding Volume Hierarchy）
   - KD-Tree

2. **并行渲染**
   - 多线程
   - GPU 加速

3. **高级材质**
   - 纹理映射
   - 次表面散射
   - 各向异性

4. **全局光照**
   - 路径追踪
   - 光子映射
   - 辐射度

### 推荐资源

1. **书籍**
   - "Ray Tracing in One Weekend" - Peter Shirley
   - "Fundamentals of Computer Graphics" - Marschner & Shirley

2. **网站**
   - raytracing.github.io
   - Scratchapixel

3. **开源项目**
   - smallpt
   - pbrt

---

## 代码片段速查

### 向量反射

```cpp
Vec3 reflect(const Vec3& normal) const {
    return *this - normal * 2.0 * this->dot(normal);
}
```

### 向量折射

```cpp
Vec3 refract(const Vec3& normal, double eta_ratio) const {
    double cos_theta = std::fmin((-(*this)).dot(normal), 1.0);
    Vec3 r_out_perp = (*this + normal * cos_theta) * eta_ratio;
    Vec3 r_out_parallel = normal * (-std::sqrt(std::fabs(1.0 - r_out_perp.length_squared())));
    return r_out_perp + r_out_parallel;
}
```

### 光线-球体求交

```cpp
double discriminant = half_b * half_b - a * c;
if (discriminant < 0) return false;

double sqrtd = std::sqrt(discriminant);
double root = (-half_b - sqrtd) / a;

if (root < t_min || t_max < root) {
    root = (-half_b + sqrtd) / a;
    if (root < t_min || t_max < root) return false;
}
```

### Schlick 近似

```cpp
double reflectance(double cosine, double ref_idx) {
    auto r0 = (1 - ref_idx) / (1 + ref_idx);
    r0 = r0 * r0;
    return r0 + (1 - r0) * std::pow((1 - cosine), 5);
}
```

### 颜色计算

```cpp
Color ray_color(const Ray& ray, int depth) {
    if (depth <= 0) return Color(0, 0, 0);

    HitRecord rec;
    if (world->hit(ray, 0.001, infinity, rec)) {
        Ray scattered;
        Vec3 attenuation;
        if (rec.material->scatter(ray, rec, attenuation, scattered)) {
            return attenuation * ray_color(scattered, depth - 1);
        }
        return Color(0, 0, 0);
    }

    // 背景渐变
    Vec3 unit = ray.direction.normalize();
    double t = 0.5 * (unit.y + 1.0);
    return Color(1, 1, 1) * (1 - t) + Color(0.5, 0.7, 1) * t;
}
```

---

*学习日期：2026-06-22*
*学习时长：约 4 小时*
*完成状态：已完成*
