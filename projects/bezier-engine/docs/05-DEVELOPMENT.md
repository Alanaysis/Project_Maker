# 05 - 开发指南

## 开发环境设置

### 前置要求

- Rust 1.70 或更高版本
- Cargo（随 Rust 一起安装）
- Git（可选，用于版本控制）

### 安装 Rust

```bash
# 使用 rustup 安装
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 验证安装
rustc --version
cargo --version
```

### 克隆项目

```bash
git clone <repository-url>
cd bezier-engine
```

## 项目结构

```
bezier-engine/
├── Cargo.toml          # 项目配置
├── README.md           # 项目说明
├── src/
│   ├── lib.rs          # 库入口
│   ├── main.rs         # 演示程序
│   ├── point.rs        # 二维点/向量
│   ├── bezier.rs       # 贝塞尔曲线实现
│   ├── subdivision.rs  # 细分算法
│   ├── editor.rs       # 曲线编辑器
│   └── renderer.rs     # SVG 渲染器
├── tests/
│   └── integration_test.rs
├── examples/
│   ├── basic_curves.rs
│   ├── curve_subdivision.rs
│   ├── svg_output.rs
│   └── interactive_editor.rs
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-ARCHITECTURE.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 开发工作流

### 1. 构建项目

```bash
# 检查代码
cargo check

# 构建项目
cargo build

# 构建发布版本
cargo build --release
```

### 2. 运行项目

```bash
# 运行演示程序
cargo run

# 运行示例
cargo run --example basic_curves
cargo run --example curve_subdivision
cargo run --example svg_output
cargo run --example interactive_editor
```

### 3. 运行测试

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
```

### 4. 代码质量

```bash
# 格式化代码
cargo fmt

# 检查代码风格
cargo clippy

# 检查文档
cargo doc --open
```

## 编码规范

### 1. 命名规范

- **类型**: PascalCase (`Point`, `QuadraticBezier`)
- **函数**: snake_case (`evaluate`, `subdivide_cubic`)
- **常量**: SCREAMING_SNAKE_CASE (`MAX_DEPTH`)
- **模块**: snake_case (`point`, `bezier`)

### 2. 文档规范

- 所有公共 API 必须有文档注释
- 使用 `///` 而非 `//`
- 包含示例代码

```rust
/// 在参数 t 处求值 (0 <= t <= 1)
///
/// # Arguments
///
/// * `t` - 参数值，范围 [0, 1]
///
/// # Returns
///
/// 曲线在参数 t 处的点
///
/// # Examples
///
/// ```
/// use bezier_engine::{Point, QuadraticBezier, BezierCurve};
///
/// let curve = QuadraticBezier::new(
///     Point::new(0.0, 0.0),
///     Point::new(50.0, 100.0),
///     Point::new(100.0, 0.0),
/// );
///
/// let point = curve.evaluate(0.5);
/// assert!((point.x - 50.0).abs() < 1e-10);
/// ```
pub fn evaluate(&self, t: f64) -> Point {
    // ...
}
```

### 3. 错误处理

- 使用 `Option` 或 `Result` 处理可能失败的操作
- 避免 panic，除非是编程错误
- 提供有意义的错误信息

```rust
// 好的做法
pub fn get_curve(&self, index: usize) -> Option<&BezierCurveType> {
    self.curves.get(index)
}

// 不好的做法
pub fn get_curve(&self, index: usize) -> &BezierCurveType {
    &self.curves[index]  // 可能 panic
}
```

### 4. 测试规范

- 每个公共函数都应该有测试
- 测试应该独立且可重复
- 使用描述性的测试名称

```rust
#[test]
fn test_quadratic_bezier_endpoints() {
    // 准备
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 执行
    let start = curve.evaluate(0.0);
    let end = curve.evaluate(1.0);

    // 断言
    assert!((start.x - 0.0).abs() < 1e-10);
    assert!((end.x - 100.0).abs() < 1e-10);
}
```

## 添加新功能

### 1. 添加新的曲线类型

1. 在 `bezier.rs` 中定义新的结构体
2. 实现 `BezierCurve` trait
3. 添加到 `BezierCurveType` 枚举
4. 更新编辑器和渲染器
5. 编写测试

```rust
// 1. 定义结构体
pub struct QuarticBezier {
    pub p0: Point,
    pub p1: Point,
    pub p2: Point,
    pub p3: Point,
    pub p4: Point,
}

// 2. 实现 trait
impl BezierCurve for QuarticBezier {
    fn degree(&self) -> usize {
        4
    }

    fn evaluate(&self, t: f64) -> Point {
        // de Casteljau 算法
        // ...
    }
}

