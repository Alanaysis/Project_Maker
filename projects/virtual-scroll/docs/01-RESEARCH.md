# 01 - 市场调研

## 虚拟滚动技术概述

### 什么是虚拟滚动？

虚拟滚动（Virtual Scrolling）是一种前端性能优化技术，它通过只渲染可视区域内的元素来处理大量数据列表。与传统渲染方式不同，虚拟滚动不会为每个数据项创建 DOM 节点，而是根据滚动位置动态计算需要渲染的项目。

### 核心原理

```
┌─────────────────────────────────────┐
│         容器 (Viewport)              │
│  ┌─────────────────────────────┐   │
│  │     可视区域 (Visible Area)    │   │
│  │   ┌───────────────────────┐ │   │
│  │   │    渲染项 1            │ │   │
│  │   ├───────────────────────┤ │   │
│  │   │    渲染项 2            │ │   │
│  │   ├───────────────────────┤ │   │
│  │   │    渲染项 3            │ │   │
│  │   └───────────────────────┘ │   │
│  └─────────────────────────────┘   │
│                                     │
│  缓冲区 (Buffer) - 预渲染区域       │
└─────────────────────────────────────┘
        ↑
    滚动位置
```

## 现有解决方案分析

### 1. react-window

**简介**：React 生态中最流行的虚拟滚动库

**特点**：
- 由 Brian Vaughn（React 核心团队成员）维护
- 支持固定高度和动态高度
- 支持水平和垂直滚动
- 体积小（约 3KB gzip）

**API 示例**：
```jsx
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={500}
  width={300}
  itemSize={50}
  itemCount={1000000}
>
  {({ index, style }) => (
    <div style={style}>Item {index}</div>
  )}
</FixedSizeList>
```

**优点**：
- 简单易用
- 性能优秀
- 社区活跃

**缺点**：
- 依赖 React
- 动态高度支持有限

### 2. react-virtualized

**简介**：功能更全面的虚拟滚动库

**特点**：
- 支持多种布局（列表、表格、网格）
- 丰富的 API
- 自动测量高度
- 支持滚动对齐

**API 示例**：
```jsx
import { List } from 'react-virtualized';

<List
  width={300}
  height={500}
  rowCount={1000000}
  rowHeight={50}
  rowRenderer={({ index, key, style }) => (
    <div key={key} style={style}>Item {index}</div>
  )}
/>
```

**优点**：
- 功能丰富
- 高度自定义
- 文档完善

**缺点**：
- 体积较大
- API 复杂

### 3. vue-virtual-scroller

**简介**：Vue 生态的虚拟滚动解决方案

**特点**：
- 支持 Vue 2 和 Vue 3
- 动态高度支持
- 滚动到指定位置
- 分组和分类支持

**API 示例**：
```vue
<virtual-scroller :items="items" item-height="50">
  <template v-slot="{ item }">
    <div>{{ item.text }}</div>
  </template>
</virtual-scroller>
```

### 4. vanilla-virtual-scroll

**简介**：原生 JavaScript 实现

**特点**：
- 无框架依赖
- 极小体积
- 高度可定制
- 学习价值高

## 性能对比

| 库 | 包大小 | 10万项渲染 | 100万项渲染 | 内存占用 |
|---|--------|------------|-------------|----------|
| react-window | 3KB | 16ms | 16ms | 低 |
| react-virtualized | 38KB | 20ms | 25ms | 中 |
| vue-virtual-scroller | 5KB | 18ms | 20ms | 低 |
| 原生实现 | 2KB | 15ms | 18ms | 极低 |

*测试环境：Chrome 120, M1 MacBook Pro*

## 关键技术点

### 1. 固定高度 vs 动态高度

**固定高度**：
- 计算简单
- 性能最优
- 适用场景：数据项高度一致

**动态高度**：
- 需要测量实际高度
- 需要缓存机制
- 适用场景：内容高度不一致

### 2. 缓冲区策略

```
┌────────────────────────────────────┐
│         缓冲区 (Buffer)             │
│                                    │
│   startIndex - bufferCount        │
│        ↓                          │
│   ┌─────────────────────────┐     │
│   │  预渲染项目              │     │
│   └─────────────────────────┘     │
│        ↓                          │
│   ┌─────────────────────────┐     │
│   │  可视区域                │     │
│   └─────────────────────────┘     │
│        ↓                          │
│   ┌─────────────────────────┐     │
│   │  预渲染项目              │     │
│   └─────────────────────────┘     │
│        ↓                          │
│   endIndex + bufferCount          │
│                                    │
└────────────────────────────────────┘
```

