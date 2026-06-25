//! 基本曲线示例
//!
//! 演示如何创建和操作贝塞尔曲线。

use bezier_engine::{Point, QuadraticBezier, CubicBezier, BezierCurve};

fn main() {
    println!("=== 基本贝塞尔曲线示例 ===\n");

    // 创建二次贝塞尔曲线
    let quad = QuadraticBezier::new(
        Point::new(0.0, 0.0),
        Point::new(50.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("二次贝塞尔曲线: {}", quad);
    println!("控制点: P0={}, P1={}, P2={}", quad.p0, quad.p1, quad.p2);

    // 在曲线上采样
    println!("\n曲线上的点:");
    for i in 0..=10 {
        let t = i as f64 / 10.0;
        let point = quad.evaluate(t);
        println!("  t={:.1}: {}", t, point);
    }

    // 计算曲线长度
    let length = quad.length(100);
    println!("\n曲线长度 (100段近似): {:.2}", length);

    // 创建三次贝塞尔曲线
    println!("\n--- 三次贝塞尔曲线 ---\n");

    let cubic = CubicBezier::new(
        Point::new(0.0, 0.0),
        Point::new(33.0, 100.0),
        Point::new(67.0, 100.0),
        Point::new(100.0, 0.0),
    );

    println!("三次贝塞尔曲线: {}", cubic);
    println!("控制点: P0={}, P1={}, P2={}, P3={}", cubic.p0, cubic.p1, cubic.p2, cubic.p3);

    // 计算导数
    println!("\n导数 (切线向量):");
    for i in 0..=5 {
        let t = i as f64 / 5.0;
        let deriv = cubic.evaluate_derivative(t);
        println!("  t={:.1}: {}", t, deriv);
    }

    // 升阶
    println!("\n--- 升阶操作 ---\n");
    let elevated = quad.elevate_to_cubic();
    println!("二次曲线升阶后: {}", elevated);
    println!("验证: 二次曲线 t=0.5 = {}", quad.evaluate(0.5));
    println!("验证: 升阶曲线 t=0.5 = {}", elevated.evaluate(0.5));

    // 找最近点
    println!("\n--- 最近点查找 ---\n");
    let query = Point::new(40.0, 60.0);
    let t = cubic.closest_point_parameter(&query, 200);
    let closest = cubic.evaluate(t);
    println!("查询点: {}", query);
    println!("曲线上的最近点: {} (t={:.3})", closest, t);
    println!("距离: {:.2}", query.distance_to(&closest));

    // 包围盒
    let (min, max) = cubic.bounding_box();
    println!("\n包围盒: ({}, {})", min, max);
}
