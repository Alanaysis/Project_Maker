#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Lab {
    pub l: f64,
    pub a: f64,
    pub b: f64,
}

impl Lab {
    pub fn new(l: f64, a: f64, b: f64) -> Self {
        Lab { l, a, b }
    }

    pub fn to_rgb(&self) -> super::rgb::RGB {
        let fy = (self.l + 16.0) / 116.0;
        let fx = self.a / 500.0 + fy;
        let fz = fy - self.b / 200.0;

        let x_ref = 95.047;
        let y_ref = 100.0;
        let z_ref = 108.883;

        let x = if fx.powi(3) > 0.008856 { fx.powi(3) } else { (fx - 16.0 / 116.0) / 7.787 };
        let y = if fy.powi(3) > 0.008856 { fy.powi(3) } else { (fy - 16.0 / 116.0) / 7.787 };
        let z = if fz.powi(3) > 0.008856 { fz.powi(3) } else { (fz - 16.0 / 116.0) / 7.787 };

        let r_lin = 3.2406 * x - 1.5372 * y - 0.4986 * z;
        let g_lin = -0.9689 * x + 1.8758 * y + 0.0415 * z;
        let b_lin = 0.0557 * x - 0.2040 * y + 1.0570 * z;

        let gamma = |v: f64| -> f64 {
            if v > 0.0031308 { 1.055 * v.powf(1.0 / 2.4) - 0.055 }
            else { 12.92 * v }
        };

        super::rgb::RGB::new(
            gamma(r_lin / x_ref) * 100.0,
            gamma(g_lin / y_ref) * 100.0,
            gamma(b_lin / z_ref) * 100.0,
        )
    }

    pub fn from_rgb(rgb: &super::rgb::RGB) -> Self {
        let gamma_inv = |v: f64| -> f64 {
            let v = v / 100.0;
            if v > 0.04045 { (v / 1.055).powf(2.4) }
            else { v / 12.92 }
        };

        let r_lin = gamma_inv(rgb.r);
        let g_lin = gamma_inv(rgb.g);
        let b_lin = gamma_inv(rgb.b);

        let x = 0.4124 * r_lin + 0.3576 * g_lin + 0.1805 * b_lin;
        let y = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin;
        let z = 0.0193 * r_lin + 0.1192 * g_lin + 0.9505 * b_lin;

        let x_ref = 95.047;
        let y_ref = 100.0;
        let z_ref = 108.883;

        let fx = if x > 0.008856 * x_ref { x.powf(1.0 / 3.0) } else { 7.787 * x / x_ref + 16.0 / 116.0 };
        let fy = if y > 0.008856 * y_ref { y.powf(1.0 / 3.0) } else { 7.787 * y / y_ref + 16.0 / 116.0 };
        let fz = if z > 0.008856 * z_ref { z.powf(1.0 / 3.0) } else { 7.787 * z / z_ref + 16.0 / 116.0 };

        Lab::new(116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))
    }

    pub fn delta_e(other: &Self, other2: &Self) -> f64 {
        ((other.l - other2.l).powi(2) + (other.a - other2.a).powi(2) + (other.b - other2.b).powi(2)).sqrt()
    }

    pub fn to_string(&self) -> String {
        format!("Lab(L:{:.1}, a:{:.1}, b:{:.1})", self.l, self.a, self.b)
    }
}
