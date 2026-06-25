use color_space::{RGB, Lab, Converter};

fn main() {
    println!("=== 颜色距离演示 ===\n");

    let colors = vec![
        ("红", RGB::from_u8(255, 0, 0)),
        ("橙", RGB::from_u8(255, 165, 0)),
        ("黄", RGB::from_u8(255, 255, 0)),
        ("绿", RGB::from_u8(0, 255, 0)),
        ("青", RGB::from_u8(0, 255, 255)),
        ("蓝", RGB::from_u8(0, 0, 255)),
        ("紫", RGB::from_u8(128, 0, 128)),
        ("品红", RGB::from_u8(255, 0, 255)),
    ];

    let white = RGB::from_u8(255, 255, 255);
    let lab_white = Converter::rgb_to_lab(&white);

    println!("相对于白色的 Delta E:\n");
    for (name, rgb) in &colors {
        let lab = Converter::rgb_to_lab(rgb);
        let de = Converter::lab_delta_e(&lab, &lab_white);
        let (r, g, b) = rgb.to_u8();
        let brightness = (r as u32 + g as u32 + b as u32) / 3;
        let ch = if brightness < 85 { '#' } else if brightness < 170 { '*' } else { '.' };
        println!("  {} {}  Delta E = {:.2}", ch, name, de);
    }

    println!("\n颜色之间两两距离:\n");
    for i in 0..colors.len() {
        for j in (i + 1)..colors.len() {
            let lab1 = Converter::rgb_to_lab(&colors[i].1);
            let lab2 = Converter::rgb_to_lab(&colors[j].1);
            let de = Converter::lab_delta_e(&lab1, &lab2);
            println!("  {} vs {}: Delta E = {:.2}", colors[i].0, colors[j].0, de);
        }
    }
}
