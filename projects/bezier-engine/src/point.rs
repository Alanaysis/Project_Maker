//! 二维点和向量操作

use std::fmt;
use std::ops::{Add, Sub, Mul, Div};

/// 二维点/向量
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    /// 创建新点
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// 原点
    pub fn origin() -> Self {
        Self { x: 0.0, y: 0.0 }
    }

    /// 计算到另一点的距离
    pub fn distance_to(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }

    /// 计算到另一点的平方距离（避免开方，用于比较）
    pub fn distance_squared_to(&self, other: &Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        dx * dx + dy * dy
    }

    /// 线性插值
    pub fn lerp(&self, other: &Point, t: f64) -> Point {
        Point {
            x: self.x + (other.x - self.x) * t,
            y: self.y + (other.y - self.y) * t,
        }
    }

    /// 计算向量长度
    pub fn length(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }

    /// 归一化向量
    pub fn normalize(&self) -> Point {
        let len = self.length();
        if len < 1e-10 {
            return Point::origin();
        }
        Point {
            x: self.x / len,
            y: self.y / len,
        }
    }

    /// 计算点积
    pub fn dot(&self, other: &Point) -> f64 {
        self.x * other.x + self.y * other.y
    }

    /// 计算叉积（z 分量）
    pub fn cross(&self, other: &Point) -> f64 {
        self.x * other.y - self.y * other.x
    }
}

impl Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

impl Sub for Point {
    type Output = Point;

    fn sub(self, other: Point) -> Point {
        Point {
            x: self.x - other.x,
            y: self.y - other.y,
        }
    }
}

impl Mul<f64> for Point {
    type Output = Point;

    fn mul(self, scalar: f64) -> Point {
        Point {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

impl Mul<Point> for f64 {
    type Output = Point;

    fn mul(self, point: Point) -> Point {
        Point {
            x: self * point.x,
            y: self * point.y,
        }
    }
}

impl Div<f64> for Point {
    type Output = Point;

    fn div(self, scalar: f64) -> Point {
        Point {
            x: self.x / scalar,
            y: self.y / scalar,
        }
    }
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_point_creation() {
        let p = Point::new(3.0, 4.0);
        assert_eq!(p.x, 3.0);
        assert_eq!(p.y, 4.0);
    }

    #[test]
    fn test_distance() {
        let p1 = Point::new(0.0, 0.0);
        let p2 = Point::new(3.0, 4.0);
        assert!((p1.distance_to(&p2) - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_lerp() {
        let p1 = Point::new(0.0, 0.0);
        let p2 = Point::new(10.0, 20.0);
        let mid = p1.lerp(&p2, 0.5);
        assert!((mid.x - 5.0).abs() < 1e-10);
        assert!((mid.y - 10.0).abs() < 1e-10);
    }

    #[test]
    fn test_arithmetic() {
        let p1 = Point::new(1.0, 2.0);
        let p2 = Point::new(3.0, 4.0);

        let sum = p1 + p2;
        assert_eq!(sum, Point::new(4.0, 6.0));

        let diff = p2 - p1;
        assert_eq!(diff, Point::new(2.0, 2.0));

        let scaled = p1 * 2.0;
        assert_eq!(scaled, Point::new(2.0, 4.0));
    }

    #[test]
    fn test_normalize() {
        let p = Point::new(3.0, 4.0);
        let n = p.normalize();
        assert!((n.length() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_dot_cross() {
        let p1 = Point::new(1.0, 0.0);
        let p2 = Point::new(0.0, 1.0);

        assert!((p1.dot(&p2)).abs() < 1e-10);
        assert!((p1.cross(&p2) - 1.0).abs() < 1e-10);
    }
}
