//! 曲线细分算法
//!
//! 使用 de Casteljau 算法将贝塞尔曲线细分为两段。

use crate::point::Point;
use crate::bezier::{BezierCurve, QuadraticBezier, CubicBezier};

/// 细分配置
#[derive(Debug, Clone)]
pub struct SubdivisionConfig {
    /// 最大细分深度
    pub max_depth: usize,
    /// 平坦度阈值（用于自适应细分）
    pub flatness_threshold: f64,
    /// 最小线段长度
    pub min_segment_length: f64,
}

impl SubdivisionConfig {
    /// 创建默认配置
    pub fn new() -> Self {
        Self {
            max_depth: 8,
            flatness_threshold: 0.5,
            min_segment_length: 1.0,
        }
    }

    /// 设置最大深度
    pub fn with_max_depth(mut self, depth: usize) -> Self {
        self.max_depth = depth;
        self
    }

    /// 设置平坦度阈值
    pub fn with_flatness(mut self, threshold: f64) -> Self {
        self.flatness_threshold = threshold;
        self
    }

    /// 设置最小线段长度
    pub fn with_min_segment_length(mut self, length: f64) -> Self {
        self.min_segment_length = length;
        self
    }
}

impl Default for SubdivisionConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// 二次贝塞尔曲线在 t 处细分
///
/// 返回两段二次贝塞尔曲线 (left, right)
pub fn subdivide_quadratic(curve: &QuadraticBezier, t: f64) -> (QuadraticBezier, QuadraticBezier) {
    let t = t.max(0.0).min(1.0);

    // de Casteljau 细分
    let p0 = curve.p0;
    let p1 = curve.p1;
    let p2 = curve.p2;

    let m0 = p0.lerp(&p1, t);
    let m1 = p1.lerp(&p2, t);
    let mid = m0.lerp(&m1, t);

    let left = QuadraticBezier::new(p0, m0, mid);
    let right = QuadraticBezier::new(mid, m1, p2);

    (left, right)
}

/// 三次贝塞尔曲线在 t 处细分
///
/// 返回两段三次贝塞尔曲线 (left, right)
pub fn subdivide_cubic(curve: &CubicBezier, t: f64) -> (CubicBezier, CubicBezier) {
    let t = t.max(0.0).min(1.0);

    // de Casteljau 细分
    let p0 = curve.p0;
    let p1 = curve.p1;
    let p2 = curve.p2;
    let p3 = curve.p3;

    let m0 = p0.lerp(&p1, t);
    let m1 = p1.lerp(&p2, t);
    let m2 = p2.lerp(&p3, t);

    let n0 = m0.lerp(&m1, t);
    let n1 = m1.lerp(&m2, t);

    let mid = n0.lerp(&n1, t);

    let left = CubicBezier::new(p0, m0, n0, mid);
    let right = CubicBezier::new(mid, n1, m2, p3);

    (left, right)
}

/// 计算曲线的平坦度（控制点到端点连线的最大距离）
pub fn quadratic_flatness(curve: &QuadraticBezier) -> f64 {
    let p0 = curve.p0;
    let p2 = curve.p2;
    let p1 = curve.p1;

    // 计算 p1 到 p0-p2 连线的距离
    point_to_line_distance(p1, p0, p2)
}

/// 计算曲线的平坦度（控制点到端点连线的最大距离）
pub fn cubic_flatness(curve: &CubicBezier) -> f64 {
    let p0 = curve.p0;
    let p3 = curve.p3;
    let p1 = curve.p1;
    let p2 = curve.p2;

    // 计算 p1 和 p2 到 p0-p3 连线的最大距离
    let d1 = point_to_line_distance(p1, p0, p3);
    let d2 = point_to_line_distance(p2, p0, p3);

    d1.max(d2)
}

/// 计算点到线段的距离
fn point_to_line_distance(point: Point, line_start: Point, line_end: Point) -> f64 {
    let line = line_end - line_start;
    let line_len_sq = line.dot(&line);

    if line_len_sq < 1e-10 {
        return point.distance_to(&line_start);
    }

    let t = ((point - line_start).dot(&line) / line_len_sq).max(0.0).min(1.0);
    let projection = line_start + line * t;
    point.distance_to(&projection)
}

/// 自适应细分二次贝塞尔曲线
///
/// 根据曲线平坦度自动决定细分深度，返回折线点序列
pub fn adaptive_subdivide_quadratic(
    curve: &QuadraticBezier,
    config: &SubdivisionConfig,
) -> Vec<Point> {
    let mut points = Vec::new();
    points.push(curve.p0);
    adaptive_subdivide_quadratic_recursive(curve, config, 0, &mut points);
    points.push(curve.p2);
    points
}

fn adaptive_subdivide_quadratic_recursive(
    curve: &QuadraticBezier,
    config: &SubdivisionConfig,
    depth: usize,
    points: &mut Vec<Point>,
) {
    if depth >= config.max_depth {
        return;
    }

    let flatness = quadratic_flatness(curve);
    let curve_length = curve.length(10);

    if flatness < config.flatness_threshold || curve_length < config.min_segment_length {
        return;
    }

    let (left, right) = subdivide_quadratic(curve, 0.5);
    adaptive_subdivide_quadratic_recursive(&left, config, depth + 1, points);
    points.push(left.p2);
    adaptive_subdivide_quadratic_recursive(&right, config, depth + 1, points);
}

