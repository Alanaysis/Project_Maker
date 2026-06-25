# 开发手册

## 1. 编译说明

### 1.1 环境要求

**编译器**
- GCC 8.0+ (推荐 GCC 10+)
- Clang 7.0+ (推荐 Clang 12+)
- MSVC 2019+ (Visual Studio 2019)

**构建工具**
- CMake 3.16+
- Make (Linux/macOS) 或 Ninja

**操作系统**
- Linux (Ubuntu 20.04+, Fedora 32+)
- macOS 10.15+
- Windows 10 (MSVC 或 MinGW)

### 1.2 依赖安装

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install build-essential cmake
# 可选：ALSA 开发库（用于音频输出）
sudo apt install libasound2-dev
```

**Fedora/RHEL**
```bash
sudo dnf install gcc-c++ cmake make
# 可选
sudo dnf install alsa-lib-devel
```

**macOS**
```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 CMake（使用 Homebrew）
brew install cmake
```

**Windows**
```bash
# 使用 vcpkg 安装依赖
vcpkg install cmake

# 或使用 Visual Studio Installer 安装 C++ 开发工具
```

### 1.3 编译步骤

**基本编译**
```bash
# 进入项目目录
cd projects/audio-engine

# 创建构建目录
mkdir build
cd build

# 配置（Release 模式）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 编译（使用所有核心）
make -j$(nproc)

# 或使用 Ninja（更快）
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
ninja
```

**Debug 模式编译**
```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```

**自定义安装路径**
```bash
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc)
sudo make install
```

### 1.4 CMake 配置选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | Release | 构建类型（Debug/Release） |
| `CMAKE_INSTALL_PREFIX` | /usr/local | 安装路径 |
| `BUILD_TESTS` | ON | 是否构建测试 |
| `BUILD_EXAMPLES` | ON | 是否构建示例 |

## 2. 运行方式

### 2.1 运行示例程序

所有示例程序位于 `build/bin/` 目录。

**音频基础示例**
```bash
# 采样原理演示
./bin/basic_sampling

# 量化处理演示
./bin/basic_quantization

# 采样率转换
./bin/basic_sample_rate

# 位深度处理
./bin/basic_bit_depth

# 声道处理
./bin/basic_channels
```

**编解码示例**
```bash
# PCM 编解码
./bin/pcm_codec

# WAV 文件读写
./bin/wav_codec

# MP3 概念演示
./bin/mp3_codec

# AAC 概念演示
./bin/aac_codec

# Opus 概念演示
./bin/opus_codec
```

**音频处理示例**
```bash
# 音量调节
./bin/processing_volume

# 淡入淡出
./bin/processing_fade

# 混音器
./bin/processing_mixer

# 均衡器
./bin/processing_equalizer

# 压缩器
./bin/processing_compressor

# 限幅器
./bin/processing_limiter
```

**音频效果示例**
```bash
# 混响效果
./bin/effects_reverb

# 延迟效果
./bin/effects_delay

# 合唱效果
./bin/effects_chorus

# 失真效果
./bin/effects_distortion

# 降噪效果
./bin/effects_noise_reduction
```

**音频分析示例**
```bash
# FFT 分析
./bin/analysis_fft

# 频谱分析
./bin/analysis_spectrum

# 节奏检测
./bin/analysis_rhythm

# 音高检测
./bin/analysis_pitch

# 特征提取
./bin/analysis_features
```

**音频合成示例**
```bash
# 波形合成
./bin/synthesis_waveform

# FM 合成
./bin/synthesis_fm

# 减法合成
./bin/synthesis_subtractive

# 采样合成
./bin/synthesis_sampler
```

**实际应用示例**
```bash
# 音频播放器
./bin/app_player

# 音频编辑器
./bin/app_editor

# 音频分析工具
./bin/app_analyzer

# 音频合成器
./bin/app_synthesizer
```

### 2.2 输出文件

大部分示例会生成 WAV 文件，可以使用任何音频播放器播放：

```bash
# 生成的文件位于当前目录
ls *.wav

# 使用命令行播放（Linux）
aplay output.wav

# 使用命令行播放（macOS）
afplay output.wav
```

### 2.3 预期输出

每个示例程序都会：
1. 打印处理过程信息
2. 生成输出文件（通常是 WAV）
3. 显示处理结果统计

示例输出：
```
=== Audio Sampling Demo ===
Generating sine wave: 440 Hz, 44100 Hz sample rate, 1.0 seconds
Samples generated: 44100
Peak amplitude: 1.0
RMS level: 0.707
Output saved to: sampling_440hz.wav
```

## 3. 开发指南

### 3.1 代码风格

**命名规范**
- 类名：PascalCase（如 `AudioBuffer`）
- 函数名：snake_case（如 `process_audio`）
- 变量名：snake_case（如 `sample_rate`）
- 常量：UPPER_SNAKE_CASE（如 `MAX_AMPLITUDE`）
- 文件名：snake_case.cpp（如 `wav_codec.cpp`）

**代码组织**
```cpp
// 1. 包含头文件
#include "audio_engine.h"
#include <iostream>
#include <vector>

