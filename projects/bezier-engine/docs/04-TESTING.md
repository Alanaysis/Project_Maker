# 04 - 测试策略

## 测试概述

贝塞尔曲线引擎采用多层次的测试策略，确保代码的正确性和可靠性。

### 测试金字塔

```
        ┌─────────────┐
        │   集成测试    │  少量，验证模块协作
        ├─────────────┤
        │   单元测试    │  大量，验证单个函数
        └─────────────┘
```

## 单元测试

### 测试组织

每个模块都有对应的 `#[cfg(test)]` 模块：

```rust
// src/point.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_point_creation() {
        let p = Point::new(3.0, 4.0);
        assert_eq!(p.x, 3.0);
        assert_eq!(p.y, 4.0);
    }
}
```

### 测试分类

#### 1. Point 模块测试

| 测试名称 | 描述 |
|---------|------|
| `test_point_creation` | 测试点的创建 |
| `test_distance` | 测试距离计算 |
| `test_lerp` | 测试线性插值 |
| `test_arithmetic` | 测试算术运算 |
| `test_normalize` | 测试向量归一化 |
| `test_dot_cross` | 测试点积和叉积 |

#### 2. Bezier 模块测试

| 测试名称 | 描述 |
|---------|------|
| `test_quadratic_bezier_endpoints` | 测试端点正确性 |
| `test_quadratic_bezier_midpoint` | 测试中点计算 |
| `test_cubic_bezier_endpoints` | 测试端点正确性 |
| `test_cubic_bezier_midpoint` | 测试中点计算 |
| `test_derivative` | 测试导数计算 |
| `test_elevate_to_cubic` | 测试曲线升阶 |
| `test_bounding_box` | 测试包围盒计算 |
| `test_curve_length` | 测试曲线长度计算 |

#### 3. Subdivision 模块测试

| 测试名称 | 描述 |
|---------|------|
| `test_quadratic_subdivision_endpoints` | 测试细分端点 |
| `test_cubic_subdivision_endpoints` | 测试细分端点 |
| `test_subdivision_preserves_curve` | 测试细分保持曲线形状 |
| `test_flatness` | 测试平坦度计算 |
| `test_uniform_subdivision` | 测试均匀细分 |
| `test_adaptive_subdivision` | 测试自适应细分 |

#### 4. Editor 模块测试

| 测试名称 | 描述 |
|---------|------|
| `test_editor_add_curves` | 测试添加曲线 |
| `test_editor_select` | 测试选择操作 |
| `test_editor_move_point` | 测试移动控制点 |
| `test_editor_split_curve` | 测试分割曲线 |
| `test_editor_reverse_curve` | 测试反转曲线 |
| `test_editor_elevate_to_cubic` | 测试提升曲线 |
| `test_editor_find_nearest` | 测试查找最近点 |

#### 5. Renderer 模块测试

| 测试名称 | 描述 |
|---------|------|
| `test_svg_renderer_quadratic` | 测试二次曲线渲染 |
| `test_svg_renderer_cubic` | 测试三次曲线渲染 |
| `test_svg_renderer_no_control_points` | 测试无控制点渲染 |
| `test_svg_renderer_custom_style` | 测试自定义样式 |
| `test_curve_to_polyline` | 测试曲线转折线 |
| `test_points_to_text` | 测试点格式化 |

## 集成测试

### 测试文件

集成测试位于 `tests/integration_test.rs`，验证模块间的协作。

### 测试分类

#### 1. 点操作集成测试

```rust
#[test]
fn test_point_basic_operations() {
    let p1 = Point::new(3.0, 4.0);
    let p2 = Point::new(6.0, 8.0);

    // 距离
    assert!((p1.distance_to(&p2) - 5.0).abs() < 1e-10);

    // 插值
    let mid = p1.lerp(&p2, 0.5);
    assert!((mid.x - 4.5).abs() < 1e-10);
}
```

#### 2. 曲线操作集成测试

```rust
#[test]
fn test_quadratic_bezier_evaluation() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 端点
    let start = curve.evaluate(0.0);
    let end = curve.evaluate(1.0);
    assert!((start.x - 0.0).abs() < 1e-10);
    assert!((end.x - 100.0).abs() < 1e-10);

    // 中点
    let mid = curve.evaluate(0.5);
    assert!((mid.x - 50.0).abs() < 1e-10);
    assert!((mid.y - 50.0).abs() < 1e-10);
}
```

#### 3. 编辑器集成测试

```rust
#[test]
fn test_editor_split_curve() {
    let mut editor = CurveEditor::new();

    editor.add_cubic(CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    assert_eq!(editor.curve_count(), 1);

    let result = editor.split_curve(0, 0.5);
    assert!(result.is_some());
    assert_eq!(editor.curve_count(), 2);
}
```

#### 4. 渲染器集成测试

