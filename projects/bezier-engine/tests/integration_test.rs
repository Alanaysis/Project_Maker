//! 集成测试

use bezier_engine::{
    Point, QuadraticBezier, CubicBezier, BezierCurve,
    CurveEditor, SvgRenderer, SvgStyle, SvgColor, BezierCurveType,
    SubdivisionConfig, subdivide_quadratic, subdivide_cubic,
    adaptive_subdivide_cubic,
    uniform_subdivide_quadratic,
    renderer::{curve_to_polyline, points_to_text},
};

// ==================== 点操作测试 ====================

#[test]
fn test_point_basic_operations() {
    let p1 = Point::new(3.0, 4.0);
    let p2 = Point::new(6.0, 8.0);

    // 距离
    assert!((p1.distance_to(&p2) - 5.0).abs() < 1e-10);

    // 插值
    let mid = p1.lerp(&p2, 0.5);
    assert!((mid.x - 4.5).abs() < 1e-10);
    assert!((mid.y - 6.0).abs() < 1e-10);

    // 算术
    let sum = p1 + p2;
    assert_eq!(sum, Point::new(9.0, 12.0));

    let scaled = p1 * 2.0;
    assert_eq!(scaled, Point::new(6.0, 8.0));
}

#[test]
fn test_point_vector_operations() {
    let p = Point::new(3.0, 4.0);

    // 长度
    assert!((p.length() - 5.0).abs() < 1e-10);

    // 归一化
    let n = p.normalize();
    assert!((n.length() - 1.0).abs() < 1e-10);

    // 点积
    let p1 = Point::new(1.0, 0.0);
    let p2 = Point::new(0.0, 1.0);
    assert!((p1.dot(&p2)).abs() < 1e-10);

    // 叉积
    assert!((p1.cross(&p2) - 1.0).abs() < 1e-10);
}

// ==================== 二次贝塞尔曲线测试 ====================

#[test]
fn test_quadratic_bezier_evaluation() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 端点
    let start = curve.evaluate(0.0);
    let end = curve.evaluate(1.0);
    assert!((start.x - 0.0).abs() < 1e-10);
    assert!((end.x - 100.0).abs() < 1e-10);

    // 中点
    let mid = curve.evaluate(0.5);
    assert!((mid.x - 50.0).abs() < 1e-10);
    assert!((mid.y - 50.0).abs() < 1e-10);

    // 边界情况
    let t_neg = curve.evaluate(-0.1);
    let t_over = curve.evaluate(1.1);
    assert!((t_neg.x - 0.0).abs() < 1e-10);
    assert!((t_over.x - 100.0).abs() < 1e-10);
}

#[test]
fn test_quadratic_bezier_derivative() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // t=0 处的导数
    let deriv = curve.evaluate_derivative(0.0);
    assert!((deriv.x - 100.0).abs() < 1e-10);
    assert!((deriv.y - 200.0).abs() < 1e-10);

    // t=1 处的导数
    let deriv = curve.evaluate_derivative(1.0);
    assert!((deriv.x - 100.0).abs() < 1e-10);
    assert!((deriv.y - (-200.0)).abs() < 1e-10);
}

#[test]
fn test_quadratic_bezier_length() {
    // 直线曲线
    let line = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 0.0),
        Point::new(100.0, 0.0),
    );
    let length = line.length(100);
    assert!((length - 100.0).abs() < 1.0);

    // 弯曲曲线应该更长
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );
    let length = curve.length(100);
    assert!(length > 100.0);
}

#[test]
fn test_quadratic_bezier_closest_point() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 查询点在控制点附近
    let query = Point::new(48.0, 102.0);
    let t = curve.closest_point_parameter(&query, 100);
    let closest = curve.evaluate(t);
    let dist = query.distance_to(&closest);

    // 距离应该小于到端点的距离
    let dist_to_start = query.distance_to(&Point::new(0.0, 0.0));
    let dist_to_end = query.distance_to(&Point::new(100.0, 0.0));
    assert!(dist < dist_to_start);
    assert!(dist < dist_to_end);
}

