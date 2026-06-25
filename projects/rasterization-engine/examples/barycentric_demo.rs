use rasterization::{Rasterizer, Triangle, Point};

fn main() {
    let mut ras = Rasterizer::new(50, 25);
    ras.clear(0x000000);

    // Barycentric test
    let tri = Triangle::new(
        Point::new(5.0, 5.0),
        Point::new(25.0, 20.0),
        Point::new(5.0, 20.0),
    );

    println!("三角形顶点: ({}, {}), ({}, {}), ({}, {})",
        tri.a.x, tri.a.y, tri.b.x, tri.b.y, tri.c.x, tri.c.y);
    println!("面积: {:.2}", tri.area());

    // Test barycentric coordinates
    let test_points = vec![
        Point::new(10.0, 10.0),
        Point::new(20.0, 18.0),
        Point::new(30.0, 15.0),
    ];

    for p in &test_points {
        if let Some((w1, w2, w3)) = tri.barycentric(p) {
            println!("  [{:.0},{:.0}] 在三角形内: w=({:.2}, {:.2}, {:.2})",
                p.x, p.y, w1, w2, w3);
        } else {
            println!("  [{:.0},{:.0}] 在三角形外", p.x, p.y);
        }
    }

    ras.fill_triangle(&tri, 0xff6600);

    println!("\n光栅化输出:\n");
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
