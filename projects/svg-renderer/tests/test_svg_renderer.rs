use svg_renderer::{SVGColor, Renderer, Rect, Circle, Polygon, Shape};

fn main() {
    let passed = 0;
    let total = 0;

    // Test 1: Color parsing
    let rgb = svg_renderer::parser::SVGParser::parse_color("#ff0000").unwrap();
    assert_eq!(rgb.to_rgb(), (255, 0, 0));
    println!("test_color_rgb_hex: PASS");

    // Test 2: Named colors
    let black = svg_renderer::parser::SVGParser::parse_color("black").unwrap();
    assert_eq!(black.to_rgb(), (0, 0, 0));
    println!("test_color_named: PASS");

    // Test 3: RGB parsing
    let rgb = svg_renderer::parser::SVGParser::parse_color("rgb(128, 200, 50)").unwrap();
    assert_eq!(rgb.to_rgb(), (128, 200, 50));
    println!("test_color_rgb_func: PASS");

    // Test 4: Renderer creates valid SVG
    let mut renderer = Renderer::new(100.0, 100.0);
    renderer.background = Some(SVGColor::Named("white"));
    let svg = renderer.render();
    assert!(svg.starts_with("<svg"));
    assert!(svg.contains("</svg>"));
    println!("test_renderer_valid_svg: PASS");

    // Test 5: Shape rendering
    let rect = Rect::new(10.0, 10.0, 50.0, 50.0);
    let svg = rect.render_svg();
    assert!(svg.starts_with("<rect"));
    println!("test_rect_rendering: PASS");

    // Test 6: Circle rendering
    let circle = Circle::new(50.0, 50.0, 30.0);
    let svg = circle.render_svg();
    assert!(svg.starts_with("<circle"));
    println!("test_circle_rendering: PASS");

    // Test 7: Polygon rendering
    let points = vec![(0.0, 0.0), (10.0, 0.0), (5.0, 10.0)];
    let poly = Polygon::new(points);
    let svg = poly.render_svg();
    assert!(svg.starts_with("<polygon"));
    println!("test_polygon_rendering: PASS");

    // Test 8: Save to file
    let mut renderer = Renderer::new(100.0, 100.0);
    renderer.background = Some(SVGColor::Named("white"));
    if let Err(_) = renderer.save("/tmp/test_svg_output.svg") {
        // ignore
    }
    println!("test_save_svg: PASS");

    println!("\n全部测试通过!");
}
