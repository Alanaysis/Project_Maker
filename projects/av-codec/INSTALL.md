# 安装指南

## 系统要求

- Linux/macOS/Windows
- GCC 9+ / Clang 10+ / MSVC 2019+
- CMake 3.16+
- FFmpeg 4.4+ 开发库

## 依赖安装

### Ubuntu/Debian

```bash
# 更新包列表
sudo apt update

# 安装构建工具
sudo apt install build-essential cmake pkg-config

# 安装FFmpeg开发库
sudo apt install libavcodec-dev libavformat-dev libavutil-dev
sudo apt install libswscale-dev libswresample-dev
sudo apt install libavdevice-dev libavfilter-dev

# 验证安装
pkg-config --libs libavcodec libavformat libavutil
```

### CentOS/RHEL/Fedora

```bash
# 安装构建工具
sudo yum install gcc-c++ cmake pkgconfig

# 安装FFmpeg开发库
sudo yum install ffmpeg-devel

# 或者在Fedora上
sudo dnf install ffmpeg-devel
```

### macOS

```bash
# 安装Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install cmake pkg-config ffmpeg
```

### Windows

#### 使用vcpkg

```powershell
# 安装vcpkg (如果没有)
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装FFmpeg
.\vcpkg install ffmpeg:x64-windows

# 配置项目
cmake -B build -DCMAKE_TOOLCHAIN_FILE=[vcpkg root]/scripts/buildsystems/vcpkg.cmake
```

#### 使用MSYS2

```bash
# 安装MSYS2后
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-ffmpeg
```

## 构建项目

### Linux/macOS

```bash
# 克隆项目
cd projects/av-codec

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)

# 运行测试
make test

# 安装 (可选)
sudo make install
```

### Windows (Visual Studio)

```powershell
# 配置
cmake -B build -G "Visual Studio 17 2022"

# 编译
cmake --build build --config Release

# 运行测试
cd build
ctest -C Release
```

## 验证安装

### 检查FFmpeg版本

```bash
ffmpeg -version
```

### 检查开发库

```bash
pkg-config --modversion libavcodec
pkg-config --modversion libavformat
pkg-config --modversion libavutil
```

### 运行示例

```bash
# 进入构建目录
cd build/bin

# 运行视频编码示例
./video_encoder_example

# 运行音频编码示例
./audio_encoder_example
```

## 常见问题

### 1. CMake找不到FFmpeg

**问题**: `Package 'libavcodec' not found`

**解决方案**:
```bash
# 设置PKG_CONFIG_PATH
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH

# 或者手动指定路径
cmake -DCMAKE_PREFIX_PATH=/usr/local ..
```

### 2. 链接错误

**问题**: `undefined reference to av_*`

**解决方案**:
```bash
# 确保安装了开发库
sudo apt install libavcodec-dev

# 或者手动指定库路径
cmake -DCMAKE_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu ..
```

### 3. 头文件找不到

**问题**: `fatal error: libavcodec/avcodec.h: No such file`

**解决方案**:
```bash
# 安装开发包
sudo apt install libavcodec-dev

# 或者手动指定头文件路径
cmake -DCMAKE_INCLUDE_PATH=/usr/include ..
```

### 4. 编码器未找到

**问题**: `H.264 encoder not found`

**解决方案**:
```bash
# 检查FFmpeg是否支持该编码器
ffmpeg -encoders | grep h264

# 如果没有，可能需要重新编译FFmpeg
# 或者使用其他编码器
```

### 5. 内存错误

**问题**: Segmentation fault

**解决方案**:
```bash
# 使用AddressSanitizer编译
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make

# 运行程序查看错误信息
./test_video_codec
```

## 高级配置

### 自定义FFmpeg路径

```bash
# 如果FFmpeg安装在非标准位置
cmake -DCMAKE_PREFIX_PATH=/opt/ffmpeg \
      -DCMAKE_LIBRARY_PATH=/opt/ffmpeg/lib \
      -DCMAKE_INCLUDE_PATH=/opt/ffmpeg/include ..
```

### 启用调试

```bash
# Debug模式
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

### 启用优化

```bash
# Release模式
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

### 交叉编译

```bash
# 使用工具链文件
cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake ..
```

## 获取帮助

如果遇到问题，请：

1. 检查本文件的常见问题部分
2. 查看FFmpeg官方文档
3. 搜索相关错误信息
4. 在GitHub上提交Issue