#[test]
fn test_quadratic_elevate_to_cubic() {
    let quad = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let cubic = quad.elevate_to_cubic();

    // 端点应该一致
    let start = cubic.evaluate(0.0);
    let end = cubic.evaluate(1.0);
    assert!((start.x - 0.0).abs() < 1e-10);
    assert!((end.x - 100.0).abs() < 1e-10);

    // 中点应该一致
    let mid_quad = quad.evaluate(0.5);
    let mid_cubic = cubic.evaluate(0.5);
    assert!((mid_quad.x - mid_cubic.x).abs() < 1e-10);
    assert!((mid_quad.y - mid_cubic.y).abs() < 1e-10);
}

// ==================== 三次贝塞尔曲线测试 ====================

#[test]
fn test_cubic_bezier_evaluation() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 端点
    let start = curve.evaluate(0.0);
    let end = curve.evaluate(1.0);
    assert!((start.x - 0.0).abs() < 1e-10);
    assert!((end.x - 100.0).abs() < 1e-10);

    // 中点
    let mid = curve.evaluate(0.5);
    assert!((mid.x - 50.0).abs() < 1e-10);
    assert!((mid.y - 75.0).abs() < 1e-10);
}

#[test]
fn test_cubic_bezier_bounding_box() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(100.0, 50.0),
        Point::new(0.0, 50.0),
        Point::new(100.0, 0.0),
    );

    let (min, max) = curve.bounding_box();
    assert!((min.x - 0.0).abs() < 1e-10);
    assert!((min.y - 0.0).abs() < 1e-10);
    assert!((max.x - 100.0).abs() < 1e-10);
    assert!((max.y - 50.0).abs() < 1e-10);
}

#[test]
fn test_cubic_bezier_derivative() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(33.0, 100.0),
        Point::new(67.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // t=0 处的导数
    let deriv = curve.evaluate_derivative(0.0);
    // 应该是 3(P1-P0) = (99, 300)
    assert!((deriv.x - 99.0).abs() < 1e-10);
    assert!((deriv.y - 300.0).abs() < 1e-10);
}

// ==================== 细分测试 ====================

#[test]
fn test_quadratic_subdivision() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let (left, right) = subdivide_quadratic(&curve, 0.5);

    // 连续性
    let mid_left = left.evaluate(1.0);
    let mid_right = right.evaluate(0.0);
    assert!((mid_left.x - mid_right.x).abs() < 1e-10);
    assert!((mid_left.y - mid_right.y).abs() < 1e-10);

    // 端点
    assert!((left.p0.x - 0.0).abs() < 1e-10);
    assert!((right.p2.x - 100.0).abs() < 1e-10);
}

#[test]
fn test_cubic_subdivision() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let (left, right) = subdivide_cubic(&curve, 0.5);

    // 连续性
    let mid_left = left.evaluate(1.0);
    let mid_right = right.evaluate(0.0);
    assert!((mid_left.x - mid_right.x).abs() < 1e-10);
    assert!((mid_left.y - mid_right.y).abs() < 1e-10);

    // 端点
    assert!((left.p0.x - 0.0).abs() < 1e-10);
    assert!((right.p3.x - 100.0).abs() < 1e-10);
}

#[test]
fn test_uniform_subdivision() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let points = uniform_subdivide_quadratic(&curve, 10);
    assert_eq!(points.len(), 11);

    // 第一个点是起点
    assert!((points[0].x - 0.0).abs() < 1e-10);
    // 最后一个点是终点
    assert!((points[10].x - 100.0).abs() < 1e-10);
}

#[test]
fn test_adaptive_subdivision() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let config = SubdivisionConfig::new()
        .with_max_depth(5)
        .with_flatness(1.0);

    let points = adaptive_subdivide_cubic(&curve, &config);

    // 应该生成多个点
    assert!(points.len() > 2);

    // 端点
    assert!((points[0].x - 0.0).abs() < 1e-10);
    let last = points.len() - 1;
    assert!((points[last].x - 100.0).abs() < 1e-10);
}