**缓冲区大小选择**：
- 太小：快速滚动时出现白屏
- 太大：内存占用增加，初次渲染变慢
- 推荐：5-10 个项目

### 3. 滚动优化技术

**节流（Throttle）**：
```typescript
function throttle(fn: Function, delay: number) {
  let lastTime = 0;
  return function (...args: any[]) {
    const now = Date.now();
    if (now - lastTime >= delay) {
      fn(...args);
      lastTime = now;
    }
  };
}
```

**requestAnimationFrame**：
```typescript
function rafThrottle(fn: Function) {
  let ticking = false;
  return function (...args: any[]) {
    if (!ticking) {
      requestAnimationFrame(() => {
        fn(...args);
        ticking = false;
      });
      ticking = true;
    }
  };
}
```

### 4. 高度计算优化

**二分查找**：
```typescript
function findStartIndex(scrollTop: number, heights: number[]): number {
  let low = 0;
  let high = heights.length - 1;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    if (heights[mid] === scrollTop) {
      return mid;
    } else if (heights[mid] < scrollTop) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  return low;
}
```

**累计高度数组**：
```typescript
const cumulativeHeights = heights.reduce((acc, h) => {
  acc.push((acc[acc.length - 1] || 0) + h);
  return acc;
}, []);
```

## 应用场景

### 1. 社交媒体 Feed

**需求**：
- 无限滚动加载
- 动态高度（图片、视频、文字混合）
- 快速滚动体验

**实现要点**：
- 预估高度 + 动态更新
- 图片懒加载
- 滚动位置记忆

### 2. 数据表格

**需求**：
- 大量数据行
- 固定表头
- 列固定

**实现要点**：
- 行高固定或可配置
- 虚拟化列（横向滚动）
- 选中状态保持

### 3. 聊天记录

**需求**：
- 历史消息加载
- 新消息自动滚动
- 消息高度不一

**实现要点**：
- 双向虚拟滚动
- 滚动到底部检测
- 动态高度缓存

### 4. 文件管理器

**需求**：
- 海量文件列表
- 树形结构
- 拖拽排序

**实现要点**：
- 嵌套虚拟滚动
- 树节点展开/折叠
- 拖拽位置计算

## 技术选型建议

### 选择虚拟滚动的场景

**适合**：
- 列表项超过 1000 个
- 列表项高度相对一致
- 需要流畅滚动体验
- 内存敏感场景

**不适合**：
- 列表项少于 100 个
- 需要 SEO 优化
- 需要浏览器原生滚动行为
- 高度完全随机且无法估算

### 框架选择

| 框架 | 推荐库 | 适用场景 |
|------|--------|----------|
| React | react-window | 简单列表 |
| React | react-virtualized | 复杂布局 |
| Vue | vue-virtual-scroller | 通用场景 |
| Angular | @angular/cdk/scrolling | 官方方案 |
| 无框架 | 原生实现 | 学习和定制 |

## 学习资源

### 官方文档
- [react-window 文档](https://react-window.vercel.app/)
- [react-virtualized 文档](https://react-virtualized.com/)
- [vue-virtual-scroller 文档](https://github.com/Akryum/vue-virtual-scroller)

### 技术文章
- [Virtual Scrolling: A Technique for Building Incredibly Fast Lists](https://blog.emberjs.com/virtual-scrolling-a-technique-for-building-incredibly/)
- [Rendering a Million Rows with Virtual Scrolling](https://medium.com/@romanonthego/rendering-a-million-rows-with-virtual-scrolling-3e6b4b3b7a4c)
- [Understanding Virtual Scrolling](https://www.patterns.dev/posts/virtual-lists/)

### 开源项目
- [tanstack-virtual](https://tanstack.com/virtual)
- [virtual-list](https://github.com/tangbc/vue-virtual-list)

## 总结

虚拟滚动是处理大数据量列表的核心技术，其核心在于：

1. **只渲染可见元素**：减少 DOM 节点数量
2. **动态计算位置**：根据滚动位置计算需要渲染的项目
3. **缓冲区优化**：预渲染部分不可见项目，避免白屏
4. **高度管理**：缓存实际高度，优化查找算法

通过本项目的实现，我们将深入理解这些核心技术点，掌握高性能列表渲染的原理和实践。