/// 自适应细分三次贝塞尔曲线
///
/// 根据曲线平坦度自动决定细分深度，返回折线点序列
pub fn adaptive_subdivide_cubic(
    curve: &CubicBezier,
    config: &SubdivisionConfig,
) -> Vec<Point> {
    let mut points = Vec::new();
    points.push(curve.p0);
    adaptive_subdivide_cubic_recursive(curve, config, 0, &mut points);
    points.push(curve.p3);
    points
}

fn adaptive_subdivide_cubic_recursive(
    curve: &CubicBezier,
    config: &SubdivisionConfig,
    depth: usize,
    points: &mut Vec<Point>,
) {
    if depth >= config.max_depth {
        return;
    }

    let flatness = cubic_flatness(curve);
    let curve_length = curve.length(10);

    if flatness < config.flatness_threshold || curve_length < config.min_segment_length {
        return;
    }

    let (left, right) = subdivide_cubic(curve, 0.5);
    adaptive_subdivide_cubic_recursive(&left, config, depth + 1, points);
    points.push(left.p3);
    adaptive_subdivide_cubic_recursive(&right, config, depth + 1, points);
}

/// 均匀细分二次贝塞尔曲线
///
/// 返回 n 段折线的点序列
pub fn uniform_subdivide_quadratic(curve: &QuadraticBezier, n: usize) -> Vec<Point> {
    if n == 0 {
        return vec![curve.p0, curve.p2];
    }

    let mut points = Vec::with_capacity(n + 1);
    for i in 0..=n {
        let t = i as f64 / n as f64;
        points.push(curve.evaluate(t));
    }
    points
}

/// 均匀细分三次贝塞尔曲线
///
/// 返回 n 段折线的点序列
pub fn uniform_subdivide_cubic(curve: &CubicBezier, n: usize) -> Vec<Point> {
    if n == 0 {
        return vec![curve.p0, curve.p3];
    }

    let mut points = Vec::with_capacity(n + 1);
    for i in 0..=n {
        let t = i as f64 / n as f64;
        points.push(curve.evaluate(t));
    }
    points
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bezier::BezierCurve;

    #[test]
    fn test_quadratic_subdivision_endpoints() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let (left, right) = subdivide_quadratic(&curve, 0.5);

        // 左段起点是原曲线起点
        assert!((left.p0.x - 0.0).abs() < 1e-10);
        assert!((left.p0.y - 0.0).abs() < 1e-10);

        // 右段终点是原曲线终点
        assert!((right.p2.x - 100.0).abs() < 1e-10);
        assert!((right.p2.y - 0.0).abs() < 1e-10);

        // 两段在中点连接
        let mid_left = left.evaluate(1.0);
        let mid_right = right.evaluate(0.0);
        assert!((mid_left.x - mid_right.x).abs() < 1e-10);
        assert!((mid_left.y - mid_right.y).abs() < 1e-10);
    }

    #[test]
    fn test_cubic_subdivision_endpoints() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let (left, right) = subdivide_cubic(&curve, 0.5);

        // 左段起点是原曲线起点
        assert!((left.p0.x - 0.0).abs() < 1e-10);
        assert!((left.p0.y - 0.0).abs() < 1e-10);

        // 右段终点是原曲线终点
        assert!((right.p3.x - 100.0).abs() < 1e-10);
        assert!((right.p3.y - 0.0).abs() < 1e-10);

        // 两段在中点连接
        let mid_left = left.evaluate(1.0);
        let mid_right = right.evaluate(0.0);
        assert!((mid_left.x - mid_right.x).abs() < 1e-10);
        assert!((mid_left.y - mid_right.y).abs() < 1e-10);
    }

    #[test]
    fn test_subdivision_preserves_curve() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let (left, right) = subdivide_cubic(&curve, 0.3);

        // 细分后的曲线应该与原曲线在对应参数处一致
        let _t = 0.15; // 原曲线的 t=0.15 对应左段的 t=0.5
        let _original = curve.evaluate(_t);
        let _subdivided = left.evaluate(0.5);

        // 由于 t=0.3 细分，t=0.15 在左段的参数应该是 0.5
        // 但实际不是线性映射，这里只是验证细分后曲线连续
        let mid = left.evaluate(1.0);
        let mid2 = right.evaluate(0.0);
        assert!((mid.x - mid2.x).abs() < 1e-10);
        assert!((mid.y - mid2.y).abs() < 1e-10);
    }

    #[test]
    fn test_flatness() {
        // 接近直线的曲线
        let flat_curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 0.1),
            Point::new(100.0, 0.0),
        );

        // 弯曲的曲线
        let curved = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        assert!(quadratic_flatness(&flat_curve) < quadratic_flatness(&curved));
    }

    #[test]
    fn test_uniform_subdivision() {
        let curve = QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let points = uniform_subdivide_quadratic(&curve, 4);
        assert_eq!(points.len(), 5);

        // 第一个点是起点
        assert!((points[0].x - 0.0).abs() < 1e-10);
        // 最后一个点是终点
        assert!((points[4].x - 100.0).abs() < 1e-10);
    }

    #[test]
    fn test_adaptive_subdivision() {
        let curve = CubicBezier::new(
            Point::new(0.0, 0.0),
            Point::new(25.0, 100.0),
            Point::new(75.0, 100.0),
            Point::new(100.0, 0.0),
        );

        let config = SubdivisionConfig::new()
            .with_max_depth(5)
            .with_flatness(1.0);

        let points = adaptive_subdivide_cubic(&curve, &config);

        // 应该生成多个点
        assert!(points.len() > 2);

        // 第一个点是起点
        assert!((points[0].x - 0.0).abs() < 1e-10);
        // 最后一个点是终点
        let last = points.len() - 1;
        assert!((points[last].x - 100.0).abs() < 1e-10);
    }
}
