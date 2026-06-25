use crate::color::SVGColor;
use crate::path::Path;

pub trait Shape {
    fn render_svg(&self) -> String;
    fn fill_color(&self) -> Option<SVGColor>;
    fn stroke_color(&self) -> Option<SVGColor>;
    fn stroke_width(&self) -> f64;
}

#[derive(Debug, Clone)]
pub struct Rect {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
    pub rx: f64,
    pub ry: f64,
    pub fill: Option<SVGColor>,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Rect {
    pub fn new(x: f64, y: f64, w: f64, h: f64) -> Self {
        Rect {
            x, y, width: w, height: h,
            rx: 0.0, ry: 0.0,
            fill: None, stroke: None, stroke_width: 1.0,
        }
    }

    pub fn with_fill(mut self, color: SVGColor) -> Self {
        self.fill = Some(color);
        self
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Rect {
    fn render_svg(&self) -> String {
        let mut s = format!("<rect x=\"{:.1}\" y=\"{:.1}\" width=\"{:.1}\" height=\"{:.1}\"", self.x, self.y, self.width, self.height);
        if self.rx > 0.0 || self.ry > 0.0 {
            s.push_str(&format!(" rx=\"{:.1}\" ry=\"{:.1}\"", self.rx, self.ry));
        }
        if let Some(fill) = self.fill {
            let (r, g, b) = fill.to_rgb();
            s.push_str(&format!(" fill=\"#{:02x}{:02x}{:02x}\"", r, g, b));
        }
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { self.fill }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Circle {
    pub cx: f64,
    pub cy: f64,
    pub r: f64,
    pub fill: Option<SVGColor>,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Circle {
    pub fn new(cx: f64, cy: f64, r: f64) -> Self {
        Circle { cx, cy, r, fill: None, stroke: None, stroke_width: 1.0 }
    }

    pub fn with_fill(mut self, color: SVGColor) -> Self {
        self.fill = Some(color);
        self
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Circle {
    fn render_svg(&self) -> String {
        let mut s = format!("<circle cx=\"{:.1}\" cy=\"{:.1}\" r=\"{:.1}\"", self.cx, self.cy, self.r);
        if let Some(fill) = self.fill {
            let (r, g, b) = fill.to_rgb();
            s.push_str(&format!(" fill=\"#{:02x}{:02x}{:02x}\"", r, g, b));
        }
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { self.fill }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Ellipse {
    pub cx: f64,
    pub cy: f64,
    pub rx: f64,
    pub ry: f64,
    pub fill: Option<SVGColor>,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Ellipse {
    pub fn new(cx: f64, cy: f64, rx: f64, ry: f64) -> Self {
        Ellipse { cx, cy, rx, ry, fill: None, stroke: None, stroke_width: 1.0 }
    }

    pub fn with_fill(mut self, color: SVGColor) -> Self {
        self.fill = Some(color);
        self
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Ellipse {
    fn render_svg(&self) -> String {
        let mut s = format!("<ellipse cx=\"{:.1}\" cy=\"{:.1}\" rx=\"{:.1}\" ry=\"{:.1}\"", self.cx, self.cy, self.rx, self.ry);
        if let Some(fill) = self.fill {
            let (r, g, b) = fill.to_rgb();
            s.push_str(&format!(" fill=\"#{:02x}{:02x}{:02x}\"", r, g, b));
        }
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { self.fill }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Line {
    pub x1: f64,
    pub y1: f64,
    pub x2: f64,
    pub y2: f64,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Line {
    pub fn new(x1: f64, y1: f64, x2: f64, y2: f64) -> Self {
        Line { x1, y1, x2, y2, stroke: None, stroke_width: 1.0 }
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Line {
    fn render_svg(&self) -> String {
        let mut s = format!("<line x1=\"{:.1}\" y1=\"{:.1}\" x2=\"{:.1}\" y2=\"{:.1}\"", self.x1, self.y1, self.x2, self.y2);
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { None }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Polygon {
    pub points: Vec<(f64, f64)>,
    pub fill: Option<SVGColor>,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Polygon {
    pub fn new(points: Vec<(f64, f64)>) -> Self {
        Polygon { points, fill: None, stroke: None, stroke_width: 1.0 }
    }

    pub fn to_svg_points(&self) -> String {
        self.points.iter()
            .map(|(x, y)| format!("{:.1},{:.1}", x, y))
            .collect::<Vec<_>>()
            .join(" ")
    }

    pub fn with_fill(mut self, color: SVGColor) -> Self {
        self.fill = Some(color);
        self
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Polygon {
    fn render_svg(&self) -> String {
        let mut s = format!("<polygon points=\"{}\"", self.to_svg_points());
        if let Some(fill) = self.fill {
            let (r, g, b) = fill.to_rgb();
            s.push_str(&format!(" fill=\"#{:02x}{:02x}{:02x}\"", r, g, b));
        }
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { self.fill }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Polyline {
    pub points: Vec<(f64, f64)>,
    pub stroke: Option<SVGColor>,
    pub stroke_width: f64,
}

impl Polyline {
    pub fn new(points: Vec<(f64, f64)>) -> Self {
        Polyline { points, stroke: None, stroke_width: 1.0 }
    }

    pub fn with_stroke(mut self, color: SVGColor) -> Self {
        self.stroke = Some(color);
        self
    }
}

impl Shape for Polyline {
    fn render_svg(&self) -> String {
        let mut s = format!("<polyline points=\"{}\"", self.points.iter()
            .map(|(x, y)| format!("{:.1},{:.1}", x, y))
            .collect::<Vec<_>>()
            .join(" "));
        if let Some(stroke) = self.stroke {
            let (r, g, b) = stroke.to_rgb();
            s.push_str(&format!(" stroke=\"#{:02x}{:02x}{:02x}\"", r, g, b));
            s.push_str(&format!(" stroke-width=\"{:.1}\"", self.stroke_width));
        }
        s.push_str(" />");
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { None }
    fn stroke_color(&self) -> Option<SVGColor> { self.stroke }
    fn stroke_width(&self) -> f64 { self.stroke_width }
}

#[derive(Debug, Clone)]
pub struct Text {
    pub x: f64,
    pub y: f64,
    pub content: String,
    pub fill: Option<SVGColor>,
    pub font_size: f64,
}

impl Text {
    pub fn new(x: f64, y: f64, content: &str) -> Self {
        Text { x, y, content: content.to_string(), fill: None, font_size: 16.0 }
    }

    pub fn with_fill(mut self, color: SVGColor) -> Self {
        self.fill = Some(color);
        self
    }
}

impl Shape for Text {
    fn render_svg(&self) -> String {
        let mut s = format!("<text x=\"{:.1}\" y=\"{:.1}\" font-size=\"{:.1}\"", self.x, self.y, self.font_size);
        if let Some(fill) = self.fill {
            let (r, g, b) = fill.to_rgb();
            s.push_str(&format!(" fill=\"#{:02x}{:02x}{:02x}\"", r, g, b));
        }
        s.push_str(&format!(">{}</text>", self.content));
        s
    }

    fn fill_color(&self) -> Option<SVGColor> { self.fill }
    fn stroke_color(&self) -> Option<SVGColor> { None }
    fn stroke_width(&self) -> f64 { 0.0 }
}