// ==================== 编辑器测试 ====================

#[test]
fn test_editor_basic_operations() {
    let mut editor = CurveEditor::new();

    // 添加曲线
    let idx = editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));
    assert_eq!(idx, 0);
    assert_eq!(editor.curve_count(), 1);

    // 选择
    assert!(editor.select_curve(0));
    assert!(editor.select_point(0, 1));
    assert_eq!(editor.selected_curve(), Some(0));
    assert_eq!(editor.selected_point(), Some(1));
}

#[test]
fn test_editor_move_point() {
    let mut editor = CurveEditor::new();

    editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    editor.select_point(0, 1);
    editor.move_selected_point(Point::new(10.0, -20.0));

    if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(0) {
        assert!((curve.p1.x - 60.0).abs() < 1e-10);
        assert!((curve.p1.y - 80.0).abs() < 1e-10);
    } else {
        panic!("Expected quadratic curve");
    }
}

#[test]
fn test_editor_split_curve() {
    let mut editor = CurveEditor::new();

    editor.add_cubic(CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    assert_eq!(editor.curve_count(), 1);

    let result = editor.split_curve(0, 0.5);
    assert!(result.is_some());
    assert_eq!(editor.curve_count(), 2);
}

#[test]
fn test_editor_reverse_curve() {
    let mut editor = CurveEditor::new();

    editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    editor.reverse_curve(0);

    if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(0) {
        assert!((curve.p0.x - 100.0).abs() < 1e-10);
        assert!((curve.p2.x - 0.0).abs() < 1e-10);
    } else {
        panic!("Expected quadratic curve");
    }
}

#[test]
fn test_editor_elevate_to_cubic() {
    let mut editor = CurveEditor::new();

    editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    assert!(editor.elevate_to_cubic(0));

    if let Some(BezierCurveType::Cubic(_)) = editor.get_curve(0) {
        // 成功
    } else {
        panic!("Expected cubic curve after elevation");
    }
}

#[test]
fn test_editor_find_nearest() {
    let mut editor = CurveEditor::new();

    editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    // 查找接近 (50, 100) 的控制点
    let result = editor.find_nearest_control_point(Point::new(48.0, 102.0), 10.0);
    assert!(result.is_some());
    let (curve_idx, point_idx) = result.unwrap();
    assert_eq!(curve_idx, 0);
    assert_eq!(point_idx, 1); // p1 = (50, 100)
}

#[test]
fn test_editor_remove_curve() {
    let mut editor = CurveEditor::new();

    editor.add_quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));
    editor.add_cubic(CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    assert_eq!(editor.curve_count(), 2);

    editor.remove_curve(0);
    assert_eq!(editor.curve_count(), 1);

    // 删除后应该可以访问剩余曲线
    assert!(editor.get_curve(0).is_some());
}

// ==================== 渲染器测试 ====================

#[test]
fn test_svg_renderer_quadratic() {
    let renderer = SvgRenderer::new(200.0, 200.0);
    let curve = QuadraticBezier::new(
        Point::new(10.0, 10.0),
        Point::new(100.0, 150.0),
        Point::new(190.0, 10.0),
    );

    let svg = renderer.render_quadratic(&curve);

    assert!(svg.contains("<svg"));
    assert!(svg.contains("</svg>"));
    assert!(svg.contains("Q"));
    assert!(svg.contains("M 10 10"));
}

#[test]
fn test_svg_renderer_cubic() {
    let renderer = SvgRenderer::new(300.0, 200.0);
    let curve = CubicBezier::new(
        Point::new(10.0, 100.0),
        Point::new(80.0, 10.0),
        Point::new(220.0, 190.0),
        Point::new(290.0, 100.0),
    );

    let svg = renderer.render_cubic(&curve);

    assert!(svg.contains("<svg"));
    assert!(svg.contains("C"));
    assert!(svg.contains("M 10 100"));
}

