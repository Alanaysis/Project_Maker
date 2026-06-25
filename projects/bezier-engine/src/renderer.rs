//! SVG 渲染器
//!
//! 将贝塞尔曲线渲染为 SVG 格式输出。

use crate::point::Point;
use crate::bezier::{QuadraticBezier, CubicBezier, BezierCurveType};
use crate::subdivision::{adaptive_subdivide_quadratic, adaptive_subdivide_cubic, SubdivisionConfig};

/// SVG 颜色
#[derive(Debug, Clone)]
pub struct SvgColor {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: f64,
}

impl SvgColor {
    pub fn new(r: u8, g: u8, b: u8, a: f64) -> Self {
        Self { r, g, b, a }
    }

    pub fn rgb(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b, a: 1.0 }
    }

    pub fn to_string(&self) -> String {
        if (self.a - 1.0).abs() < 0.01 {
            format!("rgb({},{},{})", self.r, self.g, self.b)
        } else {
            format!("rgba({},{},{},{})", self.r, self.g, self.b, self.a)
        }
    }
}

/// SVG 样式
#[derive(Debug, Clone)]
pub struct SvgStyle {
    pub stroke_color: SvgColor,
    pub stroke_width: f64,
    pub fill_color: Option<SvgColor>,
    pub control_point_color: SvgColor,
    pub control_point_radius: f64,
    pub control_line_color: SvgColor,
    pub show_control_points: bool,
    pub show_control_lines: bool,
}

impl SvgStyle {
    pub fn default_style() -> Self {
        Self {
            stroke_color: SvgColor::rgb(0, 0, 0),
            stroke_width: 2.0,
            fill_color: None,
            control_point_color: SvgColor::rgb(255, 0, 0),
            control_point_radius: 4.0,
            control_line_color: SvgColor::new(128, 128, 128, 0.5),
            show_control_points: true,
            show_control_lines: true,
        }
    }
}

impl Default for SvgStyle {
    fn default() -> Self {
        Self::default_style()
    }
}

/// SVG 渲染器
#[derive(Debug)]
pub struct SvgRenderer {
    width: f64,
    height: f64,
    style: SvgStyle,
    background_color: Option<SvgColor>,
}

impl SvgRenderer {
    /// 创建新的 SVG 渲染器
    pub fn new(width: f64, height: f64) -> Self {
        Self {
            width,
            height,
            style: SvgStyle::default(),
            background_color: Some(SvgColor::rgb(255, 255, 255)),
        }
    }

    /// 设置样式
    pub fn with_style(mut self, style: SvgStyle) -> Self {
        self.style = style;
        self
    }

    /// 设置背景颜色
    pub fn with_background(mut self, color: SvgColor) -> Self {
        self.background_color = Some(color);
        self
    }

    /// 无背景
    pub fn without_background(mut self) -> Self {
        self.background_color = None;
        self
    }

    /// 渲染单条二次贝塞尔曲线为 SVG
    pub fn render_quadratic(&self, curve: &QuadraticBezier) -> String {
        let mut svg = String::new();
        svg.push_str(&self.svg_header());

        // 绘制曲线
        svg.push_str(&self.quadratic_path(curve));

        // 绘制控制点和连线
        if self.style.show_control_lines {
            svg.push_str(&self.control_lines(&[curve.p0, curve.p1, curve.p2]));
        }
        if self.style.show_control_points {
            svg.push_str(&self.control_points(&[curve.p0, curve.p1, curve.p2]));
        }

        svg.push_str(&self.svg_footer());
        svg
    }

    /// 渲染单条三次贝塞尔曲线为 SVG
    pub fn render_cubic(&self, curve: &CubicBezier) -> String {
        let mut svg = String::new();
        svg.push_str(&self.svg_header());

        // 绘制曲线
        svg.push_str(&self.cubic_path(curve));

        // 绘制控制点和连线
        if self.style.show_control_lines {
            svg.push_str(&self.control_lines(&[curve.p0, curve.p1, curve.p2, curve.p3]));
        }
        if self.style.show_control_points {
            svg.push_str(&self.control_points(&[curve.p0, curve.p1, curve.p2, curve.p3]));
        }

        svg.push_str(&self.svg_footer());
        svg
    }

