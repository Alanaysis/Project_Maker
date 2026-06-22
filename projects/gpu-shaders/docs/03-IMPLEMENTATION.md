# Implementation: GPU Shader Library

## 1. Implementation Overview

The shader library is implemented in two layers:
1. **GLSL Shader Layer**: The actual shader source code (.vert, .frag files)
2. **Python Tooling Layer**: Parser, validator, and library manager

## 2. GLSL Shader Implementation

### Basic Shaders

#### passthrough.vert
- Implements standard Model-View-Projection (MVP) transformation
- Uses normal matrix (`transpose(inverse(model))`) for correct normal transformation
- Outputs world-space position, normal, and texture coordinates

#### solid_color.frag
- Simplest fragment shader: outputs uniform color
- Useful for debugging, wireframe overlays, solid objects

#### texture.frag
- Samples 2D texture using `texture()` function
- Supports tint blending via `mix()` with configurable strength

#### gradient.frag
- Implements three gradient types using texture coordinates
- Linear: dot product with direction vector
- Radial: distance from center
- Angular: `atan()` for circular gradients

### Lighting Shaders

#### ambient.frag
- Simplest lighting: `ambient = strength * color`
- No geometry dependency (direction-independent)

#### diffuse.frag
- Lambertian reflection: `max(dot(N, L), 0.0)`
- N = surface normal, L = light direction
- Combined with ambient for base illumination

#### phong.frag
- Full Phong model: Ambient + Diffuse + Specular
- Specular uses reflection vector: `R = reflect(-L, N)`
- Specular intensity: `pow(max(dot(V, R), 0.0), shininess)`

#### blinn_phong.frag
- Optimized Phong using half-vector: `H = normalize(L + V)`
- Cheaper than Phong (no reflect() call)
- Often looks better due to how highlights fade

#### directional.frag
- Light direction is uniform (same for all fragments)
- No position dependency (infinite distance)
- Used for sunlight, moonlight

#### point_light.frag
- Light position is uniform, direction computed per-fragment
- Attenuation: `1.0 / (constant + linear*d + quadratic*d^2)`
- Typical values: constant=1.0, linear=0.09, quadratic=0.032

#### spotlight.frag
- Cone-shaped light with inner/outer cutoff angles
- Smooth edge falloff using `smoothstep`-like calculation
- Uses cosine of angles for efficient comparison

#### multi_light.frag
- Supports up to 4 point lights and 2 spot lights
- Uses structs for light data organization
- Loops over lights, accumulating contributions

### Post-Processing Shaders

#### screen_quad.vert
- Renders full-screen triangle/quad
- Passes texture coordinates to fragment shader

#### grayscale.frag
- Perceptual luminance: `0.2126*R + 0.7152*G + 0.0722*B`
- Intensity parameter for partial desaturation

#### sepia.frag
- Sepia transformation matrix applied to RGB
- Based on standard sepia tone values

#### blur.frag
- Separable Gaussian blur (single axis per pass)
- Configurable radius and sigma
- Two-pass approach: horizontal then vertical

#### edge_detection.frag
- Sobel operator: two 3x3 kernels (horizontal + vertical)
- Edge magnitude: `sqrt(edgeX^2 + edgeY^2)`
- Configurable edge color and background

#### vignette.frag
- Distance-based darkening from screen center
- `smoothstep` for soft falloff edges
- Configurable radius and softness

#### chromatic_aberration.frag
- Per-channel offset based on distance from center
- Simulates lens distortion
- R channel offset positive, B channel offset negative

#### bloom.frag
- Two modes: bright pass (extract) and combine
- Bright pass: `max(luminance - threshold, 0.0) * color`
- Combine: original + blurred bloom * intensity

#### hdr_tonemapping.frag
- Three operators: Reinhard, ACES, Uncharted2
- Reinhard: `color / (color + 1.0)` - simple compression
- ACES: Filmic curve used in many games
- Uncharted2: Filmic look with adjustable shoulder

## 3. Python Tooling Implementation

### Shader Parser (shader_parser.py)

#### Lexical Analysis
- Comment removal (single-line `//` and multi-line `/* */`)
- Regex-based token extraction

#### Structural Extraction
- Version: `#version NNN profile`
- Uniforms: `uniform type name;` and `uniform type name[N];`
- Inputs/Outputs: `layout(location=N) in/out type name;`
- Functions: `type name(params) { body }`
- Defines: `#define NAME VALUE`

#### Validation Rules
- Main function must exist
- Braces must be balanced
- Parentheses must be balanced
- Version directive recommended
- Deprecated keywords generate warnings

### Shader Library (shader_library.py)

#### Loading
- Directory scanning for .vert and .frag files
- String-based loading for dynamic shaders
- Automatic type detection from file extension

#### Pass Creation
- Combines vertex and fragment shaders
- Collects uniforms from both shaders
- Validates both shaders independently

#### Effect Creation
- Groups multiple passes into effects
- Supports category tagging
- Validates all passes in an effect

## 4. Test Strategy

### Parser Tests
- Version parsing (various GLSL versions)
- Uniform extraction (scalars, vectors, matrices, arrays, samplers)
- Input/output extraction (with and without locations)
- Function extraction (various return types and parameters)
- Comment handling (single-line, multi-line, inline)
- Validation (missing main, unbalanced syntax)
- Type detection (vertex vs fragment)

### Library Tests
- Directory loading (all categories)
- Shader validation (all shaders pass)
- Pass creation (various combinations)
- Effect creation (single and multi-pass)
- String loading (dynamic shaders)
- Source retrieval and error reporting

### Integration Tests
- All shaders parse without errors
- All shaders have main() function
- All shaders have balanced syntax
- Uniform consistency across shader categories

## 5. Error Handling

### Parser Errors
- Missing main() function
- Unbalanced braces or parentheses
- Invalid syntax patterns

### Parser Warnings
- Missing version directive
- Deprecated keywords (varying, attribute, gl_FragColor)
- Potential issues that don't prevent compilation

### Library Errors
- Shader not found (loading/validation)
- Invalid shader type
- Pass creation failures
