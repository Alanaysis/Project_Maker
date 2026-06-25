#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CMYK {
    pub c: f64,
    pub m: f64,
    pub y: f64,
    pub k: f64,
}

impl CMYK {
    pub fn new(c: f64, m: f64, y: f64, k: f64) -> Self {
        CMYK {
            c: c.clamp(0.0, 1.0),
            m: m.clamp(0.0, 1.0),
            y: y.clamp(0.0, 1.0),
            k: k.clamp(0.0, 1.0),
        }
    }

    pub fn to_rgb(&self) -> super::rgb::RGB {
        let r = (1.0 - self.c) * (1.0 - self.k);
        let g = (1.0 - self.m) * (1.0 - self.k);
        let b = (1.0 - self.y) * (1.0 - self.k);
        super::rgb::RGB::new(r, g, b)
    }

    pub fn from_rgb(rgb: &super::rgb::RGB) -> Self {
        let k = 1.0 - rgb.r.max(rgb.g).max(rgb.b);
        if k >= 1.0 {
            return CMYK::new(0.0, 0.0, 0.0, 1.0);
        }
        let c = (1.0 - rgb.r - k) / (1.0 - k);
        let m = (1.0 - rgb.g - k) / (1.0 - k);
        let y = (1.0 - rgb.b - k) / (1.0 - k);
        CMYK::new(c, m, y, k)
    }

    pub fn to_string(&self) -> String {
        format!("CMYK(C:{:.1}%, M:{:.1}%, Y:{:.1}%, K:{:.1}%)",
            self.c * 100.0, self.m * 100.0, self.y * 100.0, self.k * 100.0)
    }
}
