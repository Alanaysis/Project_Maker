# 音视频编解码器 (AV-Codec)

一个用于学习音视频编解码原理的简易实现项目。

## 项目概述

本项目实现了一个基础的音视频编解码器，帮助理解：
- H.264/H.265 视频编码原理
- AAC 音频编码原理
- 容器格式封装（MP4/FLV）
- 编解码完整流程

## 核心流程

```
原始数据 → 预处理 → 编码 → 压缩 → 传输 → 解码 → 渲染
```

## 功能特性

### 视频编码
- H.264 软编码支持
- 可配置编码参数（码率、分辨率、帧率）
- 支持 I/P/B 帧编码
- 运动估计和运动补偿

### 音频编码
- AAC 音频编码
- 支持多声道
- 可配置采样率和码率

### 容器封装
- MP4 格式封装
- FLV 格式封装
- 音视频流复用

## 系统要求

- Linux/macOS/Windows
- GCC 9+ / Clang 10+ / MSVC 2019+
- CMake 3.16+
- FFmpeg 4.4+ (libavcodec, libavformat, libavutil, libswscale, libswresample)

## 快速开始

### 安装依赖

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential cmake
sudo apt install libavcodec-dev libavformat-dev libavutil-dev
sudo apt install libswscale-dev libswresample-dev
sudo apt install libavdevice-dev
```

#### macOS
```bash
brew install cmake ffmpeg
```

#### Windows (vcpkg)
```powershell
vcpkg install ffmpeg
```

### 构建项目

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
```

### 使用示例

#### 视频编码示例
```bash
./build/bin/video_encoder -i input.yuv -o output.h264 \
    -w 1920 -h 1080 -f 30 -b 2000000
```

#### 音频编码示例
```bash
./build/bin/audio_encoder -i input.pcm -o output.aac \
    -r 44100 -c 2 -b 128000
```

#### 容器封装示例
```bash
./build/bin/muxer -v video.h264 -a audio.aac -o output.mp4
```

## 项目结构

```
av-codec/
├── CMakeLists.txt          # CMake构建配置
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── include/                # 头文件
│   ├── av_codec.h          # 编解码器接口
│   ├── video_encoder.h     # 视频编码器
│   ├── video_decoder.h     # 视频解码器
│   ├── audio_encoder.h     # 音频编码器
│   ├── audio_decoder.h     # 音频解码器
│   ├── muxer.h             # 复用器
│   ├── demuxer.h           # 解复用器
│   └── codec_types.h       # 类型定义
├── src/                    # 源代码
│   ├── video_encoder.cpp   # 视频编码实现
│   ├── video_decoder.cpp   # 视频解码实现
│   ├── audio_encoder.cpp   # 音频编码实现
│   ├── audio_decoder.cpp   # 音频解码实现
│   ├── muxer.cpp           # 复用器实现
│   ├── demuxer.cpp         # 解复用器实现
│   └── utils.cpp           # 工具函数
├── tests/                  # 测试代码
│   ├── test_video_codec.cpp
│   ├── test_audio_codec.cpp
│   └── test_muxer.cpp
├── examples/               # 示例程序
│   ├── video_encoder_example.cpp
│   ├── audio_encoder_example.cpp
│   └── muxer_example.cpp
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
└── build/                  # 构建输出
```

## 编码参数说明

### 视频编码参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| -w, --width | 视频宽度 | 1920 |
| -h, --height | 视频高度 | 1080 |
| -f, --fps | 帧率 | 30 |
| -b, --bitrate | 码率(bps) | 2000000 |
| -g, --gop | GOP大小 | 30 |
| --preset | 编码预设 | medium |
| --profile | 编码档次 | high |

### 音频编码参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| -r, --samplerate | 采样率 | 44100 |
| -c, --channels | 声道数 | 2 |
| -b, --bitrate | 码率(bps) | 128000 |

## 学习资源

- [FFmpeg官方文档](https://ffmpeg.org/documentation.html)
- [H.264标准](https://www.itu.int/rec/T-REC-H.264)
- [AAC标准](https://www.iso.org/standard/43345.html)

## 常见问题

### Q: 编译时找不到FFmpeg库？
A: 确保已安装FFmpeg开发包，并设置正确的PKG_CONFIG_PATH。

### Q: 编码后的视频无法播放？
A: 检查编码参数是否正确，确保容器格式与编码格式兼容。

### Q: 如何调整编码质量？
A: 可以通过调整码率、预设和量化参数来控制编码质量。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
