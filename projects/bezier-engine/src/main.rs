//! 贝塞尔曲线引擎演示程序

use bezier_engine::{
    Point, QuadraticBezier, CubicBezier, BezierCurve, BezierCurveType,
    CurveEditor, SvgRenderer, SvgStyle, SvgColor,
    SubdivisionConfig,
    renderer::curve_to_polyline, renderer::points_to_text,
};

fn main() {
    println!("=== 贝塞尔曲线引擎演示 ===\n");

    // 1. 基本曲线创建和求值
    demo_basic_curves();

    // 2. 曲线细分
    demo_subdivision();

    // 3. 曲线编辑
    demo_editor();

    // 4. SVG 输出
    demo_svg_output();

    println!("\n=== 演示完成 ===");
}

fn demo_basic_curves() {
    println!("--- 1. 基本曲线操作 ---");

    // 二次贝塞尔曲线
    let quad = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("二次贝塞尔曲线: {}", quad);
    println!("  阶数: {}", quad.degree());
    println!("  t=0: {}", quad.evaluate(0.0));
    println!("  t=0.5: {}", quad.evaluate(0.5));
    println!("  t=1: {}", quad.evaluate(1.0));
    println!("  曲线长度 (100段): {:.2}", quad.length(100));

    // 三次贝塞尔曲线
    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("\n三次贝塞尔曲线: {}", cubic);
    println!("  阶数: {}", cubic.degree());
    println!("  t=0: {}", cubic.evaluate(0.0));
    println!("  t=0.5: {}", cubic.evaluate(0.5));
    println!("  t=1: {}", cubic.evaluate(1.0));
    println!("  曲线长度 (100段): {:.2}", cubic.length(100));

    // 升阶
    let elevated = quad.elevate_to_cubic();
    println!("\n升阶后的曲线: {}", elevated);

    println!();
}

fn demo_subdivision() {
    println!("--- 2. 曲线细分 ---");

    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 均匀细分
    let config = SubdivisionConfig::new()
        .with_max_depth(4)
        .with_flatness(1.0);

    let curve_type = bezier_engine::BezierCurveType::Cubic(cubic.clone());
    let points = curve_to_polyline(&curve_type, &config);

    println!("自适应细分结果 ({} 个点):", points.len());
    println!("  {}", points_to_text(&points));

    // 控制点上的最近点
    let query_point = Point::new(50.0, 80.0);
    let t = cubic.closest_point_parameter(&query_point, 100);
    let closest = cubic.evaluate(t);
    println!("\n查询点: {}", query_point);
    println!("  曲线上最近点: {} (t={:.3})", closest, t);
    println!("  距离: {:.2}", query_point.distance_to(&closest));

    println!();
}

fn demo_editor() {
    println!("--- 3. 曲线编辑 ---");

    let mut editor = CurveEditor::new();

    // 添加曲线
    let quad = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );
    let idx = editor.add_quadratic(quad);
    println!("添加二次曲线，索引: {}", idx);

    let cubic = CubicBezier::new(
        Point::new(200.0, 0.0),
        Point::new(225.0, 100.0),
        Point::new(275.0, 100.0),
        Point::new(300.0, 0.0),
    );
    let idx = editor.add_cubic(cubic);
    println!("添加三次曲线，索引: {}", idx);

    println!("曲线总数: {}", editor.curve_count());

    // 选择和移动
    editor.select_point(0, 1);
    println!("选择控制点: 曲线{}, 点{}", 0, 1);

    editor.move_selected_point(Point::new(0.0, -30.0));
    println!("移动控制点 (0, -30)");

    if let Some(curve) = editor.get_curve(0) {
        println!("移动后曲线上的中点: {}", curve.evaluate(0.5));
    }

    // 分割曲线
    println!("\n在 t=0.5 处分割曲线...");
    if let Some((left, right)) = editor.split_curve(0, 0.5) {
        println!("分割成功，新曲线索引: {} 和 {}", left, right);
        println!("曲线总数: {}", editor.curve_count());
    }

    // 反转曲线
    println!("\n反转曲线 1...");
    editor.reverse_curve(1);
    if let Some(BezierCurveType::Cubic(curve)) = editor.get_curve(1) {
        println!("反转后起点: {}, 终点: {}", curve.p0, curve.p3);
    }

    // 提升到三次
    println!("\n提升曲线 0 到三次...");
    editor.elevate_to_cubic(0);
    if let Some(curve) = editor.get_curve(0) {
        println!("提升后阶数: {}", curve.degree());
    }

    println!();
}

fn demo_svg_output() {
    println!("--- 4. SVG 输出 ---");

    let renderer = SvgRenderer::new(400.0, 200.0);

    // 创建曲线
    let cubic = CubicBezier::new(
        Point::new(20.0, 100.0),
        Point::new(100.0, 20.0),
        Point::new(300.0, 180.0),
        Point::new(380.0, 100.0),
    );

    // 渲染为 SVG
    let svg = renderer.render_cubic(&cubic);

    println!("生成 SVG (前 200 字符):");
    println!("  {}...", &svg[..200.min(svg.len())]);
    println!("\nSVG 字符串长度: {} 字节", svg.len());

    // 自定义样式
    let style = SvgStyle {
        stroke_color: SvgColor::rgb(0, 128, 255),
        stroke_width: 3.0,
        control_point_radius: 5.0,
        ..SvgStyle::default()
    };

    let styled_svg = SvgRenderer::new(400.0, 200.0)
        .with_style(style)
        .render_cubic(&cubic);

    println!("\n自定义样式 SVG 长度: {} 字节", styled_svg.len());

    // 保存到文件的提示
    println!("\n提示: 可以将 SVG 字符串写入 .svg 文件，用浏览器查看");
}
