use rasterization::{Rasterizer, Triangle, Point, Rectangle, Circle, Shape};

fn main() {
    let mut ras = Rasterizer::new(40, 20);
    ras.clear(0x000000);

    // Fill triangle
    let tri = Triangle::new(
        Point::new(10.0, 5.0),
        Point::new(20.0, 15.0),
        Point::new(5.0, 15.0),
    );
    ras.fill_triangle(&tri, 0xff4444);

    // Draw line
    ras.draw_line(20, 10, 35, 10, 0x44ff44);

    // Fill rect
    ras.fill_rect(25, 5, 35, 15, 0x4444ff);

    // Draw circle
    let circle = Circle::new(10.0, 10.0, 4.0, 0xffff00);
    circle.render(&mut ras);

    // ASCII output
    println!("光栅化输出:\n");
    let pixels = ras.render();
    for y in 0..ras.height {
        let mut line = String::new();
        for x in 0..ras.width {
            let p = pixels[y * ras.width + x];
            let r = (p & 0xff) as u8;
            let g = ((p >> 8) & 0xff) as u8;
            let b = ((p >> 16) & 0xff) as u8;
            let brightness = (r as u32 + g as u32 + b as u32) / 3;
            if brightness == 0 {
                line.push(' ');
            } else if brightness < 128 {
                line.push('#');
            } else {
                line.push('*');
            }
        }
        println!(" {}", line);
    }
}
