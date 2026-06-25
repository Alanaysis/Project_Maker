//! 曲线细分示例
//!
//! 演示贝塞尔曲线的细分算法。

use bezier_engine::{
    Point, QuadraticBezier, CubicBezier, BezierCurve,
    SubdivisionConfig, subdivide_cubic,
    adaptive_subdivide_cubic,
    uniform_subdivide_quadratic, uniform_subdivide_cubic,
    renderer::points_to_text,
};

fn main() {
    println!("=== 贝塞尔曲线细分示例 ===\n");

    // 1. 固定点细分
    demo_fixed_subdivision();

    // 2. 均匀细分
    demo_uniform_subdivision();

    // 3. 自适应细分
    demo_adaptive_subdivision();
}

fn demo_fixed_subdivision() {
    println!("--- 1. 固定点细分 ---\n");

    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("原始曲线: {}", cubic);

    // 在 t=0.5 处细分
    let (left, right) = subdivide_cubic(&cubic, 0.5);
    println!("\n在 t=0.5 处细分:");
    println!("  左段: {}", left);
    println!("  右段: {}", right);

    // 验证连续性
    let mid_left = left.evaluate(1.0);
    let mid_right = right.evaluate(0.0);
    println!("\n连续性验证:");
    println!("  左段终点: {}", mid_left);
    println!("  右段起点: {}", mid_right);
    println!("  距离: {:.10}", mid_left.distance_to(&mid_right));

    // 在不同位置细分
    println!("\n在不同位置细分:");
    for t in [0.25, 0.5, 0.75] {
        let (left, _right) = subdivide_cubic(&cubic, t);
        let mid = left.evaluate(1.0);
        println!("  t={:.2}: 分割点 = {}", t, mid);
    }
}

fn demo_uniform_subdivision() {
    println!("\n--- 2. 均匀细分 ---\n");

    let quad = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("二次曲线: {}", quad);

    // 不同段数的细分
    for n in [4, 8, 16] {
        let points = uniform_subdivide_quadratic(&quad, n);
        println!("\n{} 段细分 ({} 个点):", n, points.len());
        println!("  {}", points_to_text(&points));
    }

    // 三次曲线
    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    let points = uniform_subdivide_cubic(&cubic, 10);
    println!("\n三次曲线 10 段细分:");
    println!("  {}", points_to_text(&points));
}

fn demo_adaptive_subdivision() {
    println!("\n--- 3. 自适应细分 ---\n");

    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(25.0, 100.0),
        Point::new(75.0, 100.0),
        Point::new(100.0, 0.0),
    );

    // 不同配置的自适应细分
    let configs = vec![
        ("低精度", SubdivisionConfig::new().with_max_depth(2).with_flatness(5.0)),
        ("中精度", SubdivisionConfig::new().with_max_depth(5).with_flatness(1.0)),
        ("高精度", SubdivisionConfig::new().with_max_depth(8).with_flatness(0.1)),
    ];

    for (name, config) in configs {
        let points = adaptive_subdivide_cubic(&cubic, &config);
        println!("{}配置: {} 个点", name, points.len());

        // 计算折线长度
        let mut length = 0.0;
        for i in 0..points.len() - 1 {
            length += points[i].distance_to(&points[i + 1]);
        }
        println!("  折线长度: {:.2}", length);
        println!("  原始曲线长度: {:.2}", cubic.length(100));
    }

    // 比较接近直线的曲线
    println!("\n--- 接近直线的曲线 ---\n");

    let flat_curve = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(33.0, 1.0),
        Point::new(67.0, 1.0),
        Point::new(100.0, 0.0),
    );

    let config = SubdivisionConfig::new().with_max_depth(5).with_flatness(1.0);
    let points = adaptive_subdivide_cubic(&flat_curve, &config);
    println!("接近直线的曲线自适应细分: {} 个点", points.len());
    println!("  (由于平坦度低，细分点数少)");
}
