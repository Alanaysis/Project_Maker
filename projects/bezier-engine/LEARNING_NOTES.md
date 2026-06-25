# 贝塞尔曲线引擎 - 学习笔记

## 项目概述

本项目实现了一个完整的贝塞尔曲线引擎，用于创建、编辑和渲染贝塞尔曲线。通过这个项目，我深入学习了贝塞尔曲线的数学原理、曲线编辑操作和渲染技术。

## 核心学习目标

1. **理解贝塞尔曲线数学** - 掌握 de Casteljau 算法和 Bernstein 多项式
2. **掌握曲线编辑操作** - 学会移动控制点、分割曲线、反转方向等
3. **学会曲线渲染** - 实现 SVG 格式输出和自适应细分

## 学习路径

### 阶段 1: 数学基础

#### 1.1 线性插值 (Lerp)

线性插值是贝塞尔曲线的基础：

```
lerp(a, b, t) = a + (b - a) * t = a * (1 - t) + b * t
```

其中 `t ∈ [0, 1]`：
- `t = 0` 时返回 `a`
- `t = 1` 时返回 `b`
- `t = 0.5` 时返回 `a` 和 `b` 的中点

**Rust 实现**:
```rust
pub fn lerp(&self, other: &Point, t: f64) -> Point {
    Point {
        x: self.x + (other.x - self.x) * t,
        y: self.y + (other.y - self.y) * t,
    }
}
```

**关键洞察**: 线性插值可以看作是加权平均，权重由参数 `t` 决定。

#### 1.2 de Casteljau 算法

de Casteljau 算法是贝塞尔曲线求值的核心，通过递归线性插值实现。

**算法步骤**:
1. 给定控制点 P₀, P₁, ..., Pₙ 和参数 t
2. 计算相邻控制点的线性插值，得到新的控制点序列
3. 重复步骤 2，直到只剩一个点
4. 该点即为曲线在参数 t 处的值

**二次曲线示例**:
```
控制点: P₀, P₁, P₂
参数: t

第一层:
  A = lerp(P₀, P₁, t)
  B = lerp(P₁, P₂, t)

第二层:
  C = lerp(A, B, t)

结果: C 就是曲线上的点
```

**三次曲线示例**:
```
控制点: P₀, P₁, P₂, P₃
参数: t

第一层:
  A = lerp(P₀, P₁, t)
  B = lerp(P₁, P₂, t)
  C = lerp(P₂, P₃, t)

第二层:
  D = lerp(A, B, t)
  E = lerp(B, C, t)

第三层:
  F = lerp(D, E, t)

结果: F 就是曲线上的点
```

**Rust 实现**:
```rust
fn evaluate(&self, t: f64) -> Point {
    let t = t.max(0.0).min(1.0);

    // 第一层
    let a = self.p0.lerp(&self.p1, t);
    let b = self.p1.lerp(&self.p2, t);
    let c = self.p2.lerp(&self.p3, t);

    // 第二层
    let d = a.lerp(&b, t);
    let e = b.lerp(&c, t);

    // 第三层
    d.lerp(&e, t)
}
```

**关键洞察**: de Casteljau 算法不仅用于求值，还自然地支持曲线细分。

#### 1.3 贝塞尔曲线公式

贝塞尔曲线可以用 Bernstein 多项式表示：

```
B(t) = Σᵢ₌₀ⁿ Bᵢ,ₙ(t) * Pᵢ
```

其中 Bernstein 基函数：
```
Bᵢ,ₙ(t) = C(n, i) * t^i * (1-t)^(n-i)
```

**二次曲线**:
```
B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
```

**三次曲线**:
```
B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
```

**关键洞察**: de Casteljau 算法和 Bernstein 多项式是等价的，但 de Casteljau 更数值稳定。

### 阶段 2: 曲线操作

#### 2.1 导数计算

贝塞尔曲线的导数是比原曲线低一阶的贝塞尔曲线：

**二次曲线导数**:
```
B'(t) = 2[(1-t)(P₁-P₀) + t(P₂-P₁)]
```

导数控制点: `2(P₁-P₀)`, `2(P₂-P₁)`

**三次曲线导数**:
```
B'(t) = 3[(1-t)²(P₁-P₀) + 2(1-t)t(P₂-P₁) + t²(P₃-P₂)]
```

