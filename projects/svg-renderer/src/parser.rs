use crate::color::SVGColor;

pub struct SVGParser;

impl SVGParser {
    pub fn parse_color(color_str: &str) -> Option<SVGColor> {
        let s = color_str.trim();
        if s.starts_with('#') {
            let hex = &s[1..];
            if hex.len() == 6 {
                if let Ok(val) = u32::from_str_radix(hex, 16) {
                    return Some(SVGColor::Hex(val));
                }
            }
        }
        if s.starts_with("rgb(") {
            let inner = &s[4..s.len()-1];
            let parts: Vec<&str> = inner.split(',').collect();
            if parts.len() == 3 {
                if let (Ok(r), Ok(g), Ok(b)) = (
                    parts[0].trim().parse::<u8>(),
                    parts[1].trim().parse::<u8>(),
                    parts[2].trim().parse::<u8>(),
                ) {
                    return Some(SVGColor::RGB(r, g, b));
                }
            }
        }
        // Named colors
        let lower = s.to_lowercase();
        let named = ["black", "white", "red", "green", "blue", "yellow", "cyan", "magenta"];
        if named.contains(&lower.as_str()) {
            return Some(SVGColor::Named(Box::leak(lower.into_boxed_str())));
        }
        None
    }

    pub fn parse_path(path_str: &str) -> Vec<String> {
        path_str.split_whitespace().map(|s| s.to_string()).collect()
    }
}
