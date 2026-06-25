use color_space::{RGB, HSL, HSV, Lab, Converter};

fn main() {
    // Test 1: RGB -> HSL roundtrip
    let rgb = RGB::from_u8(128, 200, 64);
    let hsl = Converter::rgb_to_hsl(&rgb);
    let rgb_back = Converter::hsl_to_rgb(&hsl);
    let (r1, g1, b1) = rgb.to_u8();
    let (r2, g2, b2) = rgb_back.to_u8();
    assert_eq!((r1, g1, b1), (r2, g2, b2));
    println!("test_rgb_hsl_roundtrip: PASS");

    // Test 2: RGB -> HSV roundtrip
    let hsv = Converter::rgb_to_hsv(&rgb);
    let rgb_back = Converter::hsv_to_rgb(&hsv);
    let (r2, g2, b2) = rgb_back.to_u8();
    assert_eq!((r1, g1, b1), (r2, g2, b2));
    println!("test_rgb_hsv_roundtrip: PASS");

    // Test 3: RGB -> Lab -> RGB roundtrip
    let lab = Converter::rgb_to_lab(&rgb);
    let rgb_back = Converter::lab_to_rgb(&lab);
    let (r2, g2, b2) = rgb_back.to_u8();
    // Lab roundtrip has some precision loss
    assert!((r1 as i32 - r2 as i32).abs() <= 2);
    assert!((g1 as i32 - g2 as i32).abs() <= 2);
    assert!((b1 as i32 - b2 as i32).abs() <= 2);
    println!("test_rgb_lab_roundtrip: PASS");

    // Test 4: HSL hue range
    let hsl = HSL::new(400.0, 0.5, 0.5);
    assert!(hsl.h >= 0.0 && hsl.h < 360.0);
    println!("test_hsl_hue_range: PASS");

    // Test 5: HSV saturation clamping
    let hsv = HSV::new(180.0, 1.5, -0.5);
    assert_eq!(hsv.s, 1.0);
    assert_eq!(hsv.v, 0.0);
    println!("test_hsv_clamp: PASS");

    // Test 6: Luminance
    let white = RGB::from_u8(255, 255, 255);
    let black = RGB::from_u8(0, 0, 0);
    let gray = RGB::from_u8(128, 128, 128);
    assert!(white.luminance() > gray.luminance());
    assert!(gray.luminance() > black.luminance());
    println!("test_luminance: PASS");

    // Test 7: Color distance
    let red = RGB::from_u8(255, 0, 0);
    let green = RGB::from_u8(0, 255, 0);
    let same_red = RGB::from_u8(255, 0, 0);
    assert!(red.distance(&green) > red.distance(&same_red));
    println!("test_distance: PASS");

    // Test 8: Delta E
    let lab_red = Converter::rgb_to_lab(&RGB::from_u8(255, 0, 0));
    let lab_green = Converter::rgb_to_lab(&RGB::from_u8(0, 255, 0));
    let lab_blue = Converter::rgb_to_lab(&RGB::from_u8(0, 0, 255));
    let de_rg = Converter::lab_delta_e(&lab_red, &lab_green);
    let de_rb = Converter::lab_delta_e(&lab_red, &lab_blue);
    assert!(de_rg > 0.0 && de_rb > 0.0);
    println!("test_delta_e: PASS");

    println!("\n全部测试通过!");
}
