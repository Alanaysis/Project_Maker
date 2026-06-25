//! 贝塞尔曲线实现
//!
//! 实现二次和三次贝塞尔曲线，使用 de Casteljau 算法进行求值。

use crate::point::Point;
use std::fmt;

/// 贝塞尔曲线 trait
pub trait BezierCurve {
    /// 获取控制点
    fn control_points(&self) -> &[Point];

    /// 获取曲线阶数
    fn degree(&self) -> usize;

    /// 在参数 t 处求值 (0 <= t <= 1)
    fn evaluate(&self, t: f64) -> Point;

    /// 计算导数曲线（返回控制点）
    fn derivative_points(&self) -> Vec<Point>;

    /// 在参数 t 处求导
    fn evaluate_derivative(&self, t: f64) -> Point {
        let deriv_points = self.derivative_points();
        let n = deriv_points.len();
        if n == 0 {
            return Point::origin();
        }

        // 对导数控制点使用 de Casteljau
        let mut points = deriv_points.clone();
        for _ in 0..n - 1 {
            let mut next = Vec::with_capacity(points.len() - 1);
            for i in 0..points.len() - 1 {
                next.push(points[i].lerp(&points[i + 1], t));
            }
            points = next;
        }
        points[0]
    }

    /// 计算曲线长度（数值积分）
    fn length(&self, num_segments: usize) -> f64 {
        if num_segments == 0 {
            return 0.0;
        }

        let dt = 1.0 / num_segments as f64;
        let mut length = 0.0;
        let mut prev = self.evaluate(0.0);

        for i in 1..=num_segments {
            let t = i as f64 * dt;
            let curr = self.evaluate(t);
            length += prev.distance_to(&curr);
            prev = curr;
        }

        length
    }

    /// 找到曲线上距离给定点最近的点（参数 t）
    fn closest_point_parameter(&self, point: &Point, num_samples: usize) -> f64 {
        if num_samples == 0 {
            return 0.0;
        }

        let mut best_t = 0.0;
        let mut best_dist_sq = f64::MAX;

        // 粗采样
        for i in 0..=num_samples {
            let t = i as f64 / num_samples as f64;
            let p = self.evaluate(t);
            let dist_sq = point.distance_squared_to(&p);
            if dist_sq < best_dist_sq {
                best_dist_sq = dist_sq;
                best_t = t;
            }
        }

        // 牛顿迭代优化
        for _ in 0..10 {
            let grad = self.evaluate_derivative(best_t);
            let p = self.evaluate(best_t);
            let diff = p - *point;

            // 梯度下降步长
            let grad_dot = grad.dot(&grad);
            if grad_dot < 1e-10 {
                break;
            }

            let step = diff.dot(&grad) / grad_dot;
            best_t = (best_t - step * 0.5).max(0.0).min(1.0);
        }

        best_t
    }
}

/// 二次贝塞尔曲线: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
#[derive(Debug, Clone)]
pub struct QuadraticBezier {
    pub p0: Point,
    pub p1: Point,
    pub p2: Point,
}

impl QuadraticBezier {
    /// 创建新的二次贝塞尔曲线
    pub fn new(p0: Point, p1: Point, p2: Point) -> Self {
        Self { p0, p1, p2 }
    }

    /// 升阶到三次贝塞尔曲线
    pub fn elevate_to_cubic(&self) -> CubicBezier {
        // 升阶公式: Q1 = P0 + (2/3)(P1-P0), Q2 = P2 + (2/3)(P1-P2)
        let q0 = self.p0;
        let q1 = self.p0 + (self.p1 - self.p0) * (2.0 / 3.0);
        let q2 = self.p2 + (self.p1 - self.p2) * (2.0 / 3.0);
        let q3 = self.p2;
        CubicBezier::new(q0, q1, q2, q3)
    }
}

impl BezierCurve for QuadraticBezier {
    fn control_points(&self) -> &[Point] {
        // 返回切片需要静态生命周期，这里返回空切片
        // 实际使用时通过 clone 获取控制点
        &[]
    }

    fn degree(&self) -> usize {
        2
    }

    fn evaluate(&self, t: f64) -> Point {
        let t = t.max(0.0).min(1.0);

        // de Casteljau 算法
        let a = self.p0.lerp(&self.p1, t);
        let b = self.p1.lerp(&self.p2, t);
        a.lerp(&b, t)
    }

    fn derivative_points(&self) -> Vec<Point> {
        // 导数曲线的控制点: 2(P₁-P₀), 2(P₂-P₁)
        vec![
            (self.p1 - self.p0) * 2.0,
            (self.p2 - self.p1) * 2.0,
        ]
    }
}

impl fmt::Display for QuadraticBezier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "QuadraticBezier({}, {}, {})", self.p0, self.p1, self.p2)
    }
}

/// 三次贝塞尔曲线: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
#[derive(Debug, Clone)]
pub struct CubicBezier {
    pub p0: Point,
    pub p1: Point,
    pub p2: Point,
    pub p3: Point,
}

impl CubicBezier {
    /// 创建新的三次贝塞尔曲线
    pub fn new(p0: Point, p1: Point, p2: Point, p3: Point) -> Self {
        Self { p0, p1, p2, p3 }
    }

