//! SVG 输出示例
//!
//! 演示如何将贝塞尔曲线渲染为 SVG 格式。

use bezier_engine::{
    Point, QuadraticBezier, CubicBezier,
    SvgRenderer, SvgStyle, SvgColor, BezierCurveType,
    SubdivisionConfig,
    renderer::{curve_to_polyline, points_to_text},
};

fn main() {
    println!("=== SVG 输出示例 ===\n");

    // 1. 基本 SVG 输出
    demo_basic_svg();

    // 2. 自定义样式
    demo_custom_style();

    // 3. 多曲线渲染
    demo_multiple_curves();

    // 4. 折线渲染
    demo_polyline();

    // 5. 完整示例文件
    demo_complete_svg();
}

fn demo_basic_svg() {
    println!("--- 1. 基本 SVG 输出 ---\n");

    let renderer = SvgRenderer::new(300.0, 200.0);

    // 二次曲线
    let quad = QuadraticBezier::new(
        Point::new(20.0, 100.0),
        Point::new(150.0, 20.0),
        Point::new(280.0, 100.0),
    );

    let svg = renderer.render_quadratic(&quad);
    println!("二次曲线 SVG ({} 字节):", svg.len());
    println!("  {}...\n", &svg[..150.min(svg.len())]);

    // 三次曲线
    let cubic = CubicBezier::new(
        Point::new(20.0, 100.0),
        Point::new(80.0, 20.0),
        Point::new(220.0, 180.0),
        Point::new(280.0, 100.0),
    );

    let svg = renderer.render_cubic(&cubic);
    println!("三次曲线 SVG ({} 字节):", svg.len());
}

fn demo_custom_style() {
    println!("\n--- 2. 自定义样式 ---\n");

    // 蓝色粗线
    let style1 = SvgStyle {
        stroke_color: SvgColor::rgb(0, 100, 200),
        stroke_width: 4.0,
        control_point_radius: 6.0,
        control_point_color: SvgColor::rgb(255, 100, 0),
        ..SvgStyle::default()
    };

    let renderer1 = SvgRenderer::new(200.0, 150.0).with_style(style1);
    let curve = QuadraticBezier::new(
        Point::new(20.0, 75.0),
        Point::new(100.0, 20.0),
        Point::new(180.0, 75.0),
    );

    let svg1 = renderer1.render_quadratic(&curve);
    println!("蓝色样式 SVG: {} 字节", svg1.len());

    // 无控制点
    let style2 = SvgStyle {
        stroke_color: SvgColor::rgb(200, 50, 50),
        stroke_width: 2.5,
        show_control_points: false,
        show_control_lines: false,
        ..SvgStyle::default()
    };

    let renderer2 = SvgRenderer::new(200.0, 150.0).with_style(style2);
    let svg2 = renderer2.render_quadratic(&curve);
    println!("无控制点 SVG: {} 字节", svg2.len());

    // 透明背景
    let renderer3 = SvgRenderer::new(200.0, 150.0).without_background();
    let svg3 = renderer3.render_quadratic(&curve);
    println!("透明背景 SVG: {} 字节", svg3.len());
}

fn demo_multiple_curves() {
    println!("\n--- 3. 多曲线渲染 ---\n");

    let renderer = SvgRenderer::new(400.0, 200.0);

    let curves = vec![
        BezierCurveType::Quadratic(QuadraticBezier::new(
            Point::new(20.0, 100.0),
            Point::new(100.0, 20.0),
            Point::new(180.0, 100.0),
        )),
        BezierCurveType::Cubic(CubicBezier::new(
            Point::new(220.0, 100.0),
            Point::new(260.0, 20.0),
            Point::new(340.0, 180.0),
            Point::new(380.0, 100.0),
        )),
    ];

    let svg = renderer.render_curves(&curves);
    println!("多曲线 SVG: {} 字节", svg.len());
    println!("包含 {} 条曲线", curves.len());
}

fn demo_polyline() {
    println!("\n--- 4. 折线渲染 ---\n");

    let cubic = CubicBezier::new(
        Point::new(20.0, 100.0),
        Point::new(80.0, 20.0),
        Point::new(220.0, 180.0),
        Point::new(280.0, 100.0),
    );

    let curve_type = BezierCurveType::Cubic(cubic);
    let config = SubdivisionConfig::new().with_max_depth(4).with_flatness(1.0);
    let points = curve_to_polyline(&curve_type, &config);

    println!("细分点数: {}", points.len());
    println!("点序列: {}", points_to_text(&points));

    let renderer = SvgRenderer::new(300.0, 200.0);
    let svg = renderer.render_polyline(&points);
    println!("\n折线 SVG: {} 字节", svg.len());
}