#[test]
fn test_svg_renderer_custom_style() {
    let style = SvgStyle {
        stroke_color: SvgColor::rgb(255, 0, 0),
        stroke_width: 3.0,
        control_point_radius: 6.0,
        ..SvgStyle::default()
    };

    let renderer = SvgRenderer::new(200.0, 200.0).with_style(style);
    let curve = QuadraticBezier::new(
        Point::new(10.0, 10.0),
        Point::new(100.0, 150.0),
        Point::new(190.0, 10.0),
    );

    let svg = renderer.render_quadratic(&curve);

    assert!(svg.contains("rgb(255,0,0)"));
    assert!(svg.contains("stroke-width=\"3\""));
    assert!(svg.contains("r=\"6\""));
}

#[test]
fn test_svg_renderer_no_control_points() {
    let style = SvgStyle {
        show_control_points: false,
        show_control_lines: false,
        ..SvgStyle::default()
    };

    let renderer = SvgRenderer::new(200.0, 200.0).with_style(style);
    let curve = QuadraticBezier::new(
        Point::new(10.0, 10.0),
        Point::new(100.0, 150.0),
        Point::new(190.0, 10.0),
    );

    let svg = renderer.render_quadratic(&curve);

    assert!(!svg.contains("<circle"));
    assert!(!svg.contains("<line"));
}

#[test]
fn test_svg_renderer_multiple_curves() {
    let renderer = SvgRenderer::new(400.0, 200.0);

    let curves = vec![
        BezierCurveType::Quadratic(QuadraticBezier::new(
            Point::new(10.0, 100.0),
            Point::new(100.0, 10.0),
            Point::new(190.0, 100.0),
        )),
        BezierCurveType::Cubic(CubicBezier::new(
            Point::new(210.0, 100.0),
            Point::new(260.0, 10.0),
            Point::new(340.0, 190.0),
            Point::new(390.0, 100.0),
        )),
    ];

    let svg = renderer.render_curves(&curves);

    assert!(svg.contains("<svg"));
    assert!(svg.contains("</svg>"));
    // 应该包含两条路径
    assert!(svg.matches("<path").count() >= 2);
}

#[test]
fn test_curve_to_polyline() {
    let curve = BezierCurveType::Quadratic(QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ));

    let config = SubdivisionConfig::new().with_max_depth(3);
    let points = curve_to_polyline(&curve, &config);

    assert!(points.len() >= 2);
    assert!((points.first().unwrap().x - 0.0).abs() < 1e-10);
    assert!((points.last().unwrap().x - 100.0).abs() < 1e-10);
}

#[test]
fn test_points_to_text() {
    let points = vec![
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    ];

    let text = points_to_text(&points);
    assert_eq!(text, "(0.00, 0.00) -> (50.00, 100.00) -> (100.00, 0.00)");
}

// ==================== 边界情况测试 ====================

#[test]
fn test_degenerate_curve() {
    // 退化曲线（所有控制点重合）
    let curve = QuadraticBezier::new(
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
        Point::new(50.0, 50.0),
    );

    let point = curve.evaluate(0.5);
    assert!((point.x - 50.0).abs() < 1e-10);
    assert!((point.y - 50.0).abs() < 1e-10);

    let length = curve.length(10);
    assert!((length - 0.0).abs() < 1e-10);
}

#[test]
fn test_very_small_curve() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(0.001, 0.001),
        Point::new(0.002, 0.0),
    );

    let length = curve.length(10);
    assert!(length < 0.01);
}

#[test]
fn test_large_curve() {
    let curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(1000.0, 5000.0),
        Point::new(5000.0, 5000.0),
        Point::new(10000.0, 0.0),
    );

    let length = curve.length(100);
    assert!(length > 10000.0);
}

#[test]
fn test_closest_point_on_endpoint() {
    let curve = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 查询点在起点附近
    let query = Point::new(1.0, 1.0);
    let t = curve.closest_point_parameter(&query, 100);
    assert!(t < 0.1);

    // 查询点在终点附近
    let query = Point::new(99.0, 1.0);
    let t = curve.closest_point_parameter(&query, 100);
    assert!(t > 0.9);
}
