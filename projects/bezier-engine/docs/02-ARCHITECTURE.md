# 02 - 架构设计

## 整体架构

贝塞尔曲线引擎采用模块化设计，各模块职责清晰，便于扩展和维护。

```
┌─────────────────────────────────────────────────────────┐
│                     bezier-engine                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌────────┐ │
│  │  Point   │  │  Bezier │  │ Subdivision │  │ Editor │ │
│  │  Module  │  │  Module │  │   Module    │  │ Module │ │
│  └────┬─────┘  └────┬────┘  └──────┬──────┘  └────┬───┘ │
│       │              │              │              │      │
│       └──────────────┴──────────────┴──────────────┘      │
│                          │                                │
│                    ┌─────┴─────┐                          │
│                    │ Renderer  │                          │
│                    │  Module   │                          │
│                    └───────────┘                          │
└─────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Point 模块 (`point.rs`)

**职责**: 提供二维点和向量的基本操作

**核心类型**:
```rust
pub struct Point {
    pub x: f64,
    pub y: f64,
}
```

**主要功能**:
- 点的创建和基本操作
- 向量运算（加法、减法、标量乘法）
- 距离计算
- 线性插值（lerp）
- 点积和叉积
- 归一化

**设计决策**:
- 使用 `f64` 而非 `f32` 以提供更高的精度
- 实现 `Copy` trait 以简化使用
- 实现 `Display` trait 便于调试
- 实现运算符重载以提供自然的语法

### 2. Bezier 模块 (`bezier.rs`)

**职责**: 实现贝塞尔曲线的核心数学

**核心类型**:
```rust
pub trait BezierCurve {
    fn control_points(&self) -> &[Point];
    fn degree(&self) -> usize;
    fn evaluate(&self, t: f64) -> Point;
    fn derivative_points(&self) -> Vec<Point>;
    fn evaluate_derivative(&self, t: f64) -> Point;
    fn length(&self, num_segments: usize) -> f64;
    fn closest_point_parameter(&self, point: &Point, num_samples: usize) -> f64;
}

pub struct QuadraticBezier {
    pub p0: Point,  // 起点
    pub p1: Point,  // 控制点
    pub p2: Point,  // 终点
}

pub struct CubicBezier {
    pub p0: Point,  // 起点
    pub p1: Point,  // 控制点 1
    pub p2: Point,  // 控制点 2
    pub p3: Point,  // 终点
}
```

**主要功能**:
- 曲线求值（de Casteljau 算法）
- 导数计算
- 曲线长度计算（数值积分）
- 最近点查找
- 包围盒计算（仅三次曲线）
- 曲线升阶（二次到三次）

**设计决策**:
- 使用 trait 抽象统一接口
- 具体类型公开控制点字段，便于编辑
- 求值使用 de Casteljau 算法而非 Bernstein 多项式，因为：
  - 数值稳定性更好
  - 便于实现细分
  - 递归结构清晰

### 3. Subdivision 模块 (`subdivision.rs`)

**职责**: 实现曲线细分算法

**核心类型**:
```rust
pub struct SubdivisionConfig {
    pub max_depth: usize,
    pub flatness_threshold: f64,
    pub min_segment_length: f64,
}
```

**主要功能**:
- 固定点细分（在指定参数 t 处细分）
- 均匀细分（等分为 n 段）
- 自适应细分（根据平坦度自动细分）
- 平坦度计算

**设计决策**:
- 使用 Builder 模式配置细分参数
- 自适应细分使用递归实现
- 平坦度定义为控制点到端点连线的最大距离

**算法流程**:
```
自适应细分:
1. 计算曲线平坦度
2. 如果平坦度 < 阈值，停止
3. 如果深度 >= 最大深度，停止
4. 在 t=0.5 处细分曲线
5. 递归处理左右两段
6. 合并结果
```

### 4. Editor 模块 (`editor.rs`)

**职责**: 提供曲线编辑功能

**核心类型**:
```rust
pub struct CurveEditor {
    curves: Vec<BezierCurveType>,
    selected_curve: Option<usize>,
    selected_point: Option<usize>,
}
```

**主要功能**:
- 添加/删除曲线
- 选择曲线和控制点
- 移动控制点
- 设置控制点位置
- 分割曲线
- 反转曲线方向
- 曲线升阶
- 查找最近点

**设计决策**:
- 使用枚举 `BezierCurveType` 统一处理不同类型的曲线
- 维护选中状态，便于交互式编辑
- 查找操作返回索引而非引用，避免借用冲突

### 5. Renderer 模块 (`renderer.rs`)

**职责**: 将曲线渲染为 SVG 格式

**核心类型**:
```rust
pub struct SvgRenderer {
    width: f64,
    height: f64,
    style: SvgStyle,
    background_color: Option<SvgColor>,
}

