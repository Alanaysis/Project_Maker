use svg_renderer::{Renderer, SVGColor, Rect, Circle, Polygon, Line};

fn main() {
    let mut renderer = Renderer::new(300.0, 300.0);
    renderer.background = Some(SVGColor::Named("white"));

    // Draw a star
    let n = 5;
    let cx = 150.0;
    let cy = 150.0;
    let outer_r = 100.0;
    let inner_r = 50.0;
    let mut points: Vec<(f64, f64)> = Vec::new();

    for i in 0..n * 2 {
        let angle = std::f64::consts::FRAC_PI_2 + (i as f64) * std::f64::consts::PI / n as f64;
        let r = if i % 2 == 0 { outer_r } else { inner_r };
        let x = cx + r * angle.cos();
        let y = cy - r * angle.sin();
        points.push((x, y));
    }

    renderer.add_shape(Box::new(Polygon::new(points.clone())
        .with_fill(SVGColor::RGB(255, 200, 0))
        .with_stroke(SVGColor::Named("black"))));

    // Add circles at vertices
    for (x, y) in &points {
        renderer.add_shape(Box::new(Circle::new(*x, *y, 5.0)
            .with_fill(SVGColor::Named("red"))));
    }

    // Add lines connecting center to vertices
    for (x, y) in &points {
        renderer.add_shape(Box::new(Line::new(cx, cy, *x, *y)
            .with_stroke(SVGColor::RGB(200, 200, 200))));
    }

    // Save
    renderer.save("star.svg").unwrap();
    println!("五角星 SVG 已保存到 star.svg");
    println!("\n内容预览:\n{}", renderer.render());
}
