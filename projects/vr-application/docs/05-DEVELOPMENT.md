# 开发手册

## 1. 环境搭建

### 1.1 系统要求

**操作系统**:
- Windows 10/11 (推荐)
- Linux (Ubuntu 20.04+, Fedora 36+)
- macOS (有限支持)

**硬件要求**:
- CPU: Intel i5-8400 / AMD Ryzen 5 2600 或更高
- GPU: NVIDIA GTX 1060 / AMD RX 580 或更高
- RAM: 8GB 或更高
- VR 设备: 支持 OpenXR 的头显（可选，有桌面模拟模式）

### 1.2 开发工具

#### 必需工具
| 工具 | 版本 | 用途 | 安装方式 |
|------|------|------|----------|
| C++ 编译器 | GCC 9+ / Clang 10+ / MSVC 2019+ | 编译代码 | 系统自带或包管理器 |
| CMake | 3.15+ | 构建系统 | 包管理器或官网 |
| Git | 2.30+ | 版本控制 | 包管理器或官网 |

#### 推荐 IDE
| IDE | 平台 | 特点 |
|-----|------|------|
| Visual Studio 2022 | Windows | 功能强大，调试方便 |
| CLion | 跨平台 | C++ 支持好，CMake 集成 |
| VS Code + C++ Extension | 跨平台 | 轻量，插件丰富 |

### 1.3 依赖安装

#### Windows

**使用 vcpkg（推荐）**:
```powershell
# 安装 vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装依赖
.\vcpkg install glfw3 glew glm openxr-loader

# 设置环境变量
set VCPKG_ROOT=C:\path\to\vcpkg
```

**手动安装**:
1. GLFW: https://www.glfw.org/download
2. GLEW: http://glew.sourceforge.net/
3. GLM: https://github.com/g-truc/glm
4. OpenXR: https://github.com/KhronosGroup/OpenXR-SDK

#### Linux (Ubuntu/Debian)

```bash
# 基础工具
sudo apt update
sudo apt install build-essential cmake git

# 图形库依赖
sudo apt install libglfw3-dev libglew-dev libglm-dev

# OpenXR（可选）
sudo apt install libopenxr-loader-dev

# 或者从源码编译 OpenXR
git clone https://github.com/KhronosGroup/OpenXR-SDK.git
cd OpenXR-SDK
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

#### Linux (Fedora)

```bash
# 基础工具
sudo dnf install gcc-c++ cmake git

# 图形库依赖
sudo dnf install glfw-devel glew-devel glm-devel

# OpenXR（可选）
sudo dnf install openxr-devel
```

#### macOS

```bash
# 使用 Homebrew
brew install cmake glfw glew glm

# OpenXR（可能需要从源码编译）
brew install openxr-loader
```

### 1.4 VR 运行时安装

**如果拥有 VR 设备**:

| 平台 | 运行时 | 安装方式 |
|------|--------|----------|
| Windows | SteamVR | Steam 客户端安装 |
| Windows | Oculus Runtime | Oculus 软件 |
| Windows | Windows Mixed Reality | Windows 自带 |
| Linux | SteamVR | Steam 客户端安装 |

**如果没有 VR 设备**:
项目提供桌面模拟模式，使用鼠标和键盘模拟 VR 输入。

## 2. 项目构建

### 2.1 获取源码

```bash
# 克隆项目
git clone https://github.com/your-username/vr-application.git
cd vr-application
```

### 2.2 构建项目

#### 使用 CMake（推荐）

```bash
# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 或者使用 vcpkg（Windows）
cmake .. -DCMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake

# 编译
cmake --build .

# 或者使用 make（Linux/macOS）
make -j$(nproc)
```

#### 使用 IDE

**Visual Studio**:
1. 打开 Visual Studio
2. 选择"打开本地文件夹"
3. 选择项目根目录
4. 等待 CMake 配置完成
5. 选择构建配置（Debug/Release）
6. 点击"生成"->"生成解决方案"

**CLion**:
1. 打开 CLion
2. 选择 "Open" 并选择项目根目录
3. 等待 CMake 配置完成
4. 点击运行按钮

### 2.3 构建选项

```cmake
# CMake 构建选项
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_EXAMPLES "Build example programs" ON)
option(USE_OPENXR "Enable OpenXR support" ON)
option(USE_DESKTOP_MODE "Enable desktop simulation mode" ON)
option(ENABLE_DEBUG_TOOLS "Enable debug visualization tools" ON)
```

**自定义构建**:
```bash
# 禁用测试，启用桌面模式
cmake .. -DBUILD_TESTS=OFF -DUSE_DESKTOP_MODE=ON

# Release 模式优化
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### 2.4 运行程序

```bash
# 运行主程序
./vr_application

# 运行示例
./examples/basic_scene
./examples/interaction_demo

# 运行测试
./tests/vr_tests
```

