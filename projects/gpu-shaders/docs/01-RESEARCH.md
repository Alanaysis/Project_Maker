# Research: GPU Shader Programming

## 1. Shader Languages Overview

### GLSL (OpenGL Shading Language)
- Used with OpenGL and Vulkan (via SPIR-V compilation)
- C-like syntax with GPU-specific types (vec2/3/4, mat2/3/4, sampler types)
- Version 330 core is the most widely supported modern profile
- Vertex and fragment shaders are separate compilation units

### HLSL (High Level Shading Language)
- Microsoft's shader language for Direct3D
- Similar syntax to GLSL but with different type names (float2/3/4 vs vec2/3/4)
- Compiled to DXBC or DXIL bytecode

### Key Differences
| Feature | GLSL | HLSL |
|---------|------|------|
| Vector types | vec2, vec3, vec4 | float2, float3, float4 |
| Matrix types | mat4 | float4x4 |
| Texture sampling | texture(sampler, uv) | tex.Sample(sampler, uv) |
| Entry point | main() | Configurable |
| Platform | OpenGL/Vulkan | Direct3D |

## 2. Graphics Pipeline

### Modern OpenGL Pipeline
```
Vertex Data → Vertex Shader → Tessellation → Geometry Shader →
Rasterization → Fragment Shader → Per-Fragment Ops → Framebuffer
```

### Vertex Shader Responsibilities
- Transform vertex positions (model → world → view → clip space)
- Pass data to fragment shader via varyings
- Compute per-vertex lighting (Gouraud shading)

### Fragment Shader Responsibilities
- Compute per-pixel color
- Sample textures
- Apply lighting calculations (Phong shading)
- Output final fragment color

### Key Concepts
- **Vertex Attributes**: Position, normal, texcoord, color (layout locations)
- **Uniforms**: Per-draw constants (matrices, light positions, material properties)
- **Varyings**: Interpolated values passed from vertex to fragment shader
- **Framebuffer**: Render target for off-screen rendering

## 3. Lighting Models Research

### Ambient Lighting
- Constant base illumination
- Simulates indirect light bouncing
- Formula: `ambient = ambientStrength * ambientColor`

### Diffuse (Lambertian) Reflection
- Light scatters equally in all directions
- Brightness depends on angle between surface normal and light direction
- Formula: `diffuse = max(dot(N, L), 0.0) * lightColor`

### Specular Reflection (Phong Model)
- Mirror-like reflection
- Depends on view angle and light reflection direction
- Formula: `specular = pow(max(dot(R, V), 0.0), shininess) * lightColor`

### Blinn-Phong Optimization
- Uses half-vector H = normalize(L + V) instead of reflection vector R
- Computationally cheaper: no reflect() call needed
- Often produces more visually pleasing highlights
- Formula: `specular = pow(max(dot(N, H), 0.0), shininess) * lightColor`

### Light Types
- **Directional**: Parallel rays, no position (sunlight)
- **Point**: Omnidirectional, attenuates with distance
- **Spot**: Cone-shaped with inner/outer cutoff angles

## 4. Post-Processing Research

### Render-to-Texture Workflow
1. Render scene to framebuffer object (FBO) with color attachment
2. Use color attachment as texture input for post-processing shader
3. Render full-screen quad with post-processing shader
4. Output to screen or next pass's FBO

### Common Post-Processing Effects
- **Tone Mapping**: HDR to LDR conversion (Reinhard, ACES, Uncharted2)
- **Bloom**: Extract bright areas, blur, combine with scene
- **Blur**: Separable Gaussian (horizontal + vertical passes)
- **Edge Detection**: Sobel, Laplacian, Canny operators
- **Color Grading**: LUT-based color transformation

### Multi-Pass Effects
- Bloom requires multiple passes: bright extract → blur → combine
- Depth of Field: near blur + far blur + composite
- Screen Space Reflections: ray march → blur → composite

## 5. Performance Considerations

### Shader Optimization Techniques
- Minimize branch divergence (if/else in fragment shaders)
- Use mediump/lowp precision qualifiers on mobile
- Avoid dependent texture reads when possible
- Use half-precision floats for color calculations
- Batch draw calls to minimize uniform uploads

### Memory and Bandwidth
- Texture compression (ASTC, ETC2, BC) reduces bandwidth
- Mipmapping improves cache coherency
- Render target format selection (RGBA8 vs RGBA16F vs RGBA32F)

## 6. Tools and Resources

### Development Tools
- RenderDoc: GPU frame debugger
- Nsight: NVIDIA GPU profiler
- Shader playground: Online GLSL/HLSL editors
- glslangValidator: Reference GLSL compiler

### Reference Materials
- "Real-Time Rendering" by Akenine-Moller et al.
- "Foundations of Game Engine Development, Volume 2: Rendering" by Lengyel
- LearnOpenGL.com: Comprehensive OpenGL tutorials
- Khronos OpenGL/GLSL specifications
