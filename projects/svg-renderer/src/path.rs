use crate::color::SVGColor;

#[derive(Debug, Clone)]
pub struct Path {
    pub commands: Vec<PathCommand>,
}

#[derive(Debug, Clone)]
pub enum PathCommand {
    MoveTo(f64, f64),
    LineTo(f64, f64),
    HorizontalLineTo(f64),
    VerticalLineTo(f64),
    CurveTo(f64, f64, f64, f64, f64, f64),
    ClosePath,
}

impl Path {
    pub fn new() -> Self {
        Path {
            commands: Vec::new(),
        }
    }

    pub fn to_svg(&self) -> String {
        let mut d = String::new();
        for cmd in &self.commands {
            match cmd {
                PathCommand::MoveTo(x, y) => d.push_str(&format!("M{x:.1},{y:.1} ")),
                PathCommand::LineTo(x, y) => d.push_str(&format!("L{x:.1},{y:.1} ")),
                PathCommand::HorizontalLineTo(x) => d.push_str(&format!("H{x:.1} ")),
                PathCommand::VerticalLineTo(y) => d.push_str(&format!("V{y:.1} ")),
                PathCommand::CurveTo(x1, y1, x2, y2, x, y) => {
                    d.push_str(&format!("C{x1:.1},{y1:.1} {x2:.1},{y2:.1} {x:.1},{y:.1} "));
                }
                PathCommand::ClosePath => d.push_str("Z "),
            }
        }
        d.trim().to_string()
    }
}
