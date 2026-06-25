use crate::rasterizer::Rasterizer;
use crate::shapes::Shape;

pub struct Renderer {
    pub rasterizer: Rasterizer,
}

impl Renderer {
    pub fn new(width: usize, height: usize) -> Self {
        Renderer {
            rasterizer: Rasterizer::new(width, height),
        }
    }

    pub fn clear(&mut self, color: u32) {
        self.rasterizer.clear(color);
    }

    pub fn render(&mut self, shape: &dyn Shape) {
        shape.render(&mut self.rasterizer);
    }

    pub fn render_list(&mut self, shapes: &[Box<dyn Shape>]) {
        for shape in shapes {
            self.render(shape.as_ref());
        }
    }

    pub fn get_pixels(&self) -> Vec<u32> {
        self.rasterizer.render()
    }
}