    /// 渲染多条曲线
    pub fn render_curves(&self, curves: &[BezierCurveType]) -> String {
        let mut svg = String::new();
        svg.push_str(&self.svg_header());

        for curve in curves {
            match curve {
                BezierCurveType::Quadratic(quad) => {
                    svg.push_str(&self.quadratic_path(quad));
                    if self.style.show_control_lines {
                        svg.push_str(&self.control_lines(&[quad.p0, quad.p1, quad.p2]));
                    }
                    if self.style.show_control_points {
                        svg.push_str(&self.control_points(&[quad.p0, quad.p1, quad.p2]));
                    }
                }
                BezierCurveType::Cubic(cubic) => {
                    svg.push_str(&self.cubic_path(cubic));
                    if self.style.show_control_lines {
                        svg.push_str(&self.control_lines(&[cubic.p0, cubic.p1, cubic.p2, cubic.p3]));
                    }
                    if self.style.show_control_points {
                        svg.push_str(&self.control_points(&[cubic.p0, cubic.p1, cubic.p2, cubic.p3]));
                    }
                }
            }
        }

        svg.push_str(&self.svg_footer());
        svg
    }

    /// 渲染折线（细分后的点序列）
    pub fn render_polyline(&self, points: &[Point]) -> String {
        let mut svg = String::new();
        svg.push_str(&self.svg_header());

        if points.len() >= 2 {
            svg.push_str(&format!(
                r#"<polyline points="{}" fill="none" stroke="{}" stroke-width="{}"/>"#,
                points.iter()
                    .map(|p| format!("{},{}", p.x, p.y))
                    .collect::<Vec<_>>()
                    .join(" "),
                self.style.stroke_color.to_string(),
                self.style.stroke_width
            ));
        }

        svg.push_str(&self.svg_footer());
        svg
    }

    fn svg_header(&self) -> String {
        let mut header = format!(
            r#"<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}">"#,
            self.width, self.height, self.width, self.height
        );

        if let Some(ref bg) = self.background_color {
            header.push_str(&format!(
                r#"<rect width="100%" height="100%" fill="{}"/>"#,
                bg.to_string()
            ));
        }

        header
    }

    fn svg_footer(&self) -> String {
        "</svg>".to_string()
    }

    fn quadratic_path(&self, curve: &QuadraticBezier) -> String {
        format!(
            r#"<path d="M {} {} Q {} {} {} {}" fill="none" stroke="{}" stroke-width="{}"/>"#,
            curve.p0.x, curve.p0.y,
            curve.p1.x, curve.p1.y,
            curve.p2.x, curve.p2.y,
            self.style.stroke_color.to_string(),
            self.style.stroke_width
        )
    }

    fn cubic_path(&self, curve: &CubicBezier) -> String {
        format!(
            r#"<path d="M {} {} C {} {} {} {} {} {}" fill="none" stroke="{}" stroke-width="{}"/>"#,
            curve.p0.x, curve.p0.y,
            curve.p1.x, curve.p1.y,
            curve.p2.x, curve.p2.y,
            curve.p3.x, curve.p3.y,
            self.style.stroke_color.to_string(),
            self.style.stroke_width
        )
    }

    fn control_lines(&self, points: &[Point]) -> String {
        if points.len() < 2 {
            return String::new();
        }

        let mut lines = String::new();
        for i in 0..points.len() - 1 {
            lines.push_str(&format!(
                r#"<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}" stroke-dasharray="5,5"/>"#,
                points[i].x, points[i].y,
                points[i + 1].x, points[i + 1].y,
                self.style.control_line_color.to_string(),
                1.0
            ));
        }
        lines
    }

    fn control_points(&self, points: &[Point]) -> String {
        let mut circles = String::new();
        for (i, point) in points.iter().enumerate() {
            let color = if i == 0 || i == points.len() - 1 {
                // 端点用不同颜色
                SvgColor::rgb(0, 128, 255).to_string()
            } else {
                self.style.control_point_color.to_string()
            };

            circles.push_str(&format!(
                r#"<circle cx="{}" cy="{}" r="{}" fill="{}"/>"#,
                point.x, point.y,
                self.style.control_point_radius,
                color
            ));
        }
        circles
    }
}

