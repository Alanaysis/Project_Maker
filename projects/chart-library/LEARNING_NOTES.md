# 学习笔记

## 核心知识点

### 1. Canvas 渲染原理

Canvas 是基于像素的渲染技术，核心 API 包括：
- `getContext('2d')`: 获取 2D 渲染上下文
- `beginPath()`: 开始新路径
- `moveTo()` / `lineTo()`: 绘制直线
- `arc()`: 绘制圆弧
- `fill()` / `stroke()`: 填充/描边

**关键点**: Canvas 是立即模式，绘制后无法单独修改图形元素。

### 2. 坐标系统

图表库的核心是坐标转换：
```
数据空间 → 归一化 → 屏幕空间

归一化: value_norm = (value - min) / (max - min)
屏幕: pixel = padding + value_norm * plotWidth
```

### 3. 比例尺设计

比例尺是数据到可视化的映射：
- **线性比例尺**: 连续数据映射
- **分类比例尺**: 离散数据映射
- **时间比例尺**: 时间数据映射

### 4. 事件处理

Canvas 事件需要手动实现命中检测：
- 计算鼠标坐标
- 判断是否在图形区域内
- 触发相应事件

## 实践心得

### 1. 高 DPI 适配

```typescript
// 设置 Canvas 物理尺寸
canvas.width = width * dpr;
canvas.height = height * dpr;

// 设置 CSS 尺寸
canvas.style.width = `${width}px`;
canvas.style.height = `${height}px`;

// 缩放上下文
ctx.scale(dpr, dpr);
```

### 2. 动画实现

使用 requestAnimationFrame 实现流畅动画：
```typescript
function animate(duration: number, callback: (t: number) => void): void {
  const start = performance.now();
  function frame(time: number) {
    const t = Math.min((time - start) / duration, 1);
    callback(t);
    if (t < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
```

### 3. 内存管理

- 及时移除事件监听器
- 避免在渲染循环中创建对象
- 使用对象池复用频繁创建的对象

## 遇到的问题与解决方案

### 问题 1: Canvas 尺寸与显示尺寸不一致
**现象**: 图表模糊
**原因**: 未考虑 devicePixelRatio
**解决方案**: 设置正确的物理像素尺寸

### 问题 2: 鼠标事件坐标不准确
**现象**: 点击位置偏移
**原因**: CSS 尺寸与 Canvas 尺寸不匹配
**解决方案**: 正确转换坐标

### 问题 3: 大数据量卡顿
**现象**: 渲染慢、交互卡
**原因**: 每帧重绘所有元素
**解决方案**: 脏矩形重绘、虚拟化

## 总结

图表库开发的核心挑战：
1. 坐标系统的正确实现
2. 渲染性能优化
3. 交互体验设计
4. 跨浏览器兼容

通过这个项目，深入理解了：
- Canvas 渲染机制
- 数据可视化原理
- 前端性能优化
