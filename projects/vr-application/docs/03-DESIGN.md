# 技术设计文档

## 1. 架构概述

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    VR Application                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   VR     │  │ Rendering│  │  Input   │  │  Scene   │  │
│  │  System  │  │  Engine  │  │  System  │  │  Manager │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │          │
│  ┌────┴─────────────┴─────────────┴─────────────┴─────┐   │
│  │                  Core Engine                        │   │
│  └────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  OpenXR  │  │  OpenGL  │  │   GLFW   │  │   GLM    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
vr-application/
├── src/
│   ├── core/                    # 核心引擎
│   │   ├── Application.cpp      # 应用程序主类
│   │   ├── Engine.cpp           # 引擎核心
│   │   └── Timer.cpp            # 时间管理
│   │
│   ├── rendering/               # 渲染系统
│   │   ├── Renderer.cpp         # 渲染器
│   │   ├── Shader.cpp           # 着色器管理
│   │   ├── Camera.cpp           # 相机系统
│   │   ├── Mesh.cpp             # 网格加载
│   │   └── Material.cpp         # 材质系统
│   │
│   ├── vr/                      # VR 系统
│   │   ├── VRSystem.cpp         # VR 系统管理
│   │   ├── VRSession.cpp        # VR 会话
│   │   ├── VRRender.cpp         # VR 渲染
│   │   └── VRTracking.cpp       # 追踪系统
│   │
│   ├── input/                   # 输入系统
│   │   ├── InputManager.cpp     # 输入管理
│   │   ├── Controller.cpp       # 手柄控制
│   │   └── HandTracking.cpp     # 手部追踪
│   │
│   └── scene/                   # 场景系统
│       ├── Scene.cpp            # 场景管理
│       ├── Object.cpp           # 场景对象
│       └── Transform.cpp        # 变换组件
│
├── include/                     # 头文件
├── shaders/                     # 着色器
├── tests/                       # 测试
└── examples/                    # 示例
```

## 2. 核心模块设计

### 2.1 应用程序生命周期

```
┌──────────────┐
│   初始化     │
│  (Init)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   主循环     │◄──────────────┐
│  (Main Loop) │               │
└──────┬───────┘               │
       │                       │
       ▼                       │
┌──────────────┐               │
│  处理输入    │               │
│(Process Input)│              │
└──────┬───────┘               │
       │                       │
       ▼                       │
┌──────────────┐               │
│  更新场景    │               │
│(Update Scene)│               │
└──────┬───────┘               │
       │                       │
       ▼                       │
┌──────────────┐               │
│  渲染画面    │               │
│(Render Frame)│               │
└──────┬───────┘               │
       │                       │
       └───────────────────────┘
       │
       ▼
┌──────────────┐
│   清理       │
│  (Cleanup)   │
└──────────────┘
```

### 2.2 渲染管线设计

```
输入数据
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│                    渲染管线                                  │
├─────────────────────────────────────────────────────────────┤
│  顶点数据 → 顶点着色器 → 图元装配 → 光栅化 → 片段着色器    │
│     │           │           │          │          │         │
│     ▼           ▼           ▼          ▼          ▼         │
│  VBO/VAO    变换计算    三角形      像素化    颜色计算       │
│             MVP矩阵     生成        插值      光照/纹理     │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
帧缓冲 → 畸变校正 → VR 输出
```

### 2.3 VR 立体渲染流程

```
           ┌─────────────────┐
           │   场景数据      │
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│   左眼渲染    │       │   右眼渲染    │
│              │       │              │
│  视图矩阵L   │       │  视图矩阵R   │
│  投影矩阵L   │       │  投影矩阵R   │
│  视口L       │       │  视口R       │
└───────┬───────┘       └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    ▼
           ┌─────────────────┐
           │   畸变校正      │
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │   VR 输出       │
           └─────────────────┘
```

## 3. 数据结构设计

### 3.1 核心数据结构

```cpp
// 向量和矩阵
struct Vec3 {
    float x, y, z;
};

struct Vec4 {
    float x, y, z, w;
};

struct Mat4 {
    float m[4][4];
};

struct Quat {
    float x, y, z, w;
};

// 变换
struct Transform {
    Vec3 position;
    Quat rotation;
    Vec3 scale;
};

// 顶点
struct Vertex {
    Vec3 position;
    Vec3 normal;
    Vec2 texCoord;
};

// 渲染对象
struct RenderObject {
    GLuint vao;
    GLuint vbo;
    GLuint ebo;
    uint32_t indexCount;
    Material material;
    Transform transform;
};

