use color_space::{RGB, HSL, HSV, Lab, CMYK, Converter};

fn main() {
    println!("=== 颜色空间引擎演示 ===\n");

    // Test RGB -> HSL
    let rgb = RGB::from_u8(255, 128, 0);
    println!("原始 RGB: {}", rgb.to_string());

    let hsl = Converter::rgb_to_hsl(&rgb);
    println!("  -> HSL: {}", hsl.to_string());

    let hsv = Converter::rgb_to_hsv(&rgb);
    println!("  -> HSV: {}", hsv.to_string());

    let lab = Converter::rgb_to_lab(&rgb);
    println!("  -> Lab: {}", lab.to_string());

    let cmyk = Converter::rgb_to_cmyk(&rgb);
    println!("  -> CMYK: {}", cmyk.to_string());

    // Test roundtrip
    println!("\n=== 往返转换 ===");
    let rgb2 = Converter::hsl_to_rgb(&hsl);
    let (r, g, b) = rgb2.to_u8();
    println!("HSL -> RGB: RGB({}, {}, {})", r, g, b);

    let rgb3 = Converter::hsv_to_rgb(&hsv);
    let (r, g, b) = rgb3.to_u8();
    println!("HSV -> RGB: RGB({}, {}, {})", r, g, b);

    let rgb4 = Converter::lab_to_rgb(&lab);
    let (r, g, b) = rgb4.to_u8();
    println!("Lab -> RGB: RGB({}, {}, {})", r, g, b);

    let rgb5 = Converter::cmyk_to_rgb(&cmyk);
    let (r, g, b) = rgb5.to_u8();
    println!("CMYK -> RGB: RGB({}, {}, {})", r, g, b);

    // Color distance
    println!("\n=== 颜色距离 (Delta E) ===");
    let red = Converter::rgb_to_lab(&RGB::from_u8(255, 0, 0));
    let green = Converter::rgb_to_lab(&RGB::from_u8(0, 255, 0));
    let blue = Converter::rgb_to_lab(&RGB::from_u8(0, 0, 255));
    let white = Converter::rgb_to_lab(&RGB::from_u8(255, 255, 255));

    println!("红 vs 绿: Delta E = {:.2}", Converter::lab_delta_e(&red, &green));
    println!("红 vs 蓝: Delta E = {:.2}", Converter::lab_delta_e(&red, &blue));
    println!("红 vs 白: Delta E = {:.2}", Converter::lab_delta_e(&red, &white));
    println!("绿 vs 蓝: Delta E = {:.2}", Converter::lab_delta_e(&green, &blue));

    // Color wheel
    println!("\n=== 色相环 (HSV) ===");
    for h in (0..360).step_by(30) {
        let hsv = HSV::new(h as f64, 1.0, 1.0);
        let rgb = Converter::hsv_to_rgb(&hsv);
        let (r, g, b) = rgb.to_u8();
        let brightness = (r as u32 + g as u32 + b as u32) / 3;
        let ch = if brightness < 85 { '#' } else if brightness < 170 { '*' } else { '.' };
        println!(" H={:3}°  {} RGB({}, {}, {})", h, ch, r, g, b);
    }

    println!("\n所有演示完成!");
}
