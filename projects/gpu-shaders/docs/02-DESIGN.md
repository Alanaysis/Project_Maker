# Design: GPU Shader Library Architecture

## 1. Design Goals

### Primary Goals
- Provide a complete library of common GLSL shader effects
- Enable easy composition of shaders into rendering pipelines
- Support validation and analysis without requiring a GPU
- Serve as a learning resource for shader programming

### Secondary Goals
- Clean, well-commented shader code for educational purposes
- Consistent uniform naming conventions across shaders
- Modular design allowing shader reuse
- Python tooling for shader management and testing

## 2. Architecture Overview

### Shader Organization
```
src/
├── basic/           # Foundation shaders (vertex transform, colors)
├── lighting/        # Lighting model implementations
├── postprocessing/  # Screen-space post-processing effects
└── utils/           # Python shader management tools
```

### Layer Architecture
```
┌─────────────────────────────────────┐
│          Application Layer          │
│    (Demo programs, user code)       │
├─────────────────────────────────────┤
│        Shader Library Layer         │
│  (Loading, validation, management)  │
├─────────────────────────────────────┤
│        Shader Parser Layer          │
│  (GLSL parsing, analysis)           │
├─────────────────────────────────────┤
│         GLSL Shader Layer           │
│  (Vertex, fragment, compute)        │
└─────────────────────────────────────┘
```

## 3. Shader Design Patterns

### Vertex Shader Pattern
All vertex shaders follow a consistent pattern:
```glsl
// 1. Declare inputs with layout locations
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

// 2. Declare outputs (varyings)
out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

// 3. Declare uniforms
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// 4. Transform and pass data
void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTexCoord;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
```

### Fragment Shader Pattern
Fragment shaders follow a lighting model pattern:
```glsl
// 1. Receive interpolated data
in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

// 2. Declare output
out vec4 FragColor;

// 3. Declare uniforms (lights, materials)
uniform vec3 lightPos;
uniform vec3 viewPos;

// 4. Calculate lighting
void main() {
    // Normalize interpolated normal
    vec3 norm = normalize(Normal);

    // Calculate components (ambient, diffuse, specular)
    // Combine and output
    FragColor = vec4(result, 1.0);
}
```

### Post-Processing Pattern
Post-processing shaders use a screen-space quad:
```glsl
// 1. Receive screen-space coordinates
in vec2 TexCoord;

// 2. Declare output
out vec4 FragColor;

// 3. Sample input texture
uniform sampler2D screenTexture;

// 4. Apply effect
void main() {
    vec4 color = texture(screenTexture, TexCoord);
    // Apply effect to color
    FragColor = result;
}
```

## 4. Uniform Naming Convention

### Consistent Naming
| Category | Pattern | Examples |
|----------|---------|----------|
| Matrices | camelCase | `model`, `view`, `projection` |
| Light position | `lightPos` | `lightPos`, `lightPos2` |
| Light color | `lightColor` | `lightColor`, `lightColor2` |
| Light direction | `lightDir` | `lightDir` |
| Object color | `objectColor` | `objectColor` |
| View position | `viewPos` | `viewPos` |
| Material props | camelCase | `shininess`, `specularStrength` |
| Textures | descriptive | `screenTexture`, `textureSampler` |
| Parameters | camelCase | `intensity`, `blurRadius` |

### Standard Uniforms (All Lighting Shaders)
```glsl
uniform vec3 lightPos;       // or lightDir for directional
uniform vec3 lightColor;
uniform vec3 objectColor;
uniform vec3 viewPos;
uniform float ambientStrength;
uniform float specularStrength;
uniform float shininess;
```

## 5. Shader Composition

### Pass-Based Composition
Shaders are composed into passes:
- Each pass has one vertex shader and one fragment shader
- Passes can be chained (output of one becomes input of next)
- Uniforms are collected from both shaders in a pass

### Effect Composition
Effects group multiple passes:
- Single-pass effects (most lighting, basic post-processing)
- Multi-pass effects (bloom: bright extract + blur + combine)
- Pipeline effects (full rendering pipeline)

## 6. Python Tooling Design

### Shader Parser
- Pure-Python GLSL lexer and parser
- Extracts: version, uniforms, inputs, outputs, functions, defines
- Validates: balanced braces/parens, main() presence
- No GPU or OpenGL dependency

### Shader Library
- Loads shaders from files or strings
- Creates passes and effects
- Validates shader programs
- Lists and queries shader metadata

## 7. Extensibility

### Adding New Shaders
1. Create `.vert` or `.frag` file in appropriate category
2. Follow naming conventions for uniforms
3. Add comprehensive comments
4. Parser automatically picks up new files

### Adding New Categories
1. Create new directory under `src/`
2. Add shaders following the patterns
3. Library's `load_directory` handles discovery
4. Tests automatically validate new shaders
