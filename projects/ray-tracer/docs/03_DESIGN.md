# 技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Examples)                     │
├─────────────────────────────────────────────────────────┤
│                    渲染层 (Renderer)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ PathTrace│  │BiDirPT   │  │PhotonMap │  │ Basic   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────┤
│                    核心层 (Core)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Material │  │  Light   │  │ Texture  │  │ Camera  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────┤
│                    几何层 (Geometry)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Sphere  │  │ Triangle │  │   Box    │  │Cylinder │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────┤
│                    基础层 (Foundation)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │   Vec3   │  │   Ray    │  │ Hitable  │  │  AABB   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖

```
Vec3 ◄─── Ray ◄─── Hitable ◄─── Sphere/Triangle/Box/Cylinder
  │                                │
  │                                ▼
  │                           Material
  │                                │
  ▼                                ▼
Camera ◄──────────────────── Renderer
  │                                │
  │                                ▼
  └──────────────────────────► Light/Texture
```

## 2. 核心类设计

### 2.1 Vec3 向量类

```cpp
class Vec3 {
public:
    double x, y, z;

    // 基本运算
    Vec3 operator+(const Vec3& v) const;
    Vec3 operator-(const Vec3& v) const;
    Vec3 operator*(double t) const;
    Vec3 operator/(double t) const;

    // 向量运算
    double dot(const Vec3& v) const;      // 点积
    Vec3 cross(const Vec3& v) const;      // 叉积
    double length() const;                 // 长度
    Vec3 normalize() const;                // 单位化

    // 反射和折射
    Vec3 reflect(const Vec3& normal) const;
    Vec3 refract(const Vec3& normal, double eta) const;
};
```

**设计要点**：
- 使用 `double` 精度
- 支持链式运算
- 提供反射和折射方法

### 2.2 Ray 光线类

```cpp
class Ray {
public:
    Vec3 origin;      // 起点
    Vec3 direction;   // 方向（单位向量）

    Vec3 at(double t) const;  // 计算光线上某点
};
```

**设计要点**：
- 方向自动单位化
- 提供参数化方法

### 2.3 Hitable 可命中物体接口

```cpp
class Hitable {
public:
    virtual bool hit(const Ray& ray, double t_min, double t_max,
                     HitRecord& rec) const = 0;
};

struct HitRecord {
    Vec3 point;       // 命中点
    Vec3 normal;      // 法线
    double t;         // 光线参数
    bool front_face;  // 是否正面
    shared_ptr<Material> material;

    void set_face_normal(const Ray& ray, const Vec3& outward_normal);
};
```

**设计要点**：
- 使用虚函数实现多态
- HitRecord 存储命中信息
- 支持正面/背面判断

### 2.4 Material 材质接口

```cpp
class Material {
public:
    virtual bool scatter(const Ray& ray_in, const HitRecord& rec,
                         Vec3& attenuation, Ray& scattered) const = 0;
};
```

**设计要点**：
- 策略模式实现不同材质
- 返回散射光线和衰减系数
- 支持递归追踪

### 2.5 Camera 相机类

```cpp
class Camera {
public:
    Vec3 origin;
    Vec3 lower_left_corner;
    Vec3 horizontal, vertical;
    Vec3 u, v, w;  // 相机坐标系
    double lens_radius;

    Ray get_ray(double s, double t) const;
};
```

**设计要点**：
- 支持视角（FOV）控制
- 支持景深效果
- 使用相机坐标系

## 3. 几何体设计

### 3.1 Sphere 球体

```cpp
class Sphere : public Hitable {
    Vec3 center;
    double radius;
    shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override;
};
```

**相交算法**：
```
a·t² + 2b·t + c = 0
其中：
a = d·d
b = (o - c)·d
c = (o - c)·(o - c) - r²
```

### 3.2 Triangle 三角形

```cpp
class Triangle : public Hitable {
    Vec3 v0, v1, v2;  // 三个顶点
    Vec3 normal;       // 预计算法线
    shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override;
};
```

**相交算法**：Moller-Trumbore 算法
```
t = (edge2 · q) / (edge1 · p)
其中：
edge1 = v1 - v0
edge2 = v2 - v0
p = d × edge2
a = edge1 · p
```

### 3.3 AABB 轴对齐包围盒

```cpp
class AABB : public Hitable {
    Vec3 min_point, max_point;
    shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override;
};
```

**相交算法**：Slab 方法
```
对每个轴：
t0 = (min - origin) / direction
t1 = (max - origin) / direction
tmin = max(tmin, t0)
tmax = min(tmax, t1)
如果 tmin > tmax，则不相交
```

### 3.4 Cylinder 圆柱体

```cpp
class Cylinder : public Hitable {
    Vec3 center;
    double radius, height;
    shared_ptr<Material> material;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override;
};
```

**相交算法**：
- 侧面：类似球体，但忽略 Y 分量
- 底面/顶面：平面相交 + 圆内判断