// 3. 添加到枚举
pub enum BezierCurveType {
    Quadratic(QuadraticBezier),
    Cubic(CubicBezier),
    Quartic(QuarticBezier),  // 新增
}
```

### 2. 添加新的细分算法

1. 在 `subdivision.rs` 中添加新函数
2. 使用 `SubdivisionConfig` 配置参数
3. 返回统一的 `Vec<Point>` 格式
4. 编写测试

```rust
// 添加新的细分算法
pub fn uniform_subdivide_quartic(
    curve: &QuarticBezier,
    n: usize,
) -> Vec<Point> {
    let mut points = Vec::with_capacity(n + 1);
    for i in 0..=n {
        let t = i as f64 / n as f64;
        points.push(curve.evaluate(t));
    }
    points
}
```

### 3. 添加新的渲染格式

1. 创建新的渲染器模块
2. 实现类似的接口
3. 复用现有的曲线类型
4. 编写测试

```rust
// 添加 JSON 渲染器
pub struct JsonRenderer;

impl JsonRenderer {
    pub fn render_curve(&self, curve: &BezierCurveType) -> String {
        serde_json::to_string_pretty(&curve).unwrap()
    }
}
```

## 调试技巧

### 1. 使用 println! 调试

```rust
fn evaluate(&self, t: f64) -> Point {
    println!("Evaluating at t={}", t);
    println!("Control points: {:?}", self.control_points());
    // ...
}
```

### 2. 使用 dbg! 宏

```rust
fn evaluate(&self, t: f64) -> Point {
    dbg!(t);
    dbg!(self.p0);
    // ...
}
```

### 3. 可视化调试

生成 SVG 文件进行可视化调试：

```rust
let svg = renderer.render_curve(&curve);
std::fs::write("debug.svg", svg).unwrap();
```

### 4. 单步调试

使用 `cargo test` 的 `--nocapture` 选项查看输出：

```bash
cargo test -- --nocapture
```

## 性能优化

### 1. 使用基准测试

```rust
#[bench]
fn bench_quadratic_evaluate(b: &mut Bencher) {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    b.iter(|| {
        for i in 0..1000 {
            let t = i as f64 / 1000.0;
            curve.evaluate(t);
        }
    });
}
```

### 2. 使用 cargo-flamegraph

```bash
# 安装
cargo install flamegraph

# 生成火焰图
cargo flamegraph --bench
```

### 3. 优化热点

1. **避免不必要的分配**: 使用迭代而非递归
2. **使用距离平方**: 避免开方运算
3. **提前终止**: 在满足条件时提前退出循环
4. **缓存结果**: 对于重复计算，缓存结果

## 发布流程

### 1. 版本管理

使用语义化版本：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 更改
MINOR: 向后兼容的功能添加
PATCH: 向后兼容的 bug 修复
```

### 2. 更新版本号

```toml
# Cargo.toml
[package]
version = "0.2.0"
```

### 3. 生成变更日志

```markdown
# Changelog

## [0.2.0] - 2024-01-01

### Added
- 添加四次贝塞尔曲线支持
- 添加 JSON 渲染器

### Fixed
- 修复自适应细分的边界情况

## [0.1.0] - 2024-01-01

### Added
- 初始版本
- 二次和三次贝塞尔曲线
- SVG 渲染器
```

### 4. 发布到 crates.io

```bash
# 登录
cargo login <token>

# 发布
cargo publish
```

## 常见问题

### 1. 编译错误

**问题**: `error[E0382]: borrow of moved value`

**解决**: 使用引用而非移动

```rust
// 错误
let curve = QuadraticBezier::new(...);
let points = curve.control_points();
let curve = curve;  // 移动

// 正确
let curve = QuadraticBezier::new(...);
let points = curve.control_points();
let curve = &curve;  // 引用
```

### 2. 浮点精度问题

**问题**: 浮点数比较失败

**解决**: 使用 epsilon 比较

```rust
// 错误
assert_eq!(a, b);

// 正确
assert!((a - b).abs() < 1e-10);
```

### 3. 生命周期问题

**问题**: `error[E0597]: borrowed value does not live long enough`

**解决**: 使用 `clone()` 或调整生命周期

```rust
// 错误
let points = curve.control_points();

// 正确
let points = curve.control_points().to_vec();
```

## 学习资源

### Rust 官方资源

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Rust Reference](https://doc.rust-lang.org/reference/)

### 贝塞尔曲线资源

- [A Primer on Bézier Curves](https://pomax.github.io/bezierinfo/)
- [Bézier Curve - Wikipedia](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)

### 图形学资源

- [Computer Graphics: Principles and Practice](https://www.amazon.com/Computer-Graphics-Principles-Practice-3rd/dp/0321399528)
- [SVG Tutorial](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial)

## 贡献指南

### 1. Fork 项目

```bash
# Fork 到你的 GitHub 账号
# 克隆你的 fork
git clone https://github.com/your-username/bezier-engine.git
```

### 2. 创建分支

```bash
git checkout -b feature/my-feature
```

### 3. 提交更改

```bash
git add .
git commit -m "feat: 添加我的功能"
```

### 4. 推送并创建 PR

```bash
git push origin feature/my-feature
# 在 GitHub 上创建 Pull Request
```

### 5. 代码审查

- 确保所有测试通过
- 确保代码符合编码规范
- 添加必要的文档
- 更新变更日志