导数控制点: `3(P₁-P₀)`, `3(P₂-P₁)`, `3(P₃-P₂)`

**Rust 实现**:
```rust
fn derivative_points(&self) -> Vec<Point> {
    vec![
        (self.p1 - self.p0) * 3.0,
        (self.p2 - self.p1) * 3.0,
        (self.p3 - self.p2) * 3.0,
    ]
}
```

**关键洞察**: 导数曲线的控制点是原控制点的差分，乘以曲线阶数。

#### 2.2 曲线细分

曲线细分使用 de Casteljau 算法在指定参数处将曲线分为两段。

**细分原理**:
在 de Casteljau 算法中，中间点自然地形成了两条子曲线的控制点。

**二次曲线细分**:
```
原曲线: P₀, P₁, P₂
参数: t

中间点:
  M₀ = lerp(P₀, P₁, t)
  M₁ = lerp(P₁, P₂, t)
  Mid = lerp(M₀, M₁, t)

左段: P₀, M₀, Mid
右段: Mid, M₁, P₂
```

**Rust 实现**:
```rust
pub fn subdivide_quadratic(curve: &QuadraticBezier, t: f64) 
    -> (QuadraticBezier, QuadraticBezier) 
{
    let t = t.max(0.0).min(1.0);

    let m0 = curve.p0.lerp(&curve.p1, t);
    let m1 = curve.p1.lerp(&curve.p2, t);
    let mid = m0.lerp(&m1, t);

    let left = QuadraticBezier::new(curve.p0, m0, mid);
    let right = QuadraticBezier::new(mid, m1, curve.p2);

    (left, right)
}
```

**关键洞察**: 细分后的两条曲线与原曲线完全一致，这是 de Casteljau 算法的优雅之处。

#### 2.3 自适应细分

自适应细分根据曲线的"平坦度"自动决定细分深度。

**平坦度定义**:
平坦度定义为控制点到端点连线的最大距离。

```rust
pub fn cubic_flatness(curve: &CubicBezier) -> f64 {
    let d1 = point_to_line_distance(curve.p1, curve.p0, curve.p3);
    let d2 = point_to_line_distance(curve.p2, curve.p0, curve.p3);
    d1.max(d2)
}
```

**自适应细分算法**:
1. 计算曲线平坦度
2. 如果平坦度 < 阈值，停止细分
3. 如果深度 >= 最大深度，停止细分
4. 在 t=0.5 处细分曲线
5. 递归处理左右两段

**关键洞察**: 平坦度越小，曲线越接近直线，需要的细分点越少。

#### 2.4 曲线升阶

曲线升阶将低阶曲线转换为高阶曲线，保持形状不变。

**二次到三次升阶公式**:
```
Q₀ = P₀
Q₁ = (2P₀ + P₁) / 3
Q₂ = (P₁ + 2P₂) / 3
Q₃ = P₂
```

**Rust 实现**:
```rust
pub fn elevate_to_cubic(&self) -> CubicBezier {
    let q0 = self.p0;
    let q1 = (self.p0 * 2.0 + self.p1) / 3.0;
    let q2 = (self.p1 * 2.0 + self.p2) / 3.0;
    let q3 = self.p2;
    CubicBezier::new(q0, q1, q2, q3)
}
```

**关键洞察**: 升阶不会改变曲线形状，但会增加控制点，提供更多的编辑自由度。

### 阶段 3: 曲线编辑

#### 3.1 控制点移动

控制点移动是最基本的编辑操作：

```rust
pub fn move_point(&mut self, curve_index: usize, point_index: usize, delta: Point) -> bool {
    match self.curves.get_mut(curve_index) {
        Some(BezierCurveType::Quadratic(ref mut curve)) => {
            match point_index {
                0 => { curve.p0 = curve.p0 + delta; true }
                1 => { curve.p1 = curve.p1 + delta; true }
                2 => { curve.p2 = curve.p2 + delta; true }
                _ => false,
            }
        }
        // ...
    }
}
```

**关键洞察**: 移动控制点会改变曲线形状，但保持曲线的连续性。

#### 3.2 曲线分割

曲线分割在指定参数处将曲线分为两段：

