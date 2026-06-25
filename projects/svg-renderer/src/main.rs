use svg_renderer::{Renderer, SVGColor, Rect, Circle, Ellipse, Line, Polygon, Polyline, Text};

fn main() {
    println!("=== SVG 渲染器演示 ===\n");

    let mut renderer = Renderer::new(400.0, 300.0);
    renderer.background = Some(SVGColor::Named("white"));

    // Background rectangles
    renderer.add_shape(Box::new(Rect::new(0.0, 0.0, 400.0, 60.0)));
    let bg_rect = renderer.shapes.last_mut().unwrap();
    // Red gradient background
    renderer.add_shape(Box::new(Rect::new(0.0, 0.0, 400.0, 60.0)
        .with_fill(SVGColor::RGB(220, 220, 255))));

    // Circles
    renderer.add_shape(Box::new(Circle::new(80.0, 150.0, 50.0)
        .with_fill(SVGColor::RGB(255, 100, 100))));
    renderer.add_shape(Box::new(Circle::new(200.0, 150.0, 50.0)
        .with_fill(SVGColor::RGB(100, 255, 100))));
    renderer.add_shape(Box::new(Circle::new(320.0, 150.0, 50.0)
        .with_fill(SVGColor::RGB(100, 100, 255))));

    // Ellipses
    renderer.add_shape(Box::new(Ellipse::new(200.0, 250.0, 80.0, 40.0)
        .with_fill(SVGColor::RGB(255, 200, 50))));

    // Rectangles
    renderer.add_shape(Box::new(Rect::new(280.0, 220.0, 80.0, 60.0)
        .with_fill(SVGColor::RGB(180, 100, 255))));

    // Lines
    renderer.add_shape(Box::new(Line::new(50.0, 250.0, 350.0, 250.0)
        .with_stroke(SVGColor::RGB(100, 100, 100))));

    // Polygon
    let poly_points = vec![
        (50.0, 20.0), (100.0, 50.0), (70.0, 100.0),
        (30.0, 80.0), (10.0, 40.0),
    ];
    renderer.add_shape(Box::new(Polygon::new(poly_points)
        .with_fill(SVGColor::RGB(255, 150, 50))));

    // Polyline
    let polyline_points = vec![
        (150.0, 200.0), (170.0, 180.0), (190.0, 210.0),
        (210.0, 170.0), (230.0, 200.0),
    ];
    renderer.add_shape(Box::new(Polyline::new(polyline_points)
        .with_stroke(SVGColor::RGB(0, 200, 200))));

    // Text
    renderer.add_shape(Box::new(Text::new(200.0, 145.0, "SVG Renderer")
        .with_fill(SVGColor::Named("black"))));
    renderer.add_shape(Box::new(Text::new(200.0, 165.0, "Rust 实现")
        .with_fill(SVGColor::Named("gray"))));

    // Save
    let svg_content = renderer.render();
    println!("生成 SVG 内容 (前 500 字符):\n{}\n...", &svg_content[..500.min(svg_content.len())]);

    // Save to file
    if let Err(e) = renderer.save("output.svg") {
        eprintln!("保存失败: {}", e);
    } else {
        println!("\nSVG 已保存到 output.svg");
    }
}
