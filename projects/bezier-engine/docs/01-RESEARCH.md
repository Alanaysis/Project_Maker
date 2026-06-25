# 01 - 市场调研

## 贝塞尔曲线简介

贝塞尔曲线（Bézier Curve）是计算机图形学中最重要的参数曲线之一，由法国工程师 Pierre Bézier 在 1960 年代为雷诺汽车公司设计车身曲线时发展而来。

### 历史背景

- **1959 年**: Paul de Casteljau 在雪铁龙公司独立发现了 de Casteljau 算法
- **1962 年**: Pierre Bézier 在雷诺公司发表了关于贝塞尔曲线的研究
- **1960-70 年代**: 贝塞尔曲线被广泛应用于 CAD/CAM 系统
- **1980 年代至今**: 成为 PostScript、TrueType、SVG 等标准的核心组件

### 数学定义

贝塞尔曲线是一种参数化曲线，由控制点 P₀, P₁, ..., Pₙ 定义：

```
B(t) = Σᵢ₌₀ⁿ (n choose i) * (1-t)^(n-i) * t^i * Pᵢ
```

其中：
- t ∈ [0, 1] 是参数
- (n choose i) 是二项式系数
- n 是曲线的阶数

## 现有实现分析

### Rust 生态系统

| 库 | 特点 | 适用场景 |
|---|---|---|
| `lyon` | 完整的 2D 图形库，包含贝塞尔曲线 | 游戏、UI 渲染 |
| `kurbo` | 简洁的 2D 曲线库 | 数据可视化 |
| `bezier-rs` | 专注于贝塞尔曲线 | 学习、研究 |
| `usvg` | SVG 解析和处理 | SVG 渲染 |

### 其他语言实现

| 语言 | 库 | 特点 |
|---|---|---|
| C++ | Skia | Google 的 2D 图形库 |
| JavaScript | Paper.js | 矢量图形框架 |
| Python | matplotlib | 数据可视化 |
| Java | JavaFX | 桌面 UI 框架 |

## 技术选型

### 为什么选择 Rust？

1. **性能**: 贝塞尔曲线计算涉及大量浮点运算，Rust 的零成本抽象和 SIMD 支持可以提供优秀的性能
2. **安全性**: Rust 的所有权系统避免了常见的内存安全问题
3. **学习价值**: 通过实现贝塞尔曲线引擎，可以深入理解 Rust 的 trait、泛型和模块系统
4. **无外部依赖**: 纯 Rust 实现，便于理解和维护

### 核心算法选择

1. **求值算法**: de Casteljau 算法
   - 数值稳定性好
   - 递归结构清晰
   - 便于实现细分

2. **细分算法**: 基于 de Casteljau 的细分
   - 固定点细分：在指定参数 t 处细分
   - 自适应细分：根据曲线平坦度自动决定细分深度

3. **渲染格式**: SVG
   - 矢量格式，无损缩放
   - 浏览器原生支持
   - 文本格式，易于调试

## 功能需求分析

### 核心功能

1. **曲线类型**
   - 二次贝塞尔曲线 (3 个控制点)
   - 三次贝塞尔曲线 (4 个控制点)

2. **曲线操作**
   - 求值：在参数 t 处计算曲线上的点
   - 导数：计算曲线的切线向量
   - 长度：数值积分计算曲线长度
   - 最近点：查找曲线上距离给定点最近的点

3. **细分算法**
   - 固定点细分：在指定参数处将曲线分为两段
   - 均匀细分：将曲线等分为 n 段
   - 自适应细分：根据曲线复杂度自动细分

4. **编辑操作**
   - 移动控制点
   - 分割曲线
   - 反转曲线方向
   - 曲线升阶（二次到三次）

5. **渲染输出**
   - SVG 格式输出
   - 控制点和连线显示
   - 自定义样式配置

### 扩展功能（可选）

- 贝塞尔曲线拼接（C0、C1、G1 连续）
- 贝塞尔曲面（张量积）
- 曲线拟合（给定点集拟合贝塞尔曲线）
- 碰撞检测（曲线与曲线、曲线与点）

## 性能考虑

### 计算复杂度

| 操作 | 时间复杂度 | 说明 |
|---|---|---|
| 求值 | O(n) | n 为曲线阶数 |
| 细分 | O(n) | 基于 de Casteljau |
| 长度计算 | O(k*n) | k 为积分段数 |
| 最近点查找 | O(k*n) | k 为采样点数 |

### 优化策略

1. **缓存**: 对于重复求值的曲线，可以缓存中间结果
2. **SIMD**: 对于批量计算，可以使用 SIMD 指令
3. **并行**: 自适应细分的不同分支可以并行处理
4. **近似**: 对于低精度要求，可以使用更简单的近似算法

## 参考资料

1. **书籍**
   - "The NURBS Book" - Les Piegl, Wayne Tiller
   - "Computer Graphics: Principles and Practice" - Hughes et al.
   - "A Primer on Bézier Curves" - Pomax (在线)

2. **论文**
   - Bézier, P. (1966). "Définition numérique des courbes et surfaces I"
   - de Casteljau, P. (1959). "Outillage méthodes calcul"

3. **在线资源**
   - [Wikipedia: Bézier curve](https://en.wikipedia.org/wiki/B%C3%A9zier_curve)
   - [A Primer on Bézier Curves](https://pomax.github.io/bezierinfo/)
   - [MDN: SVG Path](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths)
