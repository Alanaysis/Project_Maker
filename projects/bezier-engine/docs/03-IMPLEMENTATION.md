# 03 - 实现细节

## 核心算法实现

### 1. de Casteljau 算法

de Casteljau 算法是贝塞尔曲线求值的核心算法，通过递归线性插值实现。

**算法原理**:

给定控制点 P₀, P₁, ..., Pₙ 和参数 t ∈ [0, 1]：

```
Pᵢʲ = (1-t) * Pᵢʲ⁻¹ + t * Pᵢ₊₁ʲ⁻¹

其中:
- Pᵢ⁰ = Pᵢ (原始控制点)
- Pₙⁿ(t) = B(t) (曲线上的点)
```

**二次贝塞尔曲线实现**:

```rust
fn evaluate(&self, t: f64) -> Point {
    let t = t.max(0.0).min(1.0);

    // 第一层插值
    let a = self.p0.lerp(&self.p1, t);
    let b = self.p1.lerp(&self.p2, t);

    // 第二层插值
    a.lerp(&b, t)
}
```

**三次贝塞尔曲线实现**:

```rust
fn evaluate(&self, t: f64) -> Point {
    let t = t.max(0.0).min(1.0);

    // 第一层插值
    let a = self.p0.lerp(&self.p1, t);
    let b = self.p1.lerp(&self.p2, t);
    let c = self.p2.lerp(&self.p3, t);

    // 第二层插值
    let d = a.lerp(&b, t);
    let e = b.lerp(&c, t);

    // 第三层插值
    d.lerp(&e, t)
}
```

**时间复杂度**: O(n²)，其中 n 是控制点数量

**空间复杂度**: O(n)，使用迭代而非递归

### 2. 导数计算

贝塞尔曲线的导数是比原曲线低一阶的贝塞尔曲线。

**数学推导**:

对于 n 阶贝塞尔曲线：
```
B'(t) = n * Σᵢ₌₀ⁿ⁻¹ Bᵢⁿ⁻¹(t) * (Pᵢ₊₁ - Pᵢ)
```

**实现**:

```rust
fn derivative_points(&self) -> Vec<Point> {
    // 二次曲线: 2(P₁-P₀), 2(P₂-P₁)
    vec![
        (self.p1 - self.p0) * 2.0,
        (self.p2 - self.p1) * 2.0,
    ]
}

fn derivative_points(&self) -> Vec<Point> {
    // 三次曲线: 3(P₁-P₀), 3(P₂-P₁), 3(P₃-P₂)
    vec![
        (self.p1 - self.p0) * 3.0,
        (self.p2 - self.p1) * 3.0,
        (self.p3 - self.p2) * 3.0,
    ]
}
```

### 3. 曲线细分

曲线细分使用 de Casteljau 算法在指定参数处将曲线分为两段。

**二次曲线细分**:

```rust
pub fn subdivide_quadratic(curve: &QuadraticBezier, t: f64) 
    -> (QuadraticBezier, QuadraticBezier) 
{
    let t = t.max(0.0).min(1.0);

    // de Casteljau 中间点
    let m0 = curve.p0.lerp(&curve.p1, t);
    let m1 = curve.p1.lerp(&curve.p2, t);
    let mid = m0.lerp(&m1, t);

    // 左段: P0, m0, mid
    let left = QuadraticBezier::new(curve.p0, m0, mid);
    // 右段: mid, m1, P2
    let right = QuadraticBezier::new(mid, m1, curve.p2);

    (left, right)
}
```

**三次曲线细分**:

