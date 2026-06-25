# 光栅化引擎 (Rasterization Engine)

实现软件光栅化引擎，支持三角形填充、画线、矩形和圆形绘制。

## 核心循环

```
矢量图形 → 几何变换 → 光栅化 → 像素输出
```

## 学习目标

- 理解光栅化原理
- 掌握扫描线算法
- 学会抗锯齿

## 技术栈

- 主语言：Rust
- 依赖：无

## 项目结构

```
rasterization-engine/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── geometry.rs   # 几何结构
│   ├── rasterizer.rs # 帧缓冲
│   ├── renderer.rs   # 图层合成
│   └── shapes.rs     # 形状
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
cargo run --example triangle_rasterization
cargo run --example layered_rendering
cargo run --example barycentric_demo
```

### 演示

```bash
cargo run --release
```

## 核心功能

```rust
use rasterization::{Rasterizer, Triangle, Point};

let mut ras = Rasterizer::new(800, 600);
let tri = Triangle::new(
    Point::new(100.0, 50.0),
    Point::new(200.0, 200.0),
    Point::new(50.0, 200.0),
);
ras.fill_triangle(&tri, 0xff0000);
```
