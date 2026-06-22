# GPU Shader Library

A comprehensive library of GLSL shaders implementing common rendering effects, from basic vertex/fragment shaders to advanced post-processing techniques.

## Overview

This project provides a collection of production-quality GLSL shaders organized into three categories:

- **Basic Shaders**: Vertex transformation, solid colors, textures, gradients
- **Lighting Shaders**: Ambient, diffuse, Phong, Blinn-Phong, directional, point, spot, and multi-light models
- **Post-Processing Shaders**: Grayscale, sepia, blur, edge detection, vignette, chromatic aberration, bloom, HDR tone mapping

## Project Structure

```
gpu-shaders/
├── src/
│   ├── basic/                  # Basic shaders
│   │   ├── passthrough.vert    # MVP transformation vertex shader
│   │   ├── solid_color.frag    # Uniform solid color
│   │   ├── texture.frag        # Texture sampling with tint
│   │   └── gradient.frag       # Linear/radial/angular gradients
│   ├── lighting/               # Lighting model shaders
│   │   ├── ambient.frag        # Ambient lighting
│   │   ├── diffuse.frag        # Lambertian diffuse
│   │   ├── phong.frag          # Phong reflection model
│   │   ├── blinn_phong.frag    # Blinn-Phong (half-vector)
│   │   ├── directional.frag    # Directional light (sun)
│   │   ├── point_light.frag    # Point light with attenuation
│   │   ├── spotlight.frag      # Spotlight with cone falloff
│   │   └── multi_light.frag    # Multiple light sources
│   ├── postprocessing/         # Post-processing effects
│   │   ├── screen_quad.vert    # Full-screen quad vertex shader
│   │   ├── grayscale.frag      # Luminance-based grayscale
│   │   ├── sepia.frag          # Sepia tone filter
│   │   ├── blur.frag           # Separable Gaussian blur
│   │   ├── edge_detection.frag # Sobel edge detection
│   │   ├── vignette.frag       # Vignette darkening
│   │   ├── chromatic_aberration.frag  # Lens aberration
│   │   ├── bloom.frag          # HDR bloom (bright pass + combine)
│   │   └── hdr_tonemapping.frag # Reinhard/ACES/Uncharted2
│   └── utils/                  # Python shader management tools
│       ├── shader_parser.py    # GLSL parser and validator
│       └── shader_library.py   # Shader library manager
├── tests/                      # Test suite
├── examples/                   # Demo programs
└── docs/                       # Documentation
```

## Quick Start

### Using Shaders in Your Application

Each `.vert` and `.frag` file is a standalone GLSL shader that can be loaded by any OpenGL application:

```python
# Load shaders using the Python library
from src.utils.shader_library import ShaderLibrary

library = ShaderLibrary("src/")
library.load_shader("src/basic/passthrough.vert")
library.load_shader("src/lighting/phong.frag")

# Create a shader pass
pass_obj = library.create_pass("phong_pass", "passthrough", "phong")
print(f"Valid: {pass_obj.valid}")
print(f"Uniforms: {[u.name for u in pass_obj.uniforms.values()]}")
```

### Running the Demo

```bash
cd projects/gpu-shaders
python3 examples/demo_all_effects.py
```

### Running Tests

```bash
cd projects/gpu-shaders
python3 -m pytest tests/ -v
```

## Shader Categories

### Basic Shaders

| Shader | Type | Description |
|--------|------|-------------|
| `passthrough` | Vertex | Transforms vertices from model to clip space |
| `solid_color` | Fragment | Outputs uniform solid color |
| `texture` | Fragment | Samples 2D texture with optional tint |
| `gradient` | Fragment | Linear, radial, or angular gradients |

### Lighting Shaders

| Shader | Model | Key Feature |
|--------|-------|-------------|
| `ambient` | Ambient | Base illumination, direction-independent |
| `diffuse` | Lambertian | Cosine-law diffuse reflection |
| `phong` | Phong | Ambient + Diffuse + Specular |
| `blinn_phong` | Blinn-Phong | Half-vector specular (faster) |
| `directional` | Directional | Parallel light rays (sunlight) |
| `point_light` | Point | Omnidirectional with distance attenuation |
| `spotlight` | Spot | Cone-shaped light with soft edges |
| `multi_light` | Combined | Multiple lights of different types |

### Post-Processing Shaders

| Shader | Effect | Key Uniforms |
|--------|--------|--------------|
| `grayscale` | B&W conversion | `intensity` |
| `sepia` | Vintage look | `intensity` |
| `blur` | Gaussian blur | `blurRadius`, `horizontal` |
| `edge_detection` | Sobel edges | `edgeStrength`, `edgeColor` |
| `vignette` | Edge darkening | `vignetteRadius`, `vignetteSoftness` |
| `chromatic_aberration` | Color fringing | `aberrationStrength` |
| `bloom` | HDR glow | `bloomThreshold`, `bloomIntensity` |
| `hdr_tonemapping` | HDR to LDR | `exposure`, `tonemapOperator` |

## Rendering Pipeline

A typical forward rendering pipeline using these shaders:

```
1. Geometry Pass     → passthrough.vert + blinn_phong.frag
2. Bright Extract    → screen_quad.vert + bloom.frag (passType=0)
3. Bloom Blur (H)    → screen_quad.vert + blur.frag (horizontal=1)
4. Bloom Blur (V)    → screen_quad.vert + blur.frag (horizontal=0)
5. Bloom Combine     → screen_quad.vert + bloom.frag (passType=1)
6. HDR Tone Map      → screen_quad.vert + hdr_tonemapping.frag
7. Vignette          → screen_quad.vert + vignette.frag
```

## Learning Objectives

This project demonstrates:

1. **GLSL Fundamentals**: Data types, qualifiers, built-in variables
2. **Vertex Shaders**: Model-View-Projection transformation
3. **Fragment Shaders**: Per-pixel lighting calculations
4. **Lighting Models**: From ambient to multi-light setups
5. **Post-Processing**: Screen-space effects using render targets
6. **Shader Architecture**: Modular design, uniform management

## Requirements

- Python 3.8+ (for shader management tools)
- OpenGL 3.3+ (for runtime rendering, optional)
- No GPU required for validation/testing

## License

Educational project for learning GPU shader programming.
