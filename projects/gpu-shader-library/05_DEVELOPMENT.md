# 开发手册

## 环境配置

### 系统要求

#### 操作系统
- Windows 10/11
- macOS 10.15+
- Ubuntu 20.04+

#### 硬件要求
- OpenGL 4.5+ 兼容 GPU
- 4GB+ 显存推荐
- 8GB+ 系统内存

### 开发工具

#### 编译器
- GCC 10+
- Clang 12+
- MSVC 2019+

#### IDE (可选)
- Visual Studio 2019+
- CLion
- VS Code + C++ 扩展

#### 构建工具
- CMake 3.20+
- Git

### 依赖库

| 库 | 版本 | 用途 |
|----|------|------|
| GLFW | 3.3+ | 窗口管理 |
| GLAD | 0.1.36 | OpenGL 加载 |
| GLM | 0.9.9+ | 数学库 |

## 编译说明

### Linux/macOS

```bash
# 克隆项目
git clone <repository-url>
cd gpu-shader-library

# 创建构建目录
mkdir build && cd build

# 配置
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
make -j$(nproc)

# 运行示例
./bin/demo_basic_rendering
```

### Windows (Visual Studio)

```powershell
# 克隆项目
git clone <repository-url>
cd gpu-shader-library

# 创建构建目录
mkdir build
cd build

# 配置 (选择 Visual Studio 版本)
cmake .. -G "Visual Studio 17 2022"

# 打开解决方案
start GPUShaderLibrary.sln
```

### Windows (MinGW)

```bash
mkdir build && cd build
cmake .. -G "MinGW Makefiles"
mingw32-make -j$(nproc)
```

## CMake 配置选项

```cmake
# 构建示例程序
cmake -DBUILD_DEMOS=ON ..

# 构建测试
cmake -DBUILD_TESTS=ON ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..
```

## 运行方式

### 基础渲染示例

```bash
./bin/demo_basic_rendering

# 控制说明:
# W/A/S/D - 相机移动
# 鼠标    - 相机旋转
# ESC     - 退出
```

### PBR 渲染示例

```bash
./bin/demo_pbr

# 功能:
# - PBR 材质演示
# - IBL 环境光照
# - 多种材质预设
```

### 后处理示例

```bash
./bin/demo_postprocess

# 效果切换:
# 1 - 高斯模糊
# 2 - 运动模糊
# 3 - 景深
# 4 - Bloom
# 5 - 色调映射
```

### 粒子系统示例

```bash
./bin/demo_particles

# 功能:
# - GPU 粒子模拟
# - 多种发射器
# - 物理碰撞
```

### 水面渲染示例

```bash
./bin/demo_water

# 功能:
# - Gerstner 波浪
# - 反射/折射
# - 焦散效果
```

## 调试指南

### OpenGL 调试

```cpp
// 启用 OpenGL 调试输出
glEnable(GL_DEBUG_OUTPUT);
glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
glDebugMessageCallback(glDebugCallback, nullptr);

// 调试回调函数
void GLAPIENTRY glDebugCallback(GLenum source, GLenum type, GLuint id,
                                 GLenum severity, GLsizei length,
                                 const GLchar* message, const void* userParam) {
    std::cerr << "GL Debug: " << message << std::endl;
}
```

### 着色器调试

#### 使用 RenderDoc
1. 启动 RenderDoc
2. 捕获帧
3. 检查着色器状态
4. 查看中间结果

#### 输出调试
```glsl
// 输出中间变量
FragColor = vec4(debugValue, debugValue, debugValue, 1.0);

// 输出法线
FragColor = vec4(normal * 0.5 + 0.5, 1.0);

// 输出深度
FragColor = vec4(vec3(gl_FragCoord.z), 1.0);
```

### 常见问题

#### 着色器编译错误
```bash
# 检查着色器版本
# 确保 #version 声明正确
# 检查扩展支持
```

#### 链接错误
```bash
# 确保输入输出匹配
# 检查 Uniform 名称
# 验证顶点属性布局
```

#### 渲染错误
```bash
# 检查深度测试
# 验证混合模式
# 确认纹理绑定
```

## 性能分析

### GPU 性能工具

#### NVIDIA Nsight
```bash
# 安装 NVIDIA Nsight Graphics
# 启动分析
nsight .
```

#### AMD GPU PerfStudio
```bash
# 安装 AMD GPU PerfStudio
# 性能计数器分析
```

#### RenderDoc
```bash
# 帧捕获分析
# GPU 时间测量
# 内存使用追踪
```

### 性能指标

#### 帧率目标
- 60 FPS (实时渲染)
- 30 FPS (复杂场景)
- 120 FPS (VR 应用)

#### GPU 时间
- 顶点着色: < 2ms
- 片段着色: < 5ms
- 后处理: < 3ms
- 总计: < 16ms (60 FPS)

### 优化技巧

#### 减少绘制调用
```cpp
// 使用实例化渲染
glDrawElementsInstanced(GL_TRIANGLES, count, GL_UNSIGNED_INT, 0, instanceCount);

// 使用间接渲染
glMultiDrawElementsIndirect(GL_TRIANGLES, GL_UNSIGNED_INT, commands, drawCount, stride);
```

#### 减少状态切换
```cpp
// 批处理相同材质的物体
// 使用纹理图集
// 减少着色器切换
```

#### 优化着色器
```glsl
// 使用 mediump 精度 (移动设备)
mediump vec3 color;

// 避免动态分支
float factor = step(threshold, value);

// 使用内置函数
float result = dot(normal, lightDir);  // 比手写点积快
```

## 贡献指南

### 代码规范

#### 命名规范
- 文件名: 小写 + 下划线
- 类名: PascalCase
- 函数名: camelCase
- 常量: UPPER_SNAKE_CASE

#### 注释规范
```glsl
/**
 * 函数/着色器说明
 *
 * @param paramName 参数说明
 * @return 返回值说明
 */
```

### 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
style: 格式
refactor: 重构
test: 测试
chore: 构建/工具
```

### Pull Request 流程

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 编写测试
5. 更新文档
6. 提交 PR

## 许可证

MIT License

Copyright (c) 2024 GPU Shader Library

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
