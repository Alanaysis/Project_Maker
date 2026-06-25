#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RGB {
    pub r: f64,
    pub g: f64,
    pub b: f64,
}

impl RGB {
    pub fn new(r: f64, g: f64, b: f64) -> Self {
        RGB { r, g, b }
    }

    pub fn from_u8(r: u8, g: u8, b: u8) -> Self {
        RGB {
            r: r as f64 / 255.0,
            g: g as f64 / 255.0,
            b: b as f64 / 255.0,
        }
    }

    pub fn to_u8(&self) -> (u8, u8, u8) {
        (
            (self.r * 255.0).clamp(0.0, 255.0) as u8,
            (self.g * 255.0).clamp(0.0, 255.0) as u8,
            (self.b * 255.0).clamp(0.0, 255.0) as u8,
        )
    }

    pub fn luminance(&self) -> f64 {
        0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b
    }

    pub fn distance(&self, other: &RGB) -> f64 {
        ((self.r - other.r).powi(2)
            + (self.g - other.g).powi(2)
            + (self.b - other.b).powi(2)).sqrt()
    }

    pub fn to_string(&self) -> String {
        format!("RGB({:.3}, {:.3}, {:.3})", self.r, self.g, self.b)
    }
}
