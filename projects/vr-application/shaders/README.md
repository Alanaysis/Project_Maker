# 着色器文件说明

本目录包含 VR 应用程序使用的所有着色器文件。

## 着色器列表

### 1. 基础着色器 (basic)

**文件**:
- `basic.vert` - 顶点着色器
- `basic.frag` - 片段着色器

**功能**:
- Phong 光照模型
- 支持方向光和点光源
- 纹理映射
- Gamma 校正

**Uniform 变量**:
```glsl
// 变换矩阵
uniform mat4 model;       // 模型矩阵
uniform mat4 view;        // 视图矩阵
uniform mat4 projection;  // 投影矩阵

// 材质
uniform Material material;
struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    bool useTexture;
    sampler2D diffuseTexture;
};

// 方向光
uniform DirectionalLight dirLight;
struct DirectionalLight {
    vec3 direction;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

// 点光源
uniform PointLight pointLights[4];
uniform int numPointLights;
struct PointLight {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float constant;
    float linear;
    float quadratic;
};

// 相机
uniform vec3 viewPos;
```

### 2. 线框着色器 (wireframe)

**文件**:
- `wireframe.vert` - 顶点着色器
- `wireframe.frag` - 片段着色器

**功能**:
- 线框渲染
- 调试可视化

**Uniform 变量**:
```glsl
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 lineColor;
```

### 3. 畸变校正着色器 (distortion)

**文件**:
- `distortion.vert` - 顶点着色器
- `distortion.frag` - 片段着色器

**功能**:
- VR 镜头畸变校正
- 支持径向畸变模型

**Uniform 变量**:
```glsl
uniform sampler2D inputTexture;
uniform vec2 distortionCoefficients;  // k1, k2
uniform vec2 centerOffset;
uniform float scale;
```

**畸变公式**:
```
r' = r * (1 + k1*r² + k2*r⁴) * scale
```

## 着色器编程指南

### 基础概念

1. **顶点着色器**: 处理每个顶点，计算位置和传递数据
2. **片段着色器**: 处理每个像素，计算最终颜色
3. **Uniform 变量**: 从 CPU 传递到 GPU 的常量
4. **Varying 变量**: 从顶点着色器传递到片段着色器的变量

### 光照模型

本项目使用 **Phong 光照模型**:

```
最终颜色 = 环境光 + 漫反射 + 镜面反射

环境光 = 材质环境光 * 光源环境光
漫反射 = 材质漫反射 * 光源漫反射 * max(法线·光方向, 0)
镜面反射 = 材质镜面反射 * 光源镜面反射 * pow(max(视线·反射方向, 0), 光泽度)
```

### 纹理映射

```glsl
// 采样纹理
vec4 texColor = texture(diffuseTexture, texCoord);

// 应用到最终颜色
FragColor = texColor * lightingColor;
```

### Gamma 校正

```glsl
// 线性空间到 sRGB
vec3 sRGB = pow(linearColor, vec3(1.0 / 2.2));

// sRGB 到线性空间
vec3 linear = pow(sRGB, vec3(2.2));
```

## 调试技巧

### 1. 可视化法线

```glsl
// 在片段着色器中
FragColor = vec4(normal * 0.5 + 0.5, 1.0);
```

### 2. 可视化深度

```glsl
// 在片段着色器中
float depth = gl_FragCoord.z;
FragColor = vec4(vec3(depth), 1.0);
```

### 3. 可视化 UV 坐标

```glsl
// 在片段着色器中
FragColor = vec4(texCoord, 0.0, 1.0);
```

## 性能优化

1. **减少 uniform 更新**: 只在值变化时更新
2. **使用实例化渲染**: 合并相同材质的物体
3. **LOD**: 根据距离使用不同的着色器
4. **延迟渲染**: 多光源场景使用延迟渲染

## 参考资源

- [Learn OpenGL - Shaders](https://learnopengl.com/Getting-started/Shaders)
- [GLSL Specification](https://www.khronos.org/registry/OpenGL/specs/gl/GLSLangSpec.4.50.pdf)
- [Shader Tutorial](http://www.opengl-tutorial.org/beginners-tutorials/tutorial-8-basic-shading/)