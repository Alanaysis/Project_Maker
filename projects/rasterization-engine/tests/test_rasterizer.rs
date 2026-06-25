use rasterization::rasterizer::Rasterizer;
use rasterization::geometry::{Triangle, Point};

fn main() {
    let passed = 0;
    let total = 0;

    // Test 1: Clear
    let mut ras = Rasterizer::new(10, 10);
    ras.clear(0xff0000);
    assert_eq!(ras.get_pixel(0, 0), 0xff0000);
    println!("test_clear: PASS");

    // Test 2: Set pixel
    ras.set_pixel(5, 5, 0x00ff00);
    assert_eq!(ras.get_pixel(5, 5), 0x00ff00);
    println!("test_set_pixel: PASS");

    // Test 3: Fill triangle
    let mut ras2 = Rasterizer::new(10, 10);
    ras2.clear(0x000000);
    let tri = Triangle::new(
        Point::new(3.0, 3.0),
        Point::new(7.0, 3.0),
        Point::new(5.0, 7.0),
    );
    ras2.fill_triangle(&tri, 0xffffff);
    // Check center pixel is filled
    assert_eq!(ras2.get_pixel(5, 5), 0xffffff);
    println!("test_fill_triangle: PASS");

    // Test 4: Draw line
    let mut ras3 = Rasterizer::new(10, 10);
    ras3.clear(0x000000);
    ras3.draw_line(0, 5, 9, 5, 0xaaaaaa);
    assert_eq!(ras3.get_pixel(5, 5), 0xaaaaaa);
    println!("test_draw_line: PASS");

    // Test 5: Fill rect
    let mut ras4 = Rasterizer::new(10, 10);
    ras4.clear(0x000000);
    ras4.fill_rect(2, 2, 5, 5, 0xcccccc);
    assert_eq!(ras4.get_pixel(3, 3), 0xcccccc);
    println!("test_fill_rect: PASS");

    // Test 6: Out of bounds
    assert_eq!(ras.get_pixel(20, 20), 0);
    println!("test_bounds: PASS");

    println!("\n全部测试通过!");
}
