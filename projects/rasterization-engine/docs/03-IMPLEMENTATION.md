# 实现细节

## 1. Barycentric 三角形填充

### 算法
对帧缓冲中每个像素，计算其在三角形内的重心坐标。

### 核心代码
```rust
pub fn barycentric(&self, p: &Point) -> Option<(f64, f64, f64)> {
    let denom = (self.b.y - self.c.y) * (self.a.x - self.c.x)
        + (self.c.x - self.b.x) * (self.a.y - self.c.y);
    let w1 = ((self.b.y - self.c.y) * (p.x - self.c.x)
        + (self.c.x - self.b.x) * (p.y - self.c.y)) / denom;
    let w2 = ((self.c.y - self.a.y) * (p.x - self.c.x)
        + (self.a.x - self.c.x) * (p.y - self.c.y)) / denom;
    let w3 = 1.0 - w1 - w2;
    if w1 >= 0.0 && w2 >= 0.0 && w3 >= 0.0 {
        Some((w1, w2, w3))
    } else {
        None
    }
}
```

## 2. Bresenham 画线

整数增量算法，用误差项决定下一步方向。

## 3. 圆形绘制

中点圆算法的简化版：对包围盒内每个像素判断 `dx² + dy² <= r²`。
