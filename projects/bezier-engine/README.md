# 贝塞尔曲线引擎 (Bézier Curve Engine)

一个用于创建、编辑和渲染贝塞尔曲线的 Rust 库。

## 项目简介

贝塞尔曲线是计算机图形学中最重要的数学工具之一，广泛应用于字体设计、动画路径、UI 设计等领域。本项目实现了一个完整的贝塞尔曲线引擎，支持：

- **二次和三次贝塞尔曲线** - 两种最常用的曲线类型
- **曲线细分算法** - de Casteljau 算法实现精确细分
- **曲线编辑操作** - 移动控制点、分割曲线、反转方向等
- **SVG 格式输出** - 直接生成可在浏览器中查看的 SVG 文件

## 核心特性

- ✅ 二次贝塞尔曲线 (Quadratic Bézier)
- ✅ 三次贝塞尔曲线 (Cubic Bézier)
- ✅ de Casteljau 求值算法
- ✅ 曲线导数计算
- ✅ 固定点细分
- ✅ 自适应细分（基于平坦度）
- ✅ 均匀细分
- ✅ 控制点编辑
- ✅ 曲线分割
- ✅ 曲线反转
- ✅ 曲线升阶（二次到三次）
- ✅ 最近点查找
- ✅ SVG 渲染输出
- ✅ 自定义样式配置

## 快速开始

### 安装

将以下内容添加到你的 `Cargo.toml`:

```toml
[dependencies]
bezier-engine = { path = "../bezier-engine" }
```

### 基本用法

```rust
use bezier_engine::{Point, QuadraticBezier, CubicBezier, BezierCurve};

// 创建二次贝塞尔曲线
let curve = QuadraticBezier::new(
    Point::new(0.0, 0.0),    // 起点
    Point::new(50.0, 100.0),  // 控制点
    Point::new(100.0, 0.0),   // 终点
);

// 计算曲线上的点
let start = curve.evaluate(0.0);  // (0, 0)
let mid = curve.evaluate(0.5);    // (50, 50)
let end = curve.evaluate(1.0);    // (100, 0)

// 计算曲线长度
let length = curve.length(100);
```

### 曲线细分

```rust
use bezier_engine::{
    CubicBezier, BezierCurve,
    SubdivisionConfig, adaptive_subdivide_cubic,
};

let curve = CubicBezier::new(
    Point::new(0.0, 0.0),
    Point::new(25.0, 100.0),
    Point::new(75.0, 100.0),
    Point::new(100.0, 0.0),
);

// 自适应细分
let config = SubdivisionConfig::new()
    .with_max_depth(5)
    .with_flatness(1.0);

let points = adaptive_subdivide_cubic(&curve, &config);
println!("细分结果: {} 个点", points.len());
```

### SVG 输出

```rust
use bezier_engine::{CubicBezier, SvgRenderer, SvgStyle, SvgColor};

let curve = CubicBezier::new(
    Point::new(20.0, 100.0),
    Point::new(80.0, 20.0),
    Point::new(220.0, 180.0),
    Point::new(280.0, 100.0),
);

// 自定义样式
let style = SvgStyle {
    stroke_color: SvgColor::rgb(0, 128, 255),
    stroke_width: 3.0,
    ..SvgStyle::default()
};

// 渲染为 SVG
let svg = SvgRenderer::new(300.0, 200.0)
    .with_style(style)
    .render_cubic(&curve);

// 保存到文件
std::fs::write("curve.svg", svg).unwrap();
```

### 曲线编辑

```rust
use bezier_engine::{Point, QuadraticBezier, CurveEditor};

let mut editor = CurveEditor::new();

// 添加曲线
editor.add_quadratic(QuadraticBezier::new(
    Point::new(0.0, 0.0),
    Point::new(50.0, 100.0),
    Point::new(100.0, 0.0),
));

// 选择并移动控制点
editor.select_point(0, 1);
editor.move_selected_point(Point::new(10.0, -20.0));

// 分割曲线
editor.split_curve(0, 0.5);
```

## 项目结构

```
bezier-engine/
├── Cargo.toml
├── README.md
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

## 核心概念

### 贝塞尔曲线数学

贝塞尔曲线是一种参数化曲线，由控制点定义：

**二次贝塞尔曲线 (n=2)**:
```
B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
```

**三次贝塞尔曲线 (n=3)**:
```
B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
```

### de Casteljau 算法

de Casteljau 算法是一种数值稳定的贝塞尔曲线求值方法：

1. 对控制点序列进行线性插值
2. 重复步骤 1，直到只剩一个点
3. 该点即为曲线在参数 t 处的值

### 曲线细分

细分算法将一条曲线分割为两条：

1. 使用 de Casteljau 算法在参数 t 处计算中间点
2. 左段使用前半部分控制点
3. 右段使用后半部分控制点

### 自适应细分

自适应细分根据曲线的"平坦度"自动决定细分深度：

1. 计算控制点到端点连线的最大距离
2. 如果距离小于阈值，停止细分
3. 否则，将曲线一分为二，递归处理

## 运行示例

```bash
# 运行演示程序
cargo run

# 运行基本曲线示例
cargo run --example basic_curves

# 运行曲线细分示例
cargo run --example curve_subdivision

# 运行 SVG 输出示例
cargo run --example svg_output

# 运行交互式编辑器示例
cargo run --example interactive_editor
```

## 运行测试

```bash
# 运行所有测试
cargo test

# 运行单元测试
cargo test --lib

# 运行集成测试
cargo test --test integration_test

# 运行特定测试
cargo test test_quadratic_bezier
```

## 学习资源

### 贝塞尔曲线

- [Bézier Curve - Wikipedia](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)
- [A Primer on Bézier Curves](https://pomax.github.io/bezierinfo/)
- [The Beauty of Bézier Curves](https://www.youtube.com/watch?v=aVwxzDHniEw)

### de Casteljau 算法

- [De Casteljau's Algorithm](https://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm)
- [Bézier Curves and de Casteljau's Algorithm](https://www.youtube.com/watch?v=YATikPP2q70)

### SVG

- [SVG Tutorial](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial)
- [SVG Path Specification](https://www.w3.org/TR/SVG/paths.html)

## 许可证

MIT License
