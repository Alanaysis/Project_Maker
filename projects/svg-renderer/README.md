# SVG 渲染器 (SVG Renderer)

实现 SVG 矢量图形渲染器，支持路径解析、样式应用和渲染输出。

## 核心循环

```
SVG 解析 → 路径计算 → 样式应用 → 渲染输出
```

## 学习目标

- 理解 SVG 规范
- 掌握路径解析
- 学会渐变渲染

## 技术栈

- 主语言：Rust
- 依赖：无

## 项目结构

```
svg-renderer/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── parser.rs     # SVG 解析
│   ├── path.rs       # 路径
│   ├── shapes.rs     # 形状
│   ├── renderer.rs   # 渲染器
│   └── color.rs      # 颜色
├── tests/
├── examples/
└── docs/
```

## 快速开始

### 运行测试

```bash
cargo test
```

### 运行示例

```bash
cargo run --example star_rendering
cargo run --example shape_demo
```

### 演示

```bash
cargo run --release
```

## 核心功能

```rust
use svg_renderer::{Renderer, SVGColor, Circle, Rect};

let mut renderer = Renderer::new(400.0, 300.0);
renderer.background = Some(SVGColor::Named("white"));

renderer.add_shape(Box::new(Circle::new(200.0, 150.0, 50.0)
    .with_fill(SVGColor::RGB(255, 100, 100))));
renderer.add_shape(Box::new(Rect::new(100.0, 200.0, 80.0, 60.0)
    .with_fill(SVGColor::RGB(100, 200, 100))));

renderer.save("output.svg")?;
```