## 3. 核心模块解析

### 3.1 应用程序主循环

**文件**: `src/core/Application.cpp`

```cpp
// 主循环伪代码
void Application::Run() {
    while (m_isRunning) {
        // 1. 计算 deltaTime
        float deltaTime = m_timer.GetDeltaTime();

        // 2. 处理输入
        ProcessInput();

        // 3. 更新场景
        Update(deltaTime);

        // 4. 渲染
        Render();

        // 5. 交换缓冲区
        m_engine->SwapBuffers();
    }
}
```

**学习要点**:
- ⭐ 帧率控制的重要性
- ⭐ 输入处理的时机
- 💡 为什么需要 deltaTime？

### 3.2 渲染系统

**文件**: `src/rendering/Renderer.cpp`

**渲染流程**:
```
1. 清除缓冲区
2. 设置渲染状态
3. 遍历场景对象
   ├── 绑定着色器
   ├── 设置 uniform 变量
   ├── 绑定纹理
   └── 绘制网格
4. 后处理（VR 畸变校正）
5. 提交帧
```

**关键代码**:
```cpp
void Renderer::Render(const RenderObject& object) {
    // 绑定 VAO
    glBindVertexArray(object.vao);

    // 设置模型矩阵
    m_shaderProgram.SetMat4("model", object.transform.GetMatrix());

    // 设置材质
    m_shaderProgram.SetVec3("material.ambient", object.material.ambient);
    m_shaderProgram.SetVec3("material.diffuse", object.material.diffuse);
    // ...

    // 绘制
    glDrawElements(GL_TRIANGLES, object.indexCount, GL_UNSIGNED_INT, 0);
}
```

**学习要点**:
- ⭐ 渲染状态管理
- ⭐ 着色器 uniform 变量
- 💡 如何减少绘制调用？

### 3.3 VR 系统

**文件**: `src/vr/VRSystem.cpp`

**初始化流程**:
```
1. 创建 XrInstance
2. 选择 XrSystem
3. 创建 XrSession
4. 创建 XrSpace
5. 创建交换链
6. 获取视图配置
```

**帧循环**:
```cpp
void VRSystem::FrameLoop() {
    // 等待帧开始
    xrWaitFrame(m_session, &frameState);

    // 开始帧
    xrBeginFrame(m_session, &frameState);

    // 获取视图
    XrViewLocateInfo viewLocateInfo = {...};
    xrLocateViews(m_session, &viewLocateInfo, &viewState, 2, &viewCount, views);

    // 渲染每个眼睛
    for (int eye = 0; eye < 2; eye++) {
        // 设置视图矩阵
        // 设置投影矩阵
        // 渲染场景
    }

    // 结束帧
    xrEndFrame(m_session, &frameEndInfo);
}
```

**学习要点**:
- ⭐ OpenXR 会话生命周期
- ⭐ 视图定位和渲染
- 💡 如何处理会话状态变化？

### 3.4 输入系统

**文件**: `src/input/InputManager.cpp`

**输入处理流程**:
```
1. 轮询输入事件
2. 更新控制器状态
3. 处理交互
   ├── 射线检测
   ├── 碰撞检测
   └── 触发回调
4. 更新 UI 状态
```

**关键代码**:
```cpp
void InputManager::Update() {
    // 获取控制器状态
    XrActionStateGetInfo getInfo = {...};
    xrGetActionStateFloat(m_session, &getInfo, &triggerState);

    // 射线检测
    Ray ray = GetPointerRay(controllerIndex);
    HitResult hit;
    if (Raycast(ray, hit)) {
        // 处理交互
        HandleInteraction(hit);
    }
}
```

**学习要点**:
- ⭐ 输入事件处理
- ⭐ 射线检测算法
- 💡 如何实现抓取机制？

### 3.5 场景管理

**文件**: `src/scene/SceneManager.cpp`

**场景结构**:
```
Scene
├── Root Node
│   ├── Camera Node
│   ├── Light Nodes
│   └── Object Nodes
│       ├── Static Objects
│       └── Dynamic Objects
└── Resources
    ├── Meshes
    ├── Textures
    └── Materials
```

**学习要点**:
- ⭐ 场景图设计
- ⭐ 资源管理
- 💡 如何实现高效的场景遍历？

## 4. 着色器开发指南

### 4.1 着色器基础

**顶点着色器输入/输出**:
```glsl
// 输入（来自顶点缓冲区）
layout (location = 0) in vec3 aPos;      // 顶点位置
layout (location = 1) in vec3 aNormal;   // 法线
layout (location = 2) in vec2 aTexCoord; // 纹理坐标

// 输出（传递给片段着色器）
out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;
```

