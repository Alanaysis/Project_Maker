# 音视频编解码器 (AV-Codec)

一个完整的音视频编解码器项目，涵盖音视频编解码的核心技术。

## 项目概述

本项目实现了一个全面的音视频编解码器，包含：
- 视频编解码（H.264/H.265/VP9/AV1）
- 音频编解码（AAC/MP3/Opus/Vorbis）
- 容器格式（MP4/MKV/AVI/FLV/TS）
- 流媒体协议（RTMP/RTSP/HLS/DASH/WebRTC）
- 性能优化（SIMD/多线程/GPU/硬件编解码）
- 实际应用（播放器/转码器/直播推流/视频会议）

## 核心流程

```
原始数据 → 预处理 → 编码 → 压缩 → 传输 → 解码 → 渲染
```

## 功能特性

### 视频编解码
- H.264/AVC 编解码
- H.265/HEVC 编解码
- VP8/VP9 编解码
- AV1 编解码
- 帧内预测（9/35/56种模式）
- 帧间预测（运动估计/补偿）
- 变换编码（DCT/Hadamard）
- 量化（标量/死区/自适应）
- 熵编码（CAVLC/CABAC）

### 音频编解码
- AAC 编解码（LC/HE-AAC）
- MP3 编解码（Layer III）
- Opus 编解码（SILK/CELT/混合）
- Vorbis 编解码
- 频域编码（FFT/MDCT）
- 时域编码（LPC/CELP）
- 心理声学模型

### 容器格式
- MP4 容器（复用/解复用）
- MKV 容器（复用/解复用）
- AVI 容器（复用/解复用）
- FLV 容器（复用/解复用）
- TS 容器（复用/解复用）

### 流媒体协议
- RTMP 协议（客户端/服务器）
- RTSP 协议（客户端/服务器）
- HLS 协议（客户端/服务器）
- DASH 协议（客户端/服务器）
- WebRTC（对等连接）

### 性能优化
- SIMD 优化（SSE2/AVX2/NEON）
- 多线程编码（帧级/切片级并行）
- GPU 加速（CUDA/OpenCL）
- 硬件编解码（NVENC/NVDEC/QSV/VAAPI）

### 实际应用
- 视频播放器
- 视频转码器
- 直播推流
- 视频会议

## 系统要求

- Linux/macOS/Windows
- GCC 9+ / Clang 10+ / MSVC 2019+
- CMake 3.16+
- FFmpeg 4.4+（可选）

## 快速开始

### 安装依赖

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential cmake
sudo apt install libavcodec-dev libavformat-dev libavutil-dev
sudo apt install libswscale-dev libswresample-dev
```

#### macOS
```bash
brew install cmake ffmpeg
```

### 构建项目

```bash
cd projects/av-codec
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 运行示例

```bash
# 视频编码示例
./bin/video_encoder_example

# 音频编码示例
./bin/audio_encoder_example

# 容器封装示例
./bin/container_example

# 流媒体示例
./bin/streaming_example
```

## 项目结构

```
av-codec/
├── CMakeLists.txt              # CMake构建配置
├── README.md                   # 项目说明
├── include/                    # 头文件
│   ├── video/                  # 视频编解码头文件
│   ├── audio/                  # 音频编解码头文件
│   ├── container/              # 容器格式头文件
│   ├── protocol/               # 流媒体协议头文件
│   ├── optimization/           # 性能优化头文件
│   └── application/            # 应用头文件
├── src/                        # 源代码
│   ├── video/                  # 视频编解码实现
│   ├── audio/                  # 音频编解码实现
│   ├── container/              # 容器格式实现
│   ├── protocol/               # 流媒体协议实现
│   ├── optimization/           # 性能优化实现
│   └── application/            # 应用实现
├── examples/                   # 示例程序
├── tests/                      # 测试代码
└── docs/                       # 文档
```

## 编码参数说明

### 视频编码参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| width | 视频宽度 | 1920 |
| height | 视频高度 | 1080 |
| fps | 帧率 | 30 |
| bitrate | 码率(bps) | 2000000 |
| qp | 量化参数 | 26 |
| gop_size | GOP大小 | 30 |
| max_b_frames | 最大B帧数 | 3 |
| ref_frames | 参考帧数 | 4 |

### 音频编码参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| sample_rate | 采样率 | 44100 |
| channels | 声道数 | 2 |
| bitrate | 码率(bps) | 128000 |
| profile | 编码档次 | LC |

## 学习资源

- [FFmpeg官方文档](https://ffmpeg.org/documentation.html)
- [H.264标准](https://www.itu.int/rec/T-REC-H.264)
- [H.265标准](https://www.itu.int/rec/T-REC-H.265)
- [AV1标准](https://aomediacodec.github.io/av1-spec/)
- [Opus标准](https://opus-codec.org/)

## 常见问题

### Q: 编译时找不到FFmpeg库？
A: 确保已安装FFmpeg开发包，或使用 `-DUSE_FFMPEG=OFF` 禁用FFmpeg依赖。

### Q: 编码后的视频无法播放？
A: 检查编码参数是否正确，确保容器格式与编码格式兼容。

### Q: 如何调整编码质量？
A: 可以通过调整码率、量化参数和编码预设来控制编码质量。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