```rust
pub fn subdivide_cubic(curve: &CubicBezier, t: f64) 
    -> (CubicBezier, CubicBezier) 
{
    let t = t.max(0.0).min(1.0);

    // 第一层
    let m0 = curve.p0.lerp(&curve.p1, t);
    let m1 = curve.p1.lerp(&curve.p2, t);
    let m2 = curve.p2.lerp(&curve.p3, t);

    // 第二层
    let n0 = m0.lerp(&m1, t);
    let n1 = m1.lerp(&m2, t);

    // 第三层
    let mid = n0.lerp(&n1, t);

    // 左段: P0, m0, n0, mid
    let left = CubicBezier::new(curve.p0, m0, n0, mid);
    // 右段: mid, n1, m2, P3
    let right = CubicBezier::new(mid, n1, m2, curve.p3);

    (left, right)
}
```

### 4. 自适应细分

自适应细分根据曲线的"平坦度"自动决定细分深度。

**平坦度定义**:

平坦度定义为控制点到端点连线的最大距离：

```rust
pub fn cubic_flatness(curve: &CubicBezier) -> f64 {
    let d1 = point_to_line_distance(curve.p1, curve.p0, curve.p3);
    let d2 = point_to_line_distance(curve.p2, curve.p0, curve.p3);
    d1.max(d2)
}
```

**点到线段距离**:

```rust
fn point_to_line_distance(point: Point, line_start: Point, line_end: Point) -> f64 {
    let line = line_end - line_start;
    let line_len_sq = line.dot(&line);

    if line_len_sq < 1e-10 {
        return point.distance_to(&line_start);
    }

    // 投影参数
    let t = ((point - line_start).dot(&line) / line_len_sq)
        .max(0.0)
        .min(1.0);

    // 投影点
    let projection = line_start + line * t;
    point.distance_to(&projection)
}
```

**自适应细分算法**:

```rust
fn adaptive_subdivide_cubic_recursive(
    curve: &CubicBezier,
    config: &SubdivisionConfig,
    depth: usize,
    points: &mut Vec<Point>,
) {
    // 终止条件
    if depth >= config.max_depth {
        return;
    }

    let flatness = cubic_flatness(curve);
    let curve_length = curve.length(10);

    // 平坦度检查
    if flatness < config.flatness_threshold || 
       curve_length < config.min_segment_length {
        return;
    }

    // 细分
    let (left, right) = subdivide_cubic(curve, 0.5);

    // 递归处理
    adaptive_subdivide_cubic_recursive(&left, config, depth + 1, points);
    points.push(left.p3);
    adaptive_subdivide_cubic_recursive(&right, config, depth + 1, points);
}
```

### 5. 最近点查找

最近点查找使用采样 + 牛顿迭代的方法。

**算法流程**:

1. **粗采样**: 在曲线上均匀采样 N 个点
2. **找到最近点**: 计算查询点到每个采样点的距离
3. **牛顿迭代**: 使用梯度下降优化参数 t

**实现**:

```rust
fn closest_point_parameter(&self, point: &Point, num_samples: usize) -> f64 {
    // 粗采样
    let mut best_t = 0.0;
    let mut best_dist_sq = f64::MAX;

    for i in 0..=num_samples {
        let t = i as f64 / num_samples as f64;
        let p = self.evaluate(t);
        let dist_sq = point.distance_squared_to(&p);
        if dist_sq < best_dist_sq {
            best_dist_sq = dist_sq;
            best_t = t;
        }
    }

    // 牛顿迭代优化
    for _ in 0..10 {
        let grad = self.evaluate_derivative(best_t);
        let p = self.evaluate(best_t);
        let diff = p - *point;

        let grad_dot = grad.dot(&grad);
        if grad_dot < 1e-10 {
            break;
        }

        // 梯度下降步长
        let step = diff.dot(&grad) / grad_dot;
        best_t = (best_t - step * 0.5).max(0.0).min(1.0);
    }

    best_t
}
```

### 6. 曲线升阶

曲线升阶将低阶曲线转换为高阶曲线，保持形状不变。

**二次到三次升阶公式**:

```
Q₀ = P₀
Q₁ = (2P₀ + P₁) / 3
Q₂ = (P₁ + 2P₂) / 3
Q₃ = P₂
```

