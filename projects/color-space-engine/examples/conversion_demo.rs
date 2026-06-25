use color_space::{RGB, HSL, HSV, Converter};

fn main() {
    println!("=== 颜色空间转换示例 ===\n");

    let colors = vec![
        ("红色", (255u8, 0u8, 0u8)),
        ("绿色", (0u8, 255u8, 0u8)),
        ("蓝色", (0u8, 0u8, 255u8)),
        ("青色", (0u8, 255u8, 255u8)),
        ("品红", (255u8, 0u8, 255u8)),
        ("黄色", (255u8, 255u8, 0u8)),
        ("白色", (255u8, 255u8, 255u8)),
        ("黑色", (0u8, 0u8, 0u8)),
        ("灰色", (128u8, 128u8, 128u8)),
    ];

    println!("{:<10} {:<20} {:<20} {:<20}", "名称", "RGB", "HSL", "HSV");
    println!("{:-<75}", "");

    for (name, (r, g, b)) in &colors {
        let rgb = RGB::from_u8(*r, *g, *b);
        let hsl = Converter::rgb_to_hsl(&rgb);
        let hsv = Converter::rgb_to_hsv(&rgb);
        println!("{:<10} {:<20} {:<20} {:<20}", name, rgb.to_string(), hsl.to_string(), hsv.to_string());
    }

    println!("\n=== 色相环 ===");
    for h in (0..360).step_by(45) {
        let hsv = HSV::new(h as f64, 1.0, 1.0);
        let rgb = Converter::hsv_to_rgb(&hsv);
        let (r, g, b) = rgb.to_u8();
        println!("H={:3}° -> RGB({}, {}, {})", h, r, g, b);
    }
}
