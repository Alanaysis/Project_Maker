# 实现细节

## 1. SVG 颜色系统

支持命名颜色、RGB、RGBA、Hex 格式。

### 核心代码
```rust
pub enum SVGColor {
    Named(&'static str),
    RGB(u8, u8, u8),
    RGBA(u8, u8, u8, f64),
    Hex(u32),
}
```

## 2. 形状渲染

每个形状实现 `render_svg()` 方法，输出 SVG 标签。

## 3. 渲染器

收集所有形状，输出完整 SVG 文档。