**片段着色器输出**:
```glsl
out vec4 FragColor;  // 最终颜色
```

### 4.2 Uniform 变量

```glsl
// 变换矩阵
uniform mat4 model;       // 模型矩阵
uniform mat4 view;        // 视图矩阵
uniform mat4 projection;  // 投影矩阵

// 材质属性
uniform vec3 materialColor;
uniform float materialShininess;

// 光源属性
uniform vec3 lightPosition;
uniform vec3 lightColor;

// 相机位置
uniform vec3 viewPos;
```

### 4.3 光照模型

**Phong 光照模型**:
```glsl
vec3 CalculateLighting(vec3 normal, vec3 fragPos) {
    // 环境光
    vec3 ambient = lightColor * 0.1;

    // 漫反射
    vec3 lightDir = normalize(lightPosition - fragPos);
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = lightColor * diff;

    // 镜面反射
    vec3 viewDir = normalize(viewPos - fragPos);
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), materialShininess);
    vec3 specular = lightColor * spec;

    return (ambient + diffuse + specular) * materialColor;
}
```

### 4.4 VR 畸变校正着色器

```glsl
// 畸变校正片段着色器
uniform sampler2D inputTexture;
uniform vec2 distortionCoefficients;

vec2 Distort(vec2 uv) {
    vec2 centered = uv - 0.5;
    float r2 = dot(centered, centered);
    float distortion = 1.0 + distortionCoefficients.x * r2 +
                       distortionCoefficients.y * r2 * r2;
    return centered * distortion + 0.5;
}

void main() {
    vec2 distortedUV = Distort(TexCoord);
    FragColor = texture(inputTexture, distortedUV);
}
```

## 5. 调试技巧

### 5.1 OpenGL 调试

**启用调试输出**:
```cpp
// 初始化时启用调试
glEnable(GL_DEBUG_OUTPUT);
glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
glDebugMessageCallback(GLDebugCallback, nullptr);

// 调试回调函数
void GLDebugCallback(GLenum source, GLenum type, GLuint id,
                     GLenum severity, GLsizei length,
                     const GLchar* message, const void* userParam) {
    std::cerr << "GL Debug: " << message << std::endl;
}
```

**常见错误检查**:
```cpp
GLenum error = glGetError();
if (error != GL_NO_ERROR) {
    std::cerr << "OpenGL Error: " << error << std::endl;
}
```

### 5.2 VR 调试

**OpenXR 验证层**:
```cpp
// 启用验证层
const char* enabledExtensions[] = {
    "XR_KHR_opengl_enable",
    "XR_EXT_debug_utils"  // 调试扩展
};

// 创建调试 messenger
XrDebugUtilsMessengerCreateInfoEXT messengerInfo = {...};
xrCreateDebugUtilsMessengerEXT(instance, &messengerInfo, &messenger);
```

**追踪数据可视化**:
```cpp
// 显示追踪数据
void DebugTracking(const VRPose& pose) {
    ImGui::Text("Position: %.2f, %.2f, %.2f",
                pose.position.x, pose.position.y, pose.position.z);
    ImGui::Text("Orientation: %.2f, %.2f, %.2f, %.2f",
                pose.orientation.x, pose.orientation.y,
                pose.orientation.z, pose.orientation.w);
}
```

### 5.3 性能分析

**帧时间测量**:
```cpp
auto frameStart = std::chrono::high_resolution_clock::now();

// ... 渲染代码 ...

auto frameEnd = std::chrono::high_resolution_clock::now();
float frameTime = std::chrono::duration<float, std::milli>(frameEnd - frameStart).count();

if (frameTime > 11.1f) {  // 90fps = 11.1ms per frame
    std::cerr << "Frame time too long: " << frameTime << "ms" << std::endl;
}
```

**GPU 性能查询**:
```cpp
GLuint query;
glGenQueries(1, &query);

glBeginQuery(GL_TIME_ELAPSED, query);
// ... 渲染代码 ...
glEndQuery(GL_TIME_ELAPSED);

GLuint64 elapsedTime;
glGetQueryObjectui64v(query, GL_QUERY_RESULT, &elapsedTime);
float gpuTime = elapsedTime / 1000000.0f;  // 转换为毫秒
```

### 5.4 调试工具

**线框渲染**:
```cpp
// 启用线框模式
glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);

// 恢复正常模式
glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
```

**碰撞体可视化**:
```cpp
void DebugDrawCollisionShape(const CollisionShape& shape) {
    // 绘制包围盒
    glLineWidth(2.0f);
    glColor3f(0.0f, 1.0f, 0.0f);  // 绿色

    glBegin(GL_LINES);
    // ... 绘制线条 ...
    glEnd();
}
```

## 6. 常见问题解答

### 6.1 编译问题