// 2. 命名空间
namespace audio {

// 3. 类定义
class MyClass {
public:
    // 公共接口
private:
    // 私有成员
};

// 4. 函数实现
void my_function() {
    // 实现
}

} // namespace audio

// 5. main 函数
int main() {
    // 程序入口
    return 0;
}
```

### 3.2 添加新功能

**步骤 1：创建源文件**
```bash
# 在相应目录创建文件
touch src/basic/new_feature.cpp
```

**步骤 2：实现功能**
```cpp
// src/basic/new_feature.cpp
#include "audio_engine.h"
#include <iostream>

void demo_new_feature() {
    // 实现
}

int main() {
    demo_new_feature();
    return 0;
}
```

**步骤 3：更新 CMakeLists.txt**
```cmake
# 在 CMakeLists.txt 中添加
add_executable(new_feature src/basic/new_feature.cpp)
target_link_libraries(new_feature PRIVATE audio_engine)
```

**步骤 4：编译测试**
```bash
cd build
make new_feature
./bin/new_feature
```

### 3.3 调试技巧

**启用调试输出**
```cpp
#define AUDIO_DEBUG 1

#if AUDIO_DEBUG
    #define DEBUG_LOG(x) std::cout << "[DEBUG] " << x << std::endl
#else
    #define DEBUG_LOG(x)
#endif
```

**使用断言**
```cpp
#include <cassert>

void process_audio(AudioBuffer& buffer) {
    assert(!buffer.samples.empty() && "Buffer must not be empty");
    assert(buffer.sample_rate > 0 && "Sample rate must be positive");
    // ...
}
```

**内存检查（Linux）**
```bash
# 使用 Valgrind 检查内存泄漏
valgrind --leak-check=full ./bin/your_program

# 使用 Address Sanitizer
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make
./bin/your_program
```

## 4. 测试

### 4.1 运行测试

```bash
cd build
make test
# 或
ctest --output-on-failure
```

### 4.2 编写测试

```cpp
// tests/test_example.cpp
#include "audio_engine.h"
#include <cassert>
#include <cmath>

void test_audio_buffer() {
    AudioBuffer buffer;
    buffer.sample_rate = 44100;
    buffer.channels = 1;
    buffer.samples = {0.5f, -0.5f, 0.0f};

    assert(buffer.num_samples() == 3);
    assert(std::abs(buffer.duration() - 3.0/44100) < 1e-6);

    std::cout << "test_audio_buffer passed" << std::endl;
}

int main() {
    test_audio_buffer();
    return 0;
}
```

## 5. 常见问题

### 5.1 编译错误

**问题**: `fatal error: audio_engine.h: No such file or directory`
**解决**: 确保在 build 目录中运行 cmake，检查 include 路径

**问题**: `error: 'std::filesystem' is not available`
**解决**: 添加 `-lstdc++fs` 链接选项，或使用 GCC 9+

### 5.2 运行时错误

**问题**: 段错误（Segmentation fault）
**解决**: 检查数组越界，使用调试模式编译

**问题**: 音频输出全为零
**解决**: 检查采样率、振幅设置

### 5.3 性能问题

**问题**: 处理速度慢
**解决**: 使用 Release 模式编译，检查算法复杂度

## 6. 项目结构说明

```
audio-engine/
├── include/
│   └── audio_engine.h      # 统一头文件
├── src/
│   ├── basic/              # 音频基础（5个示例）
│   ├── codec/              # 编解码（5个示例）
│   ├── processing/         # 音频处理（6个示例）
│   ├── effects/            # 音频效果（5个示例）
│   ├── analysis/           # 音频分析（5个示例）
│   ├── synthesis/          # 音频合成（4个示例）
│   └── apps/               # 实际应用（4个示例）
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
└── docs/                   # 文档
    ├── 01_RESEARCH.md      # 调研文档
    ├── 02_REQUIREMENTS.md  # 需求分析
    ├── 03_DESIGN.md        # 技术设计
    ├── 04_PRODUCT.md       # 产品思考
    └── 05_DEVELOPMENT.md   # 开发手册（本文档）
```