## 4. 材质系统设计

### 4.1 Lambertian 漫反射

```cpp
class Lambertian : public Material {
    Vec3 albedo;

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 scatter_direction = rec.normal + random_unit_vector();
        scattered = Ray(rec.point, scatter_direction);
        attenuation = albedo;
        return true;
    }
};
```

**物理原理**：
- 光线在表面随机散射
- 散射方向在法线半球内均匀分布
- 能量守恒：attenuation = albedo / π

### 4.2 Metal 金属材质

```cpp
class Metal : public Material {
    Vec3 albedo;
    double fuzz;  // 模糊度

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        Vec3 reflected = ray_in.direction.reflect(rec.normal);
        scattered = Ray(rec.point, reflected + random_in_unit_sphere() * fuzz);
        attenuation = albedo;
        return scattered.direction.dot(rec.normal) > 0;
    }
};
```

**物理原理**：
- 镜面反射
- 模糊度控制反射的锐利程度
- 支持各向异性反射

### 4.3 Dielectric 电介质材质

```cpp
class Dielectric : public Material {
    double ir;  // 折射率

    bool scatter(const Ray& ray_in, const HitRecord& rec,
                 Vec3& attenuation, Ray& scattered) const override {
        double refraction_ratio = rec.front_face ? (1.0 / ir) : ir;
        // Snell 定律 + Schlick 近似
        // ...
    }
};
```

**物理原理**：
- Snell 定律：n1 * sin(θ1) = n2 * sin(θ2)
- 全内反射：当 sin(θ2) > 1 时
- Schlick 近似：计算反射率

## 5. 光源系统设计

### 5.1 PointLight 点光源

```cpp
class PointLight : public Light {
    Vec3 position;
    Vec3 color;
    double intensity;

    Vec3 direction_to(const Vec3& point) const;
    double intensity_at(const Vec3& point) const;
};
```

**光照计算**：
```
attenuation = intensity / (4π * r²)
```

### 5.2 DirectionalLight 方向光源

```cpp
class DirectionalLight : public Light {
    Vec3 direction;
    Vec3 color;
    double intensity;

    Vec3 direction_to(const Vec3& point) const;
    double intensity_at(const Vec3& point) const;
};
```

**特点**：
- 无限远光源（如太阳光）
- 无衰减
- 平行光线

### 5.3 AreaLight 面光源

```cpp
class AreaLight : public Light {
    Vec3 position;
    Vec3 u, v;  // 光源平面
    double width, height;
    Vec3 color;
    double intensity;

    Vec3 random_point(double u_rand, double v_rand) const;
};
```

**特点**：
- 产生软阴影
- 需要采样光源表面
- 支持重要性采样

## 6. 加速结构设计

### 6.1 BVH 包围盒层次结构

```cpp
class BVHNode : public Hitable {
    shared_ptr<Hitable> left, right;
    AABB box;

    bool hit(const Ray& ray, double t_min, double t_max,
             HitRecord& rec) const override;
};
```

**构建算法**：
1. 计算所有物体的包围盒
2. 选择分割轴（轮换 x, y, z）
3. 按中心点排序
4. 递归分割

**查询算法**：
1. 测试节点包围盒
2. 如果不相交，返回 false
3. 如果相交，递归测试子节点
4. 返回最近的交点

### 6.2 KD-Tree

```cpp
class KDNode {
    AABB bounds;
    shared_ptr<KDNode> left, right;
    vector<shared_ptr<Hitable>> objects;
    int split_axis;
    double split_position;
    bool is_leaf;
};
```

**构建算法**：
1. 选择分割轴（轮换 x, y, z）
2. 按中心点排序
3. 选择分割位置（中位数）
4. 递归分割

**查询算法**：
1. 测试节点包围盒
2. 如果是叶子节点，测试所有物体
3. 如果是内部节点，递归测试子节点
4. 返回最近的交点

### 6.3 八叉树

```cpp
class OctreeNode {
    AABB bounds;
    array<shared_ptr<OctreeNode>, 8> children;
    vector<shared_ptr<Hitable>> objects;
    bool is_leaf;
};
```

**构建算法**：
1. 计算整体包围盒
2. 将空间分成 8 个子空间
3. 将物体分配到子空间
4. 递归分割

**查询算法**：
1. 测试节点包围盒
2. 如果是叶子节点，测试所有物体
3. 如果是内部节点，递归测试所有子节点
4. 返回最近的交点

## 7. 渲染算法设计

### 7.1 路径追踪

```cpp
Color path_trace(const Ray& ray, int depth) {
    if (depth <= 0) return Color(0, 0, 0);

    HitRecord rec;
    if (world->hit(ray, 0.001, infinity, rec)) {
        Ray scattered;
        Vec3 attenuation;

        if (rec.material->scatter(ray, rec, attenuation, scattered)) {
            // 直接光照 + 间接光照
            return direct_light + attenuation * path_trace(scattered, depth - 1);
        }
        return Color(0, 0, 0);
    }

    return sky_color(ray);
}
```

