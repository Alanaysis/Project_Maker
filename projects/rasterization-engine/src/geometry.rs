#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    pub fn distance_to(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    pub fn lerp(&self, other: &Point, t: f64) -> Self {
        Point {
            x: self.x + (other.x - self.x) * t,
            y: self.y + (other.y - self.y) * t,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Line {
    pub start: Point,
    pub end: Point,
}

impl Line {
    pub fn new(start: Point, end: Point) -> Self {
        Line { start, end }
    }

    pub fn length(&self) -> f64 {
        self.start.distance_to(&self.end)
    }
}

#[derive(Debug, Clone)]
pub struct Triangle {
    pub a: Point,
    pub b: Point,
    pub c: Point,
}

impl Triangle {
    pub fn new(a: Point, b: Point, c: Point) -> Self {
        Triangle { a, b, c }
    }

    pub fn area(&self) -> f64 {
        0.5f64 * (self.a.x * (self.b.y - self.c.y)
            + self.b.x * (self.c.y - self.a.y)
            + self.c.x * (self.a.y - self.b.y)).abs()
    }

    pub fn barycentric(&self, p: &Point) -> Option<(f64, f64, f64)> {
        let denom = (self.b.y - self.c.y) * (self.a.x - self.c.x)
            + (self.c.x - self.b.x) * (self.a.y - self.c.y);
        if denom.abs() < 1e-10 {
            return None;
        }
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
}
