use crate::geometry::{Point, Triangle};

pub struct Rasterizer {
    pub width: usize,
    pub height: usize,
    pub buffer: Vec<u32>,
}

impl Rasterizer {
    pub fn new(width: usize, height: usize) -> Self {
        Rasterizer {
            width,
            height,
            buffer: vec![0x00000000; width * height],
        }
    }

    pub fn clear(&mut self, color: u32) {
        self.buffer.fill(color);
    }

    pub fn set_pixel(&mut self, x: usize, y: usize, color: u32) {
        if x < self.width && y < self.height {
            self.buffer[y * self.width + x] = color;
        }
    }

    pub fn get_pixel(&self, x: usize, y: usize) -> u32 {
        if x < self.width && y < self.height {
            self.buffer[y * self.width + x]
        } else {
            0
        }
    }

    pub fn fill_triangle(&mut self, tri: &Triangle, color: u32) {
        let min_x = tri.a.x.min(tri.b.x).min(tri.c.x) as usize;
        let max_x = tri.a.x.max(tri.b.x).max(tri.c.x) as usize;
        let min_y = tri.a.y.min(tri.b.y).min(tri.c.y) as usize;
        let max_y = tri.a.y.max(tri.b.y).max(tri.c.y) as usize;

        for y in min_y..=max_y {
            for x in min_x..=max_x {
                let point = Point::new(x as f64, y as f64);
                if tri.barycentric(&point).is_some() {
                    self.set_pixel(x, y, color);
                }
            }
        }
    }

    pub fn draw_line(&mut self, x0: usize, y0: usize, x1: usize, y1: usize, color: u32) {
        let dx = (x1 as i32 - x0 as i32).abs();
        let dy = (y1 as i32 - y0 as i32).abs();
        let sx = if x0 < x1 { 1i32 } else { -1 };
        let sy = if y0 < y1 { 1i32 } else { -1 };
        let mut err = dx - dy;
        let mut mut_x = x0 as i32;
        let mut mut_y = y0 as i32;

        loop {
            self.set_pixel(mut_x as usize, mut_y as usize, color);
            if mut_x == x1 as i32 && mut_y == y1 as i32 {
                break;
            }
            let e2 = 2 * err;
            if e2 > -dy {
                err -= dy;
                mut_x += sx;
            }
            if e2 < dx {
                err += dx;
                mut_y += sy;
            }
        }
    }

    pub fn fill_rect(&mut self, x0: usize, y0: usize, x1: usize, y1: usize, color: u32) {
        let (min_x, max_x) = if x0 < x1 { (x0, x1) } else { (x1, x0) };
        let (min_y, max_y) = if y0 < y1 { (y0, y1) } else { (y1, y0) };
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                self.set_pixel(x, y, color);
            }
        }
    }

    pub fn render(&self) -> Vec<u32> {
        self.buffer.clone()
    }
}