**Q: 找不到 OpenGL 头文件**
```
A: 确保安装了开发包
   Linux: sudo apt install libgl-dev
   Windows: 确保 GLEW 正确安装
```

**Q: 链接错误：undefined reference to `glfwInit'**
```
A: 确保链接了 GLFW 库
   检查 CMakeLists.txt 中的 target_link_libraries
```

**Q: OpenXR 头文件找不到**
```
A: 确保安装了 OpenXR SDK
   或者禁用 OpenXR：cmake .. -DUSE_OPENXR=OFF
```

### 6.2 运行问题

**Q: 程序启动后黑屏**
```
A: 检查以下几点：
   1. 显卡驱动是否最新
   2. OpenGL 版本是否支持（需要 4.5+）
   3. 着色器是否正确编译
```

**Q: VR 头显无画面**
```
A: 检查以下几点：
   1. VR 运行时是否启动
   2. OpenXR 会话是否创建成功
   3. 交换链是否正确创建
```

**Q: 帧率很低**
```
A: 优化建议：
   1. 减少绘制调用（实例化渲染）
   2. 降低渲染分辨率
   3. 启用视锥剔除
   4. 使用 LOD
```

### 6.3 交互问题

**Q: 手柄按钮无响应**
```
A: 检查以下几点：
   1. OpenXR action 是否正确创建
   2. action set 是否附加到 session
   3. 按钮绑定是否正确
```

**Q: 射线检测不准确**
```
A: 检查以下几点：
   1. 射线方向是否正确
   2. 碰撞体是否正确设置
   3. 检测距离是否合适
```

## 7. 最佳实践

### 7.1 代码规范

**命名规范**:
- 类名：PascalCase（如 `VRSystem`）
- 函数名：PascalCase（如 `Initialize()`）
- 变量名：camelCase（如 `frameTime`）
- 常量：UPPER_SNAKE_CASE（如 `MAX_OBJECTS`）
- 成员变量：m_ 前缀（如 `m_isRunning`）

**代码组织**:
- 头文件使用 include guard
- 实现文件包含对应的头文件
- 使用命名空间组织代码
- 保持函数简短（< 50 行）

### 7.2 性能优化

**渲染优化**:
1. 减少状态切换
2. 使用实例化渲染
3. 合批绘制调用
4. 使用纹理图集

**内存优化**:
1. 使用对象池
2. 避免频繁分配
3. 使用智能指针
4. 及时释放资源

**CPU 优化**:
1. 使用空间分区
2. 异步加载资源
3. 多线程处理
4. 缓存计算结果

### 7.3 错误处理

**原则**:
1. 早期检测错误
2. 清晰的错误信息
3. 优雅的错误恢复
4. 记录错误日志

**示例**:
```cpp
bool Initialize() {
    if (!InitializeOpenGL()) {
        LogError("Failed to initialize OpenGL");
        return false;
    }

    if (!InitializeVR()) {
        LogWarning("VR not available, using desktop mode");
        m_desktopMode = true;
    }

    return true;
}
```

## 8. 学习资源

### 8.1 官方文档
- [OpenGL 官方文档](https://www.khronos.org/registry/OpenGL-Refpages/)
- [OpenXR 规范](https://www.khronos.org/openxr/)
- [GLFW 文档](https://www.glfw.org/documentation.html)
- [GLM 文档](https://github.com/g-truc/glm)

### 8.2 教程网站
- [Learn OpenGL](https://learnopengl.com/)
- [OpenGL Tutorial](http://www.opengl-tutorial.org/)
- [OpenXR Tutorial](https://developer.oculus.com/documentation/)

### 8.3 开源项目
- [OpenXR SDK Examples](https://github.com/KhronosGroup/OpenXR-SDK-Source)
- [Three.js VR Examples](https://threejs.org/examples/#webxr_vr_sandbox)
- [Godot VR](https://github.com/GodotVR/godot_openxr)

### 8.4 书籍推荐
- 《OpenGL 编程指南》（红宝书）
- 《OpenGL 超级宝典》（蓝宝书）
- 《实时渲染》（Real-Time Rendering）
- 《VR 开发实战》

## 9. 贡献指南

### 9.1 如何贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 9.2 代码审查

**审查清单**:
- [ ] 代码符合规范
- [ ] 有适当的注释
- [ ] 包含单元测试
- [ ] 通过所有测试
- [ ] 文档已更新

### 9.3 问题报告

**报告格式**:
```
## 问题描述
简要描述问题

## 复现步骤
1. 步骤一
2. 步骤二
3. ...

## 预期行为
描述预期的行为

## 实际行为
描述实际的行为

## 环境信息
- OS: Windows 10
- GPU: NVIDIA GTX 1080
- Driver: 471.68
- VR Runtime: SteamVR 1.20.4
```

## 10. 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。