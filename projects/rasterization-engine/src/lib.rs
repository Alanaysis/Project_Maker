pub mod geometry;
pub mod rasterizer;
pub mod renderer;
pub mod shapes;

pub use geometry::{Point, Line, Triangle};
pub use rasterizer::Rasterizer;
pub use renderer::Renderer;
pub use shapes::{Shape, Circle, Rectangle, Polygon};