```rust
pub fn split_curve(&mut self, curve_index: usize, t: f64) -> Option<(usize, usize)> {
    // 使用细分算法
    let (left, right) = subdivide_cubic(&cubic, t);
    // 插入新曲线
    self.curves.insert(curve_index, BezierCurveType::Cubic(right));
    self.curves.insert(curve_index, BezierCurveType::Cubic(left));
    Some((curve_index, curve_index + 1))
}
```

**关键洞察**: 分割后的两条曲线与原曲线完全一致，可以独立编辑。

#### 3.3 曲线反转

曲线反转将曲线的方向颠倒：

```rust
pub fn reverse_curve(&mut self, curve_index: usize) -> bool {
    match self.curves.get_mut(curve_index) {
        Some(BezierCurveType::Cubic(ref mut curve)) => {
            std::mem::swap(&mut curve.p0, &mut curve.p3);
            std::mem::swap(&mut curve.p1, &mut curve.p2);
            true
        }
        // ...
    }
}
```

**关键洞察**: 反转曲线只是交换控制点的顺序，不影响曲线形状。

### 阶段 4: 渲染输出

#### 4.1 SVG 格式

SVG 是一种矢量图形格式，使用 XML 语法：

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
  <path d="M 10 100 Q 150 10 290 100" fill="none" stroke="black" stroke-width="2"/>
</svg>
```

**SVG 路径命令**:
- `M x y`: 移动到 (x, y)
- `L x y`: 直线到 (x, y)
- `Q x1 y1 x y`: 二次贝塞尔曲线
- `C x1 y1 x2 y2 x y`: 三次贝塞尔曲线

**Rust 实现**:
```rust
fn cubic_path(&self, curve: &CubicBezier) -> String {
    format!(
        r#"<path d="M {} {} C {} {} {} {} {} {}" fill="none" stroke="{}" stroke-width="{}"/>"#,
        curve.p0.x, curve.p0.y,
        curve.p1.x, curve.p1.y,
        curve.p2.x, curve.p2.y,
        curve.p3.x, curve.p3.y,
        self.style.stroke_color.to_string(),
        self.style.stroke_width
    )
}
```

**关键洞察**: SVG 直接支持贝塞尔曲线，无需细分。

#### 4.2 折线渲染

对于不支持贝塞尔曲线的渲染器，需要将曲线细分为折线：

```rust
pub fn curve_to_polyline(curve: &BezierCurveType, config: &SubdivisionConfig) -> Vec<Point> {
    match curve {
        BezierCurveType::Quadratic(quad) => {
            adaptive_subdivide_quadratic(quad, config)
        }
        BezierCurveType::Cubic(cubic) => {
            adaptive_subdivide_cubic(cubic, config)
        }
    }
}
```

**关键洞察**: 折线近似的精度取决于细分深度，需要在精度和性能之间权衡。

#### 4.3 控制点可视化

控制点和连线的可视化有助于理解曲线形状：

```rust
fn control_points(&self, points: &[Point]) -> String {
    let mut circles = String::new();
    for (i, point) in points.iter().enumerate() {
        let color = if i == 0 || i == points.len() - 1 {
            SvgColor::rgb(0, 128, 255).to_string()  // 端点
        } else {
            self.style.control_point_color.to_string()  // 控制点
        };

        circles.push_str(&format!(
            r#"<circle cx="{}" cy="{}" r="{}" fill="{}"/>"#,
            point.x, point.y,
            self.style.control_point_radius,
            color
        ));
    }
    circles
}
```

**关键洞察**: 区分端点和控制点有助于用户理解曲线结构。

## Rust 特性应用

### 1. Trait 系统

使用 trait 定义统一接口：

```rust
pub trait BezierCurve {
    fn degree(&self) -> usize;
    fn evaluate(&self, t: f64) -> Point;
    fn derivative_points(&self) -> Vec<Point>;
    // ...
}
```

**优势**:
- 代码复用
- 类型安全
- 静态分发

### 2. 枚举与模式匹配

使用枚举处理不同类型：

```rust
pub enum BezierCurveType {
    Quadratic(QuadraticBezier),
    Cubic(CubicBezier),
}

