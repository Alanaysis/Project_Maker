#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HSL {
    pub h: f64,
    pub s: f64,
    pub l: f64,
}

impl HSL {
    pub fn new(h: f64, s: f64, l: f64) -> Self {
        HSL {
            h: h % 360.0,
            s: s.clamp(0.0, 1.0),
            l: l.clamp(0.0, 1.0),
        }
    }

    pub fn to_rgb(&self) -> super::rgb::RGB {
        let c = (1.0 - (2.0 * self.l - 1.0).abs()) * self.s;
        let x = c * (1.0 - (((self.h / 60.0) % 2.0) - 1.0).abs());
        let m = self.l - c / 2.0;

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
        let l = (max + min) / 2.0;

        if max == min {
            return HSL::new(0.0, 0.0, l);
        }

        let d = max - min;
        let s = if l > 0.5 { d / (2.0 - max - min) } else { d / (max + min) };

        let h = match max {
            r if r == max => (rgb.g - rgb.b) / d + if rgb.g < rgb.b { 6.0 } else { 0.0 },
            g if g == max => (rgb.b - rgb.r) / d + 2.0,
            _ => (rgb.r - rgb.g) / d + 4.0,
        };

        HSL::new(h * 60.0, s, l / 2.0)
    }

    pub fn to_string(&self) -> String {
        format!("HSL({:.1}, {:.1}%, {:.1}%)", self.h, self.s * 100.0, self.l * 100.0)
    }
}
