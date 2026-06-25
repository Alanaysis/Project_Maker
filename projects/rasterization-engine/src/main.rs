use rasterization::{Renderer, Circle, Rectangle, Polygon};

fn main() {
    println!("=== 光栅化引擎演示 ===\n");

    let mut renderer = Renderer::new(80, 40);
    renderer.clear(0x1a1a2e);

    // Draw rectangles
    let rect = Rectangle::new(10, 10, 30, 25, 0xff0000);
    renderer.render(&rect);

    let rect2 = Rectangle::new(20, 20, 50, 35, 0x00ff00);
    renderer.render(&rect2);

    // Draw circle
    let circle = Circle::new(40.0, 20.0, 10.0, 0x0000ff);
    renderer.render(&circle);

    // Draw polygon (pentagon)
    let pts = vec![
        rasterization::Point::new(55.0, 5.0),
        rasterization::Point::new(65.0, 10.0),
        rasterization::Point::new(68.0, 22.0),
        rasterization::Point::new(58.0, 30.0),
        rasterization::Point::new(48.0, 22.0),
    ];
    let poly = Polygon::new(pts, 0xffff00);
    renderer.render(&poly);

    // Draw another circle
    let circle2 = Circle::new(15.0, 30.0, 5.0, 0xff00ff);
    renderer.render(&circle2);

    let pixels = renderer.get_pixels();

    // ASCII render
    print!("\n光栅化结果 (ASCII):\n");
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
    println!("\n渲染完成!");
}
