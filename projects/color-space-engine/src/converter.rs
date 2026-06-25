use crate::rgb::RGB;
use crate::hsl::HSL;
use crate::hsv::HSV;
use crate::lab::Lab;
use crate::cmyk::CMYK;

pub struct Converter;

impl Converter {
    pub fn rgb_to_hsl(rgb: &RGB) -> HSL {
        HSL::from_rgb(rgb)
    }

    pub fn hsl_to_rgb(hsl: &HSL) -> RGB {
        hsl.to_rgb()
    }

    pub fn rgb_to_hsv(rgb: &RGB) -> HSV {
        HSV::from_rgb(rgb)
    }

    pub fn hsv_to_rgb(hsv: &HSV) -> RGB {
        hsv.to_rgb()
    }

    pub fn rgb_to_lab(rgb: &RGB) -> Lab {
        Lab::from_rgb(rgb)
    }

    pub fn lab_to_rgb(lab: &Lab) -> RGB {
        lab.to_rgb()
    }

    pub fn rgb_to_cmyk(rgb: &RGB) -> CMYK {
        CMYK::from_rgb(rgb)
    }

    pub fn cmyk_to_rgb(cmyk: &CMYK) -> RGB {
        cmyk.to_rgb()
    }

    pub fn hsl_to_hsv(hsl: &HSL) -> HSV {
        let rgb = hsl.to_rgb();
        HSV::from_rgb(&rgb)
    }

    pub fn hsv_to_hsv(hsv: &HSV) -> HSL {
        let rgb = hsv.to_rgb();
        HSL::from_rgb(&rgb)
    }

    pub fn lab_delta_e(lab1: &Lab, lab2: &Lab) -> f64 {
        Lab::delta_e(lab1, lab2)
    }
}
