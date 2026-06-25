# 技术设计文档

## 1. 架构概述

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Shapes     │    │ Rasterizer  │    │  Renderer   │
│ (Triangle,   │───▶│ (Framebuf)  │───▶│ (Layered)   │
│  Circle,     │    │             │    │             │
│  Polygon)    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| Geometry | 几何数据结构 | `src/geometry.rs` |
| Rasterizer | 帧缓冲和光栅化 | `src/rasterizer.rs` |
| Renderer | 图层合成 | `src/renderer.rs` |
| Shapes | 形状绘制 | `src/shapes.rs` |

## 2. 核心算法

### Barycentric 三角形填充
对每个像素计算重心坐标，三个坐标都 >= 0 则在三角形内。

### Bresenham 画线
整数增量算法，无浮点运算。

## 3. 数据设计

### Framebuffer
```
buffer: Vec<u32>  // width x height, ABGR format
```

## 4. 接口设计

```rust
Rasterizer::new(width, height)
Rasterizer::fill_triangle(tri, color)
Rasterizer::draw_line(x0, y0, x1, y1, color)
Rasterizer::fill_rect(x0, y0, x1, y1, color)
Rasterizer::set_pixel(x, y, color)
```
