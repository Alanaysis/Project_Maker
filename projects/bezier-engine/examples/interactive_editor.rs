//! 交互式编辑器示例
//!
//! 演示曲线编辑器的各种操作。

use bezier_engine::{
    Point, QuadraticBezier, CubicBezier,
    CurveEditor, SvgRenderer, BezierCurveType,
};

fn main() {
    println!("=== 交互式编辑器示例 ===\n");

    // 1. 创建编辑器
    let mut editor = CurveEditor::new();

    // 2. 添加曲线
    println!("--- 添加曲线 ---");
    let idx1 = editor.add_quadratic(QuadraticBezier::new(
        Point::new(50.0, 200.0),
        Point::new(150.0, 50.0),
        Point::new(250.0, 200.0),
    ));
    println!("添加二次曲线: 索引 {}", idx1);

    let idx2 = editor.add_cubic(CubicBezier::new(
        Point::new(300.0, 200.0),
        Point::new(350.0, 50.0),
        Point::new(450.0, 50.0),
        Point::new(500.0, 200.0),
    ));
    println!("添加三次曲线: 索引 {}", idx2);

    println!("当前曲线数: {}", editor.curve_count());

    // 3. 选择和移动控制点
    println!("\n--- 选择和移动控制点 ---");

    // 选择第一条曲线的中间控制点
    editor.select_point(idx1, 1);
    println!("选择: 曲线{}, 控制点{}", idx1, 1);

    if let Some(curve) = editor.get_curve(idx1) {
        println!("移动前: {}", curve.evaluate(0.5));
    }

    // 向上移动
    editor.move_selected_point(Point::new(0.0, -50.0));
    println!("移动 (0, -50)");

    if let Some(curve) = editor.get_curve(idx1) {
        println!("移动后: {}", curve.evaluate(0.5));
    }

    // 4. 设置控制点位置
    println!("\n--- 设置控制点位置 ---");

    editor.set_point(idx2, 1, Point::new(350.0, 30.0));
    editor.set_point(idx2, 2, Point::new(450.0, 30.0));
    println!("设置曲线{}的控制点1和2为更低的位置", idx2);

    // 5. 分割曲线
    println!("\n--- 分割曲线 ---");

    println!("分割前曲线数: {}", editor.curve_count());
    if let Some((left, right)) = editor.split_curve(idx2, 0.5) {
        println!("在 t=0.5 处分割曲线{}", idx2);
        println!("新曲线索引: {} 和 {}", left, right);
        println!("分割后曲线数: {}", editor.curve_count());
    }

    // 6. 反转曲线
    println!("\n--- 反转曲线 ---");

    if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(idx1) {
        println!("反转前起点: {}", curve.p0);
    }

    editor.reverse_curve(idx1);

    if let Some(BezierCurveType::Quadratic(curve)) = editor.get_curve(idx1) {
        println!("反转后起点: {}", curve.p0);
    }

    // 7. 提升曲线
    println!("\n--- 提升曲线 ---");

    editor.elevate_to_cubic(idx1);
    if let Some(curve) = editor.get_curve(idx1) {
        println!("提升后曲线类型: {}阶", curve.degree());
    }

    // 8. 查找最近点
    println!("\n--- 查找最近点 ---");

    let query = Point::new(200.0, 100.0);
    if let Some((curve_idx, point_idx)) = editor.find_nearest_control_point(query, 50.0) {
        println!("距离({})最近的控制点: 曲线{}, 点{}", query, curve_idx, point_idx);
    }

    if let Some((curve_idx, t)) = editor.find_nearest_curve_point(query) {
        let point_on_curve = editor.get_curve(curve_idx).unwrap().evaluate(t);
        println!("距离({})最近的曲线点: 曲线{}, t={:.3}, 点={}", query, curve_idx, t, point_on_curve);
    }

    // 9. 生成 SVG
    println!("\n--- 生成 SVG ---");

    let renderer = SvgRenderer::new(600.0, 300.0);
    let mut all_curves = Vec::new();

    for i in 0..editor.curve_count() {
        if let Some(curve) = editor.get_curve(i) {
            all_curves.push(curve.clone());
        }
    }

    let svg = renderer.render_curves(&all_curves);
    println!("生成 SVG: {} 字节", svg.len());

    // 10. 删除曲线
    println!("\n--- 删除曲线 ---");

    println!("删除前曲线数: {}", editor.curve_count());
    editor.remove_curve(idx1);
    println!("删除曲线{}后: {} 条曲线", idx1, editor.curve_count());

    println!("\n编辑器演示完成!");
}
