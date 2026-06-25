use crate::geometry::Point;
use crate::rasterizer::Rasterizer;

pub trait Shape {
    fn color(&self) -> u32;
    fn render(&self, rasterizer: &mut Rasterizer);
}

#[derive(Clone)]
pub struct Circle {
    pub center: Point,
    pub radius: f64,
    pub color: u32,
}

impl Circle {
    pub fn new(x: f64, y: f64, radius: f64, color: u32) -> Self {
        Circle {
            center: Point::new(x, y),
            radius,
            color,
        }
    }
}

impl Shape for Circle {
    fn color(&self) -> u32 {
        self.color
    }

    fn render(&self, rasterizer: &mut Rasterizer) {
        let r = self.radius as usize;
        let cx = self.center.x as usize;
        let cy = self.center.y as usize;
        for y in (cy.saturating_sub(r))..=(cy.saturating_add(r).min(rasterizer.height - 1)) {
            for x in (cx.saturating_sub(r))..=(cx.saturating_add(r).min(rasterizer.width - 1)) {
                let dx = x as f64 - self.center.x;
                let dy = y as f64 - self.center.y;
                if dx * dx + dy * dy <= self.radius * self.radius {
                    rasterizer.set_pixel(x, y, self.color);
                }
            }
        }
    }
}

#[derive(Clone)]
pub struct Rectangle {
    pub x0: usize,
    pub y0: usize,
    pub x1: usize,
    pub y1: usize,
    pub color: u32,
}

impl Rectangle {
    pub fn new(x0: usize, y0: usize, x1: usize, y1: usize, color: u32) -> Self {
        Rectangle { x0, y0, x1, y1, color }
    }
}

impl Shape for Rectangle {
    fn color(&self) -> u32 {
        self.color
    }

    fn render(&self, rasterizer: &mut Rasterizer) {
        rasterizer.fill_rect(self.x0, self.y0, self.x1, self.y1, self.color);
    }
}

#[derive(Clone)]
pub struct Polygon {
    pub points: Vec<Point>,
    pub color: u32,
}

impl Polygon {
    pub fn new(points: Vec<Point>, color: u32) -> Self {
        Polygon { points, color }
    }
}

impl Shape for Polygon {
    fn color(&self) -> u32 {
        self.color
    }

    fn render(&self, rasterizer: &mut Rasterizer) {
        let n = self.points.len();
        for i in 0..n {
            let j = (i + 1) % n;
            let a = &self.points[i];
            let b = &self.points[j];
            let x0 = a.x as usize;
            let y0 = a.y as usize;
            let x1 = b.x as usize;
            let y1 = b.y as usize;
            rasterizer.draw_line(x0, y0, x1, y1, self.color);
        }
    }
}