// VR 姿态
struct VRPose {
    Vec3 position;
    Quat orientation;
    Vec3 linearVelocity;
    Vec3 angularVelocity;
};

// VR 视图
struct VRView {
    Mat4 projectionMatrix;
    Mat4 viewMatrix;
    VRPose pose;
};
```

### 3.2 场景图结构

```
Scene
├── Root Node
│   ├── Camera
│   │   ├── VR Camera (Stereo)
│   │   └── Debug Camera (Mono)
│   │
│   ├── Light
│   │   ├── Directional Light
│   │   └── Point Lights[]
│   │
│   └── Objects
│       ├── Static Objects[]
│       │   ├── Mesh
│       │   ├── Material
│       │   └── Transform
│       │
│       └── Interactive Objects[]
│           ├── Mesh
│           ├── Material
│           ├── Transform
│           ├── Physics (optional)
│           └── Interaction
│
└── Environment
    ├── Skybox
    └── Ground Plane
```

## 4. 接口设计

### 4.1 核心接口

```cpp
// 应用程序接口
class IApplication {
public:
    virtual bool Initialize() = 0;
    virtual void Run() = 0;
    virtual void Shutdown() = 0;
    virtual bool IsRunning() const = 0;
};

// 渲染器接口
class IRenderer {
public:
    virtual bool Initialize() = 0;
    virtual void BeginFrame() = 0;
    virtual void Render(const RenderObject& object) = 0;
    virtual void EndFrame() = 0;
    virtual void Shutdown() = 0;
};

// VR 系统接口
class IVRSystem {
public:
    virtual bool Initialize() = 0;
    virtual bool PollEvents() = 0;
    virtual VRPose GetHeadPose() const = 0;
    virtual VRPose GetControllerPose(int controller) const = 0;
    virtual VRView GetView(int eye) const = 0;
    virtual void SubmitFrame() = 0;
    virtual void Shutdown() = 0;
};

// 输入管理器接口
class IInputManager {
public:
    virtual bool Initialize() = 0;
    virtual void Update() = 0;
    virtual bool IsButtonPressed(int button) const = 0;
    virtual float GetTriggerValue(int controller) const = 0;
    virtual Vec2 GetThumbstick(int controller) const = 0;
    virtual void Shutdown() = 0;
};

// 场景管理器接口
class ISceneManager {
public:
    virtual bool LoadScene(const std::string& path) = 0;
    virtual void Update(float deltaTime) = 0;
    virtual void Render(IRenderer& renderer) = 0;
    virtual void UnloadScene() = 0;
};
```

### 4.2 渲染器详细接口

```cpp
class Renderer : public IRenderer {
private:
    // 着色器程序
    ShaderProgram m_shaderProgram;

    // 帧缓冲
    struct Framebuffer {
        GLuint fbo;
        GLuint colorTexture;
        GLuint depthTexture;
    };

    // VR 渲染目标
    struct VRRenderTargets {
        Framebuffer leftEye;
        Framebuffer rightEye;
        uint32_t width;
        uint32_t height;
    } m_vrTargets;

public:
    // 初始化渲染器
    bool Initialize() override;

    // 设置渲染状态
    void SetViewMatrix(const Mat4& view);
    void SetProjectionMatrix(const Mat4& projection);
    void SetModelMatrix(const Mat4& model);

    // 渲染调用
    void DrawMesh(const Mesh& mesh, const Material& material);
    void DrawIndexed(const VertexBuffer& vb, const IndexBuffer& ib);

    // VR 特定
    void BeginVREye(int eye);
    void EndVREye(int eye);
    void SubmitVRFrame();

