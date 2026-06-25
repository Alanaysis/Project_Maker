# 技术设计文档

## 1. 架构概述

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Parser  │    │  Shapes  │    │ Renderer │
│ (SVG)    │───▶│ (SVG)    │───▶│ (SVG)    │
└──────────┘    └──────────┘    └──────────┘
       │                    │
       └───────┬────────────┘
               ▼
         ┌─────────────┐
         │  SVG Output │
         └─────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| SVGParser | SVG 解析 | `src/parser.rs` |
| Path | 路径数据 | `src/path.rs` |
| Shapes | 形状定义 | `src/shapes.rs` |
| Renderer | SVG 渲染 | `src/renderer.rs` |
| SVGColor | 颜色系统 | `src/color.rs` |

## 2. 数据设计

### 形状 trait
```rust
pub trait Shape {
    fn render_svg(&self) -> String;
    fn fill_color(&self) -> Option<SVGColor>;
    fn stroke_color(&self) -> Option<SVGColor>;
    fn stroke_width(&self) -> f64;
}
```

### 形状类型
- Rect: 矩形
- Circle: 圆形
- Ellipse: 椭圆
- Line: 线段
- Polygon: 多边形
- Polyline: 折线
- Text: 文本

## 3. 接口设计

```rust
Renderer::new(width, height)
Renderer::add_shape(shape)
Renderer::render() -> String
Renderer::save(path) -> Result<()>
```