pub struct SvgStyle {
    pub stroke_color: SvgColor,
    pub stroke_width: f64,
    pub fill_color: Option<SvgColor>,
    pub control_point_color: SvgColor,
    pub control_point_radius: f64,
    pub control_line_color: SvgColor,
    pub show_control_points: bool,
    pub show_control_lines: bool,
}
```

**主要功能**:
- 渲染单条曲线
- 渲染多条曲线
- 渲染折线（细分结果）
- 自定义样式配置
- 控制点和连线显示

**设计决策**:
- 使用 Builder 模式配置渲染器
- SVG 直接生成字符串，无需额外依赖
- 支持透明背景

## 数据流

```
输入: 控制点
  │
  ▼
┌─────────────┐
│  BezierCurve │
│  创建曲线    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  求值/导数   │────▶│  编辑操作    │
│  计算       │     │  (Editor)   │
└──────┬──────┘     └──────┬──────┘
       │                    │
       ▼                    ▼
┌─────────────┐     ┌─────────────┐
│  细分算法    │     │  修改控制点  │
│  (Subdivide) │     │             │
└──────┬──────┘     └──────┬──────┘
       │                    │
       └──────────┬─────────┘
                  │
                  ▼
           ┌─────────────┐
           │  SVG 渲染    │
           │  (Renderer)  │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │  SVG 输出    │
           └─────────────┘
```

## 类型系统设计

### 枚举 vs Trait

项目同时使用了 trait 和枚举：

1. **Trait (`BezierCurve`)**:
   - 定义统一接口
   - 允许静态分发
   - 适用于算法实现

2. **枚举 (`BezierCurveType`)**:
   - 运行时多态
   - 适用于需要存储不同类型曲线的场景
   - 编辑器使用枚举管理曲线集合

### 为什么使用枚举而非 trait object？

```rust
// 使用枚举
pub enum BezierCurveType {
    Quadratic(QuadraticBezier),
    Cubic(CubicBezier),
}

// 使用 trait object
pub struct CurveEditor {
    curves: Vec<Box<dyn BezierCurve>>,
}
```

选择枚举的原因：
1. **性能**: 避免动态分发的开销
2. **简单性**: 不需要处理生命周期问题
3. **编辑需求**: 编辑器需要修改控制点，trait object 会导致借用问题

## 错误处理

### 设计原则

1. **防御性编程**: 输入验证和边界检查
2. **优雅降级**: 无效输入返回默认值而非 panic
3. **Option 类型**: 使用 `Option` 表示可能失败的操作
4. **无 panic**: 库代码不应 panic

### 示例

```rust
// 边界检查
pub fn evaluate(&self, t: f64) -> Point {
    let t = t.max(0.0).min(1.0);  // 钳位到 [0, 1]
    // ...
}

// Option 返回
pub fn get_curve(&self, index: usize) -> Option<&BezierCurveType> {
    self.curves.get(index)
}
```

## 扩展性设计

### 添加新的曲线类型

1. 定义新的结构体
2. 实现 `BezierCurve` trait
3. 添加到 `BezierCurveType` 枚举
4. 更新编辑器和渲染器

### 添加新的渲染格式

1. 创建新的渲染器模块
2. 实现类似的接口
3. 复用现有的曲线类型

### 添加新的细分算法

1. 在 `subdivision` 模块中添加新函数
2. 使用 `SubdivisionConfig` 配置参数
3. 返回统一的 `Vec<Point>` 格式

## 依赖关系

```
point.rs ◄─── bezier.rs
   │              │
   │              ▼
   │         subdivision.rs
   │              │
   ▼              ▼
editor.rs ◄─── renderer.rs
```

- `point.rs` 是基础模块，被所有其他模块依赖
- `bezier.rs` 依赖 `point.rs`
- `subdivision.rs` 依赖 `bezier.rs` 和 `point.rs`
- `editor.rs` 依赖 `bezier.rs` 和 `subdivision.rs`
- `renderer.rs` 依赖 `bezier.rs`、`subdivision.rs` 和 `point.rs`