/// 生成曲线的折线近似（用于非 SVG 渲染器）
pub fn curve_to_polyline(curve: &BezierCurveType, config: &SubdivisionConfig) -> Vec<Point> {
    match curve {
        BezierCurveType::Quadratic(quad) => {
            adaptive_subdivide_quadratic(quad, config)
        }
        BezierCurveType::Cubic(cubic) => {
            adaptive_subdivide_cubic(cubic, config)
        }
    }
}

/// 将点序列格式化为简单的文本格式（用于调试）
pub fn points_to_text(points: &[Point]) -> String {
    points.iter()
        .map(|p| format!("({:.2}, {:.2})", p.x, p.y))
        .collect::<Vec<_>>()
        .join(" -> ")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_svg_renderer_quadratic() {
        let renderer = SvgRenderer::new(200.0, 200.0);
        let curve = QuadraticBezier::new(
            Point::new(10.0, 10.0),
            Point::new(100.0, 150.0),
            Point::new(190.0, 10.0),
        );

        let svg = renderer.render_quadratic(&curve);

        assert!(svg.contains("<svg"));
        assert!(svg.contains("</svg>"));
        assert!(svg.contains("Q"));
        assert!(svg.contains("M 10 10"));
    }

    #[test]
    fn test_svg_renderer_cubic() {
        let renderer = SvgRenderer::new(300.0, 200.0);
        let curve = CubicBezier::new(
            Point::new(10.0, 100.0),
            Point::new(80.0, 10.0),
            Point::new(220.0, 190.0),
            Point::new(290.0, 100.0),
        );

        let svg = renderer.render_cubic(&curve);

        assert!(svg.contains("<svg"));
        assert!(svg.contains("C"));
        assert!(svg.contains("M 10 100"));
    }

    #[test]
    fn test_svg_renderer_no_control_points() {
        let style = SvgStyle {
            show_control_points: false,
            show_control_lines: false,
            ..SvgStyle::default()
        };

        let renderer = SvgRenderer::new(200.0, 200.0).with_style(style);
        let curve = QuadraticBezier::new(
            Point::new(10.0, 10.0),
            Point::new(100.0, 150.0),
            Point::new(190.0, 10.0),
        );

        let svg = renderer.render_quadratic(&curve);

        assert!(!svg.contains("<circle"));
        assert!(!svg.contains("<line"));
    }

    #[test]
    fn test_svg_renderer_custom_style() {
        let style = SvgStyle {
            stroke_color: SvgColor::rgb(255, 0, 0),
            stroke_width: 3.0,
            control_point_radius: 6.0,
            ..SvgStyle::default()
        };

        let renderer = SvgRenderer::new(200.0, 200.0).with_style(style);
        let curve = QuadraticBezier::new(
            Point::new(10.0, 10.0),
            Point::new(100.0, 150.0),
            Point::new(190.0, 10.0),
        );

        let svg = renderer.render_quadratic(&curve);

        assert!(svg.contains("rgb(255,0,0)"));
        assert!(svg.contains("stroke-width=\"3\""));
        assert!(svg.contains("r=\"6\""));
    }

    #[test]
    fn test_curve_to_polyline() {
        let curve = BezierCurveType::Quadratic(QuadraticBezier::new(
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        ));

        let config = SubdivisionConfig::new().with_max_depth(3);
        let points = curve_to_polyline(&curve, &config);

        assert!(points.len() >= 2);
        assert!((points.first().unwrap().x - 0.0).abs() < 1e-10);
        assert!((points.last().unwrap().x - 100.0).abs() < 1e-10);
    }

    #[test]
    fn test_points_to_text() {
        let points = vec![
            Point::new(0.0, 0.0),
            Point::new(50.0, 100.0),
            Point::new(100.0, 0.0),
        ];

        let text = points_to_text(&points);
        assert_eq!(text, "(0.00, 0.00) -> (50.00, 100.00) -> (100.00, 0.00)");
    }
}
