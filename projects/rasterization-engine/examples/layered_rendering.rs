use rasterization::{Renderer, Circle, Rectangle, Polygon, Point};

fn main() {
    let mut renderer = Renderer::new(60, 30);
    renderer.clear(0x111111);

    // Background rectangles
    let bg = Rectangle::new(5, 5, 55, 25, 0x222244);
    renderer.render(&bg);

    // Colored circles
    let c1 = Circle::new(15.0, 15.0, 8.0, 0xff3333);
    renderer.render(&c1);

    let c2 = Circle::new(30.0, 15.0, 8.0, 0x33ff33);
    renderer.render(&c2);

    let c3 = Circle::new(45.0, 15.0, 8.0, 0x3333ff);
    renderer.render(&c3);

    // Overlapping rect
    let over = Rectangle::new(20, 8, 40, 22, 0x888888);
    renderer.render(&over);

    // Star polygon
    let pts = vec![
        Point::new(50.0, 2.0),
        Point::new(52.0, 8.0),
        Point::new(58.0, 8.0),
        Point::new(53.0, 12.0),
        Point::new(55.0, 18.0),
        Point::new(50.0, 14.0),
        Point::new(45.0, 18.0),
        Point::new(47.0, 12.0),
        Point::new(42.0, 8.0),
        Point::new(48.0, 8.0),
    ];
    let star = Polygon::new(pts, 0xffff00);
    renderer.render(&star);

    let pixels = renderer.get_pixels();
    println!("合成渲染结果:\n");
    for y in 0..renderer.rasterizer.height {
        let mut line = String::new();
        for x in 0..renderer.rasterizer.width {
            let p = pixels[y * renderer.rasterizer.width + x];
            let r = (p & 0xff) as u8;
            let g = ((p >> 8) & 0xff) as u8;
            let b = ((p >> 16) & 0xff) as u8;
            let brightness = (r as u32 + g as u32 + b as u32) / 3;
            if brightness == 0 {
                line.push(' ');
            } else if brightness < 85 {
                line.push('#');
            } else if brightness < 170 {
                line.push('*');
            } else {
                line.push('.');
            }
        }
        println!(" {}", line);
    }
}
