//! # 贝塞尔曲线引擎 (Bézier Curve Engine)
//!
//! 一个用于创建、编辑和渲染贝塞尔曲线的 Rust 库。
//!
//! ## 功能特性
//!
//! - 支持二次和三次贝塞尔曲线
//! - 曲线细分算法（de Casteljau）
//! - 曲线编辑操作（移动控制点、分割曲线）
//! - SVG 格式输出
//! - 点在曲线上的最近点查找
//!
//! ## 快速开始
//!
//! ```rust
//! use bezier_engine::{Point, QuadraticBezier, CubicBezier, BezierCurve};
//!
//! // 创建二次贝塞尔曲线
//! let quad = QuadraticBezier::new(
//!     Point::new(0.0, 0.0),
//!     Point::new(50.0, 100.0),
//!     Point::new(100.0, 0.0),
//! );
//!
//! // 计算曲线上的点
//! let mid = quad.evaluate(0.5);
//! println!("中点: ({}, {})", mid.x, mid.y);
//! ```

pub mod point;
pub mod bezier;
pub mod subdivision;
pub mod editor;
pub mod renderer;

pub use point::Point;
pub use bezier::{BezierCurve, QuadraticBezier, CubicBezier, BezierCurveType};
pub use subdivision::{
    SubdivisionConfig, subdivide_quadratic, subdivide_cubic,
    adaptive_subdivide_quadratic, adaptive_subdivide_cubic,
    uniform_subdivide_quadratic, uniform_subdivide_cubic,
};
pub use editor::CurveEditor;
pub use renderer::{SvgRenderer, SvgStyle, SvgColor};