match curve {
    BezierCurveType::Quadratic(c) => c.evaluate(t),
    BezierCurveType::Cubic(c) => c.evaluate(t),
}
```

**优势**:
- 运行时多态
- 避免动态分发
- 明确的所有权

### 3. 运算符重载

实现自然的数学语法：

```rust
impl Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}
```

**优势**:
- 代码可读性
- 自然的数学表达
- 类型安全

### 4. Builder 模式

使用 Builder 模式配置复杂对象：

```rust
SubdivisionConfig::new()
    .with_max_depth(5)
    .with_flatness(1.0)
    .with_min_segment_length(1.0)
```

**优势**:
- 灵活的配置
- 可读的代码
- 默认值支持

### 5. 模块系统

使用模块组织代码：

```rust
// lib.rs
pub mod point;
pub mod bezier;
pub mod subdivision;
pub mod editor;
pub mod renderer;

pub use point::Point;
pub use bezier::{BezierCurve, QuadraticBezier, CubicBezier};
```

**优势**:
- 清晰的组织
- 封装实现细节
- 便于扩展

## 调试经验

### 1. 浮点精度问题

**问题**: 浮点数比较失败

**解决**: 使用 epsilon 比较

```rust
// 错误
assert_eq!(a, b);

// 正确
assert!((a - b).abs() < 1e-10);
```

### 2. 边界情况

**问题**: 参数超出范围

**解决**: 钳位到有效范围

```rust
let t = t.max(0.0).min(1.0);
```

### 3. 数值稳定性

**问题**: de Casteljau 算法的数值稳定性

**解决**: 使用 de Casteljau 而非 Bernstein 多项式

```rust
// de Casteljau (更稳定)
let a = self.p0.lerp(&self.p1, t);
let b = self.p1.lerp(&self.p2, t);
a.lerp(&b, t)

// Bernstein (可能不稳定)
let mt = 1.0 - t;
mt * mt * self.p0 + 2.0 * mt * t * self.p1 + t * t * self.p2
```

## 性能优化经验

### 1. 避免不必要的分配

```rust
// 不好
fn evaluate(&self, t: f64) -> Point {
    let mut points = vec![self.p0, self.p1, self.p2, self.p3];
    // ...
}

// 好
fn evaluate(&self, t: f64) -> Point {
    let a = self.p0.lerp(&self.p1, t);
    let b = self.p1.lerp(&self.p2, t);
    let c = self.p2.lerp(&self.p3, t);
    // ...
}
```

### 2. 使用距离平方

```rust
// 不好
let dist = p1.distance_to(&p2);
if dist < threshold { ... }

// 好
let dist_sq = p1.distance_squared_to(&p2);
if dist_sq < threshold * threshold { ... }
```

### 3. 提前终止

```rust
// 牛顿迭代
for _ in 0..10 {
    let grad = self.evaluate_derivative(best_t);
    let grad_dot = grad.dot(&grad);

    if grad_dot < 1e-10 {
        break;  // 提前终止
    }

    // ...
}
```

## 项目收获

### 1. 数学理解

- 深入理解了贝塞尔曲线的数学原理
- 掌握了 de Casteljau 算法的实现
- 理解了曲线细分的数学基础

### 2. Rust 技能

- 熟练使用 trait 系统
- 掌握枚举和模式匹配
- 理解模块系统和代码组织

### 3. 软件工程

- 学会了模块化设计
- 掌握了测试策略
- 理解了性能优化

### 4. 图形学知识

- 了解了 SVG 格式
- 理解了曲线渲染技术
- 掌握了可视化设计

## 未来学习方向

### 1. 高级曲线

- 非均匀有理 B 样条 (NURBS)
- 贝塞尔曲面
- 曲线拟合

### 2. 渲染技术

- GPU 加速渲染
- 抗锯齿算法
- 曲线碰撞检测

### 3. 应用领域

- 字体设计
- 动画路径
- UI 设计

## 总结

通过这个项目，我不仅学会了贝塞尔曲线的数学原理和实现技术，还深入理解了 Rust 的特性和最佳实践。这个项目为我打下了坚实的图形学基础，为未来的学习和开发奠定了基础。

**关键收获**:
1. de Casteljau 算法是贝塞尔曲线的核心
2. 曲线细分是渲染的基础
3. Rust 的 trait 系统非常适合图形学编程
4. 测试和文档是项目成功的关键
