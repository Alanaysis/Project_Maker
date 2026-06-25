use crate::color::SVGColor;
use crate::shapes::Shape;

pub struct Renderer {
    pub width: f64,
    pub height: f64,
    pub shapes: Vec<Box<dyn Shape>>,
    pub background: Option<SVGColor>,
}

impl Renderer {
    pub fn new(width: f64, height: f64) -> Self {
        Renderer {
            width, height,
            shapes: Vec::new(),
            background: None,
        }
    }

    pub fn add_shape(&mut self, shape: Box<dyn Shape>) {
        self.shapes.push(shape);
    }

    pub fn clear(&mut self) {
        self.shapes.clear();
    }

    pub fn render(&self) -> String {
        let mut svg = String::new();
        svg.push_str(&format!("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{:.0}\" height=\"{:.0}\" viewBox=\"0 0 {:.0} {:.0}\">\n", self.width, self.height, self.width, self.height));

        if let Some(bg) = self.background {
            let (r, g, b) = bg.to_rgb();
            svg.push_str(&format!("  <rect width=\"{:.0}\" height=\"{:.0}\" fill=\"#{:02x}{:02x}{:02x}\"/>\n", self.width, self.height, r, g, b));
        }

        for shape in &self.shapes {
            svg.push_str(&format!("  {}\n", shape.render_svg()));
        }

        svg.push_str("</svg>");
        svg
    }

    pub fn save(&self, path: &str) -> std::io::Result<()> {
        std::fs::write(path, self.render())
    }
}