    /// 获取曲线的包围盒
    pub fn bounding_box(&self) -> (Point, Point) {
        let min_x = self.p0.x.min(self.p1.x).min(self.p2.x).min(self.p3.x);
        let min_y = self.p0.y.min(self.p1.y).min(self.p2.y).min(self.p3.y);
        let max_x = self.p0.x.max(self.p1.x).max(self.p2.x).max(self.p3.x);
        let max_y = self.p0.y.max(self.p1.y).max(self.p2.y).max(self.p3.y);

        (Point::new(min_x, min_y), Point::new(max_x, max_y))
    }
}

impl BezierCurve for CubicBezier {
    fn control_points(&self) -> &[Point] {
        &[]
    }

    fn degree(&self) -> usize {
        3
    }

    fn evaluate(&self, t: f64) -> Point {
        let t = t.max(0.0).min(1.0);

        // de Casteljau 算法
        let a = self.p0.lerp(&self.p1, t);
        let b = self.p1.lerp(&self.p2, t);
        let c = self.p2.lerp(&self.p3, t);

        let d = a.lerp(&b, t);
        let e = b.lerp(&c, t);

        d.lerp(&e, t)
    }

    fn derivative_points(&self) -> Vec<Point> {
        // 导数曲线的控制点: 3(P₁-P₀), 3(P₂-P₁), 3(P₃-P₂)
        vec![
            (self.p1 - self.p0) * 3.0,
            (self.p2 - self.p1) * 3.0,
            (self.p3 - self.p2) * 3.0,
        ]
    }
}

impl fmt::Display for CubicBezier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "CubicBezier({}, {}, {}, {})", self.p0, self.p1, self.p2, self.p3)
    }
}

/// 贝塞尔曲线枚举，用于统一处理
#[derive(Debug, Clone)]
pub enum BezierCurveType {
    Quadratic(QuadraticBezier),
    Cubic(CubicBezier),
}

impl BezierCurveType {
    /// 在参数 t 处求值
    pub fn evaluate(&self, t: f64) -> Point {
        match self {
            BezierCurveType::Quadratic(c) => c.evaluate(t),
            BezierCurveType::Cubic(c) => c.evaluate(t),
        }
    }

    /// 获取控制点列表
    pub fn control_points_vec(&self) -> Vec<Point> {
        match self {
            BezierCurveType::Quadratic(c) => vec![c.p0, c.p1, c.p2],
            BezierCurveType::Cubic(c) => vec![c.p0, c.p1, c.p2, c.p3],
        }
    }

    /// 获取阶数
    pub fn degree(&self) -> usize {
        match self {
            BezierCurveType::Quadratic(_) => 2,
            BezierCurveType::Cubic(_) => 3,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_quadratic_bezier_endpoints() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let start = curve.evaluate(0.0);
        let end = curve.evaluate(1.0);

        assert!((start.x - 0.0).abs() < 1e-10);
        assert!((start.y - 0.0).abs() < 1e-10);
        assert!((end.x - 100.0).abs() < 1e-10);
        assert!((end.y - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_quadratic_bezier_midpoint() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let mid = curve.evaluate(0.5);
        // 中点应该是 (50, 50)
        assert!((mid.x - 50.0).abs() < 1e-10);
        assert!((mid.y - 50.0).abs() < 1e-10);
    }

    #[test]
    fn test_cubic_bezier_endpoints() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let start = curve.evaluate(0.0);
        let end = curve.evaluate(1.0);

        assert!((start.x - 0.0).abs() < 1e-10);
        assert!((start.y - 0.0).abs() < 1e-10);
        assert!((end.x - 100.0).abs() < 1e-10);
        assert!((end.y - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_cubic_bezier_midpoint() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let mid = curve.evaluate(0.5);
        // 中点应该是 (50, 75)
        // B(0.5) = 0.125*P0 + 0.375*P1 + 0.375*P2 + 0.125*P3
        // y = 0.125*0 + 0.375*100 + 0.375*100 + 0.125*0 = 75
        assert!((mid.x - 50.0).abs() < 1e-10);
        assert!((mid.y - 75.0).abs() < 1e-10);
    }

    #[test]
    fn test_derivative() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let deriv = curve.evaluate_derivative(0.0);
        // 在 t=0 处，导数应该是 2(P1-P0) = (100, 200)
        assert!((deriv.x - 100.0).abs() < 1e-10);
        assert!((deriv.y - 200.0).abs() < 1e-10);
    }

    #[test]
    fn test_elevate_to_cubic() {
        let quad = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let cubic = quad.elevate_to_cubic();

        // 验证端点一致
        let start = cubic.evaluate(0.0);
        let end = cubic.evaluate(1.0);
        assert!((start.x - 0.0).abs() < 1e-10);
        assert!((end.x - 100.0).abs() < 1e-10);
    }

    #[test]
    fn test_bounding_box() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(100.0, 50.0),
            Point::new(0.0, 50.0),
            Point::new(100.0, 0.0),
        );

        let (min, max) = curve.bounding_box();
        assert!((min.x - 0.0).abs() < 1e-10);
        assert!((min.y - 0.0).abs() < 1e-10);
        assert!((max.x - 100.0).abs() < 1e-10);
        assert!((max.y - 50.0).abs() < 1e-10);
    }

    #[test]
    fn test_curve_length() {
        // 直线曲线长度应该接近直线距离
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 0.0),
            Point::new(100.0, 0.0),
        );

        let length = curve.length(100);
        assert!((length - 100.0).abs() < 1.0); // 允许小误差
    }
}
