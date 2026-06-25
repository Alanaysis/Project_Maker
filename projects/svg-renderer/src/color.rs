#[derive(Debug, Clone, Copy, PartialEq)]
pub enum SVGColor {
    Named(&'static str),
    RGB(u8, u8, u8),
    RGBA(u8, u8, u8, f64),
    Hex(u32),
}

impl SVGColor {
    pub fn to_rgb(&self) -> (u8, u8, u8) {
        match self {
            SVGColor::Named(name) => match *name {
                "black" => (0, 0, 0),
                "white" => (255, 255, 255),
                "red" => (255, 0, 0),
                "green" => (0, 128, 0),
                "blue" => (0, 0, 255),
                "yellow" => (255, 255, 0),
                "cyan" => (0, 255, 255),
                "magenta" => (255, 0, 255),
                _ => (0, 0, 0),
            },
            SVGColor::RGB(r, g, b) => (*r, *g, *b),
            SVGColor::RGBA(r, g, b, _) => (*r, *g, *b),
            SVGColor::Hex(val) => {
                let r = ((val >> 16) & 0xff) as u8;
                let g = ((val >> 8) & 0xff) as u8;
                let b = (val & 0xff) as u8;
                (r, g, b)
            }
        }
    }

    pub fn brightness(&self) -> u8 {
        let (r, g, b) = self.to_rgb();
        ((r as u32 + g as u32 + b as u32) / 3u32) as u8
    }
}