fn demo_complete_svg() {
    println!("\n--- 5. 完整 SVG 文件 ---\n");

    let svg_content = generate_complete_svg();
    println!("完整 SVG 文件内容:");
    println!("  长度: {} 字节", svg_content.len());
    println!("  包含: 多条曲线 + 控制点 + 注释");
    println!("\n可保存为 .svg 文件用浏览器打开查看");
}

fn generate_complete_svg() -> String {
    let mut svg = String::new();

    // SVG 头部
    svg.push_str(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\
         <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"600\" height=\"400\" viewBox=\"0 0 600 400\">\n\
         <rect width=\"100%\" height=\"100%\" fill=\"#f0f0f0\"/>\n\
         <text x=\"300\" y=\"30\" text-anchor=\"middle\" font-size=\"20\" font-family=\"Arial\">贝塞尔曲线示例</text>\n",
    );

    // 曲线 1: 基本 S 形
    svg.push_str(
        "\n<!-- 曲线 1: S 形 -->\n\
         <path d=\"M 50 350 C 50 150 250 150 250 350\" fill=\"none\" stroke=\"#2196F3\" stroke-width=\"3\"/>\n\
         <circle cx=\"50\" cy=\"350\" r=\"5\" fill=\"#1976D2\"/>\n\
         <circle cx=\"50\" cy=\"150\" r=\"4\" fill=\"#FF5722\"/>\n\
         <circle cx=\"250\" cy=\"150\" r=\"4\" fill=\"#FF5722\"/>\n\
         <circle cx=\"250\" cy=\"350\" r=\"5\" fill=\"#1976D2\"/>\n",
    );

    // 曲线 2: 心形轮廓
    svg.push_str(
        "\n<!-- 曲线 2: 心形轮廓 -->\n\
         <path d=\"M 400 200 C 400 100 550 100 550 200 C 550 300 400 350 400 350 C 400 350 250 300 250 200 C 250 100 400 100 400 200 Z\"\n\
         fill=\"rgba(244, 67, 54, 0.3)\" stroke=\"#F44336\" stroke-width=\"2\"/>\n",
    );

    // 曲线 3: 二次曲线
    svg.push_str(
        "\n<!-- 曲线 3: 二次曲线 -->\n\
         <path d=\"M 50 50 Q 150 150 250 50\" fill=\"none\" stroke=\"#4CAF50\" stroke-width=\"3\"/>\n\
         <line x1=\"50\" y1=\"50\" x2=\"150\" y2=\"150\" stroke=\"#4CAF50\" stroke-width=\"1\" stroke-dasharray=\"5,5\" opacity=\"0.5\"/>\n\
         <line x1=\"150\" y1=\"150\" x2=\"250\" y2=\"50\" stroke=\"#4CAF50\" stroke-width=\"1\" stroke-dasharray=\"5,5\" opacity=\"0.5\"/>\n\
         <circle cx=\"150\" cy=\"150\" r=\"4\" fill=\"#FF5722\"/>\n",
    );

    // 图例
    svg.push_str(
        "\n<!-- 图例 -->\n\
         <rect x=\"420\" y=\"30\" width=\"160\" height=\"120\" fill=\"white\" stroke=\"#ccc\" rx=\"5\"/>\n\
         <text x=\"430\" y=\"55\" font-size=\"12\" font-family=\"Arial\">图例:</text>\n\
         <line x1=\"430\" y1=\"70\" x2=\"460\" y2=\"70\" stroke=\"#2196F3\" stroke-width=\"3\"/>\n\
         <text x=\"470\" y=\"75\" font-size=\"10\" font-family=\"Arial\">三次贝塞尔曲线</text>\n\
         <line x1=\"430\" y1=\"90\" x2=\"460\" y2=\"90\" stroke=\"#4CAF50\" stroke-width=\"3\"/>\n\
         <text x=\"470\" y=\"95\" font-size=\"10\" font-family=\"Arial\">二次贝塞尔曲线</text>\n\
         <circle cx=\"445\" cy=\"115\" r=\"4\" fill=\"#FF5722\"/>\n\
         <text x=\"470\" y=\"120\" font-size=\"10\" font-family=\"Arial\">控制点</text>\n\
         <circle cx=\"445\" cy=\"135\" r=\"4\" fill=\"#1976D2\"/>\n\
         <text x=\"470\" y=\"140\" font-size=\"10\" font-family=\"Arial\">端点</text>\n",
    );

    svg.push_str("</svg>");
    svg
}
