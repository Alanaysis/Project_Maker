# Development Guide: GPU Shader Library

## 1. Development Setup

### Prerequisites
- Python 3.8+ (for tooling)
- Text editor with GLSL syntax highlighting (recommended: VS Code with GLSL extensions)
- OpenGL 3.3+ capable GPU (optional, for runtime rendering)

### Getting Started
```bash
# Clone/navigate to project
cd projects/gpu-shaders

# Verify Python environment
python3 --version

# Run tests to verify setup
python3 -m pytest tests/ -v

# Run demo
python3 examples/demo_all_effects.py
```

## 2. Adding New Shaders

### Step 1: Choose Category
Place the shader in the appropriate directory:
- `src/basic/` - Foundation shaders
- `src/lighting/` - Lighting models
- `src/postprocessing/` - Screen-space effects

### Step 2: Create Shader File

#### For Vertex Shaders (.vert)
```glsl
#version 330 core

// Description of what this vertex shader does

layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTexCoord;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
```

#### For Fragment Shaders (.frag)
```glsl
#version 330 core

// Description of what this fragment shader does

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

// Uniforms follow naming convention
uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 objectColor;

void main()
{
    // Implementation
    FragColor = vec4(result, 1.0);
}
```

### Step 3: Follow Naming Conventions
- Use camelCase for uniform names
- Use descriptive names (`lightPos` not `lp`)
- Match existing patterns in the category

### Step 4: Add Comments
- File header: describe the shader's purpose
- Uniform declarations: explain each parameter
- Complex calculations: explain the math
- Reference algorithms or papers where applicable

### Step 5: Validate
```bash
# Run tests to verify new shader
python3 -m pytest tests/ -v

# Run demo to see shader info
python3 examples/demo_all_effects.py
```

## 3. Shader Development Workflow

### Iterative Development
1. Write shader code with comments
2. Run parser to check syntax
3. Fix any errors reported
4. Test in rendering application (if available)
5. Iterate on visual results

### Common Patterns

#### Adding a New Lighting Model
```glsl
// 1. Receive standard varyings
in vec3 FragPos;
in vec3 Normal;

// 2. Declare standard uniforms
uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 objectColor;
uniform vec3 viewPos;

// 3. Implement your lighting model
void main()
{
    vec3 norm = normalize(Normal);

    // Your lighting calculation here
    vec3 result = yourLightingModel(norm, ...);

    FragColor = vec4(result, 1.0);
}
```

#### Adding a New Post-Processing Effect
```glsl
// 1. Receive screen coordinates
in vec2 TexCoord;

// 2. Declare output
out vec4 FragColor;

// 3. Sample input texture
uniform sampler2D screenTexture;

// 4. Apply effect
void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    // Your effect here
    vec3 result = applyYourEffect(color.rgb);

    FragColor = vec4(result, color.a);
}
```

## 4. Testing New Shaders

### Automatic Validation
All shaders are automatically validated by the test suite:
- Parsing succeeds without errors
- Main function exists
- Braces and parentheses are balanced
- No deprecated keywords

### Manual Testing
```python
from src.utils.shader_library import ShaderLibrary

library = ShaderLibrary("src/")
info = library.load_shader("src/your_category/new_shader.frag")

print(f"Uniforms: {[u.name for u in info.uniforms]}")
print(f"Errors: {info.errors}")
print(f"Warnings: {info.warnings}")
```

## 5. Code Style Guidelines

### GLSL Style
- Use 4-space indentation
- Place opening brace on same line as function
- Comment complex calculations
- Group uniforms by category
- Use descriptive variable names

### Python Style
- Follow PEP 8
- Use type hints
- Write docstrings for classes and functions
- Keep functions focused and small

## 6. Debugging Shaders

### Common Issues and Solutions

#### Shader Compilation Error
- Check GLSL version compatibility
- Verify uniform types match usage
- Ensure all variables are declared before use

#### Visual Artifacts
- **Black screen**: Check MVP matrix setup
- **Flat lighting**: Verify normal transformation
- **Wrong colors**: Check color space and gamma
- **Z-fighting**: Adjust near/far plane distances

#### Performance Issues
- Reduce texture samples in fragment shader
- Use lower precision where possible
- Minimize branching in fragment shaders
- Batch draw calls

## 7. Contributing

### Checklist for New Shaders
- [ ] Placed in correct category directory
- [ ] Follows naming conventions
- [ ] Has comprehensive comments
- [ ] Passes all tests
- [ ] Works with the demo program
- [ ] Documentation updated if needed

### Review Process
1. Parser validation passes
2. All existing tests still pass
3. New shader has adequate comments
4. Uniform names follow conventions
5. Effect can be created and validated
