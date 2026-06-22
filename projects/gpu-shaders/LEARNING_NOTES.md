# Learning Notes: GPU Shader Programming

## What I Learned

### GLSL Fundamentals

**Data Types**: GLSL has GPU-optimized types not found in standard C:
- `vec2/3/4`: 2D/3D/4D floating-point vectors
- `mat2/3/4`: 2x2/3x3/4x4 matrices
- `sampler2D`: Texture sampler handle
- `ivec/uvec/bvec`: Integer, unsigned, boolean vectors

**Qualifiers**: GLSL uses qualifiers to define variable roles:
- `in`/`out`: Per-vertex inputs and outputs (varyings)
- `uniform`: Per-draw constants (same for all vertices/fragments)
- `layout(location=N)`: Explicit attribute binding
- `const`: Compile-time constants

**Built-in Variables**: Special variables provided by the GPU:
- `gl_Position`: Vertex shader output (clip-space position)
- `gl_FragCoord`: Fragment position in window coordinates
- `gl_FrontFace`: Whether fragment is front-facing

### Vertex Shader Concepts

**Coordinate Spaces**: Understanding the transformation pipeline:
1. **Model Space**: Object's local coordinates
2. **World Space**: Global scene coordinates
3. **View Space**: Camera-relative coordinates
4. **Clip Space**: After projection (what gl_Position expects)
5. **NDC**: Normalized Device Coordinates (after perspective divide)
6. **Screen Space**: Final pixel coordinates

**MVP Matrix**: The core transformation chain:
```
clipPos = projection * view * model * vec4(position, 1.0)
```

**Normal Transformation**: Normals must use the inverse transpose:
```
normalMatrix = transpose(inverse(mat3(model)))
worldNormal = normalMatrix * localNormal
```

### Fragment Shader Concepts

**Interpolation**: Values passed from vertex to fragment shader are
automatically interpolated across the triangle. This is why we must
re-normalize normals in fragment shaders.

**Texture Sampling**: The `texture()` function samples a texture:
```glsl
vec4 color = texture(sampler2D, vec2(u, v));
// Returns RGBA value, filtered by texture settings
```

**Discarding Fragments**: Can skip fragments entirely:
```glsl
if (alpha < 0.01) discard;  // Transparent cutout
```

### Lighting Models

**Ambient Lighting**: Simplest model, provides base illumination:
- No geometry dependency
- Prevents completely black shadows
- Typically a fraction of the light color

**Diffuse (Lambertian)**: Matte surface reflection:
- Uses cosine of angle between normal and light direction
- `max(dot(N, L), 0.0)` prevents negative values
- Brightest when surface faces light directly

**Specular (Phong)**: Shiny highlight reflection:
- Depends on view direction and light reflection
- `pow(max(dot(V, R), 0.0), shininess)` controls highlight size
- Higher shininess = smaller, sharper highlight

**Blinn-Phong Optimization**: Uses half-vector instead of reflection:
- `H = normalize(L + V)` - halfway between light and view
- `dot(N, H)` instead of `dot(V, R)`
- Computationally cheaper (no `reflect()` call)
- Often looks better due to highlight falloff behavior

**Attenuation**: Light falls off with distance:
```
attenuation = 1.0 / (constant + linear*d + quadratic*d^2)
```
- Constant: Base attenuation (usually 1.0)
- Linear: Linear falloff (0.09 typical)
- Quadratic: Quadratic falloff (0.032 typical)

### Post-Processing Techniques

**Render-to-Texture**: The foundation of post-processing:
1. Create framebuffer object (FBO) with color attachment
2. Render scene to FBO instead of screen
3. Use color attachment as texture input
4. Render full-screen quad with post-processing shader

**Separable Blur**: Gaussian blur in two passes:
- Horizontal pass: blur along X axis
- Vertical pass: blur along Y axis
- Same visual result as 2D kernel, but O(n) instead of O(n^2)

**Tone Mapping**: Converting HDR to LDR for display:
- Reinhard: Simple compression `color / (color + 1.0)`
- ACES: Filmic curve with nice highlights
- Uncharted2: Adjustable shoulder for artistic control

**Bloom**: Making bright areas glow:
1. Extract pixels above brightness threshold
2. Blur the bright pixels
3. Add blurred bright pixels back to scene
4. Tone map to prevent over-brightness

### Key Insights

1. **Precision Matters**: `mediump` vs `highp` affects performance and quality
2. **Normalization is Critical**: Always normalize interpolated normals
3. **Uniform vs Varying**: Uniforms are constant per-draw, varyings are per-vertex interpolated
4. **Texture Lookups are Expensive**: Minimize texture samples in fragment shaders
5. **Branching Costs**: GPU threads execute in lockstep; divergent branches hurt performance
6. **Linear vs sRGB**: Be aware of color space; lighting should be in linear space

### Common Pitfalls

1. **Forgetting to normalize**: Interpolated vectors lose unit length
2. **Wrong matrix order**: GLSL uses column-major; `A * v` not `v * A`
3. **Integer division**: `1/2` is 0 in GLSL, use `1.0/2.0`
4. **Precision qualifiers**: Mobile GPUs need explicit precision
5. **Texture coordinate flipping**: OpenGL texture origin is bottom-left
6. **Gamma correction**: sRGB textures need linearization before lighting

## Questions for Further Study

1. How do geometry shaders work and when are they useful?
2. What is compute shader programming and its applications?
3. How does physically-based rendering (PBR) differ from Phong?
4. What are shadow mapping techniques and their tradeoffs?
5. How do deferred rendering and forward+ rendering compare?
6. What is screen-space ambient occlusion (SSAO)?
7. How do modern engines handle transparency and order-independent rendering?
8. What are the latest advances in real-time ray tracing shaders?
