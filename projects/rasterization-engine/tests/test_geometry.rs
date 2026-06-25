use rasterization::geometry::{Point, Triangle};

fn main() {
    let passed = 0;
    let total = 0;

    // Test 1: Point distance
    let p1 = Point::new(0.0, 0.0);
    let p2 = Point::new(3.0, 4.0);
    assert!((p1.distance_to(&p2) - 5.0).abs() < 1e-6);
    println!("test_point_distance: PASS");

    // Test 2: Point lerp
    let p3 = p1.lerp(&p2, 0.5);
    assert!((p3.x - 1.5).abs() < 1e-6);
    assert!((p3.y - 2.0).abs() < 1e-6);
    println!("test_point_lerp: PASS");

    // Test 3: Triangle area
    let tri = Triangle::new(
        Point::new(0.0, 0.0),
        Point::new(4.0, 0.0),
        Point::new(0.0, 3.0),
    );
    assert!((tri.area() - 6.0).abs() < 1e-6);
    println!("test_triangle_area: PASS");

    // Test 4: Barycentric - inside point
    let tri2 = Triangle::new(
        Point::new(0.0, 0.0),
        Point::new(10.0, 0.0),
        Point::new(0.0, 10.0),
    );
    let center = Point::new(3.0, 3.0);
    assert!(tri2.barycentric(&center).is_some());
    println!("test_barycentric_inside: PASS");

    // Test 5: Barycentric - outside point
    let outside = Point::new(15.0, 15.0);
    assert!(tri2.barycentric(&outside).is_none());
    println!("test_barycentric_outside: PASS");

    // Test 6: Barycentric - vertex
    assert!(tri2.barycentric(&Point::new(0.0, 0.0)).is_some());
    println!("test_barycentric_vertex: PASS");

    println!("\n全部测试通过!");
}