```rust
#[test]
fn test_svg_renderer_multiple_curves() {
    let renderer = SvgRenderer::new(400.0, 200.0);

    let curves = vec![
        BezierCurveType::Quadratic(QuadraticBezier::new(...)),
        BezierCurveType::Cubic(CubicBezier::new(...)),
    ];

    let svg = renderer.render_curves(&curves);

    assert!(svg.contains("<svg"));
    assert!(svg.contains("</svg>"));
    assert!(svg.matches("<path").count() >= 2);
}
```

## 边界情况测试

### 1. 退化曲线

```rust
#[test]
fn test_degenerate_curve() {
    // 所有控制点重合
    let curve = QuadraticBezier::new(
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
    );

    let point = curve.evaluate(0.5);
    assert!((point.x - 50.0).abs() < 1e-10);
    assert!((point.y - 50.0).abs() < 1e-10);

    let length = curve.length(10);
    assert!((length - 0.0).abs() < 1e-10);
}
```

### 2. 极小曲线

```rust
#[test]
fn test_very_small_curve() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(0.001, 0.001),
        Point::new(0.002, 0.0),
    );

    let length = curve.length(10);
    assert!(length < 0.01);
}
```

### 3. 极大曲线

```rust
#[test]
fn test_large_curve() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(1000.0, 5000.0),
        Point::new(5000.0, 5000.0),
        Point::new(10000.0, 0.0),
    );

    let length = curve.length(100);
    assert!(length > 10000.0);
}
```

### 4. 参数边界

```rust
#[test]
fn test_parameter_boundaries() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 负参数
    let t_neg = curve.evaluate(-0.1);
    assert!((t_neg.x - 0.0).abs() < 1e-10);

    // 超出参数
    let t_over = curve.evaluate(1.1);
    assert!((t_over.x - 100.0).abs() < 1e-10);
}
```

## 测试工具

### 断言宏

```rust
// 基本断言
assert_eq!(a, b);
assert_ne!(a, b);
assert!(condition);

// 浮点数比较
assert!((a - b).abs() < 1e-10);
```

### 测试辅助函数

```rust
// 创建测试曲线
fn create_test_quadratic() -> QuadraticBezier {
    QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    )
}
```

## 运行测试

### 命令

```bash
# 运行所有测试
cargo test

# 运行单元测试
cargo test --lib

# 运行集成测试
cargo test --test integration_test

# 运行特定测试
cargo test test_quadratic_bezier

# 显示测试输出
cargo test -- --nocapture

# 运行测试并显示时间
cargo test -- --report-time
```

### 测试输出示例

```
running 45 tests
test point::tests::test_point_creation ... ok
test point::tests::test_distance ... ok
test point::tests::test_lerp ... ok
test bezier::tests::test_quadratic_bezier_endpoints ... ok
test bezier::tests::test_cubic_bezier_endpoints ... ok
test subdivision::tests::test_quadratic_subdivision ... ok
test editor::tests::test_editor_add_curves ... ok
test renderer::tests::test_svg_renderer ... ok
test integration_test::test_point_basic_operations ... ok
test integration_test::test_quadratic_bezier_evaluation ... ok
...

test result: ok. 45 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

## 测试覆盖率

### 覆盖目标

- **行覆盖率**: > 90%
- **分支覆盖率**: > 80%
- **函数覆盖率**: 100%

### 覆盖率工具

```bash
# 安装 cargo-tarpaulin
cargo install cargo-tarpaulin

# 生成覆盖率报告
cargo tarpaulin --out Html

# 查看报告
open tarpaulin-report.html
```

## 持续集成

### GitHub Actions 配置

```yaml
name: Rust

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: cargo test
      - run: cargo clippy
      - run: cargo fmt --check
```

## 测试最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 格式: `test_<功能>_<场景>`
- 示例: `test_quadratic_bezier_endpoints`

### 2. 测试结构

```rust
#[test]
fn test_example() {
    // 1. 准备 (Arrange)
    let curve = QuadraticBezier::new(...);

    // 2. 执行 (Act)
    let result = curve.evaluate(0.5);

    // 3. 断言 (Assert)
    assert!((result.x - 50.0).abs() < 1e-10);
}
```

### 3. 测试独立性

- 每个测试应该独立运行
- 不依赖测试执行顺序
- 不共享可变状态

### 4. 测试可读性

- 测试应该易于理解
- 避免复杂的测试逻辑
- 使用有意义的变量名

## 已知测试限制

1. **浮点精度**: 使用 1e-10 作为精度阈值
2. **数值积分**: 曲线长度计算依赖采样数量
3. **最近点查找**: 牛顿迭代可能陷入局部最优

## 未来改进

1. **属性测试**: 使用 proptest 进行随机测试
2. **基准测试**: 添加性能基准测试
3. **模糊测试**: 使用 cargo-fuzz 进行模糊测试
4. **快照测试**: 对 SVG 输出进行快照测试