**算法流程**：
1. 从相机发射光线
2. 计算光线与场景的交点
3. 在交点处计算直接光照
4. 随机选择散射方向
5. 递归追踪散射光线
6. 累积间接光照

### 7.2 双向路径追踪

```
相机路径: C0 → C1 → C2 → ... → Cm
光源路径: L0 → L1 → L2 → ... → Ln

连接: Cm → Ln
```

**算法流程**：
1. 从相机发射光线，构建相机路径
2. 从光源发射光线，构建光源路径
3. 连接路径端点
4. 计算路径贡献

### 7.3 光子映射

```cpp
struct Photon {
    Vec3 position;
    Vec3 power;
    Vec3 direction;
};

void emit_photons(const shared_ptr<Hitable>& world, int num_photons) {
    for (int i = 0; i < num_photons; i++) {
        // 从光源发射光子
        Ray photon_ray = emit_from_light();
        trace_photon(photon_ray, world, power, depth);
    }
}
```

**算法流程**：
1. 从光源发射光子
2. 追踪光子路径
3. 存储光子到光子图
4. 使用光子图计算光照

## 8. 纹理系统设计

### 8.1 纹理接口

```cpp
class Texture {
public:
    virtual Vec3 value(double u, double v, const Vec3& p) const = 0;
};
```

### 8.2 棋盘格纹理

```cpp
class CheckerTexture : public Texture {
    shared_ptr<Texture> odd, even;
    double scale;

    Vec3 value(double u, double v, const Vec3& p) const override {
        double sines = sin(scale * p.x) * sin(scale * p.y) * sin(scale * p.z);
        return sines < 0 ? odd->value(u, v, p) : even->value(u, v, p);
    }
};
```

### 8.3 噪声纹理

```cpp
class NoiseTexture : public Texture {
    double scale;

    Vec3 value(double u, double v, const Vec3& p) const override {
        double noise = perlin_noise(p * scale);
        return color * (0.5 * (1.0 + sin(scale * p.z + 10.0 * noise)));
    }
};
```

## 9. 采样策略设计

### 9.1 随机采样

```cpp
double u = (i + random_double()) / width;
double v = (j + random_double()) / height;
```

### 9.2 分层采样

```cpp
int sqrt_samples = sqrt(samples_per_pixel);
for (int si = 0; si < sqrt_samples; si++) {
    for (int sj = 0; sj < sqrt_samples; sj++) {
        double u = (i + (si + random_double()) / sqrt_samples) / width;
        double v = (j + (sj + random_double()) / sqrt_samples) / height;
    }
}
```

### 9.3 Halton 序列

```cpp
double halton(int index, int base) {
    double f = 1.0, r = 0.0;
    while (index > 0) {
        f /= base;
        r += f * (index % base);
        index /= base;
    }
    return r;
}
```

## 10. 多线程设计

### 10.1 行级并行

```cpp
void render(const string& filename, int num_threads) {
    vector<thread> threads;
    int rows_per_thread = height / num_threads;

    for (int t = 0; t < num_threads; t++) {
        int start_row = t * rows_per_thread;
        int end_row = (t == num_threads - 1) ? height : start_row + rows_per_thread;
        threads.emplace_back(render_rows, start_row, end_row);
    }

    for (auto& thread : threads) {
        thread.join();
    }
}
```

### 10.2 线程安全

- 使用 `std::atomic` 计数器
- 使用 `std::mutex` 保护共享数据
- 避免数据竞争

## 11. 文件组织

```
include/
├── vec3.h                 # 基础向量类
├── ray.h                  # 光线类
├── hitable.h              # 可命中物体接口
├── sphere.h               # 球体和平面
├── triangle.h             # 三角形
├── box.h                  # 盒子
├── cylinder.h             # 圆柱和圆锥
├── material.h             # 基础材质
├── advanced_material.h    # 高级材质
├── texture.h              # 纹理系统
├── light.h                # 光源系统
├── camera.h               # 相机
├── renderer.h             # 基础渲染器
├── advanced_renderer.h    # 高级渲染器
├── advanced_features.h    # 高级特性
├── scene.h                # 场景工厂
├── bvh.h                  # BVH 加速
├── kdtree.h               # KD-Tree 加速
└── octree.h               # 八叉树和均匀网格
```

## 12. 扩展点设计

### 12.1 添加新几何体

1. 继承 `Hitable` 接口
2. 实现 `hit()` 方法
3. 在场景中使用

### 12.2 添加新材质

1. 继承 `Material` 接口
2. 实现 `scatter()` 方法
3. 在物体上应用

### 12.3 添加新光源

1. 继承 `Light` 接口
2. 实现光照计算方法
3. 在渲染器中使用

### 12.4 添加新纹理

1. 继承 `Texture` 接口
2. 实现 `value()` 方法
3. 在材质中使用