    // 状态管理
    void SetWireframeMode(bool enabled);
    void SetDepthTest(bool enabled);
    void SetBlending(bool enabled);
};
```

## 5. 类图设计

### 5.1 核心类图

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                            │
├─────────────────────────────────────────────────────────────┤
│ - m_engine: Engine*                                         │
│ - m_vrSystem: VRSystem*                                     │
│ - m_renderer: Renderer*                                     │
│ - m_inputManager: InputManager*                             │
│ - m_sceneManager: SceneManager*                             │
│ - m_isRunning: bool                                         │
├─────────────────────────────────────────────────────────────┤
│ + Initialize(): bool                                        │
│ + Run(): void                                               │
│ + Shutdown(): void                                          │
│ - ProcessInput(): void                                      │
│ - Update(float deltaTime): void                             │
│ - Render(): void                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Engine                               │
├─────────────────────────────────────────────────────────────┤
│ - m_window: GLFWwindow*                                     │
│ - m_timer: Timer                                            │
│ - m_isInitialized: bool                                     │
├─────────────────────────────────────────────────────────────┤
│ + InitializeWindow(int width, int height, const char* title)│
│ + GetDeltaTime(): float                                     │
│ + GetFPS(): int                                             │
│ + ShouldClose(): bool                                       │
│ + SwapBuffers(): void                                       │
│ + PollEvents(): void                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       VRSystem                              │
├─────────────────────────────────────────────────────────────┤
│ - m_instance: XrInstance                                    │
│ - m_session: XrSession                                      │
│ - m_space: XrSpace                                          │
│ - m_headPose: VRPose                                        │
│ - m_controllerPoses: VRPose[2]                              │
├─────────────────────────────────────────────────────────────┤
│ + Initialize(): bool                                        │
│ + PollEvents(): bool                                        │
│ + GetHeadPose(): VRPose                                     │
│ + GetControllerPose(int controller): VRPose                 │
│ + GetView(int eye): VRView                                  │
│ + SubmitFrame(): void                                       │
│ + Shutdown(): void                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       Renderer                              │
├─────────────────────────────────────────────────────────────┤
│ - m_shaderProgram: ShaderProgram                            │
│ - m_vrTargets: VRRenderTargets                              │
│ - m_currentView: Mat4                                       │
│ - m_currentProjection: Mat4                                 │
├─────────────────────────────────────────────────────────────┤
│ + Initialize(): bool                                        │
│ + BeginFrame(): void                                        │
│ + Render(const RenderObject& object): void                  │
│ + EndFrame(): void                                          │
│ + Shutdown(): void                                          │
└─────────────────────────────────────────────────────────────┘
```

## 6. 着色器设计

### 6.1 顶点着色器

```glsl
#version 450 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

out VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoord;
} vs_out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    vs_out.FragPos = vec3(model * vec4(aPos, 1.0));
    vs_out.Normal = mat3(transpose(inverse(model))) * aNormal;
    vs_out.TexCoord = aTexCoord;

    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
```

### 6.2 片段着色器

```glsl
#version 450 core

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoord;
} fs_in;

out vec4 FragColor;

// 材质
struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    sampler2D diffuseTexture;
};

// 光源
struct Light {
    vec3 direction;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

uniform Material material;
uniform Light light;
uniform vec3 viewPos;

void main()
{
    // 环境光
    vec3 ambient = light.ambient * material.ambient;

    // 漫反射
    vec3 norm = normalize(fs_in.Normal);
    vec3 lightDir = normalize(-light.direction);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = light.diffuse * (diff * material.diffuse);

    // 镜面反射
    vec3 viewDir = normalize(viewPos - fs_in.FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);
    vec3 specular = light.specular * (spec * material.specular);

    // 纹理
    vec3 textureColor = texture(material.diffuseTexture, fs_in.TexCoord).rgb;

    // 最终颜色
    vec3 result = (ambient + diffuse + specular) * textureColor;
    FragColor = vec4(result, 1.0);
}
```

## 7. VR 畸变校正

### 7.1 畸变模型

```
原始图像                畸变后图像
    ┌──────┐               ┌──────┐
    │      │               │ ╭──╮ │
    │      │      ──→      │╭╯  ╰╮│
    │      │               │╰╮  ╭╯│
    └──────┘               │ ╰──╯ │
                           └──────┘

畸变公式:
r_distorted = r * (1 + k1*r² + k2*r⁴ + k3*r⁶ + k4*r⁸)

其中:
- r: 原始距离
- k1, k2, k3, k4: 畸变系数
```

### 7.2 畸变校正着色器

```glsl
#version 450 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D inputTexture;
uniform vec2 distortionCoefficients;  // k1, k2
uniform vec2 centerOffset;

void main()
{
    // 计算到中心的距离
    vec2 uv = TexCoord - 0.5 - centerOffset;
    float r2 = dot(uv, uv);
    float r4 = r2 * r2;

    // 应用畸变
    float distortion = 1.0 + distortionCoefficients.x * r2 +
                       distortionCoefficients.y * r4;

    vec2 distortedUV = uv * distortion + 0.5 + centerOffset;

    // 检查边界
    if (distortedUV.x < 0.0 || distortedUV.x > 1.0 ||
        distortedUV.y < 0.0 || distortedUV.y > 1.0) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        FragColor = texture(inputTexture, distortedUV);
    }
}
```

