use svg_renderer::{Renderer, SVGColor, Rect, Circle, Ellipse, Polygon, Polyline};

fn main() {
    let mut renderer = Renderer::new(500.0, 400.0);
    renderer.background = Some(SVGColor::Named("white"));

    // Title
    renderer.add_shape(Box::new(Rect::new(0.0, 0.0, 500.0, 40.0)
        .with_fill(SVGColor::RGB(50, 50, 100))));
    renderer.add_shape(Box::new(svg_renderer::Text::new(250.0, 28.0, "SVG 渲染器 - 示例")
        .with_fill(SVGColor::Named("white"))));

    // Color palette
    let colors = vec![
        SVGColor::RGB(255, 0, 0),
        SVGColor::RGB(255, 165, 0),
        SVGColor::RGB(255, 255, 0),
        SVGColor::RGB(0, 255, 0),
        SVGColor::RGB(0, 0, 255),
        SVGColor::RGB(128, 0, 128),
    ];

    for (i, color) in colors.iter().enumerate() {
        let x = 20.0 + (i as f64) * 75.0;
        renderer.add_shape(Box::new(Circle::new(x + 25.0, 100.0, 25.0)
            .with_fill(*color)));
        renderer.add_shape(Box::new(svg_renderer::Text::new(x + 10.0, 140.0, "色块")
            .with_fill(SVGColor::Named("black"))));
    }

    // Geometric shapes
    renderer.add_shape(Box::new(Rect::new(40.0, 200.0, 80.0, 80.0)
        .with_fill(SVGColor::RGB(200, 100, 100))));
    renderer.add_shape(Box::new(Ellipse::new(120.0, 240.0, 50.0, 30.0)
        .with_fill(SVGColor::RGB(100, 200, 100))));
    renderer.add_shape(Box::new(Circle::new(220.0, 240.0, 40.0)
        .with_fill(SVGColor::RGB(100, 100, 200))));

    // Chart-like bars
    let bars = vec![30.0, 55.0, 45.0, 70.0, 60.0, 40.0];
    for (i, height) in bars.iter().enumerate() {
        let x = 300.0 + (i as f64) * 30.0;
        let bar_color = SVGColor::RGB(100 + (i as u8) * 30, 150, 200);
        renderer.add_shape(Box::new(Rect::new(x, 350.0 - height, 20.0, *height)
            .with_fill(bar_color)));
    }

    renderer.save("demo_svg.svg").unwrap();
    println!("SVG 已保存到 demo_svg.svg");
    println!("\n内容预览:\n{}", renderer.render());
}
