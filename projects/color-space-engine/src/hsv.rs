#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HSV {
    pub h: f64,
    pub s: f64,
    pub v: f64,
}

impl HSV {
    pub fn new(h: f64, s: f64, v: f64) -> Self {
        HSV {
            h: h % 360.0,
            s: s.clamp(0.0, 1.0),
            v: v.clamp(0.0, 1.0),
        }
    }

    pub fn to_rgb(&self) -> super::rgb::RGB {
        let c = self.v * self.s;
        let x = c * (1.0 - (((self.h / 60.0) % 2.0) - 1.0).abs());
        let m = self.v - c;

        let (r1, g1, b1) = match self.h {
            h if h < 60.0 => (c, x, 0.0),
            h if h < 120.0 => (x, c, 0.0),
            h if h < 180.0 => (0.0, c, x),
            h if h < 240.0 => (0.0, x, c),
            h if h < 300.0 => (x, 0.0, c),
            _ => (c, 0.0, x),
        };

        super::rgb::RGB::new(r1 + m, g1 + m, b1 + m)
    }

    pub fn from_rgb(rgb: &super::rgb::RGB) -> Self {
        let max = rgb.r.max(rgb.g).max(rgb.b);
        let min = rgb.r.min(rgb.g).min(rgb.b);
        let v = max;

        if max == 0.0 {
            return HSV::new(0.0, 0.0, 0.0);
        }

        let s = if max == 0.0 { 0.0 } else { (max - min) / max };

        let h = match max {
            r if r == max => (rgb.g - rgb.b) / (max - min + 1e-10) + if rgb.g < rgb.b { 6.0 } else { 0.0 },
            g if g == max => (rgb.b - rgb.r) / (max - min + 1e-10) + 2.0,
            _ => (rgb.r - rgb.g) / (max - min + 1e-10) + 4.0,
        };

        HSV::new(h * 60.0, s, v)
    }

    pub fn to_string(&self) -> String {
        format!("HSV({:.1}, {:.1}%, {:.1}%)", self.h, self.s * 100.0, self.v * 100.0)
    }
}
