# 快速开始指南

## 1. 环境准备

### 1.1 系统要求

**操作系统**:
- Windows 10/11
- Linux (Ubuntu 20.04+, Fedora 36+)
- macOS (有限支持)

**硬件要求**:
- CPU: Intel i5 或 AMD Ryzen 5 以上
- GPU: 支持 OpenGL 4.5 的显卡
- RAM: 8GB 以上
- VR 设备（可选，有桌面模拟模式）

### 1.2 安装依赖

#### Windows

**使用 vcpkg（推荐）**:
```powershell
# 安装 vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装依赖
.\vcpkg install glfw3 glew glm
```

**或者手动下载**:
1. GLFW: https://www.glfw.org/download
2. GLEW: http://glew.sourceforge.net/
3. GLM: https://github.com/g-truc/glm

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install build-essential cmake git
sudo apt install libglfw3-dev libglew-dev libglm-dev
```

#### Linux (Fedora)

```bash
sudo dnf install gcc-c++ cmake git
sudo dnf install glfw-devel glew-devel glm-devel
```

#### macOS

```bash
brew install cmake glfw glew glm
```

## 2. 获取源码

```bash
# 克隆项目
git clone <repository-url>
cd vr-application
```

## 3. 构建项目

### 3.1 使用构建脚本（推荐）

```bash
# Linux/macOS
./build.sh

# 或者使用 Debug 模式
./build.sh --debug

# 查看所有选项
./build.sh --help
```

### 3.2 手动构建

```bash
# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译
cmake --build . -j4

# 或者使用 make
make -j4
```

### 3.3 Windows 特殊说明

**使用 vcpkg**:
```powershell
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake
cmake --build . --config Release
```

**使用 Visual Studio**:
1. 打开 Visual Studio
2. 选择"打开本地文件夹"
3. 选择项目根目录
4. 等待 CMake 配置完成
5. 点击"生成"->"生成解决方案"

## 4. 运行程序

### 4.1 运行主程序

```bash
# Linux/macOS
./build/bin/vr_application

# Windows
build\bin\Release\vr_application.exe
```

### 4.2 运行示例

```bash
# 基本场景示例
./build/bin/examples/basic_scene

# 交互演示示例
./build/bin/examples/interaction_demo
```

### 4.3 命令行选项

```bash
./vr_application [选项]

选项:
  --vr              启用 VR 模式
  --desktop         启用桌面模式（默认）
  --width <值>      设置窗口宽度
  --height <值>     设置窗口高度
  --fullscreen      启用全屏
  --no-vsync        禁用垂直同步
  --help            显示帮助信息
```

## 5. 基本操作

### 5.1 桌面模式控制

| 按键 | 功能 |
|------|------|
| W | 前进 |
| S | 后退 |
| A | 左移 |
| D | 右移 |
| Space | 上升 |
| Shift | 下降 |
| 鼠标移动 | 视角旋转 |
| F1 | 切换调试信息 |
| F2 | 切换线框模式 |
| F3 | 切换包围盒显示 |
| F4 | 切换网格显示 |
| ESC | 退出 |

### 5.2 VR 模式控制

| 按钮 | 功能 |
|------|------|
| 触发器 | 选择/抓取 |
| 抓取按钮 | 抓取物体 |
| 摇杆 | 移动 |
| 菜单按钮 | 打开菜单 |

## 6. 项目结构

```
vr-application/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   ├── rendering/         # 渲染相关
│   ├── vr/               # VR 相关
│   ├── input/            # 输入处理
│   └── scene/            # 场景管理
├── include/               # 头文件
├── shaders/               # 着色器
├── tests/                 # 单元测试
├── examples/              # 示例程序
├── docs/                  # 文档
└── assets/                # 资源文件
```

## 7. 学习路径

### 7.1 入门阶段

1. **运行示例程序**
   - 编译并运行 `basic_scene`
   - 尝试不同的控制操作
   - 观察渲染效果

2. **阅读源代码**
   - 从 `main.cpp` 开始
   - 理解应用程序生命周期
   - 学习渲染流程

3. **修改示例**
   - 尝试修改颜色
   - 添加新的物体
   - 调整光照参数

### 7.2 进阶阶段

1. **理解渲染管线**
   - 学习着色器代码
   - 理解矩阵变换
   - 掌握光照模型

2. **学习 VR 原理**
   - 理解立体渲染
   - 学习头部追踪
   - 掌握交互设计

3. **性能优化**
   - 学习渲染优化技巧
   - 理解批处理和实例化
   - 掌握性能分析工具

### 7.3 高级阶段

1. **扩展功能**
   - 添加新的几何体
   - 实现物理系统
   - 添加音频支持

2. **深入研究**
   - 学习 OpenXR 标准
   - 研究高级渲染技术
   - 探索 VR 交互设计

## 8. 常见问题

### Q: 编译时找不到 OpenGL 头文件

**A**: 确保安装了开发包
```bash
# Linux
sudo apt install libgl-dev

# 或者
sudo apt install mesa-common-dev
```

### Q: 链接时找不到 GLFW

**A**: 确保 GLFW 已正确安装
```bash
# Linux
sudo apt install libglfw3-dev

# 或者使用 vcpkg
vcpkg install glfw3
```

### Q: 运行时黑屏

**A**: 检查以下几点：
1. 显卡驱动是否最新
2. OpenGL 版本是否支持（需要 4.5+）
3. 着色器是否正确编译

### Q: 帧率很低

**A**: 优化建议：
1. 降低渲染分辨率
2. 减少绘制调用
3. 启用视锥剔除
4. 使用 Release 模式编译

### Q: 如何启用 VR 模式

**A**: 需要：
1. 支持 OpenXR 的 VR 头显
2. 安装 VR 运行时（如 SteamVR）
3. 使用 `--vr` 参数启动程序

## 9. 调试技巧

### 9.1 启用调试输出

```cpp
// 在代码中启用 OpenGL 调试
glEnable(GL_DEBUG_OUTPUT);
glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);
```

### 9.2 使用 RenderDoc

1. 下载 RenderDoc: https://renderdoc.org/
2. 启动程序时附加 RenderDoc
3. 捕获帧进行分析

### 9.3 性能分析

```bash
# Linux 使用 perf
perf record ./vr_application
perf report

# 使用 Valgrind 检测内存泄漏
valgrind --leak-check=full ./vr_application
```

## 10. 下一步

1. **阅读文档**: 查看 `docs/` 目录下的详细文档
2. **学习笔记**: 参考 `LEARNING_NOTES.md` 进行学习
3. **修改代码**: 尝试修改示例代码
4. **添加功能**: 实现新的功能模块
5. **分享经验**: 与其他学习者交流

## 11. 获取帮助

- 查看项目文档
- 搜索 GitHub Issues
- 加入社区讨论
- 阅读参考资料

## 12. 参考资源

- [OpenGL 教程](https://learnopengl.com/)
- [OpenXR 文档](https://www.khronos.org/openxr/)
- [VR 开发最佳实践](https://developer.oculus.com/documentation/)
- [GLM 文档](https://github.com/g-truc/glm)