## 8. 性能优化策略

### 8.1 渲染优化

| 策略 | 实现方式 | 预期效果 |
|------|----------|----------|
| **视锥剔除** | 检查物体是否在视锥内 | 减少 30-50% 绘制调用 |
| **遮挡剔除** | GPU 查询遮挡 | 减少 20-40% 片段处理 |
| **LOD** | 根据距离切换模型 | 减少 50%+ 顶点数 |
| **实例化渲染** | 合并相同材质物体 | 减少 80%+ 绘制调用 |
| **纹理图集** | 合并小纹理 | 减少纹理切换 |

### 8.2 内存优化

```
对象池模式
┌─────────────────────────────────────────┐
│              Object Pool                │
├─────────────────────────────────────────┤
│  Active Objects    │   Free Objects     │
│  ┌──┐ ┌──┐ ┌──┐   │   ┌──┐ ┌──┐ ┌──┐ │
│  │○ │ │○ │ │○ │   │   │○ │ │○ │ │○ │ │
│  └──┘ └──┘ └──┘   │   └──┘ └──┘ └──┘ │
└─────────────────────────────────────────┘

使用时从 Free 取出，用完放回 Free
避免频繁的 new/delete
```

### 8.3 VR 特定优化

1. **异步时间扭曲（ATW）**
   - 在 CPU 等待 GPU 时应用
   - 使用上一帧的姿态数据
   - 减少感知延迟

2. **注视点渲染（Foveated Rendering）**
   - 中心区域高分辨率
   - 边缘区域低分辨率
   - 减少 30-50% 像素处理

3. **多分辨率渲染**
   - 不同区域不同分辨率
   - 根据注视点调整
   - 优化 GPU 负载

## 9. 错误处理设计

### 9.1 错误类型

```cpp
enum class ErrorCode {
    // 初始化错误
    VR_INIT_FAILED,
    OPENGL_INIT_FAILED,
    WINDOW_INIT_FAILED,

    // 运行时错误
    VR_SESSION_LOST,
    RENDER_ERROR,
    SHADER_COMPILE_ERROR,

    // 资源错误
    FILE_NOT_FOUND,
    TEXTURE_LOAD_FAILED,
    MODEL_LOAD_FAILED,

    // 输入错误
    CONTROLLER_DISCONNECTED,
    TRACKING_LOST
};
```

### 9.2 错误处理策略

```
错误发生
    │
    ▼
┌──────────────┐
│  捕获错误    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  可恢复？    │────→│  恢复操作    │
└──────┬───────┘  是  └──────────────┘
       │ 否
       ▼
┌──────────────┐
│  记录日志    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  优雅退出    │
└──────────────┘
```

## 10. 测试策略

### 10.1 单元测试

- 数学库测试（向量、矩阵、四元数）
- 着色器编译测试
- 资源加载测试
- 输入处理测试

### 10.2 集成测试

- 渲染管线测试
- VR 系统集成测试
- 场景管理测试

### 10.3 性能测试

- 帧率测试
- 内存使用测试
- 追踪延迟测试

## 11. 部署设计

### 11.1 构建系统

```cmake
# CMakeLists.txt 结构
cmake_minimum_required(VERSION 3.15)
project(VRApplication)

# 依赖查找
find_package(OpenGL REQUIRED)
find_package(glfw3 REQUIRED)
find_package(GLEW REQUIRED)
find_package(glm REQUIRED)

# OpenXR（可选）
find_package(OpenXR QUIET)

# 编译选项
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 源文件
add_executable(vr_application
    src/main.cpp
    src/core/Application.cpp
    src/rendering/Renderer.cpp
    src/vr/VRSystem.cpp
    # ...
)

# 链接库
target_link_libraries(vr_application
    OpenGL::GL
    glfw
    GLEW::GLEW
    glm::glm
)
```

### 11.2 依赖管理

| 依赖 | 版本 | 用途 |
|------|------|------|
| OpenGL | 4.5+ | 图形渲染 |
| GLFW | 3.3+ | 窗口管理 |
| GLEW | 2.1+ | OpenGL 扩展 |
| GLM | 0.9.9+ | 数学库 |
| OpenXR | 1.0+ | VR 运行时（可选） |

## 12. 安全设计

### 12.1 输入验证

- 验证所有外部输入
- 防止缓冲区溢出
- 资源路径验证

### 12.2 资源管理

- RAII 模式管理资源
- 智能指针避免内存泄漏
- 异常安全设计