**实现**:

```rust
pub fn elevate_to_cubic(&self) -> CubicBezier {
    let q0 = self.p0;
    let q1 = (self.p0 * 2.0 + self.p1) / 3.0;
    let q2 = (self.p1 * 2.0 + self.p2) / 3.0;
    let q3 = self.p2;
    CubicBezier::new(q0, q1, q2, q3)
}
```

## 线性插值实现

点的线性插值是所有算法的基础：

```rust
pub fn lerp(&self, other: &Point, t: f64) -> Point {
    Point {
        x: self.x + (other.x - self.x) * t,
        y: self.y + (other.y - self.y) * t,
    }
}
```

**优化**: 编译器通常会将此优化为 `self * (1-t) + other * t`

## SVG 生成

SVG 生成直接使用字符串拼接，无需额外依赖。

**二次曲线 SVG 路径**:

```rust
fn quadratic_path(&self, curve: &QuadraticBezier) -> String {
    format!(
        r#"<path d="M {} {} Q {} {} {} {}" fill="none" stroke="{}" stroke-width="{}"/>"#,
        curve.p0.x, curve.p0.y,
        curve.p1.x, curve.p1.y,
        curve.p2.x, curve.p2.y,
        self.style.stroke_color.to_string(),
        self.style.stroke_width
    )
}
```

**三次曲线 SVG 路径**:

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

## 性能优化

### 1. 避免不必要的分配

```rust
// 使用迭代而非递归的 de Casteljau
fn evaluate(&self, t: f64) -> Point {
    let t = t.max(0.0).min(1.0);

    // 直接计算，无需分配临时数组
    let a = self.p0.lerp(&self.p1, t);
    let b = self.p1.lerp(&self.p2, t);
    a.lerp(&b, t)
}
```

### 2. 使用距离平方

```rust
// 避免开方运算
pub fn distance_squared_to(&self, other: &Point) -> f64 {
    let dx = self.x - other.x;
    let dy = self.y - other.y;
    dx * dx + dy * dy
}
```

### 3. 提前终止

```rust
// 牛顿迭代提前终止
if grad_dot < 1e-10 {
    break;
}
```

## 测试策略

### 单元测试

每个模块都有对应的单元测试：

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_quadratic_bezier_endpoints() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let start = curve.evaluate(0.0);
        let end = curve.evaluate(1.0);

        assert!((start.x - 0.0).abs() < 1e-10);
        assert!((end.x - 100.0).abs() < 1e-10);
    }
}
```

### 集成测试

集成测试验证模块间的协作：

```rust
#[test]
fn test_editor_split_curve() {
    let mut editor = CurveEditor::new();
    editor.add_cubic(CubicBezier::new(...));

    let result = editor.split_curve(0, 0.5);
    assert!(result.is_some());
    assert_eq!(editor.curve_count(), 2);
}
```

### 边界情况测试

测试退化和极端情况：

```rust
#[test]
fn test_degenerate_curve() {
    let curve = QuadraticBezier::new(
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
    );

    let point = curve.evaluate(0.5);
    assert!((point.x - 50.0).abs() < 1e-10);
}
```

## 已知限制

1. **仅支持二次和三次曲线**: 不支持更高阶的贝塞尔曲线
2. **无曲线拼接**: 不支持多段曲线的连续性控制
3. **无曲线拟合**: 不支持从点集拟合贝塞尔曲线
4. **数值精度**: 使用 f64，对于极端情况可能有精度问题

## 未来改进方向

1. **支持任意阶贝塞尔曲线**: 使用动态数组存储控制点
2. **曲线拼接**: 实现 C0、C1、G1 连续
3. **曲线拟合**: 从点集拟合贝塞尔曲线
4. **贝塞尔曲面**: 扩展到三维曲面
5. **GPU 加速**: 使用 wgpu 或 OpenGL 进行批量计算
